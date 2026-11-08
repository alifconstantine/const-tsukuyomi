#!/usr/bin/env bash
# Prasyarat: checkout Git bersih pada Linux x86_64, dependency Archiso dan
# keyring CachyOS siap. Wrapper tidak menaikkan hak akses sendiri:
# sudo -n bash tests/live/build.sh --output NEW_DIR --packages-dir DIR --calamares-dir DIR
# Parent NEW_DIR harus sudah ada; semua artefak dipertahankan, termasuk saat gagal.
set -euo pipefail
umask 022

usage() {
    printf '%s\n' 'Usage: sudo -n bash tests/live/build.sh --output NEW_DIR --packages-dir DIR --calamares-dir DIR'
}

die() {
    printf 'ConstOS build evidence: %s\n' "$*" >&2
    exit 1
}

output_arg=
packages_dir=
calamares_dir=
while (( $# )); do
    case "$1" in
        -h|--help) usage; exit 0 ;;
        --output)
            [[ -z $output_arg && -n ${2:-} && $2 != -* ]] || die '--output requires one new directory'
            output_arg=$2
            shift 2
            ;;
        --packages-dir|--calamares-dir)
            [[ -n ${2:-} && $2 != -* ]] || die "$1 requires one directory"
            case "$1" in
                --packages-dir) [[ -z $packages_dir ]] || die 'duplicate --packages-dir'; packages_dir=$2 ;;
                --calamares-dir) [[ -z $calamares_dir ]] || die 'duplicate --calamares-dir'; calamares_dir=$2 ;;
            esac
            shift 2
            ;;
        *) usage >&2; die "unknown argument: $1" ;;
    esac
done
[[ -n $output_arg && -n $packages_dir && -n $calamares_dir ]] || { usage >&2; exit 1; }
packages_dir=$(cd -- "$packages_dir" && pwd -P)
calamares_dir=$(cd -- "$calamares_dir" && pwd -P)
[[ $(uname -s) == Linux && $(uname -m) == x86_64 ]] || die 'requires an x86_64 Linux host and native Linux checkout'
(( EUID == 0 )) || die 'run with sudo -n bash; the wrapper requires root and never invokes sudo itself'
command -v python3 >/dev/null || die 'install Python 3 on the build host'
command -v tee >/dev/null || die 'install coreutils on the build host'
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
output_parent=$(cd -- "$(dirname -- "$output_arg")" && pwd -P) || die 'output parent must already exist'
output="$output_parent/$(basename -- "$output_arg")"
mkdir -- "$output" || die 'output must be a new directory; existing files are never removed'
output=$(cd -- "$output" && pwd -P)

# Perintah Git root hanya mempercayai checkout ini, tanpa mengubah konfigurasi global.
source_git() {
    git -c safe.directory="$repo_dir" --no-optional-locks -C "$repo_dir" "$@"
}

finish() {
    local status=$1
    trap - EXIT
    printf 'Build exit status: %s\nEvidence: %s\n' "$status" "$output"
    python3 - "$output" "$status" "$source_sha" "$source_clean" \
        "$iso_filename" "$iso_sha256" "$started_at_utc" "$built_at_utc" \
        "$repo_dir" "$work_dir" "$staged_profile" <<'PY' || status=1
import datetime
import json
import os
from pathlib import Path
import platform
import sys

(output, exit_code, source_sha, source_clean, iso_filename, iso_sha256,
 started_at, built_at, source_dir, work_dir, staged_profile) = sys.argv[1:]
metadata = {
    "schema_version": 1,
    "status": "success" if exit_code == "0" else "failure",
    "exit_code": int(exit_code),
    "source_sha": source_sha or None,
    "source_clean": source_clean == "true",
    "iso_sha256": iso_sha256 or None,
    "iso_filename": iso_filename or None,
    "started_at_utc": started_at,
    "built_at_utc": built_at or None,
    "finished_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "source_dir": source_dir,
    "work_dir": work_dir or None,
    "staged_profile": staged_profile or None,
    "host": {
        "uname": list(os.uname()),
        "python": platform.python_version(),
        "packages_file": "host-packages.txt",
    },
    "logs": {"build": "build.log", "staging": "staging.log",
             "source_status": "source-status.txt"},
    "package_manifests": {
        "target": "local-packages.sha256", "target_sources": "package-sources.sha256",
        "installer": "installer-packages.sha256", "installer_sources": "installer-sources.sha256",
    },
}
with (Path(output) / "build.json").open("x", encoding="utf-8") as stream:
    json.dump(metadata, stream, indent=2)
    stream.write("\n")
PY
    exit "$status"
}

