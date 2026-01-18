from domain.remote_domain import RemoteDomain
import gi
from infrastructure.api.nix_file_api import NixFileApi
from infrastructure.api.system_api import SystemApi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from infrastructure.ui.remote_edit_window import RemoteEditWindow


class RemoteListWindow(Adw.Window):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)

        remote_domain= RemoteDomain(SystemApi(),NixFileApi())

        remote_list=remote_domain.get_list()

        self.set_title(_('Remote Shares'))
        self.set_default_size(500, 400)
        self.set_modal(True)
        self.set_transient_for(parent)

        # Create toolbar view with header bar
        toolbar_view = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()
        toolbar_view.add_top_bar(header_bar)

        # Create preferences page for listing shares
        pref_page = Adw.PreferencesPage()

        pref_group = Adw.PreferencesGroup()
        pref_group.set_title(_('Available Shares'))
        pref_group.set_description(_('List of remote Samba shares'))

        for remote_loop in remote_list:
            row = Adw.ActionRow()
            row.set_title(remote_loop.path)
            row.set_subtitle(remote_loop.remote_path)
            row.set_icon_name('folder-remote-symbolic')

            # Add edit button
            edit_button = Gtk.Button()
            edit_button.set_icon_name('document-edit-symbolic')
            edit_button.set_valign(Gtk.Align.CENTER)
            edit_button.add_css_class('flat')
            edit_button.connect('clicked', self.on_edit_clicked, remote_loop)
            row.add_suffix(edit_button)

            pref_group.add(row)

        

        pref_page.add(pref_group)

        toolbar_view.set_content(pref_page)
        self.set_content(toolbar_view)

    def on_edit_clicked(self, _button, remote):
        window = RemoteEditWindow(self, remote)
        window.present()
