"""Regresi batas disk dan arsip preflight; tidak membuka block device nyata."""
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    'constos_installer_backend', Path(__file__).resolve().parents[2] / 'installer/scripts/backend.py',
)
backend = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backend)


class DiskSafetyTests(unittest.TestCase):
    def setUp(self):
        self.disk = {
            'path': '/dev/vda', 'type': 'disk', 'size': 32 * 1024**3,
            'model': 'QA disk', 'serial': 'QA-EMPTY', 'wwn': None,
            'maj:min': '254:0', 'ro': False, 'rm': False, 'mountpoints': [None],
        }

    def reject(self, disk, signatures, reason):
        def capture(args):
            if args[0] == 'lsblk':
                return json.dumps({'blockdevices': [disk]})
            if args[0] == 'wipefs':
                return json.dumps({'signatures': signatures})
            raise AssertionError(f'Unexpected command: {args[0]}')

        with patch.object(backend, 'os', SimpleNamespace(stat=lambda _: SimpleNamespace(st_mode=stat.S_IFBLK))), \
                patch.object(backend, 'capture', side_effect=capture):
            with self.assertRaisesRegex(RuntimeError, reason):
                backend.disk_identity('/dev/vda')

    def test_rejects_partitioned_disk_even_without_mounts(self):
        self.disk['children'] = [{'path': '/dev/vda1'}]
        self.reject(self.disk, [], 'partitions or mounts')

    def test_rejects_mounted_whole_disk_without_partitions(self):
        self.disk['mountpoints'] = ['/media/data']
        self.reject(self.disk, [], 'partitions or mounts')

    def test_rejects_filesystem_signature_without_partitions(self):
        self.reject(self.disk, [{'type': 'btrfs', 'offset': '0x10040'}], 'signature')

    def test_rejects_disk_below_minimum_size(self):
        self.disk['size'] -= 1
        self.reject(self.disk, [], 'at least 32 GiB')

    def test_rejects_removable_disk(self):
        self.disk['rm'] = True
        self.reject(self.disk, [], 'non-removable disk')


class DiskConfirmationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name)
        self.disk = {'path': '/dev/vda', 'size': 40 * 1024**3, 'serial': 'QA-EMPTY'}
        (self.work / 'eligible-disks.json').write_text(json.dumps([self.disk]))

    def test_confirmation_must_match_exact_path(self):
        with patch.object(backend, 'WORK', self.work), patch.object(backend, 'disk_identity') as probe:
            with self.assertRaisesRegex(RuntimeError, 'exact disk path'):
                backend.confirm_disk('/dev/vda', '/dev/vda ')
            probe.assert_not_called()
        self.assertFalse((self.work / 'disk.json').exists())

    def test_confirmation_rejects_unlisted_or_replaced_disk(self):
        replaced = {**self.disk, 'serial': 'OTHER-DISK'}
        with patch.object(backend, 'WORK', self.work), patch.object(backend, 'disk_identity', return_value=replaced):
            for path in ('/dev/vdb', '/dev/vda'):
                with self.subTest(path=path), self.assertRaisesRegex(RuntimeError, 'unavailable or its identity changed'):
                    backend.confirm_disk(path, path)
        self.assertFalse((self.work / 'disk.json').exists())

    def test_confirmed_disk_persists_its_reviewed_identity(self):
        with patch.object(backend, 'WORK', self.work), patch.object(backend, 'disk_identity', return_value=self.disk):
            backend.confirm_disk('/dev/vda', '/dev/vda')
        self.assertEqual(json.loads((self.work / 'disk.json').read_text()), self.disk)


class PreflightSafetyTests(unittest.TestCase):
    def test_modified_archive_blocks_partitioning(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / 'cache').mkdir()
            archive = work / 'cache/base-1-1-any.pkg.tar.zst'
            archive.write_bytes(b'original signed package fixture')
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            (work / 'transaction.json').write_text(json.dumps([
                {'filename': archive.name, 'sha256': digest},
            ]))
            disk = {'path': '/dev/vda', 'size': 32 * 1024**3, 'serial': 'QA-EMPTY'}
            (work / 'disk.json').write_text(json.dumps(disk))
            archive.write_bytes(b'modified after preflight')
            with patch.object(backend, 'WORK', work), \
                    patch.object(backend, 'require_live'), \
                    patch.object(backend, 'disk_identity', return_value=disk), \
                    patch.object(backend, 'command', side_effect=AssertionError('Mutasi disk sebelum validasi')) as command:
                with self.assertRaisesRegex(RuntimeError, 'changed after preflight'):
                    backend.storage()
                command.assert_not_called()

    def test_replaced_disk_blocks_partitioning(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            confirmed = {'path': '/dev/vda', 'size': 32 * 1024**3, 'serial': 'QA-EMPTY'}
            (work / 'disk.json').write_text(json.dumps(confirmed))
            replaced = {**confirmed, 'serial': 'OTHER-DISK'}
            with patch.object(backend, 'WORK', work), \
                    patch.object(backend, 'require_live'), \
                    patch.object(backend, 'disk_identity', return_value=replaced), \
                    patch.object(backend, 'command', side_effect=AssertionError('Mutasi disk sebelum validasi')) as command:
                with self.assertRaisesRegex(RuntimeError, 'disk changed'):
                    backend.storage()
                command.assert_not_called()


if __name__ == '__main__':
    unittest.main()
