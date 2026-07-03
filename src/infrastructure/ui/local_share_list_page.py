from domain.local_share_domain import LocalShareDomain
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from infrastructure.ui.local_share_edit_page import LocalShareEditPage


class LocalShareListPage(Adw.NavigationPage):

    _local_share_domain:LocalShareDomain
    _navigation_view:Adw.NavigationView


    def __init__(self, local_share_domain:LocalShareDomain, navigation_view:Adw.NavigationView,show_notification, on_save_clicked, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._navigation_view=navigation_view

        self._show_notification=show_notification
        self._on_save_clicked=on_save_clicked
        self.set_title(_('Local Shares'))

        self._local_share_domain=local_share_domain

        self._navigation_view.connect('popped', self._on_page_popped)

        self.build()

    def build(self):
        local_share_list = self._local_share_domain.get_list()

        # Create toolbar view with header bar
        toolbar_view = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()

        # Save button in header bar
        save_button = Gtk.Button()
        save_button.set_icon_name('media-floppy-symbolic')
        save_button.set_label(_('Save on disk'))
        save_button.set_tooltip_text(_('Save on disk'))
        save_button.connect('clicked', self._on_save_clicked)
        save_button.add_css_class('destructive-action')
        save_button.set_sensitive(self._local_share_domain.need_to_save())
        self.save_button = save_button
        header_bar.pack_end(save_button)

        toolbar_view.add_top_bar(header_bar)

        # Create preferences page for listing shares
        pref_page = Adw.PreferencesPage()

        pref_group = Adw.PreferencesGroup()
        pref_group.set_title(_('Available Shares'))
        pref_group.set_description(_('List of local folders shared via Samba'))

        for local_share_loop in local_share_list:
            row = Adw.ActionRow()
            row.set_title(local_share_loop.name)
            row.set_subtitle(local_share_loop.path)
            row.set_icon_name('folder-symbolic')

            # Add edit button
            edit_button = Gtk.Button()
            edit_button.set_icon_name('document-edit-symbolic')
            edit_button.set_valign(Gtk.Align.CENTER)
            edit_button.add_css_class('flat')
            edit_button.connect('clicked', self.on_edit_clicked, local_share_loop)
            row.add_suffix(edit_button)

            # Add delete button
            delete_button = Gtk.Button()
            delete_button.set_icon_name('user-trash-symbolic')
            delete_button.set_valign(Gtk.Align.CENTER)
            delete_button.add_css_class('flat')
            delete_button.add_css_class('destructive-action')
            delete_button.connect('clicked', self.on_delete_clicked, local_share_loop)
            row.add_suffix(delete_button)

            pref_group.add(row)

        pref_page.add(pref_group)

        toolbar_view.set_content(pref_page)
        self.set_child(toolbar_view)


    def _on_page_popped(self, _navigation_view, _page):
        self.build()


    def on_edit_clicked(self, _button, local_share):
        page = LocalShareEditPage(self._local_share_domain,self._navigation_view, local_share,self._show_notification)
        self._navigation_view.push(page)

    def on_delete_clicked(self, _button, local_share):
        dialog = Adw.AlertDialog()
        dialog.set_heading(_('Delete Share'))
        dialog.set_body(_('Are you sure you want to delete the share "%s"?') % local_share.name)

        dialog.add_response('cancel', _('Cancel'))
        dialog.add_response('delete', _('Delete'))
        dialog.set_response_appearance('delete', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response('cancel')
        dialog.set_close_response('cancel')

        dialog.connect('response', self._on_delete_response, local_share)
        dialog.present(self.get_root())

    def _on_delete_response(self, _dialog, response, local_share):
        if response != 'delete':
            return

        self._local_share_domain.delete_item(local_share.name)
        self.build()
