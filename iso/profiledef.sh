#!/usr/bin/env bash
# shellcheck disable=SC2034

iso_name="constos"
iso_label="CONSTOS_$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y%m)"
iso_publisher="ConstOS Project <https://github.com/alifconstantine/const-tsukuyomi>"
iso_application="Const Tsukuyomi Installer"
iso_version="$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y.%m.%d)"
install_dir="arch"
buildmodes=('iso')

bootmodes=('uefi.grub')

arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '15' '-b' '1M')

file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/gshadow"]="0:0:400"
  ["/root"]="0:0:750"
  ["/etc/sudoers.d"]="0:0:750"
  ["/etc/sudoers.d/g_wheel"]="0:0:440"
  ["/root/.automated_script.sh"]="0:0:755"
  ["/root/.gnupg"]="0:0:700"
  ["/usr/local/bin/const-sandbox"]="0:0:755"
  ["/usr/bin/constos-install"]="0:0:755"
  ["/usr/bin/constos-tui"]="0:0:755"
  ["/usr/bin/constd"]="0:0:755"
  ["/usr/lib/constos-installer/backend.py"]="0:0:755"
  ["/usr/lib/constos-installer/kiosk"]="0:0:755"
  ["/usr/lib/constos-installer/live-session"]="0:0:755"
  ["/usr/local/bin/choose-mirror"]="0:0:755"
  ["/usr/local/bin/dmcheck"]="0:0:755"
  ["/usr/local/bin/remove-nvidia"]="0:0:755"
  ["/usr/local/bin/prepare-live-desktop.sh"]="0:0:755"
)
