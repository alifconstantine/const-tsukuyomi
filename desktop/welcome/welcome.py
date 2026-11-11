#!/usr/bin/python
import subprocess
import sys
from threading import Thread

import gi

from catalog import APPS, install_app, installed_apps

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
            "apps", 0, GLib.OptionFlags.NONE, GLib.OptionArg.NONE, "Open Recommended Apps", None,
        )
        self.window = None
        self.busy = False
        self.installed = None
        self.install_buttons = {}

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        if len(command_line.get_arguments()) != 1:
            return 2
        if self.window is None:
            self.build_window()
        if not self.busy:
            self.show_apps()
        self.window.present()
        return 0

    def build_window(self):
        self.window = Gtk.ApplicationWindow(
            application=self, title="Recommended Apps · Tsukuyomi", default_width=560, default_height=460,
        )
        self.window.connect("close-request", self.close_requested)
        scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.window.set_child(scroll)
        self.stack = Gtk.Stack()
        scroll.set_child(self.stack)
        self.stack.add_named(self.apps_page(), "apps")

    def page(self, title, subtitle):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        for edge in ("top", "bottom", "start", "end"):
            page.set_property(f"margin-{edge}", 24)
        page.append(text_label(title, "title-1"))
        page.append(text_label(subtitle))
        return page

    def apps_page(self):
        page = self.page(
            "Recommended Apps",
            "Install downloads the app and its required runtimes from Flathub for this account.",
        )
        for app_id, (name, description) in APPS.items():
            row = Gtk.Box(spacing=12)
            caption = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3, hexpand=True)
            caption.append(text_label(name, "heading"))
            caption.append(text_label(description))
            row.append(caption)
            action = button("Install", lambda _, selected=app_id: self.start_install(selected))
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
        self.back = button("Shortcut guide", lambda *_: subprocess.Popen(["/usr/lib/constos/welcome/guide.py"]))
        self.refresh = button("Refresh", self.refresh_apps)
        actions.append(self.back)
        actions.append(self.refresh)
        page.append(actions)
        return page

    def show_apps(self, *_):
        self.window.set_title("Recommended Apps · Tsukuyomi")
        self.stack.set_visible_child_name("apps")
        self.refresh_apps()

    def close_requested(self, *_):
        if self.busy:
            return True
        self.window = None
        self.installed = None
        return False

    def refresh_buttons(self):
        for app_id, action in self.install_buttons.items():
            present = self.installed is not None and app_id in self.installed
            action.set_label("Installed" if present else "Install")
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
            self.apps_status.set_label(f"Could not check installed apps. {error}" if error else "")

        self.run_task("Checking installed apps…", installed_apps, completed)

    def start_install(self, app_id):
        if self.busy or self.installed is None or app_id in self.installed:
            return
        name = APPS[app_id][0]

        def completed(_, error):
            if error:
                self.apps_status.set_label(f"Could not install {name}. {error}")
            else:
                self.installed.add(app_id)
                self.apps_status.set_label(f"{name} is installed. Open it from the app launcher.")

        self.run_task(f"Installing {name} from Flathub…", lambda: install_app(app_id), completed)


if __name__ == "__main__":
    sys.exit(Welcome().run(sys.argv))
