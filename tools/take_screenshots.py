#!/usr/bin/env python3
"""Generate the README screenshots (docs/screenshots/*.png).

The application is started with fake data: nothing is read from or written to
/etc/nixos, the real bookmarks, the desktop or the system user list. Each page
is opened in turn and the window is rendered to a PNG file.

Usage (from the repository root, inside `nix develop`):

    python tools/take_screenshots.py                 # English, light theme
    python tools/take_screenshots.py --lang fr --theme dark --output /tmp/shots

A display is required (X11 or Wayland session); the window is visible while
the screenshots are taken.
"""

import argparse
import gettext
import os
import sys
from types import SimpleNamespace

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, 'src')
sys.path.insert(0, SRC_DIR)

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw, GLib, Graphene, Gtk

# ---------------------------------------------------------------------------
# Fake data
# ---------------------------------------------------------------------------

FAKE_USERS = [
    SimpleNamespace(pw_name='alice', pw_uid=1000),
    SimpleNamespace(pw_name='bob', pw_uid=1001),
]

FAKE_GROUPS = [
    SimpleNamespace(gr_name='users', gr_gid=100),
    SimpleNamespace(gr_name='alice', gr_gid=1000),
]


def fake_file_systems() -> dict:
    # Fresh lists on every call: RemoteShare.set_options() mutates them
    return {
        '/media/nas-photos': {
            'device': '//192.168.1.10/photos',
            'fsType': 'cifs',
            'options': [
                'credentials=/home/alice/.smb-credentials',
                'noauto', 'x-systemd.automount',
                'x-systemd.idle-timeout=60',
                'x-systemd.device-timeout=5s',
                'x-systemd.mount-timeout=5s',
                'uid=1000', 'gid=100',
            ],
        },
        '/media/nas-music': {
            'device': '//192.168.1.10/music',
            'fsType': 'cifs',
            'options': [
                'credentials=/home/alice/.smb-credentials',
                'x-systemd.automount',
                'uid=1000', 'gid=100',
            ],
        },
        '/media/backup': {
            'device': '//backup-server/backup',
            'fsType': 'cifs',
            'options': [
                'credentials=/home/alice/.smb-backup',
                'noauto', 'x-systemd.automount',
                'uid=1000', 'gid=100',
            ],
        },
    }


FAKE_BOOKMARKS = [
    'file:///media/nas-photos NAS Photos',
    'file:///media/nas-music NAS Music',
    'file:///media/backup Backup',
]

FAKE_DESKTOP_SHORTCUTS = ['/media/nas-photos']

FAKE_SAMBA_SETTINGS = {
    'global': {'workgroup': 'WORKGROUP'},
    'Public': {
        'path': '/home/alice/Public',
        'comment': 'Files shared with everyone',
        'guest ok': 'yes',
        'read only': 'yes',
    },
    'Documents': {
        'path': '/home/alice/Documents',
        'comment': 'Family documents',
        'guest ok': 'no',
        'read only': 'no',
        'valid users': 'alice bob',
    },
}


class FakeSystemApi:
    """Read-only stand-in for SystemApi: never touches the real system."""

    def is_current_desktop_kde(self) -> bool:
        return False

    def get_current_desktop(self) -> str:
        return 'gnome'

    def get_gtk_bookmark_list(self) -> list:
        return list(FAKE_BOOKMARKS)

    def get_kde_bookmark_list(self) -> list:
        return list(FAKE_BOOKMARKS)

    def has_desktop_shortcut(self, mount_path: str) -> bool:
        return mount_path in FAKE_DESKTOP_SHORTCUTS

    def file_exists(self, path: str) -> bool:
        return True

    def __getattr__(self, name):
        # Any write/sudo/rebuild method is a no-op
        return lambda *args, **kwargs: None


class FakeSambaFileApi:
    def get_nix_dict(self) -> dict:
        return {'fileSystems': fake_file_systems()}

    def convert_remote_list_to_nix_content(self, remote_file_list: list) -> str:
        return ''


