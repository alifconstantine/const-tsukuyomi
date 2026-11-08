#!/usr/bin/env python3
"""Jalur online tunggal; hanya dipanggil dari ISO live sebagai root."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile

DATA = Path('/usr/share/constos/installer')
WORK = Path('/run/constos-installer')
ARTIFACTS = Path('/usr/share/constos/packages')
MIN_DISK = 32 * 1024**3


def command(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, text=True, **kwargs)


def capture(args):
    return command(args, stdout=subprocess.PIPE).stdout.strip()


def require_live():
    if os.geteuid() != 0 or platform.machine() != 'x86_64':
        raise RuntimeError('The installer requires root on x86_64.')
    release = Path('/etc/os-release').read_text()
    if not re.search(r"^ID=['\"]?constos['\"]?$", release, re.M):
        raise RuntimeError('This installation medium is not ConstOS.')
    if not any(word.startswith('archisobasedir=') or word == 'boot=archiso'
               for word in Path('/proc/cmdline').read_text().split()):
        raise RuntimeError('The system was not booted as an Archiso live image.')
    if not Path('/run/archiso/bootmnt').is_mount():
        raise RuntimeError('The installer can only run from the Archiso live image.')
    if not Path('/sys/firmware/efi/efivars').is_dir():
        raise RuntimeError('Restart the ISO in UEFI mode to install ConstOS.')
    if 'ro' in capture(['findmnt', '-no', 'OPTIONS', '/sys/firmware/efi/efivars']).split(','):
        raise RuntimeError('EFI variables must be writable to register GRUB.')


def disk_identity(device):
    """Tolak media terpakai, termasuk signature tanpa tabel partisi."""
    st = os.stat(device)
    if not stat.S_ISBLK(st.st_mode):
        raise RuntimeError('The target is not a block device.')
    rows = json.loads(capture(['lsblk', '--json', '--bytes', '--paths', '--output',
                             'PATH,TYPE,SIZE,MODEL,SERIAL,WWN,MAJ:MIN,RO,RM,MOUNTPOINTS', device]))['blockdevices']
    if len(rows) != 1:
        raise RuntimeError('The disk identity is ambiguous.')
    disk = rows[0]
    if disk['path'] != device or disk['type'] != 'disk' or disk['ro'] or disk['rm']:
        raise RuntimeError('Select an entire writable, non-removable disk.')
    if disk.get('children') or any(disk.get('mountpoints') or []):
        raise RuntimeError('The disk has partitions or mounts. Select an empty disk.')
    if int(disk['size']) < MIN_DISK:
        raise RuntimeError('The target disk must be at least 32 GiB.')
    signatures = json.loads(capture(['wipefs', '--json', '--no-act', device])).get('signatures', [])
    if signatures:
        raise RuntimeError('The disk has a filesystem or partition signature. Select an empty disk.')
    return {key: disk.get(key) for key in ('path', 'size', 'model', 'serial', 'wwn', 'maj:min')}


def packages():
    result = []
    for line in (DATA / 'target-packages.x86_64').read_text().splitlines():
        item = line.partition('#')[0].strip()
        if item:
            if not re.fullmatch(r'[a-z0-9@+_.-]+', item):
                raise RuntimeError('Invalid target package manifest.')
            result.append(item)
    if not result:
        raise RuntimeError('The target package manifest is empty.')
    return result


def local_packages():
    result = []
    for line in (ARTIFACTS / 'SHA256SUMS').read_text().splitlines():
        digest, filename = line.split(maxsplit=1)
        filename = filename.lstrip('*')
        if Path(filename).name != filename or not re.fullmatch(r'[a-f0-9]{64}', digest):
            raise RuntimeError('Invalid local package checksum manifest.')
        path = ARTIFACTS / filename
        if hashlib.file_digest(path.open('rb'), 'sha256').hexdigest() != digest:
            raise RuntimeError('Local package checksum mismatch.')
        metadata = capture(['pacman', '-Qp', str(path)]).split()
        if len(metadata) != 2 or metadata[0] not in ('constos-core', 'constos-desktop'):
            raise RuntimeError('The local artifact is not an approved ConstOS package.')
        result.append((metadata[0], path))
    if sorted(name for name, _ in result) != ['constos-core', 'constos-desktop']:
        raise RuntimeError('Exactly two local ConstOS packages are required.')
    return [path for _, path in result]


def transaction_packages():
    """Berkas tepat hasil unduhan bertanda tangan, tanpa resolusi repo baru."""
    entries = json.loads((WORK / 'transaction.json').read_text())
    if not entries:
        raise RuntimeError('The preflight package transaction is empty.')
    result = []
    for entry in entries:
        filename = entry['filename']
        if Path(filename).name != filename or not re.fullmatch(r'[a-f0-9]{64}', entry['sha256']):
            raise RuntimeError('Invalid preflight transaction manifest.')
        archive = WORK / 'cache' / filename
        with archive.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != entry['sha256']:
            raise RuntimeError('A package changed after preflight. Installation stopped.')
        result.append(archive)
    return result


def preflight():
    require_live()
    state = json.loads((WORK / 'disk.json').read_text())
    if disk_identity(state['path']) != state:
        raise RuntimeError('The disk identity changed. Restart the installer.')
    for binary in ('pacstrap', 'arch-chroot', 'genfstab', 'sfdisk', 'udevadm',
                   'mkfs.fat', 'mkfs.btrfs', 'btrfs', 'mount', 'umount', 'pacman', 'pacman-key'):
        if not shutil.which(binary):
            raise RuntimeError(f'Missing installer dependency: {binary}')
    if capture(['timedatectl', 'show', '--property=NTPSynchronized', '--value']) != 'yes':
        raise RuntimeError('The clock has not synchronized. Connect to the network and wait for time synchronization.')
    # Tidak mereset/menghapus keyring live. Pacman memverifikasi setiap signature
    # paket di bawah dengan keyring yang sudah dipersiapkan saat build ISO.
    for name in ('archlinux', 'cachyos'):
        if not Path(f'/usr/share/pacman/keyrings/{name}.gpg').is_file():
            raise RuntimeError(f'The {name} keyring is missing.')
    command(['pacman-key', '--list-keys'], stdout=subprocess.DEVNULL)
    local_packages()
    (WORK / 'db').mkdir(exist_ok=True)
    (WORK / 'cache').mkdir(exist_ok=True)
    conf = (DATA / 'pacman.conf').read_text().replace(
        '[options]\n', f'[options]\nCacheDir = {WORK}/cache\n')
    (WORK / 'pacman.conf').write_text(conf)
    # Full transaction resolution + signed download selesai SEBELUM perubahan disk.
    # Cache tmpfs dapat memerlukan beberapa GiB; ENOSPC menghentikan preflight.
    command(['pacman', '--config', WORK / 'pacman.conf', '--dbpath', WORK / 'db',
             '--logfile', WORK / 'pacman.log', '-Syw', '--noconfirm', *packages()])
    filenames = capture([
        'pacman', '--config', WORK / 'pacman.conf', '--dbpath', WORK / 'db',
        '--logfile', WORK / 'pacman.log', '-Sp', '--noconfirm', '--print-format', '%f', *packages(),
    ]).splitlines()
    entries = []
    for filename in filenames:
        if not filename or Path(filename).name != filename:
            raise RuntimeError('Invalid filename in the resolved package transaction.')
        archive = WORK / 'cache' / filename
        with archive.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        entries.append({'filename': filename, 'sha256': digest})
    (WORK / 'transaction.json').write_text(json.dumps(entries))
    transaction_packages()


def storage():
    # Revalidasi tepat sebelum syscall pertama yang mengubah disk.
    require_live()
    expected = json.loads((WORK / 'disk.json').read_text())
    if disk_identity(expected['path']) != expected:
        raise RuntimeError('The disk changed or is no longer empty. Installation stopped.')
    transaction_packages()
    device = expected['path']
    command(['sfdisk', '--lock=yes', '--wipe=never', device], input=(
        'label: gpt\nunit: sectors\n\n'
        'start=2048, size=1GiB, type=U, name="ConstOS ESP"\n'
        'type=L, name="ConstOS system"\n'))
    command(['udevadm', 'settle'])
    suffix = 'p' if device[-1].isdigit() else ''
    esp, system = device + suffix + '1', device + suffix + '2'
    command(['mkfs.fat', '-F', '32', '-n', 'CONSTOS_EFI', esp])
    command(['mkfs.btrfs', '-L', 'ConstOS', system])
    root = Path(tempfile.mkdtemp(prefix='constos-root-', dir='/mnt'))
    (WORK / 'root').write_text(str(root))
    command(['mount', system, root])
    try:
        for name in ('@', '@home', '@snapshots'):
            command(['btrfs', 'subvolume', 'create', root / name])
    finally:
        command(['umount', root])
    command(['mount', '-o', 'subvol=@,compress=zstd:3,noatime', system, root])
    for name, target in (('@home', 'home'), ('@snapshots', '.snapshots')):
        (root / target).mkdir()
        command(['mount', '-o', f'subvol={name},compress=zstd:3,noatime', system, root / target])
    (root / 'boot/efi').mkdir(parents=True)
    command(['mount', '-o', 'umask=0077', esp, root / 'boot/efi'])
    return str(root)


def bootstrap(root):
    root = Path(root)
    # -U memasang arsip tepat yang sudah diunduh/diverifikasi saat preflight.
    # Tidak ada -Sy, resolusi repo baru, atau kebutuhan jaringan sesudah partisi.
    command(['pacstrap', '-c', '-M', '-U', '-C', WORK / 'pacman.conf', root, *transaction_packages()])
    # Artefak unsigned lokal dipercaya melalui SHA256SUMS yang dimiliki ISO,
    # bukan repo file:// sementara dan bukan SigLevel Never untuk repo jaringan.
    identity = root / 'etc/os-release'
    if identity.is_symlink() and identity.readlink() == Path('../usr/lib/os-release'):
        owner = subprocess.run(['pacman', '--root', str(root), '-Qqo', str(identity)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if owner.returncode != 1:
            raise RuntimeError('The os-release symlink is package-owned or could not be checked.')
        # tmpfiles membuat symlink upstream yang tidak dimiliki paket. Hapus hanya
        # symlink ini agar backup baru core tidak dialihkan menjadi .pacnew.
        identity.unlink()
    command(['pacman', '--root', root, '--config', WORK / 'pacman.conf',
             '-U', '--noconfirm', *local_packages()])
    shutil.copyfile(root / 'usr/share/constos/pacman.conf', root / 'etc/pacman.conf')
    if not re.search(r"^ID=['\"]?constos['\"]?$", identity.read_text(), re.M):
        raise RuntimeError('The ConstOS release metadata is missing from the target.')
    (root / 'etc/fstab').write_text(capture(['genfstab', '-U', root]) + '\n')
    command(['arch-chroot', root, 'pacman-key', '--populate', 'archlinux', 'cachyos'])


def finalize(root):
    root = Path(root)
    # Akun/login dibuat modul users upstream, bukan salinan passwd/shadow live.
    passwd = (root / 'etc/passwd').read_text()
    if any(line.split(':', 1)[0] == 'liveuser' for line in passwd.splitlines()):
        raise RuntimeError('The live user exists on the target. Installation stopped.')
    if list((root / 'etc/mkinitcpio.conf.d').glob('*archiso*')):
        raise RuntimeError('Live initramfs configuration found on the target.')
    for path in (root / 'etc/sddm.conf.d').glob('*.conf'):
        if re.search(r'^\s*\[Autologin\]', path.read_text(), re.M):
            raise RuntimeError('Autologin configuration is not allowed on the target.')
    grub = root / 'etc/default/grub'
    grub_text = grub.read_text()
    grub_text = re.sub(r'^GRUB_CMDLINE_LINUX_DEFAULT=.*$',
                       'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"', grub_text, flags=re.M)
    grub.write_text(grub_text)
    for unit in ('NetworkManager.service', 'sddm.service', 'systemd-timesyncd.service',
                 'bluetooth.service', 'snapper-timeline.timer', 'snapper-cleanup.timer'):
        command(['systemctl', '--root', root, 'enable', unit])
    command(['systemctl', '--root', root, 'set-default', 'graphical.target'])
    state = root / 'var/lib/sddm/state.conf'
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text('[Last]\nSession=/usr/share/wayland-sessions/constos.desktop\n')
    command(['arch-chroot', root, 'chown', 'sddm:sddm', '/var/lib/sddm/state.conf'])
    # Snapper create-config ingin membuat .snapshots sendiri. Pertahankan subvolume
    # @snapshots terpisah dengan mount ulang sesudah config dibuat.
    config = root / 'etc/snapper/configs/root'
    if not config.exists():
        if (root / '.snapshots').is_mount():
            command(['umount', root / '.snapshots'])
        try:
            (root / '.snapshots').rmdir()
        except FileNotFoundError:
            pass
        # Di dalam chroot, snapper membutuhkan --no-dbus agar tidak mencoba menghubungi daemon host.
        command(['arch-chroot', root, 'snapper', '--no-dbus', '-c', 'root', 'create-config', '/'])
        command(['btrfs', 'subvolume', 'delete', root / '.snapshots'])
        (root / '.snapshots').mkdir()
        command(['arch-chroot', root, 'mount', '/.snapshots'])
    elif not (root / '.snapshots').is_mount():
        (root / '.snapshots').mkdir(exist_ok=True)
        command(['arch-chroot', root, 'mount', '/.snapshots'])
    snapper_text = config.read_text()
    limits = {'TIMELINE_CREATE': 'yes', 'TIMELINE_CLEANUP': 'yes',
              'TIMELINE_LIMIT_HOURLY': '6', 'TIMELINE_LIMIT_DAILY': '7',
              'TIMELINE_LIMIT_WEEKLY': '2', 'TIMELINE_LIMIT_MONTHLY': '0',
              'TIMELINE_LIMIT_YEARLY': '0', 'NUMBER_CLEANUP': 'yes',
              'NUMBER_LIMIT': '10', 'NUMBER_LIMIT_IMPORTANT': '3'}
    for key, value in limits.items():
        if re.search(rf'^{key}=', snapper_text, flags=re.M):
            snapper_text = re.sub(rf'^{key}=.*$', f'{key}="{value}"', snapper_text, flags=re.M)
        else:
            snapper_text += f'{key}="{value}"\n'
    config.write_text(snapper_text)
    (root / '.snapshots').chmod(0o750)
    command(['arch-chroot', root, 'mkinitcpio', '-P'])
    command(['arch-chroot', root, 'grub-install', '--target=x86_64-efi',
             '--efi-directory=/boot/efi', '--bootloader-id=ConstOS', '--recheck'])
    # Fallback EFI path juga membuat disk VM dapat boot ketika NVRAM direset.
    command(['arch-chroot', root, 'grub-install', '--target=x86_64-efi',
             '--efi-directory=/boot/efi', '--removable', '--no-nvram'])
    command(['arch-chroot', root, 'grub-mkconfig', '-o', '/boot/grub/grub.cfg'])
    command(['arch-chroot', root, 'snapper', '--no-dbus', '-c', 'root', 'create',
             '--description', 'Initial ConstOS installation', '--cleanup-algorithm', 'number'])


def unmount():
    marker = WORK / 'root'
    if marker.exists():
        root = Path(marker.read_text())
        if root.parent != Path('/mnt') or not root.name.startswith('constos-root-'):
            raise RuntimeError('Invalid target mount point.')
        if root.is_mount():
            command(['umount', '--recursive', root])
        root.rmdir()
        marker.unlink()


def dialog(*args):
    return capture(['zenity', *args])


def launch():
    require_live()
    WORK.mkdir(mode=0o700, exist_ok=True)
    WORK.chmod(0o700)
    with (WORK / 'lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (WORK / 'root').exists():
            raise RuntimeError('A previous installation mount still exists. Reboot the ISO before trying again.')
        # Simpan juga error loader/branding yang terjadi sebelum logger Qt siap.
        log_path = WORK / 'calamares.log'
        with log_path.open('w') as log:
            os.fchmod(log.fileno(), 0o600)
            command(['calamares', '--version'], stdout=log, stderr=subprocess.STDOUT)
        rows = json.loads(capture(['lsblk', '--json', '--paths', '--output', 'PATH,TYPE']))['blockdevices']
        eligible = []
        for row in rows:
            try:
                disk = disk_identity(row['path'])
            except (RuntimeError, subprocess.CalledProcessError):
                continue
            eligible.extend([disk['path'], f"{disk['size'] / 1024**3:.1f} GiB | {disk['model'] or '-'} | serial {disk['serial'] or '-'} | WWN {disk['wwn'] or '-'} | {disk['maj:min']}"])
        if not eligible:
            raise RuntimeError('No eligible empty disk found. Connect a fixed disk of at least 32 GiB with no partitions or filesystem signatures.')
        selected = dialog('--list', '--title=Install ConstOS — Select an empty disk', '--width=1000', '--height=420',
                          '--text=An internet connection and x86_64 UEFI are required. The installer will partition the entire selected disk.\nThis release supports empty disks only, without encryption or dual boot.',
                          '--column=Disk', '--column=Disk details', *eligible)
        disk = disk_identity(selected)
        # Plain text: metadata disk tidak ditafsirkan sebagai markup.
        identity = json.dumps(disk, ensure_ascii=False, indent=2)
        confirmed = dialog('--entry', '--no-markup', '--title=Confirm the target disk',
                           '--width=800', '--text=Target:\n' + identity + '\n\nLayout: GPT, ESP 1 GiB, Btrfs @ / @home / @snapshots.\nType the exact disk path to confirm erasing the entire disk:')
        if confirmed != selected:
            raise RuntimeError('The disk path did not match. No changes were made to the disk.')
        (WORK / 'disk.json').write_text(json.dumps(disk))
        try:
            with log_path.open('a') as log:
                return command(['calamares', '--config', '/usr/share/constos/installer/calamares'],
                               stdout=log, stderr=subprocess.STDOUT).returncode
        finally:
            unmount()


if __name__ == '__main__':
    try:
        uid = int(os.environ.get('SUDO_UID', os.getuid()))
        if uid:
            import pwd
            if pwd.getpwuid(uid).pw_name != 'liveuser':
                raise RuntimeError('The launcher is available only to the live ISO user.')
            runtime = Path(f'/run/user/{uid}')
            display = sys.argv[1] if len(sys.argv) == 2 else ''
            if not re.fullmatch(r'wayland-[0-9]+', display) or runtime.stat().st_uid != uid:
                raise RuntimeError('Invalid Wayland session.')
            if not stat.S_ISSOCK((runtime / display).stat().st_mode):
                raise RuntimeError('The Wayland socket is unavailable.')
            os.environ.update(
                XDG_RUNTIME_DIR=str(runtime), WAYLAND_DISPLAY=display,
                QT_QPA_PLATFORM='wayland', QT_QUICK_BACKEND='software',
                GDK_BACKEND='wayland', GSK_RENDERER='cairo',
            )
        sys.exit(launch())
    except subprocess.CalledProcessError as error:
        if error.cmd[0] == 'zenity' and error.returncode == 1:
            sys.exit(0)
        subprocess.run(['zenity', '--error', '--no-markup', '--text',
                        f'Installation stopped. Check /run/constos-installer/calamares.log and /run/constos-installer/pacman.log.\n{error}'])
        sys.exit(1)
    except Exception as error:
        subprocess.run(['zenity', '--error', '--no-markup', '--text', str(error)])
        sys.exit(1)
