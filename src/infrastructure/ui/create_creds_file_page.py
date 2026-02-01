from domain.credentials_file_domain import CredentialsFileDomain

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

class CreateCredsFilePage(Adw.NavigationPage):

    _credentials_file_domain:CredentialsFileDomain
    _navigation_view:Adw.NavigationView


    def __init__(self, credentials_file_domain:CredentialsFileDomain,navigation_view:Adw.NavigationView, show_notification, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._navigation_view=navigation_view

        self._show_notification=show_notification

        self._credentials_file_domain = credentials_file_domain
        self.set_title(_('Create credentials file'))

        field_width=40

        # Create toolbar view with header bar
        toolbar_view = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()
        toolbar_view.add_top_bar(header_bar)

        # Create scrollable content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # Create preferences page
        pref_page = Adw.PreferencesPage()

        # File path group
        file_group = Adw.PreferencesGroup()
        file_group.set_title(_('File'))
        file_group.set_description(_('Path where the credentials file will be saved'))

        row = Adw.ActionRow()
        row.set_title(_('File path'))
        self.entry_path = Gtk.Entry()
        self.entry_path.set_placeholder_text('/home/yourUser/smb-credentials')
        self.entry_path.set_width_chars(field_width)
        self.entry_path.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_path)
        file_group.add(row)

        pref_page.add(file_group)

        # Credentials group
        creds_group = Adw.PreferencesGroup()
        creds_group.set_title(_('Credentials'))
        creds_group.set_description(_('Samba authentication credentials'))

        row = Adw.ActionRow()
        row.set_title(_('Username'))
        self.entry_username = Gtk.Entry()
        self.entry_username.set_placeholder_text('smbuser')
        self.entry_username.set_width_chars(field_width)
        self.entry_username.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_username)
        creds_group.add(row)

        row = Adw.ActionRow()
        row.set_title(_('Password'))
        self.entry_password = Gtk.Entry()
        self.entry_password.set_placeholder_text('password')
        self.entry_password.set_visibility(False)
        self.entry_password.set_width_chars(field_width)
        self.entry_password.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_password)
        creds_group.add(row)

        pref_page.add(creds_group)

        # Save button group
        button_group = Adw.PreferencesGroup()

        button_save = Adw.ButtonRow()
        button_save.set_title(_('Create file'))
        button_save.set_start_icon_name('document-save-symbolic')
        button_save.connect('activated', self.on_save_clicked)
        button_group.add(button_save)

        pref_page.add(button_group)

        scrolled.set_child(pref_page)
        toolbar_view.set_content(scrolled)
        self.set_child(toolbar_view)

    def on_save_clicked(self, _button):
        if not self._validate():
            return

        try:
            self._credentials_file_domain.write_file(
                self.entry_path.get_text().strip(),
                self.entry_username.get_text().strip(),
                self.entry_password.get_text().strip(),
            )
            self._show_notification(_('Credentials file created'))
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

        # File path: required, must start with /
        path = self.entry_path.get_text().strip()
        path_error = not path or not path.startswith('/')
        self._set_row_error(self.entry_path, path_error)
        if path_error:
            valid = False

        # Username: required
        username = self.entry_username.get_text().strip()
        username_error = not username
        self._set_row_error(self.entry_username, username_error)
        if username_error:
            valid = False

        # Password: required
        password = self.entry_password.get_text().strip()
        password_error = not password
        self._set_row_error(self.entry_password, password_error)
        if password_error:
            valid = False

        if not valid:
            self._show_notification(_('There are error during validation'))

        return valid
