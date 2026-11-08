"""Regresi pemulihan snapshot Snapper dan batas keselamatan target terpasang."""
import errno
import importlib.util
import json
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch, call

SPEC = importlib.util.spec_from_file_location(
    'constos_installer_backend', Path(__file__).resolve().parents[2] / 'installer/scripts/backend.py',
)
backend = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backend)


class TargetRecoverySafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'etc').mkdir(parents=True)
        (self.root / 'etc/passwd').write_text('root:x:0:0::/root:/bin/bash\nqatester:x:1000:1000::/home/qatester:/bin/bash\n')
        (self.root / 'etc/mkinitcpio.conf.d').mkdir(parents=True)
        (self.root / 'etc/sddm.conf.d').mkdir(parents=True)
        (self.root / 'etc/default').mkdir(parents=True)
        (self.root / 'etc/default/grub').write_text('GRUB_CMDLINE_LINUX_DEFAULT="log_buf_len=4M"\n')

    def tearDown(self):
        self.tmp.cleanup()

    def test_finalize_rejects_liveuser_in_target(self):
        (self.root / 'etc/passwd').write_text('root:x:0:0::/root:/bin/bash\nliveuser:x:1000:1000::/home/liveuser:/bin/bash\n')
        with self.assertRaisesRegex(RuntimeError, 'Akun live ditemukan'):
            backend.finalize(self.root)

    def test_finalize_rejects_archiso_hooks_in_target(self):
        (self.root / 'etc/mkinitcpio.conf.d/archiso.conf').write_text('HOOKS=(base archiso)')
        with self.assertRaisesRegex(RuntimeError, 'Konfigurasi initramfs live ditemukan'):
            backend.finalize(self.root)

    def test_finalize_rejects_sddm_autologin_in_target(self):
        (self.root / 'etc/sddm.conf.d/10-autologin.conf').write_text('[Autologin]\nUser=liveuser\n')
        with self.assertRaisesRegex(RuntimeError, 'Konfigurasi autologin tidak diizinkan'):
            backend.finalize(self.root)

    def test_snapper_setup_preserves_files_at_unmounted_snapshot_path(self):
        snapshots = self.root / '.snapshots'
        snapshots.mkdir()
        existing = snapshots / 'retained'
        existing.write_text('keep')

        with patch.object(backend, 'command'):
            with self.assertRaises(OSError) as failure:
                backend.finalize(self.root)

        self.assertEqual(failure.exception.errno, errno.ENOTEMPTY)
        self.assertEqual(existing.read_text(), 'keep')

    def test_snapper_subvolume_and_config_creation(self):
        """Pastikan subvolume @snapshots dipertahankan dan create-config dijalankan dengan --no-dbus."""
        (self.root / '.snapshots').mkdir()
        commands = []
        def fake_command(args, **kwargs):
            commands.append(list(args))
            if 'create-config' in args:
                # Simulasikan snapper create-config membuat file konfigurasi root
                cfg = self.root / 'etc/snapper/configs/root'
                cfg.parent.mkdir(parents=True, exist_ok=True)
                cfg.write_text('SUBVOLUME="/"\nFSTYPE="btrfs"\nNUMBER_LIMIT="50"\nTIMELINE_CREATE="no"\n')

        with patch.object(backend, 'command', side_effect=fake_command):
            backend.finalize(self.root)

        # Periksa bahwa konfigurasi Snapper disesuaikan dengan limit ConstOS
        config_text = (self.root / 'etc/snapper/configs/root').read_text()
        self.assertIn('NUMBER_LIMIT="10"', config_text)
        self.assertIn('TIMELINE_CREATE="yes"', config_text)
        self.assertIn('TIMELINE_CLEANUP="yes"', config_text)

        # Periksa perintah snapper pembuat snapshot awal #1
        snapshot_cmd = [cmd for cmd in commands if 'create' in cmd and 'Instalasi awal ConstOS' in cmd]
        self.assertEqual(len(snapshot_cmd), 1)
        self.assertEqual([str(x) for x in snapshot_cmd[0]], [
            'arch-chroot', str(self.root), 'snapper', '--no-dbus', '-c', 'root', 'create',
            '--description', 'Instalasi awal ConstOS', '--cleanup-algorithm', 'number'
        ])

class SnapperFstabInvariantsTests(unittest.TestCase):
    def test_fstab_must_contain_snapshots_subvolume(self):
        """Memvalidasi bahwa fstab target Btrfs memetakan /.snapshots ke subvolume @snapshots."""
        fstab_content = (
            "UUID=fef20d26-d4f7-4362-b2d9-14a4bfdaed22 / btrfs rw,noatime,compress=zstd:3,subvol=/@ 0 0\n"
            "UUID=fef20d26-d4f7-4362-b2d9-14a4bfdaed22 /home btrfs rw,noatime,compress=zstd:3,subvol=/@home 0 0\n"
            "UUID=fef20d26-d4f7-4362-b2d9-14a4bfdaed22 /.snapshots btrfs rw,noatime,compress=zstd:3,subvol=/@snapshots 0 0\n"
            "UUID=C77D-EE31 /boot/efi vfat rw,relatime,fmask=0077,dmask=0077 0 2\n"
        )
        lines = fstab_content.strip().splitlines()
        snapshots_line = [l for l in lines if '/.snapshots' in l]
        self.assertTrue(len(snapshots_line) == 1, "fstab wajib menyertakan mountpoint /.snapshots")
        self.assertIn('subvol=/@snapshots', snapshots_line[0], "Mountpoint /.snapshots wajib mengarah ke subvolume @snapshots")


if __name__ == '__main__':
    unittest.main()
