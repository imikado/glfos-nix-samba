import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from infrastructure.ui.remote_list_page import RemoteListPage
from infrastructure.ui.remote_add_page import RemoteAddPage


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_title("Nix Samba")
        self.set_default_size(800, 600)

        # Create navigation view for in-window navigation
        self.navigation_view = Adw.NavigationView()
        self.set_content(self.navigation_view)

        # Create and push the home page
        home_page = self._create_home_page()
        self.navigation_view.push(home_page)

    def _create_home_page(self):
        page = Adw.NavigationPage.new(self._create_home_content(), _('Nix Samba'))
        return page

    def _create_home_content(self):
        # Create toolbar view with header bar
        toolbar_view = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()
        toolbar_view.add_top_bar(header_bar)

        # Create preferences page
        pref_page_remote = Adw.PreferencesPage()
        pref_page_remote.set_title(_('Remote share'))

        # First group
        pref_group_remote = Adw.PreferencesGroup()
        pref_group_remote.set_title(_('Remote share'))
        pref_group_remote.set_description(_('Mange your remote samba shares'))

        # List remote shares button
        button_remote_list = Adw.ButtonRow()
        button_remote_list.set_title(_('List remote shares'))
        button_remote_list.set_start_icon_name('view-list-symbolic')
        button_remote_list.connect('activated', self.on_list_remote_clicked)
        pref_group_remote.add(button_remote_list)

        # Add remote share button
        button_remote_add = Adw.ButtonRow()
        button_remote_add.set_title(_('Add remote share'))
        button_remote_add.set_start_icon_name('list-add-symbolic')
        button_remote_add.connect('activated', self.on_add_remote_clicked)
        pref_group_remote.add(button_remote_add)

        pref_page_remote.add(pref_group_remote)
        toolbar_view.set_content(pref_page_remote)

        return toolbar_view

    def on_list_remote_clicked(self, _button):
        page = RemoteListPage(self.navigation_view)
        self.navigation_view.push(page)

    def on_add_remote_clicked(self, _button):
        page = RemoteAddPage(self.navigation_view)
        self.navigation_view.push(page)


class AppWindow(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.dupot.glfosnixsamba")

    def do_activate(self):
        win = MainWindow(application=self)
        win.present()
