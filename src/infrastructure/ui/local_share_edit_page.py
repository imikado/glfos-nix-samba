import re

from domain.entity.local_share import LocalShare
from domain.local_share_domain import LocalShareDomain
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from infrastructure.ui.dedicated_account_rows import DedicatedAccountRows
from infrastructure.ui.valid_users_row import ValidUsersRow


ACCESS_MODE_GUEST = 0
ACCESS_MODE_USERS = 1
ACCESS_MODE_DEDICATED = 2


class LocalShareEditPage(Adw.NavigationPage):

    _local_share_domain:LocalShareDomain
    _navigation_view:Adw.NavigationView

    def __init__(self, local_share_domain:LocalShareDomain, navigation_view:Adw.NavigationView, local_share:LocalShare, show_notification, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._navigation_view=navigation_view
        self._show_notification=show_notification

        self._local_share_domain = local_share_domain
        self.local_share = local_share
        self.set_title(_('Edit Local Share'))

        field_width=360  # pixels: fixed so entries with an icon keep the same width

        # Create toolbar view with header bar
        toolbar_view = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()
        toolbar_view.add_top_bar(header_bar)

        # Create scrollable content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # Create preferences page
        pref_page = Adw.PreferencesPage()

        # Basic settings group
        basic_group = Adw.PreferencesGroup()
        basic_group.set_title(_('Basic Settings'))
        basic_group.set_description(_('Local folder to share on your network'))

        row = Adw.ActionRow()
        row.set_title(_('Share name'))
        self.entry_name = Gtk.Entry()
        self.entry_name.set_placeholder_text(_('MyShare'))
        self.entry_name.set_text(local_share.name or '')
        self.entry_name.set_size_request(field_width, -1)
        self.entry_name.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_name)
        basic_group.add(row)

        row = Adw.ActionRow()
        row.set_title(_('Local folder'))
        self.entry_path = Gtk.Entry()
        self.entry_path.set_placeholder_text('/home/user/Shared')
        self.entry_path.set_text(local_share.path or '')
        self.entry_path.set_size_request(field_width, -1)
        self.entry_path.set_valign(Gtk.Align.CENTER)
        self.entry_path.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, 'folder-open-symbolic')
        self.entry_path.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, _('Browse for folder'))
        self.entry_path.connect('icon-press', lambda entry, _icon_pos: self._on_browse_folder(entry))
        row.add_suffix(self.entry_path)
        basic_group.add(row)

        row = Adw.ActionRow()
        row.set_title(_('Comment'))
        self.entry_comment = Gtk.Entry()
        self.entry_comment.set_placeholder_text(_('Optional description'))
        self.entry_comment.set_text(local_share.comment or '')
        self.entry_comment.set_size_request(field_width, -1)
        self.entry_comment.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_comment)
        basic_group.add(row)

        pref_page.add(basic_group)

        # Access group
        access_group = Adw.PreferencesGroup()
        access_group.set_title(_('Access'))
        access_group.set_description(_('Who can access this share and how'))

        self.combo_access_mode = Adw.ComboRow()
        self.combo_access_mode.set_title(_('Access mode'))
        self.combo_access_mode.set_subtitle(_('Who can connect to this share'))
        access_mode_options = Gtk.StringList.new([
            _('Guest access (no login required)'),
            _('Restricted to specific users'),
            _('Dedicated account (this share only)'),
        ])
        self.combo_access_mode.set_model(access_mode_options)
        self.combo_access_mode.connect('notify::selected', self._on_access_mode_changed)
        access_group.add(self.combo_access_mode)

        self.row_valid_users = ValidUsersRow(local_share.valid_users)
        access_group.add(self.row_valid_users)

        self.dedicated_account_rows = DedicatedAccountRows(
            access_group, local_share_domain, local_share.dedicated_user, local_share.dedicated_password)

        if local_share.guest_ok:
            self.combo_access_mode.set_selected(ACCESS_MODE_GUEST)
        elif local_share.has_dedicated_user():
            self.combo_access_mode.set_selected(ACCESS_MODE_DEDICATED)
        else:
            self.combo_access_mode.set_selected(ACCESS_MODE_USERS)
        self._on_access_mode_changed(self.combo_access_mode, None)

        self.switch_read_only = Adw.SwitchRow()
        self.switch_read_only.set_title(_('Read only'))
        self.switch_read_only.set_subtitle(_('Prevent writing to this share'))
        self.switch_read_only.set_active(local_share.read_only)
        access_group.add(self.switch_read_only)

        pref_page.add(access_group)

        # Save button group
        button_group = Adw.PreferencesGroup()

        button_save = Adw.ButtonRow()
        button_save.set_title(_('Update share'))
        button_save.set_start_icon_name('document-save-symbolic')
        button_save.connect('activated', self.on_save_clicked)
        button_group.add(button_save)

        pref_page.add(button_group)

        scrolled.set_child(pref_page)
        toolbar_view.set_content(scrolled)
        self.set_child(toolbar_view)

    def _on_browse_folder(self, _button):
        dialog = Gtk.FileDialog()
        dialog.set_title(_('Select folder to share'))
        dialog.select_folder(self.get_root(), None, self._on_folder_selected)

    def _on_folder_selected(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                self.entry_path.set_text(folder.get_path())
        except Exception:
            pass

    def _on_access_mode_changed(self, combo_row, _param):
        access_mode = combo_row.get_selected()
        self.row_valid_users.set_visible(access_mode == ACCESS_MODE_USERS)
        self.dedicated_account_rows.set_visible(access_mode == ACCESS_MODE_DEDICATED)

    def _build_local_share(self) -> LocalShare:
        access_mode = self.combo_access_mode.get_selected()
        path = self.entry_path.get_text().strip()

        local_share = LocalShare(
            name=self.entry_name.get_text().strip(),
            path=path,
            comment=self.entry_comment.get_text().strip(),
            guest_ok=access_mode == ACCESS_MODE_GUEST,
            read_only=self.switch_read_only.get_active(),
        )

        if access_mode == ACCESS_MODE_USERS:
            local_share.valid_users = self.row_valid_users.get_selected_users()
        elif access_mode == ACCESS_MODE_DEDICATED:
            local_share.dedicated_user = self.dedicated_account_rows.get_user()
            local_share.dedicated_password = self.dedicated_account_rows.get_password()
            # The dedicated account has no right on the folder: files are accessed as its owner
            local_share.force_user = self._local_share_domain.get_folder_owner(path)

        return local_share

    def on_save_clicked(self, _button):
        if not self._validate():
            return

        local_share_to_update = self._build_local_share()

        try:
            self._local_share_domain.edit_item(self.local_share.name, local_share_to_update)

            self._show_notification(_('Save in memory, don\'t forget to press the top save button'))

            self._navigation_view.pop()
        except PermissionError as e:
            error_dialog = Adw.AlertDialog()
            error_dialog.set_heading(_('Error'))
            error_dialog.set_body(str(e))
            error_dialog.add_response('ok', _('OK'))
            error_dialog.present(self.get_root())

    def _set_row_error(self, row, has_error):
        if has_error:
            row.add_css_class('error')
        else:
            row.remove_css_class('error')

    def _validate(self) -> bool:
        valid = True

        # Share name: required, safe for a smb.conf section header
        name = self.entry_name.get_text().strip()
        name_error = not name or not re.match(r'^[A-Za-z0-9 _.-]+$', name)
        self._set_row_error(self.entry_name, name_error)
        if name_error:
            valid = False

        # Local folder: required, must be absolute
        path = self.entry_path.get_text().strip()
        path_error = not path or not path.startswith('/')
        self._set_row_error(self.entry_path, path_error)
        if path_error:
            valid = False

        # Valid users: required when access is restricted
        access_mode = self.combo_access_mode.get_selected()
        valid_users_error = access_mode == ACCESS_MODE_USERS and not self.row_valid_users.get_selected_users()
        self._set_row_error(self.row_valid_users, valid_users_error)
        if valid_users_error:
            valid = False

        # Dedicated account: name, availability and password
        dedicated_error_list = []
        if access_mode == ACCESS_MODE_DEDICATED:
            dedicated_error_list = self.dedicated_account_rows.validate(self.local_share.name)
            if dedicated_error_list:
                valid = False

        if dedicated_error_list:
            self._show_notification(dedicated_error_list[0])
        elif not valid:
            self._show_notification(_('There are error during validation'))

        return valid
