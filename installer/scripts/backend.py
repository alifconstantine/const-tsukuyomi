#!/usr/bin/env python3
"""Jalur online tunggal; hanya dipanggil dari ISO live sebagai root."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import pwd
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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
    for variable in Path('/sys/firmware/efi/efivars').glob('SecureBoot-*'):
        if variable.read_bytes()[-1:] == b'\x01':
            raise RuntimeError('Disable Secure Boot before installing ConstOS.')
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
    identity = {key: disk.get(key) for key in ('path', 'size', 'model', 'serial', 'wwn', 'maj:min')}
    # A replacement can reuse the path and major/minor, and may have no serial.
    identity['diskseq'] = (Path('/sys/dev/block') / disk['maj:min'] / 'diskseq').read_text().strip()
    return identity


def eligible_disks():
    rows = json.loads(capture(['lsblk', '--json', '--paths', '--output', 'PATH,TYPE']))['blockdevices']
    disks = []
    for row in rows:
        if row['type'] != 'disk':
            continue
        try:
            disks.append(disk_identity(row['path']))
        except (RuntimeError, subprocess.CalledProcessError, FileNotFoundError):
            continue
    return disks


def scan_disks():
    snapshot = WORK / 'eligible-disks.json'
    pending = snapshot.with_suffix('.tmp')
    pending.write_text(json.dumps(eligible_disks()))
    pending.replace(snapshot)


def confirm_disk(selection):
    try:
        disk = json.loads(selection)
    except (TypeError, ValueError) as error:
        raise RuntimeError('Select an eligible disk and review the installation plan.') from error
    candidates = json.loads((WORK / 'eligible-disks.json').read_text())
    if disk not in candidates:
        raise RuntimeError('The selected disk is no longer in the current list. Open the installer and select the disk again.')
    recheck_disk(disk)
    (WORK / 'disk.json').write_text(json.dumps(disk))


def recheck_disk(expected):
    try:
        current = disk_identity(expected['path'])
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        raise RuntimeError(f'The selected disk is unavailable or no longer eligible. Select it again.\n{error}') from error
    if current != expected:
        raise RuntimeError('The selected disk changed. Open the installer and select the disk again.')


def browser_choice(choice):
    config = json.loads((DATA / 'browsers.json').read_text())
    for item in config['items']:
        if item['id'] == choice:
            return item
    raise RuntimeError('Choose a browser or No browser and review the installation plan.')


def selected_browser():
    return browser_choice((WORK / 'browser').read_text())


def configure_browser(root):
    desktop = selected_browser()['desktop']
    if not desktop:
        return
    if not (root / 'usr/share/applications' / desktop).is_file():
        raise RuntimeError('The selected browser desktop entry was not installed.')
    mimeapps = root / 'etc/skel/.config/mimeapps.list'
    entries = ''.join(f'{kind}={desktop};\n' for kind in
                      ('x-scheme-handler/http', 'x-scheme-handler/https', 'text/html'))
    mimeapps.write_text(mimeapps.read_text().replace('[Default Applications]\n',
                                                    '[Default Applications]\n' + entries, 1))


def packages():
    result = []
    for line in (DATA / 'target-packages.x86_64').read_text().splitlines():
        item = line.partition('#')[0].strip()
        if item:
            if not re.fullmatch(r'(?:extra/)?[a-z0-9@+_.-]+', item):
                raise RuntimeError('Invalid target package manifest.')
            result.append(item)
    if not result:
        raise RuntimeError('The target package manifest is empty.')
    browser = selected_browser()['package']
    if browser:
        result.append(browser)
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


def preflight(selection, browser):
    require_live()
    confirm_disk(selection)
    (WORK / 'browser').write_text(browser_choice(browser)['id'])
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


def download():
    # Full transaction resolution + signed download selesai SEBELUM perubahan disk.
    # Cache tmpfs dapat memerlukan beberapa GiB; ENOSPC menghentikan preflight.
    try:
        command(['pacman', '--config', WORK / 'pacman.conf', '--dbpath', WORK / 'db',
                 '--logfile', WORK / 'pacman.log', '-Syw', '--noconfirm', *packages()])
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            'Could not download or verify the installation packages. Check the network and the package log, '
            'then reopen the installer. No changes were made to the disk.\n'
            'Package log: /run/constos-installer/pacman.log'
        ) from error
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
    transaction_packages()
    recheck_disk(expected)
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
    configure_browser(root)
    shutil.copyfile(root / 'usr/share/constos/pacman.conf', root / 'etc/pacman.conf')
    if not re.search(r"^ID=['\"]?constos['\"]?$", identity.read_text(), re.M):
        raise RuntimeError('The ConstOS release metadata is missing from the target.')
    (root / 'etc/fstab').write_text(capture(['genfstab', '-U', root]) + '\n')
    command(['arch-chroot', root, 'pacman-key', '--populate', 'archlinux', 'cachyos'])


def finalize(root):
    root = Path(root)
    # Akun dibuat pada target melalui useradd, terpisah dari profil live.
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
    grub_text = re.sub(r'^GRUB_(?:DISTRIBUTOR|DISABLE_BOOTNEXT)=.*(?:\n|$)', '', grub_text, flags=re.M)
    # 31_efi_bootnext upstream menghormati opsi ini; recovery/UEFI tetap tersedia.
    grub.write_text(grub_text.rstrip() + '\nGRUB_DISTRIBUTOR="Tsukuyomi"\nGRUB_DISABLE_BOOTNEXT=true\n')
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


def unmount(*, required=False):
    marker = WORK / 'root'
    if required and not marker.exists():
        raise RuntimeError('The target mount point is missing. Check the installation log.')
    if marker.exists():
        root = Path(marker.read_text())
        if root.parent != Path('/mnt') or not root.name.startswith('constos-root-'):
            raise RuntimeError('Invalid target mount point.')
        if root.is_mount():
            command(['umount', '--recursive', root])
        elif required:
            raise RuntimeError('The target was unmounted unexpectedly. Check the installation log.')
        root.rmdir()
        marker.unlink()


def validate_plan(plan):
    patterns = {
        'browser': r'[a-z]+',
        'username': r'[a-z_][a-z0-9_-]{0,31}',
        'hostname': r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?',
        'full_name': r'[^:\x00-\x1f\x7f]{0,100}',
        'password_hash': r'\$6\$[./0-9A-Za-z]{1,16}\$[./0-9A-Za-z]{86}',
        'locale': r'[a-zA-Z0-9_.@-]+',
        'timezone': r'[a-zA-Z0-9_+/-]+',
        'keymap': r'[a-zA-Z0-9_-]+',
        'xkb_layout': r'[a-zA-Z0-9_-]+',
        'xkb_variant': r'[a-zA-Z0-9_-]*',
    }
    if not isinstance(plan, dict) or not isinstance(plan.get('disk'), dict):
        raise RuntimeError('Review the disk and account before installing.')
    for key, pattern in patterns.items():
        value = plan.get(key)
        if not isinstance(value, str) or not re.fullmatch(pattern, value):
            raise RuntimeError(f'Invalid installation choice: {key}.')
    if plan['username'] in {'root', 'liveuser', 'nobody', 'bin', 'daemon', 'dbus', 'sddm'} or plan['username'].startswith('systemd-'):
        raise RuntimeError('Choose a username that is not reserved by the system.')
    browser_choice(plan['browser'])
    locales = {line.split()[0] for line in Path('/usr/share/i18n/SUPPORTED').read_text().splitlines()
               if line.strip() and not line.startswith('#')}
    if plan['locale'] not in locales:
        raise RuntimeError('Choose a supported system locale.')
    try:
        ZoneInfo(plan['timezone'])
    except (ValueError, ZoneInfoNotFoundError) as error:
        raise RuntimeError('Choose a supported time zone.') from error


def configure_target(root, plan):
    root = Path(root)
    etc = root / 'etc'
    (etc / 'hostname').write_text(plan['hostname'] + '\n')
    with (etc / 'hosts').open('a') as hosts:
        hosts.write(f"\n127.0.1.1 {plan['hostname']}\n")
    (etc / 'localtime').unlink(missing_ok=True)
    (etc / 'localtime').symlink_to(Path('/usr/share/zoneinfo') / plan['timezone'])
    (etc / 'locale.conf').write_text('LANG=' + plan['locale'] + '\n')
    supported = (root / 'usr/share/i18n/SUPPORTED').read_text().splitlines()
    (etc / 'locale.gen').write_text(next(line for line in supported if line.split()[:1] == [plan['locale']]) + '\n')
    command(['arch-chroot', root, 'locale-gen'])
    (etc / 'vconsole.conf').write_text(
        'KEYMAP={keymap}\nXKBLAYOUT={xkb_layout}\nXKBVARIANT={xkb_variant}\n'.format(**plan))
    keyboard = etc / 'X11/xorg.conf.d/00-keyboard.conf'
    keyboard.parent.mkdir(parents=True, exist_ok=True)
    keyboard.write_text('Section "InputClass"\n    Identifier "ConstOS keyboard"\n'
                        '    MatchIsKeyboard "on"\n    Option "XkbLayout" "{xkb_layout}"\n'
                        '    Option "XkbVariant" "{xkb_variant}"\nEndSection\n'.format(**plan))
    # Dux / Tsukuyomi Shell memakai penanda per seri versi untuk kartu What’s New pada login awal.
    shell_package = ''
    for pkg in ('tsukuyomi-shell-git', 'tsukuyomi-shell', 'dux-shell'):
        try:
            shell_package = capture(['pacman', '--root', root, '-Q', pkg])
            if shell_package:
                break
        except Exception:
            continue
    if release := re.match(r'^(?:tsukuyomi-shell(?:-git)?|dux-shell) (?:[0-9]+:)?v?([0-9]+\.[0-9]+)', shell_package):
        series = release[1]
        (etc / 'skel/.config/dms' / f'.changelog-{series}').write_text(series + '\n')
    user = plan['username']
    command(['arch-chroot', root, 'useradd', '-m', '-U', '-G', 'wheel', '-s', '/usr/bin/fish',
             '-c', plan['full_name'], '--', user])
    command(['arch-chroot', root, 'chpasswd', '-e'], input=user + ':' + plan['password_hash'] + '\n')
    command(['arch-chroot', root, 'usermod', '-L', 'root'])
    sudoers = etc / 'sudoers.d/10-constos-admin'
    sudoers.parent.mkdir(exist_ok=True)
    sudoers.write_text('%wheel ALL=(ALL:ALL) ALL\n')
    sudoers.chmod(0o440)
    command(['systemd-machine-id-setup', '--root', root])


def stage(name, callback, *args, **kwargs):
    print(f'@@CONST_STEP {name}', flush=True)
    return callback(*args, **kwargs)


def install(plan):
    require_live()
    validate_plan(plan)
    WORK.mkdir(mode=0o700, exist_ok=True)
    WORK.chmod(0o700)
    with (WORK / 'lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (WORK / 'root').exists():
            raise RuntimeError('A previous installation mount still exists. Reboot the ISO before trying again.')
        (WORK / 'disk.json').unlink(missing_ok=True)
        scan_disks()
        try:
            stage('preflight', preflight, json.dumps(plan['disk']), plan['browser'])
            stage('download', download)
            root = stage('storage', storage)
            stage('bootstrap', bootstrap, root)
            stage('configure', configure_target, root, plan)
            stage('finalize', finalize, root)
            stage('unmount', unmount, required=True)
        finally:
            unmount()


def main():
    os.environ.update(LANG='C.UTF-8', LC_ALL='C.UTF-8', LANGUAGE='en_US:en')
    require_live()
    uid = int(os.environ.get('SUDO_UID', os.getuid()))
    if uid and pwd.getpwuid(uid).pw_name != 'liveuser':
        raise RuntimeError('The installer is available only to the live ISO user.')
    if sys.argv[1:] == ['--list-disks']:
        print(json.dumps(eligible_disks()))
    elif len(sys.argv) == 1:
        raw = sys.stdin.buffer.read(16385)
        if len(raw) > 16384:
            raise RuntimeError('The installation plan is too large.')
        install(json.loads(raw))
    else:
        raise RuntimeError('Unknown installer command.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(f'Installation stopped: {error}', file=sys.stderr)
        sys.exit(1)
