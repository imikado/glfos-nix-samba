import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


class RemoteAddWindow(Adw.Window):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_title(_('Add Remote Share'))
        self.set_default_size(400, 300)
        self.set_modal(True)
        self.set_transient_for(parent)

        # Create toolbar view with header bar
        toolbar_view = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()
        toolbar_view.add_top_bar(header_bar)

        # Create preferences page for adding a share
        pref_page = Adw.PreferencesPage()

        pref_group = Adw.PreferencesGroup()
        pref_group.set_title(_('Share Details'))
        pref_group.set_description(_('Enter the remote Samba share details'))

        # Server address entry
        self.entry_server = Adw.EntryRow()
        self.entry_server.set_title(_('Server address'))
        pref_group.add(self.entry_server)

        # Share name entry
        self.entry_share = Adw.EntryRow()
        self.entry_share.set_title(_('Share name'))
        pref_group.add(self.entry_share)

        # Username entry
        self.entry_username = Adw.EntryRow()
        self.entry_username.set_title(_('Username'))
        pref_group.add(self.entry_username)

        # Password entry
        self.entry_password = Adw.PasswordEntryRow()
        self.entry_password.set_title(_('Password'))
        pref_group.add(self.entry_password)

        pref_page.add(pref_group)

        # Add button group
        button_group = Adw.PreferencesGroup()

        button_add = Adw.ButtonRow()
        button_add.set_title(_('Add share'))
        button_add.set_start_icon_name('list-add-symbolic')
        button_add.connect('activated', self.on_add_clicked)
        button_group.add(button_add)

        pref_page.add(button_group)

        toolbar_view.set_content(pref_page)
        self.set_content(toolbar_view)

    def on_add_clicked(self, _button):
        server = self.entry_server.get_text()
        share = self.entry_share.get_text()
        username = self.entry_username.get_text()
        print(f"Adding share: //{server}/{share} as {username}")
        self.close()