build() {
    source_sha='' source_clean=false iso_filename='' iso_sha256=''
    work_dir='' staged_profile='' built_at_utc=''
    started_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    trap 'finish "$?"' EXIT

    cd -- "$repo_dir"
    : > "$output/staging.log"
    printf 'Started UTC: %s\nCheckout: %s\nOutput: %s\n' "$started_at_utc" "$repo_dir" "$output"
    for tool in git pacman mkarchiso sha256sum; do
        command -v "$tool" >/dev/null || die "missing host tool: $tool"
    done
    pacman -Q > "$output/host-packages.txt"
    cp -- "$packages_dir/SHA256SUMS" "$output/local-packages.sha256"
    cp -- "$packages_dir/SOURCE_SHA256SUMS" "$output/package-sources.sha256"
    cp -- "$calamares_dir/SHA256SUMS" "$output/installer-packages.sha256"
    cp -- "$calamares_dir/SOURCE_SHA256SUMS" "$output/installer-sources.sha256"
    uname -a
    git --version
    bash --version
    python3 --version
    [[ -f /usr/share/pacman/keyrings/cachyos.gpg ]] || die 'install and initialize the CachyOS keyring before building'
    [[ $(source_git rev-parse --show-toplevel) == "$repo_dir" ]] || die 'wrapper must belong to the checkout root'
    source_sha=$(source_git rev-parse --verify HEAD)
    source_git status --porcelain=v1 --untracked-files=all --ignore-submodules=none > "$output/source-status.txt"
    [[ ! -s "$output/source-status.txt" ]] || die 'checkout has tracked or untracked changes (ignored artifacts are excluded)'
    source_clean=true
    printf 'Source SHA: %s\nSource clean: true\n' "$source_sha"
    for link in default.target display-manager.service multi-user.target.wants/NetworkManager.service; do
        [[ -L "$repo_dir/iso/airootfs/etc/systemd/system/$link" ]] || die "checkout lost its Linux symlink: $link"
    done

    work_dir=$(mktemp -d -- "$output/work.XXXXXX")
    mkdir -- "$work_dir/staging" "$work_dir/build"
    printf 'Work: %s\n' "$work_dir"
    bash iso/buildiso.sh --stage-only --packages-dir "$packages_dir" --calamares-dir "$calamares_dir" -w "$work_dir/staging" 2>&1 | tee "$output/staging.log"
    staged_profile=$(python3 - "$repo_dir" "$work_dir/staging" <<'PY'
from pathlib import Path
import subprocess
import sys

repo, staging = map(Path, sys.argv[1:])
profiles = list(staging.glob("profile.*"))
if len(profiles) != 1 or not profiles[0].is_dir():
    raise SystemExit("Expected exactly one staged profile")
profile = profiles[0]
entries = subprocess.check_output([
    "git", "-c", f"safe.directory={repo}", "--no-optional-locks", "-C", str(repo),
    "ls-files", "--stage", "-z", "--", "iso/airootfs",
]).split(b"\0")
for entry in entries:
    if not entry:
        continue
    attributes, raw_path = entry.split(b"\t", 1)
    if attributes.split()[0] != b"120000":
        continue
    relative = Path(raw_path.decode("utf-8"))
    source = repo / relative
    staged = profile / relative.relative_to("iso")
    if not source.is_symlink() or not staged.is_symlink():
        raise SystemExit(f"Linux symlink missing in source/staging: {relative}")
    if source.readlink() != staged.readlink():
        raise SystemExit(f"Staged symlink target differs: {relative}")
    print(f"Validated symlink: {relative} -> {staged.readlink()}", file=sys.stderr)
print(profile)
PY
    )
    printf 'Validated staged profile: %s\n' "$staged_profile" | tee -a "$output/staging.log"
    printf 'Building full ISO from checkout root with verbose Archiso output\n'
    bash iso/buildiso.sh -v --packages-dir "$packages_dir" --calamares-dir "$calamares_dir" -w "$work_dir/build" -o "$output"

    local -a isos
    shopt -s nullglob
    isos=("$output"/*.iso)
    (( ${#isos[@]} == 1 )) || die 'expected exactly one resulting ISO'
    iso_filename=${isos[0]##*/}
    [[ $iso_filename == constos-*.iso ]] || die 'resulting ISO must use the constos-*.iso name'
    local checksum
    checksum=$(sha256sum -- "${isos[0]}")
    iso_sha256=${checksum%% *}
    printf '%s  %s\n' "$iso_sha256" "$iso_filename" > "$output/$iso_filename.sha256"
    source_clean=false
    source_git status --porcelain=v1 --untracked-files=all --ignore-submodules=none > "$output/source-status.txt"
    [[ ! -s "$output/source-status.txt" && $(source_git rev-parse --verify HEAD) == "$source_sha" ]] || die 'source checkout changed during the build'
    source_clean=true
    built_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    printf 'Built UTC: %s\nISO: %s\nSHA256: %s\n' "$built_at_utc" "$iso_filename" "$iso_sha256"
}

# Pipeline menunggu tee selesai: log sudah tertulis saat caller menerima exit code.
build 2>&1 | tee "$output/build.log"
