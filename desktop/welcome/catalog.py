import os
from pathlib import Path
import subprocess


APPS = {
    "org.libreoffice.LibreOffice": ("LibreOffice", "Dokumen, spreadsheet, dan presentasi"),
    "org.videolan.VLC": ("VLC", "Putar video dan audio"),
    "org.localsend.localsend_app": ("LocalSend", "Kirim file lewat jaringan lokal"),
    "org.keepassxc.KeePassXC": ("KeePassXC", "Simpan kata sandi secara lokal"),
}
FLATHUB_URL = "https://dl.flathub.org/repo"
FLATHUB_DESCRIPTOR = "/usr/share/flatpak/remotes.d/flathub.flatpakrepo"


def welcome_marker():
    state = Path(os.environ.get("XDG_STATE_HOME", ""))
    if not state.is_absolute():
        state = Path.home() / ".local/state"
    return state / "constos/welcome-seen"


def dismiss_welcome(marker):
    if not marker.is_file():
        marker.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        marker.touch(mode=0o600)


def flatpak(*args, timeout=30):
    result = subprocess.run(
        ["/usr/bin/flatpak", *args], stdin=subprocess.DEVNULL, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=timeout,
        env={**os.environ, "LC_ALL": "C.UTF-8"},
    )
    if result.returncode != 0:
        detail = (result.stderr.strip() or result.stdout.strip()).splitlines()
        raise RuntimeError(detail[-1][-400:] if detail else "Flatpak mengembalikan kegagalan.")
    return result.stdout


def installed_apps():
    return set(flatpak("list", "--app", "--columns=application").splitlines()) & APPS.keys()


def flathub_remote():
    remotes = flatpak("remotes", "--user", "--show-disabled", "--columns=name,url,options")
    for line in remotes.splitlines():
        fields = line.split(maxsplit=2)
        if fields and fields[0] == "flathub":
            url = fields[1] if len(fields) > 1 else ""
            options = fields[2].strip().split(",") if len(fields) == 3 else []
            if url.rstrip("/") != FLATHUB_URL or {"disabled", "no-gpg-verify"}.intersection(options):
                raise RuntimeError("Remote Flathub akun ini tidak aktif atau konfigurasinya tidak cocok.")
            return True
    return False


def install_app(app_id):
    if app_id not in APPS:
        raise ValueError("Aplikasi tidak ada di katalog ConstOS.")
    if not flathub_remote():
        flatpak("remote-add", "--user", "--if-not-exists", "flathub", FLATHUB_DESCRIPTOR)
        if not flathub_remote():
            raise RuntimeError("Remote Flathub belum tersedia untuk akun ini.")
    ref = f"app/{app_id}/x86_64/stable"
    flatpak("install", "--user", "--noninteractive", "--assumeyes", "flathub", ref, timeout=1800)
    if flatpak("info", "--user", "--arch=x86_64", "--show-ref", app_id, "stable").strip() != ref:
        raise RuntimeError("Flatpak belum mengonfirmasi aplikasi yang dipasang.")
