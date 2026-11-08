import sys
sys.path.insert(0, '/usr/lib/constos-installer')
import backend
import libcalamares


def pretty_name():
    phase = libcalamares.job.configuration.get('phase')
    return {'preflight': 'Checking the disk, clock, and keyrings and downloading signed packages',
            'storage': 'Creating GPT, the EFI system partition, and Btrfs subvolumes',
            'bootstrap': 'Installing packages on the target disk',
            'finalize': 'Configuring services, Snapper, initramfs, and UEFI GRUB',
            'unmount': 'Unmounting the target filesystems'}.get(phase, 'ConstOS')


def run():
    try:
        phase = libcalamares.job.configuration['phase']
        if phase == 'preflight':
            backend.preflight(
                libcalamares.globalstorage.value('constosDiskPath'),
                libcalamares.globalstorage.value('constosDiskConfirmation'),
            )
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
            raise RuntimeError('Unknown installation step.')
        return None
    except Exception as error:
        # Jangan serialisasi globalstorage: password akun dimiliki users upstream.
        return ('ConstOS installation stopped', str(error))
