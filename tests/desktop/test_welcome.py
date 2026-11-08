import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import call, patch


SOURCE = Path(__file__).resolve().parents[2] / "desktop/welcome/catalog.py"
SPEC = importlib.util.spec_from_file_location("welcome_catalog", SOURCE)
catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog)

APP = "org.videolan.VLC"
REF = f"app/{APP}/x86_64/stable"
REMOTE = f"flathub\t{catalog.FLATHUB_URL}/\t\n"
LIST_REMOTES = call("remotes", "--user", "--show-disabled", "--columns=name,url,options")
INSTALL = call("install", "--user", "--noninteractive", "--assumeyes", "flathub", REF, timeout=1800)
INFO = call("info", "--user", "--arch=x86_64", "--show-ref", APP, "stable")


class WelcomeStateTests(unittest.TestCase):
    def test_dismissal_is_per_account_and_survives_reopening(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.dict(os.environ, {"XDG_STATE_HOME": str(root / "first")}):
                first = catalog.welcome_marker()
                self.assertFalse(first.exists())
                catalog.dismiss_welcome(first)
                catalog.dismiss_welcome(first)
                self.assertTrue(catalog.welcome_marker().is_file())
            with patch.dict(os.environ, {"XDG_STATE_HOME": str(root / "second")}):
                self.assertFalse(catalog.welcome_marker().exists())


class AppCatalogTests(unittest.TestCase):
    def test_inventory_uses_installed_refs_and_ignores_other_apps(self):
        with patch.object(catalog, "flatpak", return_value=f"{APP}\norg.other.App\n"):
            self.assertEqual(catalog.installed_apps(), {APP})

    def test_first_install_adds_and_checks_user_remote_before_installing(self):
        with patch.object(catalog, "flatpak", side_effect=["", "", REMOTE, "", REF + "\n"]) as flatpak:
            catalog.install_app(APP)
        self.assertEqual(flatpak.call_args_list, [
            LIST_REMOTES,
            call("remote-add", "--user", "--if-not-exists", "flathub",
                 catalog.FLATHUB_DESCRIPTOR),
            LIST_REMOTES, INSTALL, INFO,
        ])

    def test_rejects_untrusted_or_disabled_remote_without_changing_it(self):
        remotes = (
            "flathub\thttps://example.com/repo/\t\n",
            f"flathub\t{catalog.FLATHUB_URL}/\tno-gpg-verify\n",
            f"flathub\t{catalog.FLATHUB_URL}/\tdisabled\n",
        )
        for remote in remotes:
            with self.subTest(remote=remote), patch.object(catalog, "flatpak", return_value=remote) as flatpak:
                with self.assertRaisesRegex(RuntimeError, "konfigurasinya tidak cocok"):
                    catalog.install_app(APP)
                self.assertEqual(flatpak.call_args_list, [LIST_REMOTES])

    def test_install_requires_confirmation_from_installed_ref(self):
        with patch.object(catalog, "flatpak", side_effect=[REMOTE, "", ""]) as flatpak:
            with self.assertRaisesRegex(RuntimeError, "belum mengonfirmasi"):
                catalog.install_app(APP)
        self.assertEqual(flatpak.call_args_list, [LIST_REMOTES, INSTALL, INFO])

    def test_failed_download_can_be_retried(self):
        with patch.object(catalog, "flatpak", side_effect=[
            REMOTE, RuntimeError("offline"), REMOTE, "", REF + "\n",
        ]):
            with self.assertRaisesRegex(RuntimeError, "offline"):
                catalog.install_app(APP)
            catalog.install_app(APP)
