#!/usr/bin/env python3
"""Probe live read-only; host menyisipkan REPORT_URL dan MODE sebelum file ini.

Setiap checks[name] berisi ok dan details atau error. Report hanya sukses bila
checks tidak kosong dan semua check sukses. Tiap tahap dibatasi 60 detik;
subprocess dibatasi 8 detik atau sisa deadline, mana yang lebih kecil.
Probe tidak membuka aplikasi maupun mengirim input. Jangan kirim judul window,
isi journal, nama koneksi/SSID, environment lengkap, atau identitas serial VM.
"""

import ipaddress
import json
import os
from pathlib import Path
import pwd
import re
import shlex
import stat
import subprocess
import sys
import time
import urllib.request


STAGE_TIMEOUT = 60.0
COMMAND_TIMEOUT = 8.0
REPORT_TIMEOUT = 5.0


class Probe:
    def __init__(self, mode, report_url):
        self.mode = mode
        self.report_url = report_url
        self.stage = "started"
        self.started = time.monotonic()
        self.deadline = self.started + STAGE_TIMEOUT
        self.checks = {}
        self.metrics = {}

    def begin(self, stage):
        self.stage = stage
        self.started = time.monotonic()
        self.deadline = self.started + STAGE_TIMEOUT
        self.checks = {}
        self.metrics = {}

    def remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("stage deadline exceeded (60 seconds)")
        return remaining

    def run(self, *args):
        timeout = min(COMMAND_TIMEOUT, self.remaining())
        try:
            result = subprocess.run(
                args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, encoding="utf-8",
                errors="replace", timeout=timeout, check=False,
                env={**os.environ, "LC_ALL": "C", "SYSTEMD_COLORS": "0"},
            )
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"{args[0]} exceeded {timeout:.1f} seconds") from None
        if result.returncode:
            # Output command bisa mengandung nama koneksi, journal, atau rahasia.
            raise RuntimeError(f"{args[0]} exited with status {result.returncode}")
        return result.stdout.strip()

    def check(self, name, function):
        try:
            self.remaining()
            ok, details = function()
            self.remaining()
            self.checks[name] = {"ok": bool(ok), "details": details}
        except Exception as error:
            self.checks[name] = {
                "ok": False, "error": f"{type(error).__name__}: {error}",
            }

    def report(self):
        payload = {
            "stage": self.stage, "mode": self.mode,
            "ok": bool(self.checks) and all(c["ok"] for c in self.checks.values()),
            "checks": self.checks, "metrics": self.metrics,
            "elapsed_seconds": round(time.monotonic() - self.started, 3),
            "deadline_seconds": STAGE_TIMEOUT,
        }
        for name, check in self.checks.items():
            print(f"  {'PASS' if check['ok'] else 'FAIL'} {name}")
        if self.stage == "baseline" and self.metrics.get("kernel_release"):
            print(f"Kernel: {self.metrics['kernel_release']}")
        passed = sum(check["ok"] for check in self.checks.values())
        print(
            f"ConstOS {self.mode} / {self.stage}: "
            f"{'PASS' if payload['ok'] else 'FAIL'} "
            f"({passed}/{len(self.checks)} checks, {payload['elapsed_seconds']:.1f}s)",
            flush=True,
        )
        request = urllib.request.Request(
            self.report_url, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        # Bypass proxy environment: evidence selalu ke server host QEMU.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=REPORT_TIMEOUT) as response:
            if not 200 <= response.status < 300:
                raise RuntimeError("report server rejected evidence")
        return payload["ok"]

def read_text(path):
    return Path(path).read_text(encoding="utf-8").strip()


def unit_state(probe, unit, expected):
    state = probe.run("systemctl", "show", "--property=ActiveState", "--value", unit)
    return state == expected, {"unit": unit, "active_state": state, "expected": expected}


def release_identity():
    values = {}
    for line in read_text("/etc/os-release").splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key] = shlex.split(value)[0] if value else ""
    return values.get("ID") == "constos", {
        key: values.get(key) for key in ("ID", "NAME", "BUILD_ID")
    }


