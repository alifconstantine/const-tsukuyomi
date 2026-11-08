import sys
sys.path.insert(0, '/usr/lib/constos-installer')
import backend
import libcalamares


def pretty_name():
    phase = libcalamares.job.configuration.get('phase')
    return {'preflight': 'Memeriksa disk, waktu, keyring dan mengunduh paket bertanda tangan',
            'storage': 'Membuat GPT, ESP dan subvolume Btrfs pada disk yang dikonfirmasi',
            'bootstrap': 'Memasang paket target ConstOS (bukan menyalin sistem live)',
            'finalize': 'Mengonfigurasi layanan, Snapper, initramfs dan GRUB UEFI',
            'unmount': 'Melepas filesystem target'}.get(phase, 'ConstOS')


def run():
    try:
        phase = libcalamares.job.configuration['phase']
        if phase == 'preflight':
            backend.preflight()
        elif phase == 'storage':
            root = backend.storage()
            libcalamares.globalstorage.insert('rootMountPoint', root)
            libcalamares.globalstorage.insert('firmwareType', 'efi')
            libcalamares.globalstorage.insert('efiSystemPartition', '/boot/efi')
        elif phase == 'bootstrap':
            backend.bootstrap(libcalamares.globalstorage.value('rootMountPoint'))
        elif phase == 'finalize':
            backend.finalize(libcalamares.globalstorage.value('rootMountPoint'))
        elif phase == 'unmount':
            backend.unmount()
        else:
            raise RuntimeError('Fase installer tidak dikenal.')
        return None
    except Exception as error:
        # Jangan serialisasi globalstorage: password akun dimiliki users upstream.
        return ('Instalasi ConstOS dihentikan', str(error))
