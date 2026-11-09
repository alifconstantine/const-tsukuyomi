#!/usr/bin/env bash
# makepkg tanpa sudo/syncdeps; siapkan base-devel dan depends/makedepends dahulu.
# Contoh: bash packages/build-calamares.sh "$PWD/iso/out/calamares-$(date -u +%Y%m%dT%H%M%SZ)"
set -euo pipefail
(( EUID != 0 )) || { printf 'makepkg harus berjalan sebagai pengguna biasa.\n' >&2; exit 1; }
[[ $# == 1 ]] || { printf 'Usage: packages/build-calamares.sh OUTPUT_DIR\n' >&2; exit 2; }
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
output=$(realpath -m -- "$1")
[[ ! -e "$output" && ! -L "$output" ]] || { printf 'OUTPUT_DIR harus baru: %s\n' "$output" >&2; exit 1; }
for binary in makepkg fakeroot python3 cmake ninja; do
  command -v "$binary" >/dev/null || { printf 'Dependensi build hilang: %s\n' "$binary" >&2; exit 1; }
done
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
mkdir -p -- "$output" "$work/sources" "$work/build" "$work/logs" "$work/srcpackages"
# Build dan fingerprint memakai snapshot input yang sama, bukan checkout yang bisa berubah.
inputs=(packages/build-calamares.sh packages/constos-calamares/{PKGBUILD,qt-widgets.patch,installer-ui.patch,constosdisk.cmake,constosdisk.cpp})
for input in "${inputs[@]}"; do
  install -Dm644 -- "$repo/$input" "$work/inputs/$input"
done
python3 - "$work/inputs" "$output" "${inputs[@]}" <<'PY'
import hashlib
from pathlib import Path
import sys
inputs, output = map(Path, sys.argv[1:3])
with (output / 'SOURCE_SHA256SUMS').open('w') as sums:
    for name in sys.argv[3:]:
        with (inputs / name).open('rb') as source:
            digest = hashlib.file_digest(source, 'sha256').hexdigest()
        sums.write(f'{digest}  {name}\n')
PY
# Ninja tidak memakai MAKEFLAGS. Dua proses aman sebagai default builder 8 GiB;
# operator boleh menaikkannya lewat CMAKE_BUILD_PARALLEL_LEVEL. Tidak ada -march=native.
export CMAKE_BUILD_PARALLEL_LEVEL=${CMAKE_BUILD_PARALLEL_LEVEL:-2}
printf 'Build Calamares: maksimum %s proses paralel.\n' "$CMAKE_BUILD_PARALLEL_LEVEL"
(
  cd -- "$work/inputs/packages/constos-calamares"
  # Argumen variabel ini menimpa makepkg.conf sesudah config dimuat. Tidak ada
  # --syncdeps/--install/--nodeps: dependensi harus tersedia, bukan dipasang helper.
  makepkg --noconfirm --cleanbuild --clean --nosign \
    "PKGDEST=$output" "SRCDEST=$work/sources" "BUILDDIR=$work/build" \
    "SRCPKGDEST=$work/srcpackages" "LOGDEST=$work/logs" 'PKGEXT=.pkg.tar.zst'
)
python3 - "$output" <<'PY'
import hashlib
from pathlib import Path
import sys
output = Path(sys.argv[1])
archives = sorted(output.glob('*.pkg.tar.*'))
if (len(archives) != 1 or not archives[0].name.startswith('constos-calamares-')
        or not archives[0].name.endswith('.pkg.tar.zst')):
    raise SystemExit('Build harus menghasilkan tepat satu arsip constos-calamares .pkg.tar.zst.')
with archives[0].open('rb') as package:
    digest = hashlib.file_digest(package, 'sha256').hexdigest()
(output / 'SHA256SUMS').write_text(f'{digest}  {archives[0].name}\n')
PY
printf 'Paket installer: %s\nChecksum paket: SHA256SUMS\nFingerprint resep/helper: SOURCE_SHA256SUMS\n' "$output"
