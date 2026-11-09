import sys
sys.path.insert(0, '/usr/lib/constos-installer')
import backend
import libcalamares


def pretty_name():
    return libcalamares.job.configuration['displayName']


def run():
    try:
        phase = libcalamares.job.configuration['phase']
        if phase == 'preflight':
            backend.preflight(libcalamares.globalstorage.value('constosDiskSelection'))
        elif phase == 'download':
            backend.download()
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
            backend.unmount(required=True)
        else:
            raise RuntimeError('Unknown installation step.')
        return None
    except Exception as error:
        # Jangan serialisasi globalstorage: password akun dimiliki users upstream.
        return ('ConstOS installation stopped', str(error))
