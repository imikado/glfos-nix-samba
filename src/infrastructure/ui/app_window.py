import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from infrastructure.ui.remote_list_window import RemoteListWindow
from infrastructure.ui.remote_add_window import RemoteAddWindow


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_title("Nix Samba")
        self.set_default_size(400, 300)

        # Create toolbar view with header bar
        toolbar_view = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()
        toolbar_view.add_top_bar(header_bar)
        
        # 2. Use a ScrolledWindow to prevent the 1.4 million pixel overflow
        scrolled = Gtk.ScrolledWindow()
        #  scrolled.set_hscrollbar_policy(Gtk.PolicyType.NEVER)
        scrolled.set_propagate_natural_height(True)

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

        scrolled.set_child(pref_page_remote)
        toolbar_view.set_content(scrolled)

        toolbar_view.set_content(pref_page_remote)
        self.set_content(toolbar_view)

    def on_list_remote_clicked(self, _button):
        window = RemoteListWindow(self)
        window.present()

    def on_add_remote_clicked(self, _button):
        window = RemoteAddWindow(self)
        window.present()


class AppWindow(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.dupot.glfosnixsamba")

    def do_activate(self):
        win = MainWindow(application=self)
        win.present()
