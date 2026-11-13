import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from domain.local_share_domain import LocalShareDomain


class DedicatedAccountRows:
    """Rows to define the account created only for a local share.

    The account is a system user without Unix password and with a nologin shell:
    it cannot be used to log in to the computer, only to connect to this share.
    """

    def __init__(self, group: Adw.PreferencesGroup, local_share_domain: LocalShareDomain, original_user: str = '', original_password: str = ''):
        self._local_share_domain = local_share_domain
        # Account of the share being edited: its password may be left unchanged
        self._original_user = original_user
        self._original_password = original_password

        self.row_info = Adw.ActionRow()
        self.row_info.set_title(_('Account dedicated to this share'))
        self.row_info.set_subtitle(_('Created for this share only: it cannot be used to log in to the computer'))
        info_icon = Gtk.Image.new_from_icon_name('dialog-information-symbolic')
        self.row_info.add_prefix(info_icon)
        group.add(self.row_info)

        self.entry_user = Adw.EntryRow()
        self.entry_user.set_title(_('Account name'))
        self.entry_user.set_text(original_user)
        group.add(self.entry_user)

        self.entry_password = Adw.PasswordEntryRow()
        if original_user:
            self.entry_password.set_title(_('New password (leave empty to keep the current one)'))
        else:
            self.entry_password.set_title(_('Password'))
        group.add(self.entry_password)

        self.entry_password_confirm = Adw.PasswordEntryRow()
        self.entry_password_confirm.set_title(_('Confirm password'))
        group.add(self.entry_password_confirm)

    def set_visible(self, visible: bool):
        for row in (self.row_info, self.entry_user, self.entry_password, self.entry_password_confirm):
            row.set_visible(visible)

    def get_user(self) -> str:
        return self.entry_user.get_text().strip()

    def get_password(self) -> str:
        """New password, or the one still pending for the unchanged account ('' = keep)."""
        password = self.entry_password.get_text()
        if not password and self.get_user() == self._original_user:
            return self._original_password
        return password

    def _set_row_error(self, row, has_error):
        if has_error:
            row.add_css_class('error')
        else:
            row.remove_css_class('error')

    def validate(self, share_name_to_ignore: str = None) -> list:
        """Return the error messages (empty list when valid)."""
        error_list = []

        user = self.get_user()
        user_error = False
        if not self._local_share_domain.is_dedicated_user_name_valid(user):
            user_error = True
            error_list.append(_('Account name: lowercase letters, digits, "-" and "_" only'))
        elif not self._local_share_domain.is_dedicated_user_available(user, share_name_to_ignore):
            user_error = True
            error_list.append(_('This account name is already used'))
        self._set_row_error(self.entry_user, user_error)

        password = self.entry_password.get_text()
        password_confirm = self.entry_password_confirm.get_text()
        password_required = user != self._original_user

        password_error = False
        if password_required and not password:
            password_error = True
            error_list.append(_('A password is required for a new account'))
        elif '\n' in password or '\r' in password:
            password_error = True
            error_list.append(_('The password cannot contain a line break'))
        self._set_row_error(self.entry_password, password_error)

        confirm_error = password != password_confirm
        if confirm_error:
            error_list.append(_('Passwords do not match'))
        self._set_row_error(self.entry_password_confirm, confirm_error)

        return error_list
