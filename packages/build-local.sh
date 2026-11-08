#!/usr/bin/env bash
# Build tanpa sudo/syncdeps; dependensi runtime tetap ditulis dalam metadata paket.
set -euo pipefail
(( EUID != 0 )) || { printf 'makepkg harus berjalan sebagai pengguna biasa.\n' >&2; exit 1; }
[[ $# == 1 ]] || { printf 'Usage: packages/build-local.sh OUTPUT_DIR\n' >&2; exit 2; }
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
output=$(realpath -m -- "$1")
[[ ! -e "$output" ]] || { printf 'OUTPUT_DIR harus baru: %s\n' "$output" >&2; exit 1; }
for binary in python3 makepkg fakeroot cargo rustc; do
  command -v "$binary" >/dev/null || { printf 'Dependensi build hilang: %s\n' "$binary" >&2; exit 1; }
done
mkdir -p -- "$output"
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
python3 - "$repo" "$work" "$output" <<'PY'
import hashlib
import os
from pathlib import Path
import sys
import tarfile
repo, work, output = map(Path, sys.argv[1:])
inputs = [
    'Cargo.toml', 'Cargo.lock', 'crates',
    'assets', 'desktop', 'iso/install-boot.sh', 'iso/grub/constos',
    'iso/airootfs/etc/os-release', 'iso/airootfs/etc/systemd/zram-generator.conf',
    'iso/airootfs/etc/sysctl.d/99-constos-memory.conf', 'installer/pacman.conf',
    'packages/constos-core', 'packages/constos-desktop', 'packages/build-local.sh',
]
files = []
for name in inputs:
    path = repo / name
    if not path.exists():
        raise SystemExit(f'Sumber paket belum tersedia: {name}')
    if path.is_dir():
        files.extend(p for p in path.rglob('*') if (p.is_file() or p.is_symlink())
                     and '__pycache__' not in p.parts and p.suffix != '.pyc')
    else:
        files.append(path)
files = sorted(set(files))
with (output / 'SOURCE_SHA256SUMS').open('w') as sums, tarfile.open(work / 'constos-sources.tar', 'w') as archive:
    for path in files:
        relative = path.relative_to(repo).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        sums.write(f'{digest}  {relative}\n')
        archive.add(path, arcname='constos/' + relative, recursive=False)
PY
read -r CONSTOS_SOURCE_SHA256 _ < <(sha256sum "$work/constos-sources.tar")
export CONSTOS_SOURCE_SHA256
for package in constos-core constos-desktop; do
  install -d "$work/$package"
  install -m644 "$repo/packages/$package/PKGBUILD" "$work/$package/PKGBUILD"
  if [[ -f "$repo/packages/$package/$package.install" ]]; then
    install -m644 "$repo/packages/$package/$package.install" "$work/$package/$package.install"
  fi
  ln -s ../constos-sources.tar "$work/$package/constos-sources.tar"
  (cd "$work/$package" && PKGDEST="$output" makepkg --nodeps --noconfirm --cleanbuild --nosign)
done
python3 - "$output" <<'PY'
import hashlib
from pathlib import Path
import sys
output = Path(sys.argv[1])
packages = sorted(output.glob('*.pkg.tar.*'))
if len(packages) != 2 or any(p.suffix == '.sig' for p in packages):
    raise SystemExit('Build harus menghasilkan tepat dua arsip paket lokal tanpa signature terpisah.')
with (output / 'SHA256SUMS').open('w') as sums:
    for package in packages:
        sums.write(f'{hashlib.sha256(package.read_bytes()).hexdigest()}  {package.name}\n')
PY
printf 'Paket lokal: %s\nChecksum paket: SHA256SUMS\nFingerprint sumber: SOURCE_SHA256SUMS\n' "$output"