def live_identity():
    uid, euid = os.getuid(), os.geteuid()
    user = pwd.getpwuid(uid).pw_name
    return user == "liveuser" and uid != 0 and euid == uid, {
        "user": user, "uid": uid, "euid": euid,
    }


def system_links():
    base = Path("/etc/systemd/system")
    expected = {
        "default.target": "/usr/lib/systemd/system/graphical.target",
        "display-manager.service": "/usr/lib/systemd/system/sddm.service",
        "multi-user.target.wants/NetworkManager.service":
            "/usr/lib/systemd/system/NetworkManager.service",
    }
    details = {}
    for relative, destination in expected.items():
        path = base / relative
        is_link = path.is_symlink()
        resolved = str(path.resolve(strict=True)) if is_link else None
        details[relative] = {
            "is_symlink": is_link,
            "target": os.readlink(path) if is_link else None,
            "resolved": resolved, "expected": destination,
            "ok": is_link and resolved == destination and path.is_file(),
        }
    return all(item["ok"] for item in details.values()), details


def kernel(probe):
    release = probe.run("uname", "-r")
    package = probe.run("pacman", "-Q", "linux-cachyos-bore")
    bore_path = Path("/proc/sys/kernel/sched_bore")
    enabled = read_text(bore_path) if bore_path.exists() else None
    probe.metrics["kernel_release"] = release
    return "bore" in release.lower() and (enabled is None or enabled == "1"), {
        "release": release, "package": package, "sched_bore": enabled,
    }


def package_versions(probe):
    packages = probe.run("pacman", "-Q").splitlines()
    valid = bool(packages) and all(len(line.split()) == 2 for line in packages)
    probe.metrics["packages"] = packages
    version = probe.run("cage", "-v")
    probe.metrics["cage_version"] = version
    return valid and bool(version), {"package_count": len(packages), "cage": version}


def installer_runtime(probe):
    version = probe.run("constos-tui", "--version")
    probe.metrics["installer_version"] = version
    return bool(re.fullmatch(r"constos-tui [0-9.]+", version)), {"version": version}


def constd_snapshot(probe):
    name = "org.constos.Monitor1"
    busctl = ("busctl", "--user", "--json=short", "call")
    reply = json.loads(probe.run(*busctl, name, "/org/constos/Monitor1", name, "GetSnapshot"))
    snapshot = json.loads(reply["data"][0])
    owner = json.loads(probe.run(
        *busctl, "org.freedesktop.DBus", "/org/freedesktop/DBus",
        "org.freedesktop.DBus", "GetConnectionUnixUser", "s", name,
    ))["data"][0]
    total_kb = int(read_text("/proc/meminfo").splitlines()[0].split()[1])
    valid = (
        reply["type"] == "s"
        and owner == os.getuid() != 0
        and snapshot["cpu"]["kernel_release"] == os.uname().release
        and snapshot["memory"]["mem_total_kb"] == total_kb
        and snapshot["processes"]["total"] > 0
    )
    return valid, {"service": name, "same_user": owner == os.getuid(), "mem_total_kb": total_kb}


def live_sessions():
    sessions = sorted(entry.name for entry in Path("/usr/share/wayland-sessions").glob("*.desktop"))
    return sessions == ["constos-installer.desktop"], {"sessions": sessions}