class FakeLocalSambaFileApi:
    def get_nix_dict(self) -> dict:
        return dict(FAKE_SAMBA_SETTINGS)

    def convert_local_share_list_to_nix_content(self, local_share_list: list) -> str:
        return ''

    def get_nix_file_path(self) -> str:
        return '/etc/nixos/customConfig/samba-server.nix'


class FakeNetworkDiscoveryApi:
    def is_host_discovery_available(self) -> bool:
        return True

    def discover_hosts(self) -> list:
        from domain.entity.samba_host import SambaHost
        return [
            SambaHost('NAS', 'nas.local', '192.168.1.10'),
            SambaHost('backup-server', 'backup-server.local', '192.168.1.20'),
        ]

    def is_share_listing_available(self) -> bool:
        return True

    def list_shares(self, host, username='', password='', workgroup='') -> list:
        return ['music', 'photos', 'videos', 'IPC$']

    def read_credentials_file(self, path) -> str:
        return 'username=alice\npassword=secret\n'


def install_fakes():
    import grp
    import pwd

    import infrastructure.ui.app_window as app_window

    pwd.getpwall = lambda: list(FAKE_USERS)
    grp.getgrall = lambda: list(FAKE_GROUPS)

    app_window.SystemApi = FakeSystemApi
    app_window.SambaFileApi = FakeSambaFileApi
    app_window.LocalSambaFileApi = FakeLocalSambaFileApi

    import infrastructure.ui.remote_add_page as remote_add_page
    import infrastructure.ui.remote_edit_page as remote_edit_page
    remote_add_page.NetworkDiscoveryApi = FakeNetworkDiscoveryApi
    remote_edit_page.NetworkDiscoveryApi = FakeNetworkDiscoveryApi


# ---------------------------------------------------------------------------
# Screenshot scenario
# ---------------------------------------------------------------------------

def build_steps(win) -> list:
    """List of (file name, function that shows the page to capture)."""
    from domain.credentials_file_domain import CredentialsFileDomain
    from infrastructure.ui.create_creds_file_page import CreateCredsFilePage
    from infrastructure.ui.local_share_add_page import LocalShareAddPage
    from infrastructure.ui.local_share_edit_page import LocalShareEditPage
    from infrastructure.ui.local_share_list_page import LocalShareListPage
    from infrastructure.ui.remote_add_page import RemoteAddPage
    from infrastructure.ui.remote_edit_page import RemoteEditPage
    from infrastructure.ui.remote_list_page import RemoteListPage

    nav = win.navigation_view
    notify = win.show_notification
    remote_domain = win._remote_domain
    local_domain = win._local_share_domain

    def show(page_factory=None, after_push=None):
        def run():
            # Close the dialog left open by a previous step
            dialog = win.get_visible_dialog()
            if dialog is not None:
                dialog.force_close()
            nav.pop_to_tag('home')
            if page_factory is not None:
                page = page_factory()
                nav.push(page)
                if after_push is not None:
                    after_push(page)
        return run

    return [
        ('01-home.png', show()),
        ('02-remote-list.png', show(lambda: RemoteListPage(
            remote_domain, nav, notify, win.on_save_clicked))),
        ('03-remote-edit.png', show(lambda: RemoteEditPage(
            remote_domain, nav, remote_domain.get_list()[0], notify))),
        ('04-remote-add.png', show(lambda: RemoteAddPage(
            remote_domain, nav, notify))),
        ('05-credentials.png', show(lambda: CreateCredsFilePage(
            CredentialsFileDomain(FakeSystemApi()), nav, notify))),
        ('06-local-list.png', show(lambda: LocalShareListPage(
            local_domain, nav, notify, win.on_save_clicked))),
        ('07-local-edit.png', show(lambda: LocalShareEditPage(
            local_domain, nav, local_domain.get_list()[1], notify))),
        ('08-local-add.png', show(lambda: LocalShareAddPage(
            local_domain, nav, notify))),
        ('09-remote-browse.png', show(lambda: RemoteEditPage(
            remote_domain, nav, remote_domain.get_list()[0], notify),
            after_push=lambda page: page._on_browse_remote_address(None))),
    ]


