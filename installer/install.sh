#!/usr/bin/env bash
set -euo pipefail
root=${1:?Usage: installer/install.sh ROOT}
root=$(realpath -e -- "$root")
[[ $# == 1 && "$root" != / && -d "$root" ]] || { printf 'ROOT must be an existing staging directory other than /.\n' >&2; exit 1; }
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
install -Dm644 "$source_dir/settings.conf" "$root/usr/share/constos/installer/calamares/settings.conf"
install -d "$root/usr/share/constos/installer/calamares/modules" "$root/usr/share/constos/installer/calamares/branding/constos" \
  "$root/usr/lib/constos-installer/modules/constos" "$root/usr/share/constos/installer"
ln -sfn -- /usr/share/calamares/qml "$root/usr/share/constos/installer/calamares/qml"
for file in "$source_dir"/modules-config/*.conf; do
  [[ -f $file ]] && install -m644 -- "$file" "$root/usr/share/constos/installer/calamares/modules/"
done
install -m644 -- "$source_dir/branding/branding.desc" "$source_dir/branding/stylesheet.qss" \
  "$root/usr/share/constos/installer/calamares/branding/constos/"
install -m644 -- "$source_dir/../assets/const-logo.svg" "$root/usr/share/constos/installer/calamares/branding/constos/logo.svg"
install -m644 -- "$source_dir/../assets/exports/constos.svg" "$root/usr/share/constos/installer/calamares/branding/constos/constos.svg"
for file in "$source_dir/modules/constos/module.desc" "$source_dir/modules/constos/main.py"; do
  install -m644 -- "$file" "$root/usr/lib/constos-installer/modules/constos/"
done
install -Dm755 "$source_dir/scripts/backend.py" "$root/usr/lib/constos-installer/backend.py"
install -Dm755 "$source_dir/scripts/constos-install" "$root/usr/bin/constos-install"
install -Dm644 "$source_dir/session/constos-installer.desktop" "$root/usr/share/wayland-sessions/constos-installer.desktop"
install -Dm755 "$source_dir/session/kiosk" "$root/usr/lib/constos-installer/kiosk"
install -m644 "$source_dir/target-packages.x86_64" "$source_dir/pacman.conf" "$root/usr/share/constos/installer/"
