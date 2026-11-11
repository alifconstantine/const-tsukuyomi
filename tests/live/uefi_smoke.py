#!/usr/bin/env python3
"""Boot the unmodified live ISO through each GRUB entry."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class SmokeFailure(RuntimeError):
    pass


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class ProbeServer(ThreadingHTTPServer):
    """Serve only the probe; never expose the checkout or an arbitrary command."""

    def __init__(self, source):
        super().__init__(("127.0.0.1", 0), ProbeHandler)
        self.source = source
        self.token = secrets.token_hex(12)
        self.reports = queue.Queue()
        self.mode = None

    @property
    def guest_url(self):
        return f"http://10.0.2.2:{self.server_port}/{self.token}"


class ProbeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        mode = self.server.mode
        if mode != "fallback" or self.path != f"/{self.server.token}/{mode}.py":
            self.send_error(404)
            return
        header = f"REPORT_URL = {self.server.guest_url + '/report'!r}\nMODE = {mode!r}\n"
        body = (header + self.server.source).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/x-python")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != f"/{self.server.token}/report":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 512 * 1024:
                raise ValueError("invalid report length")
            report = json.loads(self.rfile.read(length))
            if not isinstance(report, dict) or report.get("mode") != self.server.mode:
                raise ValueError("invalid report mode")
            if report.get("stage") not in ("started", "baseline"):
                raise ValueError("invalid report stage")
            if not isinstance(report.get("ok"), bool):
                raise ValueError("invalid report status")
        except (ValueError, UnicodeError):
            self.send_error(400)
            return
        self.server.reports.put(report)
        self.send_response(204)
        self.end_headers()

    def log_message(self, *_):
        pass


class VM:
    def __init__(self, args, mode, directory):
        self.directory = directory
        self.directory.mkdir()
        self.responses = queue.Queue()
        self.sequence = 0
        self.stderr = (directory / "qemu.log").open("w", encoding="utf-8")
        self.qmp_log = (directory / "qmp.jsonl").open("w", encoding="utf-8")
        variables = directory / "uefi-vars.fd"
        shutil.copyfile(args.ovmf_vars, variables)
        cpu = "max" if args.accelerator == "tcg" else "host"
        if args.accelerator == "whpx":
            cpu = "host,vmx=off,smx=off"
        command = [
            args.qemu, "-name", f"ConstOS-smoke-{mode}",
            "-machine", "q35", "-accel", args.accelerator, "-cpu", cpu,
            "-m", "6144", "-smp", "4", "-vga", "virtio",
            "-drive", f"if=pflash,format=raw,unit=0,readonly=on,file={args.ovmf_code}",
            "-drive", f"if=pflash,format=raw,unit=1,file={variables}",
            "-drive", f"file={args.iso},media=cdrom,format=raw,readonly=on",
            "-boot", "order=d,menu=off", "-nic", "user,model=e1000e",
            "-display", "none", "-monitor", "none",
            "-serial", f"file:{directory / 'serial.log'}",
            "-qmp", "stdio", "-S", "-no-reboot",
        ]
        save_json(directory / "command.json", command)
        try:
            self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=self.stderr, text=True, encoding="utf-8", bufsize=1)
        except OSError:
            self.stderr.close()
            self.qmp_log.close()
            raise
        self.reader = threading.Thread(target=self.read_qmp, daemon=True)
        self.reader.start()

    def read_qmp(self):
        try:
            for line in self.process.stdout:
                self.qmp_log.write(line)
                self.qmp_log.flush()
                self.responses.put(json.loads(line))
        finally:
            self.responses.put(None)

    def receive(self, timeout=15):
        try:
            result = self.responses.get(timeout=timeout)
        except queue.Empty as error:
            raise SmokeFailure("QMP timed out; inspect qemu.log") from error
        if result is None:
            raise SmokeFailure(f"QEMU closed QMP (exit {self.process.poll()}); inspect qemu.log")
        return result

    def start(self):
        if "QMP" not in self.receive():
            raise SmokeFailure("Missing QMP greeting")
        self.command("qmp_capabilities")
        self.command("cont")

    def command(self, name, arguments=None):
        self.sequence += 1
        request = {"execute": name, "id": self.sequence}
        if arguments is not None:
            request["arguments"] = arguments
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        while True:
            response = self.receive()
            if response.get("id") != self.sequence:
                continue
            if "error" in response:
                raise SmokeFailure(f"QMP {name}: {response['error']}")
            return response.get("return")

    def key(self, *qcodes):
        # send-key's virtual-clock release timer can lag behind host input under TCG.
        events = [{"type": "key", "data": {"down": True, "key": {"type": "qcode", "data": key}}}
                  for key in qcodes]
        events.extend({"type": "key", "data": {"down": False, "key": {"type": "qcode", "data": key}}}
                      for key in reversed(qcodes))
        self.command("input-send-event", {"events": events})
        time.sleep(0.08)

    def type(self, text):
        symbols = {
            " ": ("spc",), "-": ("minus",), ".": ("dot",), "/": ("slash",),
            ":": ("shift", "semicolon"), "|": ("shift", "backslash"),
            "_": ("shift", "minus"), "\n": ("ret",),
        }
        for char in text:
            if char in symbols:
                self.key(*symbols[char])
            elif char.isascii() and char.islower() or char.isascii() and char.isdigit():
                self.key(char)
            elif char.isascii() and char.isupper():
                self.key("shift", char.lower())
            else:
                raise SmokeFailure(f"Unsupported keyboard character: {char!r}")

    def screenshot(self, name):
        path = self.directory / f"{name}.png"
        self.command("screendump", {"filename": str(path), "format": "png"})
        return path

    def close(self):
        if self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)
        self.reader.join(timeout=5)
        self.process.stdin.close()
        self.process.stdout.close()
        self.stderr.close()
        self.qmp_log.close()


def read_screen(args, vm, name):
    image = vm.screenshot(name)
    result = subprocess.run([args.tesseract, str(image), "stdout", "-l", "eng", "--psm", "6"],
                            capture_output=True, encoding="utf-8", timeout=15, check=True)
    (vm.directory / f"{name}.txt").write_text(result.stdout, encoding="utf-8")
    # Bitmap GRUB fonts make OCR confuse the letters O and the digit 0.
    return " ".join(result.stdout.lower().replace("0", "o").split())


def select_grub(args, vm, mode, deadline):
    while time.monotonic() < deadline:
        text = read_screen(args, vm, "boot")
        # Recognise the two public entries before allowing the default timeout.
        if re.search(r"\binstall tsukuyomi\b", text) and "tsukuyomi diagnostics (console fallback)" in text:
            if mode != "installer":
                vm.key("up")
            vm.screenshot("grub")
            if mode == "installer":
                # Exercise the real default and timeout, without selecting an entry.
                return
            vm.key("end")
            vm.key("ret")
            return
        time.sleep(0.2)
    raise SmokeFailure("GRUB entries were not recognized before the boot deadline")


def wait_installer_screen(args, vm, name, expected, deadline):
    while time.monotonic() < deadline:
        if vm.process.poll() is not None:
            raise SmokeFailure(f"QEMU exited before the {name} screen")
        text = read_screen(args, vm, "installer-waiting")
        if all(fragment in text for fragment in expected):
            return vm.screenshot(name)
        time.sleep(1)
    raise SmokeFailure(f"The {name} screen did not appear")


def next_report(server, vm, stage, deadline, results):
    while time.monotonic() < deadline:
        if vm.process.poll() is not None:
            raise SmokeFailure(f"QEMU exited before {stage}")
        try:
            report = server.reports.get(timeout=min(1, max(0.01, deadline - time.monotonic())))
        except queue.Empty:
            continue
        results.append(report)
        save_json(vm.directory / "reports.json", results)
        if not report["ok"]:
            failed = {name: check for name, check in report.get("checks", {}).items() if not check.get("ok")}
            raise SmokeFailure(f"Guest {report['stage']} failed: {failed or report.get('error', 'see reports.json')}")
        if report["stage"] != stage:
            raise SmokeFailure(f"Expected guest stage {stage}, received {report['stage']}")
        return report
    raise SmokeFailure(f"Timed out waiting for guest stage {stage}")


def run_boot(args, server, mode):
    directory = args.output / mode
    vm = VM(args, mode, directory)
    reports = []
    started = time.monotonic()
    deadline = started + args.timeout
    server.mode = mode
    try:
        vm.start()
        select_grub(args, vm, mode, min(deadline, started + 90))
        if mode == "installer":
            welcome = wait_installer_screen(
                args, vm, "installer-welcome",
                ("welcome to the tsukuyomi installer", "empty fixed disk", "confirm the installation"), deadline,
            )
            vm.key("ctrl", "c")
            actions = wait_installer_screen(
                args, vm, "installer-actions", ("choose an action", "restart", "shut down"), deadline,
            )
            return {"ok": True, "elapsed_seconds": round(time.monotonic() - started, 2),
                    "evidence": [str(welcome), str(actions)]}
        command = f"curl -fsS {server.guest_url}/{mode}.py | python\n"
        # Readiness is proven by a report from the real terminal, not by a fixed boot sleep.
        while time.monotonic() < deadline:
            text = read_screen(args, vm, "waiting")
            if not re.search(r"liveuser[@a]cachyos|automatic login", text):
                time.sleep(1)
                continue
            vm.type(command)
            try:
                next_report(server, vm, "started", min(deadline, time.monotonic() + 15), reports)
                break
            except SmokeFailure:
                if reports or vm.process.poll() is not None:
                    raise
                # Clear a partially typed command before trying again in the same terminal.
                vm.key("ctrl", "c")
                time.sleep(2)
        else:
            raise SmokeFailure("No live terminal became ready")
        next_report(server, vm, "baseline", deadline, reports)
        # Mapped surfaces precede their first rendered/animated frames.
        time.sleep(1)
        vm.screenshot("baseline")
        return {"ok": True, "elapsed_seconds": round(time.monotonic() - started, 2),
                "reports": str(directory / "reports.json")}
    except Exception:
        if vm.process.poll() is None:
            try:
                vm.screenshot("failure")
            except (OSError, SmokeFailure):
                pass
        raise
    finally:
        server.mode = None
        vm.close()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, type=Path)
    parser.add_argument("--ovmf-code", required=True, type=Path)
    parser.add_argument("--ovmf-vars", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="New evidence directory; never overwritten")
    parser.add_argument("--build-evidence", type=Path)
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    parser.add_argument("--tesseract", default="tesseract")
    parser.add_argument("--accelerator", choices=("kvm", "tcg", "whpx"), default="kvm",
                        help="Default KVM; TCG and WHPX require explicit selection")
    parser.add_argument("--timeout", type=int, default=300, help="Deadline in seconds per cold boot")
    args = parser.parse_args()
    if args.timeout < 30:
        parser.error("--timeout must be at least 30 seconds")
    if args.accelerator == "kvm" and not os.access("/dev/kvm", os.R_OK | os.W_OK):
        parser.error("KVM requires read/write access to /dev/kvm; no automatic TCG fallback")
    for name in ("iso", "ovmf_code", "ovmf_vars", "build_evidence"):
        path = getattr(args, name)
        if path is not None:
            path = path.resolve(strict=True)
            if not path.is_file() or "," in str(path):
                parser.error(f"{name} must be a file with no comma in its path")
            setattr(args, name, path)
    args.output = args.output.resolve()
    if "," in str(args.output):
        parser.error("--output cannot contain a comma")
    for name in ("qemu", "tesseract"):
        executable = shutil.which(getattr(args, name))
        if executable is None:
            parser.error(f"Missing executable: {getattr(args, name)}")
        setattr(args, name, executable)
    args.output.mkdir(parents=True, exist_ok=False)
    return args


def main():
    args = parse_args()
    summary = {"ok": False, "started_at_utc": datetime.now(timezone.utc).isoformat(),
               "iso_filename": args.iso.name, "iso_sha256": sha256(args.iso),
               "build": None, "accelerator": args.accelerator,
               "runner_sha256": sha256(Path(__file__)),
               "probe_sha256": sha256(Path(__file__).with_name("guest_probe.py")),
               "vm": {"cpus": 4, "memory_mib": 6144, "graphics": "virtio", "firmware": "UEFI", "writable_disks": []},
               "firmware_sha256": {"code": sha256(args.ovmf_code), "vars_template": sha256(args.ovmf_vars)},
               "boots": {}, "visual_review": "required; automation does not sign off appearance"}
    server = None
    thread = None
    try:
        if args.build_evidence:
            build = json.loads(args.build_evidence.read_text(encoding="utf-8"))
            if build.get("iso_sha256") != summary["iso_sha256"] or build.get("iso_filename") != args.iso.name:
                raise SmokeFailure("Build evidence does not identify this ISO")
            if build.get("status") != "success" or build.get("exit_code") != 0:
                raise SmokeFailure("Build evidence records a failed build")
            if build.get("source_clean") is not True or not build.get("source_sha"):
                raise SmokeFailure("Build evidence must identify a clean source checkout")
            summary["build"] = build
        for name in ("qemu", "tesseract"):
            result = subprocess.run([getattr(args, name), "--version"], capture_output=True, text=True,
                                    timeout=15, check=True)
            summary[f"{name}_version"] = result.stdout.splitlines()[0]
        languages = subprocess.run([args.tesseract, "--list-langs"], capture_output=True, text=True,
                                   timeout=15, check=True)
        if "eng" not in languages.stdout.splitlines():
            raise SmokeFailure("Tesseract requires the eng language model")
        server = ProbeServer(Path(__file__).with_name("guest_probe.py").read_text(encoding="utf-8"))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        for mode in ("installer", "fallback"):
            print(f"Booting {mode}; evidence: {args.output / mode}", flush=True)
            summary["boots"][mode] = run_boot(args, server, mode)
            save_json(args.output / "summary.json", summary)
        summary["ok"] = True
        print("Live UEFI smoke passed; review the saved screenshots before acceptance.", flush=True)
        return 0
    except (OSError, ValueError, SmokeFailure, subprocess.SubprocessError) as error:
        summary["error"] = str(error)
        print(f"Live UEFI smoke failed: {error}", file=sys.stderr)
        return 1
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=5)
        save_json(args.output / "summary.json", summary)


if __name__ == "__main__":
    sys.exit(main())