def save_window_png(win, path: str):
    width = win.get_width()
    height = win.get_height()

    paintable = Gtk.WidgetPaintable.new(win)
    snapshot = Gtk.Snapshot()
    paintable.snapshot(snapshot, width, height)
    node = snapshot.to_node()
    if node is None:
        raise RuntimeError('Nothing rendered for ' + path)

    renderer = win.get_renderer()
    bounds = Graphene.Rect().init(0, 0, width, height)
    texture = renderer.render_texture(node, bounds)
    texture.save_to_png(path)
    print('saved ' + os.path.relpath(path, os.getcwd()))


class ScreenshotApp(Adw.Application):

    def __init__(self, args):
        super().__init__(application_id='org.dupot.glfosnixsamba.screenshots')
        self._args = args
        self._steps = []
        self._win = None
        self.exit_code = 0

    def do_activate(self):
        from infrastructure.ui.app_window import MainWindow

        Gtk.Settings.get_default().set_property('gtk-icon-theme-name', 'Adwaita')
        # No transition animation between pages: captures are deterministic
        Gtk.Settings.get_default().set_property('gtk-enable-animations', False)

        scheme = Adw.ColorScheme.FORCE_DARK if self._args.theme == 'dark' else Adw.ColorScheme.FORCE_LIGHT
        Adw.StyleManager.get_default().set_color_scheme(scheme)

        win = MainWindow(application=self)
        win.set_default_size(self._args.width, self._args.height)
        win.navigation_view.get_visible_page().set_tag('home')
        win.present()

        self._win = win
        self._steps = build_steps(win)
        GLib.timeout_add(self._args.delay, self._next_step)

    def _next_step(self):
        if not self._steps:
            self.quit()
            return GLib.SOURCE_REMOVE

        file_name, show_page = self._steps.pop(0)
        try:
            show_page()
        except Exception as error:
            print('ERROR showing ' + file_name + ': ' + str(error), file=sys.stderr)
            self.exit_code = 1
            self.quit()
            return GLib.SOURCE_REMOVE

        # The window may not have the focus (it is started from a terminal):
        # drop the "backdrop" state so it is rendered as an active window
        self._win.unset_state_flags(Gtk.StateFlags.BACKDROP)

        # Let GTK lay out and draw the new page before capturing it
        GLib.timeout_add(self._args.delay, self._capture, file_name)
        return GLib.SOURCE_REMOVE

    def _capture(self, file_name):
        # No keyboard focus ring on the first row/field
        self._win.set_focus(None)
        try:
            save_window_png(self._win, os.path.join(self._args.output, file_name))
        except Exception as error:
            print('ERROR capturing ' + file_name + ': ' + str(error), file=sys.stderr)
            self.exit_code = 1
        GLib.idle_add(self._next_step)
        return GLib.SOURCE_REMOVE


def main():
    parser = argparse.ArgumentParser(description='Generate the README screenshots.')
    parser.add_argument('--lang', default='en', choices=['en', 'fr'], help='interface language (default: en)')
    parser.add_argument('--theme', default='light', choices=['light', 'dark'], help='color scheme (default: light)')
    parser.add_argument('--output', default=os.path.join(REPO_ROOT, 'docs', 'screenshots'),
                        help='output directory (default: docs/screenshots)')
    parser.add_argument('--width', type=int, default=800, help='window width (default: 800)')
    parser.add_argument('--height', type=int, default=600, help='window height (default: 600)')
    parser.add_argument('--delay', type=int, default=400,
                        help='milliseconds to wait before each capture (default: 400)')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    localedir = os.path.join(SRC_DIR, 'infrastructure', 'locales')
    from main import _compile_mo_if_needed
    _compile_mo_if_needed(localedir, 'nix-samba')
    gettext.translation('nix-samba', localedir, fallback=True, languages=[args.lang]).install()

    install_fakes()

    app = ScreenshotApp(args)
    app.run(None)
    sys.exit(app.exit_code)


if __name__ == '__main__':
    main()
