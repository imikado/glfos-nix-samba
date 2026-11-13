import os
import pwd

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


NO_LOGIN_SHELLS = ('nologin', 'false')


def list_human_users() -> list:
    """Return sorted names of "normal" (human) accounts.

    Keeps regular UIDs (1000-65533) with a real login shell, which excludes
    system accounts, `nobody` and NixOS build users (nixbld*, /sbin/nologin).
    """
    users = []
    for entry in pwd.getpwall():
        if entry.pw_uid < 1000 or entry.pw_uid >= 65534:
            continue
        if os.path.basename(entry.pw_shell or '') in NO_LOGIN_SHELLS:
            continue
        if entry.pw_name.startswith('nixbld'):
            continue
        users.append(entry.pw_name)
    return sorted(set(users))


class ValidUsersRow(Adw.ExpanderRow):
    """Expander row listing human users with a checkbox each."""

    def __init__(self, selected_users=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        selected_users = list(selected_users or [])

        self.set_title(_('Valid users'))
        self.set_subtitle(_('Each user needs a Samba password set with smbpasswd -a USERNAME'))

        # Keep users already configured even if they are not detected as human
        user_names = list_human_users()
        user_names += [name for name in selected_users if name not in user_names]

        self._checks = {}
        for user_name in user_names:
            row = Adw.ActionRow()
            row.set_title(user_name)
            check = Gtk.CheckButton()
            check.set_active(user_name in selected_users)
            check.set_valign(Gtk.Align.CENTER)
            check.connect('toggled', lambda _check: self._update_subtitle())
            row.add_prefix(check)
            row.set_activatable_widget(check)
            self.add_row(row)
            self._checks[user_name] = check

        if not user_names:
            row = Adw.ActionRow()
            row.set_title(_('No user found'))
            row.set_sensitive(False)
            self.add_row(row)

        self._default_subtitle = self.get_subtitle()
        self._update_subtitle()

    def _update_subtitle(self):
        selected = self.get_selected_users()
        self.set_subtitle(', '.join(selected) if selected else self._default_subtitle)

    def get_selected_users(self) -> list:
        return [name for name, check in self._checks.items() if check.get_active()]
