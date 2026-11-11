#!/usr/bin/env bash
set -euo pipefail
root=$(realpath -e -- "${1:?Usage: installer/install.sh ROOT}")
[[ $# == 1 && "$root" != / && -d "$root" ]] || { printf 'ROOT must be an existing staging directory other than /.\n' >&2; exit 1; }
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
install -Dm755 "$source_dir/scripts/backend.py" "$root/usr/lib/constos-installer/backend.py"
install -Dm755 "$source_dir/scripts/constos-install" "$root/usr/bin/constos-install"
install -Dm644 "$source_dir/session/constos-installer.desktop" "$root/usr/share/wayland-sessions/constos-installer.desktop"
install -Dm755 "$source_dir/session/kiosk" "$root/usr/lib/constos-installer/kiosk"
install -Dm755 "$source_dir/session/live-session" "$root/usr/lib/constos-installer/live-session"
install -Dm644 "$source_dir/target-packages.x86_64" "$root/usr/share/constos/installer/target-packages.x86_64"
install -Dm644 "$source_dir/pacman.conf" "$root/usr/share/constos/installer/pacman.conf"
install -Dm644 "$source_dir/browsers.json" "$root/usr/share/constos/installer/browsers.json"
install -Dm644 "$source_dir/tui/LICENSE" "$root/usr/share/licenses/constos-tui/LICENSE"
install -Dm644 "$source_dir/tui/NOTICE" "$root/usr/share/licenses/constos-tui/NOTICE"
