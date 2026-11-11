#!/usr/bin/env bash
# Staging saja: tidak menjalankan chroot, mkinitcpio, grub-install, atau systemctl.
set -euo pipefail

if (( $# != 2 )) || [[ $2 != live && $2 != installed ]]; then
    printf 'Usage: install-boot.sh ROOT live|installed\n' >&2
    exit 2
fi

source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
boot_dir="$source_dir/../desktop/boot"
root=$(realpath -m -- "$1")
[[ $root != / ]] || { printf 'Refusing to stage into the host root\n' >&2; exit 2; }
mkdir -p -- "$root"
mode=$2

install -Dm644 -- "$boot_dir/config/plymouthd.conf" "$root/usr/share/constos/boot/plymouthd.conf"
for file in constos.plymouth constos.script; do
    install -Dm644 -- "$boot_dir/plymouth/$file" "$root/usr/share/plymouth/themes/constos/$file"
done

for file in Main.qml metadata.desktop theme.conf theme/Main.qml; do
    install -Dm644 -- "$boot_dir/sddm/$file" "$root/usr/share/sddm/themes/constos/$file"
done
install -Dm644 -- "$boot_dir/config/20-constos-theme.conf" "$root/etc/sddm.conf.d/20-constos-theme.conf"
install -Dm644 -- "$boot_dir/config/99-sddm-stock.conf" "$root/usr/share/constos/boot/99-sddm-stock.conf"
install -Dm644 -- "$boot_dir/COPYING.txt" "$root/usr/share/constos/boot/COPYING.txt"
install -Dm644 -- "$boot_dir/sddm/LICENSE" "$root/usr/share/constos/boot/LICENSE"
install -Dm644 -- "$source_dir/grub/constos/theme.txt" "$root/usr/share/grub/themes/constos/theme.txt"

case "$mode" in
    live)
        install -Dm644 -- "$boot_dir/config/plymouthd.conf" "$root/etc/plymouth/plymouthd.conf"
        install -Dm644 -- "$boot_dir/config/mkinitcpio-live.conf" "$root/etc/mkinitcpio.conf.d/archiso.conf"
        install -Dm644 -- "$boot_dir/config/linux-cachyos-bore-live.preset" "$root/etc/mkinitcpio.d/linux-cachyos-bore.preset"
        install -Dm644 -- "$boot_dir/config/10-constos-live.conf" "$root/etc/sddm.conf.d/10-constos-live.conf"
        ;;
    installed)
        # File milik profil live ini tidak boleh ikut menjadi konfigurasi target.
        rm -f -- "$root/etc/mkinitcpio.conf.d/archiso.conf" "$root/etc/sddm.conf.d/10-constos-live.conf"
        install -Dm644 -- "$boot_dir/config/mkinitcpio-installed.conf" "$root/etc/mkinitcpio.conf.d/10-constos.conf"
        install -Dm755 -- "$boot_dir/grub/09_constos_theme" "$root/etc/grub.d/09_constos_theme"
        ;;
esac
