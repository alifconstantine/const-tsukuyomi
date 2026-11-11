"""Regresi batas disk dan arsip preflight; tidak membuka block device nyata."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
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
        self.disk = {'path': '/dev/vda', 'size': 40 * 1024**3, 'serial': 'QA-EMPTY', 'diskseq': '7'}
        (self.work / 'eligible-disks.json').write_text(json.dumps([self.disk]))

    def test_confirmation_rejects_raw_paths_and_incomplete_identities(self):
        with patch.object(backend, 'WORK', self.work), patch.object(backend, 'disk_identity') as probe:
            for value in ('', '/dev/vda', json.dumps({'path': '/dev/vda'})):
                with self.subTest(value=value), self.assertRaises(RuntimeError):
                    backend.confirm_disk(value)
            probe.assert_not_called()
        self.assertFalse((self.work / 'disk.json').exists())

    def test_confirmation_rejects_replaced_disk_at_the_same_path(self):
        replaced = {**self.disk, 'diskseq': '8'}
        with patch.object(backend, 'WORK', self.work), patch.object(backend, 'disk_identity', return_value=replaced):
            with self.assertRaisesRegex(RuntimeError, 'selected disk changed'):
                backend.confirm_disk(json.dumps(self.disk))
        self.assertFalse((self.work / 'disk.json').exists())

    def test_refresh_rejects_a_selection_from_the_previous_snapshot(self):
        replaced = {**self.disk, 'diskseq': '8'}
        with patch.object(backend, 'WORK', self.work), patch.object(backend, 'eligible_disks', return_value=[replaced]), \
                patch.object(backend, 'disk_identity') as probe:
            backend.scan_disks()
            with self.assertRaisesRegex(RuntimeError, 'no longer in the current list'):
                backend.confirm_disk(json.dumps(self.disk))
            probe.assert_not_called()
        self.assertFalse((self.work / 'disk.json').exists())

    def test_confirmed_disk_persists_its_reviewed_identity(self):
        with patch.object(backend, 'WORK', self.work), patch.object(backend, 'disk_identity', return_value=self.disk):
            backend.confirm_disk(json.dumps(self.disk))
        self.assertEqual(json.loads((self.work / 'disk.json').read_text()), self.disk)


class InstallerPlanTests(unittest.TestCase):
    def test_plan_without_reviewed_disk_is_rejected_before_storage(self):
        with patch.object(backend, 'require_live'), patch.object(backend, 'storage') as storage:
            with self.assertRaisesRegex(RuntimeError, 'Review the disk'):
                backend.install({'disk': '/dev/vda'})
            storage.assert_not_called()


class PreflightSafetyTests(unittest.TestCase):
    def test_unmount_job_requires_a_target_even_though_cleanup_can_be_empty(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(backend, 'WORK', Path(directory)):
            backend.unmount()
            with self.assertRaisesRegex(RuntimeError, 'target mount point is missing'):
                backend.unmount(required=True)

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
                    patch.object(backend, 'transaction_packages'), \
                    patch.object(backend, 'disk_identity', return_value=replaced), \
                    patch.object(backend, 'command', side_effect=AssertionError('Mutasi disk sebelum validasi')) as command:
                with self.assertRaisesRegex(RuntimeError, 'disk changed'):
                    backend.storage()
                command.assert_not_called()


class BrowserSelectionTests(unittest.TestCase):
    def test_selected_browser_alone_enters_transaction_and_sets_mime_defaults(self):
        source = Path(__file__).resolve().parents[2] / 'installer'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copyfile(source / 'browsers.json', root / 'browsers.json')
            (root / 'target-packages.x86_64').write_text('base\nextra/dux-shell\n')
            defaults = root / 'etc/skel/.config/mimeapps.list'
            defaults.parent.mkdir(parents=True)
            original = '[Default Applications]\ninode/directory=org.gnome.Nautilus.desktop;\n'
            applications = root / 'usr/share/applications'
            applications.mkdir(parents=True)
            browsers = {
                'firefox': ('firefox', 'firefox.desktop'),
                'chromium': ('chromium', 'chromium.desktop'),
                'zen': ('zen-browser-bin', 'zen.desktop'),
                'none': (None, None),
            }

            with patch.object(backend, 'DATA', root), patch.object(backend, 'WORK', root):
                for choice, (package, desktop) in browsers.items():
                    with self.subTest(choice=choice):
                        (root / 'browser').write_text(choice)
                        defaults.write_text(original)
                        self.assertEqual(backend.packages(), ['base', 'extra/dux-shell'] + ([package] if package else []))
                        if desktop:
                            (applications / desktop).touch()
                        backend.configure_browser(root)
                        actual = defaults.read_text()
                        self.assertIn('inode/directory=org.gnome.Nautilus.desktop;', actual)
                        for handler in ('x-scheme-handler/http', 'x-scheme-handler/https', 'text/html'):
                            if desktop:
                                self.assertIn(f'{handler}={desktop};', actual)
                            else:
                                self.assertNotIn(f'{handler}=', actual)
                with self.assertRaisesRegex(RuntimeError, 'Choose a browser'):
                    backend.browser_choice('unapproved-package')


if __name__ == '__main__':
    unittest.main()
