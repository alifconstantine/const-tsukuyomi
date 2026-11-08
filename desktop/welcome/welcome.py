#!/usr/bin/python
import subprocess
import sys
from threading import Thread

import gi

from catalog import APPS, dismiss_welcome, install_app, installed_apps, welcome_marker

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib, Gtk


def text_label(text, css=None):
    label = Gtk.Label(label=text, xalign=0, wrap=True, max_width_chars=58)
    if css:
        label.add_css_class(css)
    return label


def button(text, callback):
    widget = Gtk.Button(label=text)
    widget.connect("clicked", callback)
    return widget


class Welcome(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id="org.constos.Welcome",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )
        self.add_main_option(
            "first-login", 0, GLib.OptionFlags.NONE, GLib.OptionArg.NONE, "Buka pada login pertama", None,
        )
        self.add_main_option(
            "apps", 0, GLib.OptionFlags.NONE, GLib.OptionArg.NONE, "Buka Aplikasi Pilihan", None,
        )
        self.marker = welcome_marker()
        self.window = None
        self.busy = False
        self.welcome_opened = False
        self.installed = None
        self.install_buttons = {}

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        first_login = options.contains("first-login")
        apps = options.contains("apps")
        if len(command_line.get_arguments()) != 1 or (first_login and apps):
            return 2
        if first_login and (self.marker.is_file() or self.window is not None):
            return 0
        if self.window is None:
            self.build_window()
        if not self.busy:
            if apps:
                self.show_apps()
            else:
                self.show_welcome()
        self.window.present()
        return 0

    def build_window(self):
        self.window = Gtk.ApplicationWindow(
            application=self, title="Selamat Datang · ConstOS", default_width=560, default_height=460,
        )
        self.window.connect("close-request", self.close_requested)
        scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.window.set_child(scroll)
        self.stack = Gtk.Stack()
        scroll.set_child(self.stack)
        self.stack.add_named(self.welcome_page(), "welcome")
        self.stack.add_named(self.apps_page(), "apps")

    def page(self, title, subtitle):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        for edge in ("top", "bottom", "start", "end"):
            page.set_property(f"margin-{edge}", 24)
        page.append(text_label(title, "title-1"))
        page.append(text_label(subtitle))
        return page

    def welcome_page(self):
        page = self.page("Selamat datang di ConstOS", "Mulai dengan tiga pintasan desktop.")
        for shortcut, purpose in (
            ("Super + Space", "Buka launcher"),
            ("Super + E", "Buka file manager Thunar"),
            ("Super + Enter", "Buka terminal Foot"),
        ):
            page.append(text_label(f"{shortcut}  ·  {purpose}"))
        page.append(text_label("Super biasanya adalah tombol berlogo Windows."))
        page.append(button("Aplikasi Pilihan", self.show_apps))
        self.welcome_status = text_label("")
        page.append(self.welcome_status)
        actions = Gtk.Box(spacing=8, halign=Gtk.Align.END)
        actions.append(button("Lewati", self.finish_welcome))
        done = button("Selesai", self.finish_welcome)
        done.add_css_class("suggested-action")
        actions.append(done)
        page.append(actions)
        return page

    def apps_page(self):
        page = self.page(
            "Aplikasi Pilihan",
            "Tombol Pasang mengunduh aplikasi dan runtime yang diperlukan dari Flathub untuk akun ini.",
        )
        for app_id, (name, description) in APPS.items():
            row = Gtk.Box(spacing=12)
            caption = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3, hexpand=True)
            caption.append(text_label(name, "heading"))
            caption.append(text_label(description))
            row.append(caption)
            action = button("Pasang", lambda _, selected=app_id: self.start_install(selected))
            action.set_valign(Gtk.Align.CENTER)
            action.set_sensitive(False)
            self.install_buttons[app_id] = action
            row.append(action)
            page.append(row)
        status = Gtk.Box(spacing=8)
        self.spinner = Gtk.Spinner()
        self.apps_status = text_label("")
        self.apps_status.set_selectable(True)
        status.append(self.spinner)
        status.append(self.apps_status)
        page.append(status)
        actions = Gtk.Box(spacing=8)
        self.back = button("Kembali ke Selamat Datang", self.show_welcome)
        self.refresh = button("Muat ulang", self.refresh_apps)
        actions.append(self.back)
        actions.append(self.refresh)
        page.append(actions)
        return page

    def show_welcome(self, *_):
        self.welcome_opened = True
        self.window.set_title("Selamat Datang · ConstOS")
        self.stack.set_visible_child_name("welcome")

    def show_apps(self, *_):
        self.window.set_title("Aplikasi Pilihan · ConstOS")
        self.stack.set_visible_child_name("apps")
        self.refresh_apps()

    def save_dismissal(self):
        if self.welcome_opened:
            try:
                dismiss_welcome(self.marker)
            except OSError:
                self.show_welcome()
                self.welcome_status.set_label("Status Welcome gagal disimpan. Periksa izin direktori pengguna.")
                return False
        return True

    def finish_welcome(self, *_):
        self.window.close()

    def close_requested(self, *_):
        if self.busy or not self.save_dismissal():
            return True
        self.window = None
        self.welcome_opened = False
        self.installed = None
        return False

    def refresh_buttons(self):
        for app_id, action in self.install_buttons.items():
            present = self.installed is not None and app_id in self.installed
            action.set_label("Terpasang" if present else "Pasang")
            action.set_sensitive(not self.busy and self.installed is not None and not present)
        self.back.set_sensitive(not self.busy)
        self.refresh.set_sensitive(not self.busy)

    def run_task(self, message, task, completed):
        self.busy = True
        self.window.set_deletable(False)
        self.refresh_buttons()
        self.apps_status.set_label(message)
        self.spinner.start()

        def work():
            try:
                result = task()
            except (OSError, RuntimeError, subprocess.SubprocessError) as error:
                GLib.idle_add(self.finish_task, completed, None, error)
            else:
                GLib.idle_add(self.finish_task, completed, result, None)

        Thread(target=work, daemon=True).start()

    def finish_task(self, completed, result, error):
        self.busy = False
        self.window.set_deletable(True)
        self.spinner.stop()
        completed(result, error)
        self.refresh_buttons()
        return GLib.SOURCE_REMOVE

    def refresh_apps(self, *_):
        def completed(result, error):
            self.installed = result
            self.apps_status.set_label(f"Gagal memeriksa aplikasi. {error}" if error else "")

        self.run_task("Memeriksa aplikasi yang terpasang…", installed_apps, completed)

    def start_install(self, app_id):
        if self.busy or self.installed is None or app_id in self.installed:
            return
        name = APPS[app_id][0]

        def completed(_, error):
            if error:
                self.apps_status.set_label(f"Gagal memasang {name}. {error}")
            else:
                self.installed.add(app_id)
                self.apps_status.set_label(f"{name} terpasang. Buka dari launcher.")

        self.run_task(f"Memasang {name} dari Flathub…", lambda: install_app(app_id), completed)


if __name__ == "__main__":
    sys.exit(Welcome().run(sys.argv))
