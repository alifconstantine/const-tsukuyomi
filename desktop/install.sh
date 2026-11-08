#!/usr/bin/env bash
# Install only into a caller-owned staging/package prefix, never the host HOME.
set -euo pipefail
if [[ $# != 2 || -z $1 || $1 == / || ( $2 != live && $2 != installed ) ]]; then
    printf 'Usage: desktop/install.sh ROOT live|installed\n' >&2
    exit 2
fi
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
mkdir -p -- "$1"
root=$(cd -- "$1" && pwd -P)
[[ $root != / ]] || { printf 'Refusing the host root.\n' >&2; exit 2; }
configs=(
    hypr/hyprland.lua constos/theme.css
    waybar/config waybar/style.css wofi/config wofi/style.css
    mako/config swaylock/config wlogout/layout wlogout/style.css
    gtk-3.0/settings.ini gtk-4.0/settings.ini foot/foot.ini mimeapps.list
)
for config in "${configs[@]}"; do
    install -Dm644 -- "$source_dir/$config" "$root/etc/skel/.config/$config"
done
for helper in constos-session constos-session-start constos-lock constos-screenshot; do
    install -Dm755 -- "$source_dir/scripts/$helper" "$root/usr/bin/$helper"
done
for unit in "$source_dir/systemd/user/"*; do
    install -Dm644 -- "$unit" "$root/usr/lib/systemd/user/${unit##*/}"
done
for entry in "$source_dir/applications/"*.desktop; do
    install -Dm644 -- "$entry" "$root/usr/share/applications/${entry##*/}"
done
install -Dm644 -- "$source_dir/session/constos.desktop" "$root/usr/share/wayland-sessions/constos.desktop"
install -Dm644 -- "$source_dir/portal/hyprland-portals.conf" "$root/etc/xdg/xdg-desktop-portal/hyprland-portals.conf"
install -Dm644 -- "$source_dir/schemas/90_constos.gschema.override" "$root/usr/share/glib-2.0/schemas/90_constos.gschema.override"
install -Dm644 -- "$source_dir/pacman-hooks/31-constos-glib-schemas.hook" "$root/usr/share/libalpm/hooks/31-constos-glib-schemas.hook"

if [[ $2 == installed ]]; then
    welcome="$source_dir/welcome"
    install -Dm755 -- "$welcome/welcome.py" "$root/usr/lib/constos/welcome/welcome.py"
    install -Dm644 -- "$welcome/catalog.py" "$root/usr/lib/constos/welcome/catalog.py"
    for entry in "$welcome/"*.desktop; do
        install -Dm644 -- "$entry" "$root/usr/share/applications/${entry##*/}"
    done
    install -Dm644 -- "$welcome/constos-welcome.service" "$root/usr/lib/systemd/user/constos-welcome.service"
    install -Dm644 -- "$welcome/10-welcome.conf" "$root/usr/lib/systemd/user/constos-session.target.d/10-welcome.conf"
fi