def boot_metadata(probe):
    cmdline = shlex.split(read_text("/proc/cmdline"))
    sensitive = re.compile(r"password|passwd|token|secret|credential|ssid|(?:^|[._-])key", re.I)
    safe_cmdline = []
    for arg in cmdline:
        key, sep, value = arg.partition("=")
        safe_cmdline.append(key + "=<redacted>" if sep and sensitive.search(key) else arg)
    probe.metrics["cmdline"] = " ".join(safe_cmdline)
    boot_id = read_text("/proc/sys/kernel/random/boot_id")
    probe.metrics["boot_id"] = boot_id
    uname = os.uname()
    memory = next(
        line.split()[1] for line in read_text("/proc/meminfo").splitlines()
        if line.startswith("MemTotal:")
    )
    cpu_model = next((
        line.split(":", 1)[1].strip()
        for line in read_text("/proc/cpuinfo").splitlines()
        if line.startswith("model name")
    ), None)
    dmi = {}
    for key in ("sys_vendor", "product_name", "product_version"):
        path = Path("/sys/class/dmi/id") / key
        if path.exists() and os.access(path, os.R_OK):
            dmi[key] = read_text(path)
    probe.metrics["vm_capabilities"] = {
        "architecture": uname.machine, "cpu_count": os.cpu_count(),
        "cpu_model": cpu_model, "mem_total_kib": int(memory), "dmi": dmi,
        "virtio_gpu_module": Path("/sys/module/virtio_gpu").is_dir(),
        "efi": Path("/sys/firmware/efi").is_dir(),
    }
    return bool(cmdline) and bool(re.fullmatch(r"[0-9a-f-]{36}", boot_id)), {
        "boot_id": boot_id, "cmdline_recorded": bool(cmdline),
    }


def failed_units(probe):
    output = probe.run("systemctl", "--failed", "--no-legend", "--plain", "--no-pager")
    units = [line.split()[0] for line in output.splitlines() if line.strip()]
    return not units, {"failed_units": units}


def ipv4(value):
    address = ipaddress.IPv4Address(value)
    if address.is_loopback or address.is_link_local or address.is_unspecified or address.is_multicast:
        raise ValueError("IPv4 address is not usable for the VM network")
    return address


def network(probe):
    output = probe.run("nmcli", "--terse", "--escape", "no", "--fields", "DEVICE,TYPE,STATE", "device", "status")
    devices = []
    for line in output.splitlines():
        interface, kind, state = line.split(":", 2)
        if kind == "loopback" or interface == "lo" or state != "connected":
            continue
        if not Path("/sys/class/net", interface).is_dir():
            continue
        try:
            addresses = probe.run("nmcli", "--get-values", "IP4.ADDRESS", "device", "show", interface)
            addresses = [ipaddress.IPv4Interface(value) for value in addresses.splitlines()]
            usable = [item for item in addresses if ipv4(str(item.ip))]
            options = probe.run("nmcli", "--terse", "--escape", "no", "--mode", "multiline",
                                "--fields", "DHCP4.OPTION", "device", "show", interface)
            dhcp = {}
            for option in options.splitlines():
                field, _, value = option.partition(":")
                if field.startswith("DHCP4.OPTION[") and " = " in value:
                    key, value = value.split(" = ", 1)
                    if key in ("dhcp_server_identifier", "dhcp_lease_time"):
                        dhcp[key] = value.strip()
            server = ipv4(dhcp["dhcp_server_identifier"])
            lease_seconds = int(dhcp["dhcp_lease_time"])
            ok = bool(usable) and lease_seconds > 0
            devices.append({
                "interface": interface, "type": kind, "state": state,
                "ipv4": [str(item) for item in usable],
                "dhcp_server_ipv4": str(server), "dhcp_lease_seconds": lease_seconds,
                "ok": ok,
            })
        except Exception as error:
            devices.append({"interface": interface, "type": kind, "state": state,
                            "ok": False, "error": f"{type(error).__name__}: {error}"})
    return any(device["ok"] for device in devices), {
        "devices": devices, "scope": "local IPv4/DHCP only; internet not tested",
    }


def zram():
    devices = []
    for line in read_text("/proc/swaps").splitlines()[1:]:
        fields = line.split()
        name = Path(fields[0]).name
        if not re.fullmatch(r"zram\d+", name):
            continue
        base = Path("/sys/block") / name
        algorithms = read_text(base / "comp_algorithm")
        selected = re.search(r"\[([^]]+)\]", algorithms)
        selected = selected.group(1) if selected else None
        size = int(read_text(base / "disksize"))
        devices.append({
            "device": fields[0], "swap_kib": int(fields[2]), "disksize_bytes": size,
            "compression_algorithm": selected,
            "ok": selected == "zstd" and size > 0 and int(fields[2]) > 0,
        })
    return bool(devices) and all(device["ok"] for device in devices), {"devices": devices}


