#!/usr/bin/env bash
# Build TUI as a regular user and record the source and binary used by Archiso.
set -euo pipefail
(( EUID != 0 )) || { printf 'Go harus berjalan sebagai pengguna biasa.\n' >&2; exit 1; }
[[ $# == 1 ]] || { printf 'Usage: packages/build-installer.sh OUTPUT_DIR\n' >&2; exit 1; }
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
output=$(realpath -m -- "$1")
mkdir -- "$output"
(
    cd "$repo"
    find installer/{tui,i18n,installerplan} -type f -print0 |
        sort -z | xargs -0 sha256sum > "$output/SOURCE_SHA256SUMS"
    sha256sum packages/build-installer.sh >> "$output/SOURCE_SHA256SUMS"
    cd installer/tui
    CGO_ENABLED=0 go build -trimpath -mod=readonly -o "$output/constos-tui" .
)
(cd "$output"; sha256sum constos-tui > SHA256SUMS)