def console_tty():
    # stdin adalah pipe; /dev/tty menunjuk controlling terminal, bukan fd 0.
    with open(os.ctermid(), "rb", buffering=0) as terminal:
        is_tty = os.isatty(terminal.fileno())
        tty_number = int(read_text("/proc/self/stat").rsplit(")", 1)[1].split()[4])
        actual_device = (os.major(tty_number), os.minor(tty_number))
        expected = os.stat("/dev/tty1")
        expected_device = (os.major(expected.st_rdev), os.minor(expected.st_rdev))
    matches = is_tty and stat.S_ISCHR(expected.st_mode) and actual_device == expected_device
    return matches, {"controlling_terminal": "/dev/tty1" if matches else None,
                     "is_tty": is_tty, "device_major_minor": actual_device}


def journal(probe):
    boot_id = read_text("/proc/sys/kernel/random/boot_id").replace("-", "")
    output = probe.run("sudo", "-n", "journalctl", "--boot=0", "--no-pager", "--output=json", "--lines=20")
    entries = [json.loads(line) for line in output.splitlines() if line.strip()]
    ids = sorted({entry.get("_BOOT_ID", "") for entry in entries})
    return bool(entries) and ids == [boot_id], {
        "readable_via_sudo_n": True, "entry_count": len(entries),
        "journal_boot_ids": ids, "expected_boot_id": boot_id,
    }


def baseline(probe):
    probe.check("mode", lambda: (probe.mode == "fallback", {"mode": probe.mode}))
    probe.check("uefi", lambda: (Path("/sys/firmware/efi").is_dir(), {"efi_directory": Path("/sys/firmware/efi").is_dir()}))
    probe.check("kernel_bore", lambda: kernel(probe))
    probe.check("distro_identity", release_identity)
    probe.check("liveuser_non_root", live_identity)
    probe.check("systemd_symlinks", system_links)
    probe.check("failed_units", lambda: failed_units(probe))
    probe.check("networkmanager_active", lambda: unit_state(probe, "NetworkManager.service", "active"))
    probe.check("network_ipv4_dhcp", lambda: network(probe))
    probe.check("zram_swap_zstd", zram)
    probe.check("versions", lambda: package_versions(probe))
    probe.check("boot_metadata", lambda: boot_metadata(probe))
    probe.check("installer_runtime", lambda: installer_runtime(probe))
    probe.check("constd_snapshot", lambda: constd_snapshot(probe))
    probe.check("live_sessions", live_sessions)
    probe.check("console_boot_target", lambda: (
        "systemd.unit=multi-user.target" in shlex.split(read_text("/proc/cmdline")),
        {"expected_parameter": "systemd.unit=multi-user.target"},
    ))
    probe.check("sddm_inactive", lambda: unit_state(probe, "sddm.service", "inactive"))
    probe.check("console_tty1", console_tty)
    probe.check("current_boot_journal", lambda: journal(probe))


def main():
    probe = Probe(globals().get("MODE"), globals().get("REPORT_URL"))
    if not isinstance(probe.report_url, str) or not probe.report_url:
        print("guest probe: REPORT_URL must be injected by the host", file=sys.stderr)
        return 1
    try:
        probe.check("probe_started", lambda: (True, {"pid": os.getpid()}))
        probe.report()
        probe.begin("baseline")
        baseline(probe)
        if not probe.report():
            return 1
        return 0
    except Exception as error:
        # Jangan tampilkan exception urllib: URL berisi token per-run.
        if isinstance(error, (OSError, urllib.error.URLError)):
            print(f"guest probe: {probe.stage} reporting/IO failed ({type(error).__name__})", file=sys.stderr)
        else:
            probe.checks["unhandled_exception"] = {"ok": False, "error": f"{type(error).__name__}: {error}"}
            try:
                probe.report()
            except Exception:
                print(f"guest probe: {probe.stage} error report could not be delivered", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
