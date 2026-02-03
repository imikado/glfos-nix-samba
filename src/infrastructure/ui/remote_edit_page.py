import re
import pwd
import grp

from domain.entity.remote_share import RemoteShare
from domain.remote_domain import RemoteDomain
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


class RemoteEditPage(Adw.NavigationPage):

    _remote_domain:RemoteDomain
    _navigation_view:Adw.NavigationView

    def __init__(self, remote_domain:RemoteDomain, navigation_view:Adw.NavigationView, remote: RemoteShare,show_notification, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._navigation_view=navigation_view
        self._show_notification=show_notification

        self._remote_domain = remote_domain
        self.remote = remote
        self.set_title(_('Edit Remote Share'))

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

        # Basic settings group
        basic_group = Adw.PreferencesGroup()
        basic_group.set_title(_('Basic Settings'))
        basic_group.set_description(_('Mount point and remote share configuration'))

        row = Adw.ActionRow()
        row.set_title(_('Mount path'))
        self.entry_mount_path = Gtk.Entry()
        self.entry_mount_path.set_placeholder_text('/media/myshare')
        self.entry_mount_path.set_text(remote.path or '')
        self.entry_mount_path.set_width_chars(field_width)
        self.entry_mount_path.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_mount_path)
        basic_group.add(row)

        row = Adw.ActionRow()
        row.set_title(_('Remote address'))
        self.entry_device = Gtk.Entry()
        self.entry_device.set_placeholder_text('//192.168.1.100/Share')
        self.entry_device.set_text(remote.remote_path or '')
        self.entry_device.set_width_chars(field_width)
        self.entry_device.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_device)
        basic_group.add(row)

        row = Adw.ActionRow()
        row.set_title(_('Filesystem type'))
        self.entry_fstype = Gtk.Entry()
        self.entry_fstype.set_placeholder_text('cifs')
        self.entry_fstype.set_text(remote.fs_type or 'cifs')
        self.entry_fstype.set_width_chars(field_width)
        self.entry_fstype.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_fstype)
        basic_group.add(row)

        pref_page.add(basic_group)

        # Credentials group
        creds_group = Adw.PreferencesGroup()
        creds_group.set_title(_('Credentials'))
        creds_group.set_description(_('Authentication settings'))

        row = Adw.ActionRow()
        row.set_title(_('Credentials file'))
        self.entry_credentials = Gtk.Entry()
        self.entry_credentials.set_placeholder_text('/etc/nixos/smb-credentials')
        self.entry_credentials.set_text(self._get_option_value('credentials') or '')
        self.entry_credentials.set_width_chars(field_width)
        self.entry_credentials.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_credentials)
        browse_button = Gtk.Button(icon_name='document-open-symbolic')
        browse_button.set_valign(Gtk.Align.CENTER)
        browse_button.set_tooltip_text(_('Browse for credentials file'))
        browse_button.connect('clicked', self._on_browse_credentials)
        row.add_suffix(browse_button)
        creds_group.add(row)

        # UID dropdown with system users
        self._users = [(p.pw_name, p.pw_uid) for p in pwd.getpwall() if p.pw_uid >= 1000 and p.pw_uid < 65534]
        self._users.sort(key=lambda x: x[0])
        user_strings = [f'{name} ({uid})' for name, uid in self._users]

        self.combo_uid = Adw.ComboRow()
        self.combo_uid.set_title(_('User (UID)'))
        self.combo_uid.set_model(Gtk.StringList.new(user_strings))
        # Pre-select current UID if exists
        current_uid = self._get_option_value('uid')
        if current_uid:
            for i, (name, uid) in enumerate(self._users):
                if str(uid) == current_uid:
                    self.combo_uid.set_selected(i)
                    break
        elif self._users:
            self.combo_uid.set_selected(0)
        creds_group.add(self.combo_uid)

        # GID dropdown with system groups
        self._groups = [(g.gr_name, g.gr_gid) for g in grp.getgrall() if g.gr_gid < 65534]
        self._groups.sort(key=lambda x: x[0])
        group_strings = [f'{name} ({gid})' for name, gid in self._groups]

        self.combo_gid = Adw.ComboRow()
        self.combo_gid.set_title(_('Group (GID)'))
        self.combo_gid.set_model(Gtk.StringList.new(group_strings))
        # Pre-select current GID if exists
        current_gid = self._get_option_value('gid')
        if current_gid:
            for i, (name, gid) in enumerate(self._groups):
                if str(gid) == current_gid:
                    self.combo_gid.set_selected(i)
                    break
        elif self._groups:
            self.combo_gid.set_selected(0)
        creds_group.add(self.combo_gid)

        pref_page.add(creds_group)

        # Systemd options group
        systemd_group = Adw.PreferencesGroup()
        systemd_group.set_title(_('Systemd Options'))
        systemd_group.set_description(_('Automount and timeout settings'))

        # Mount behavior choice
        self.combo_mount_behavior = Adw.ComboRow()
        self.combo_mount_behavior.set_title(_('Mount behavior'))
        self.combo_mount_behavior.set_subtitle(_('When to mount the share'))
        mount_options = Gtk.StringList.new([
            _('Auto mount at boot'),
            _('Mount on access')
        ])
        self.combo_mount_behavior.set_model(mount_options)
        # Set initial selection based on current options
        if self._has_option('x-systemd.automount') and self._has_option('noauto'):
            self.combo_mount_behavior.set_selected(1)  # Mount on access
        else:
            self.combo_mount_behavior.set_selected(0)  # Auto mount at boot
        systemd_group.add(self.combo_mount_behavior)

        # Idle timeout
        row = Adw.ActionRow()
        row.set_title(_('Idle timeout (seconds)'))
        self.entry_idle_timeout = Gtk.Entry()
        self.entry_idle_timeout.set_placeholder_text('300')
        self.entry_idle_timeout.set_text(self._get_option_value('x-systemd.idle-timeout') or '300')
        self.entry_idle_timeout.set_width_chars(field_width)
        self.entry_idle_timeout.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_idle_timeout)
        systemd_group.add(row)

        # Device timeout
        row = Adw.ActionRow()
        row.set_title(_('Device timeout'))
        self.entry_device_timeout = Gtk.Entry()
        self.entry_device_timeout.set_placeholder_text('10s')
        self.entry_device_timeout.set_text(self._get_option_value('x-systemd.device-timeout') or '10s')
        self.entry_device_timeout.set_width_chars(field_width)
        self.entry_device_timeout.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_device_timeout)
        systemd_group.add(row)

        # Mount timeout
        row = Adw.ActionRow()
        row.set_title(_('Mount timeout'))
        self.entry_mount_timeout = Gtk.Entry()
        self.entry_mount_timeout.set_placeholder_text('10s')
        self.entry_mount_timeout.set_text(self._get_option_value('x-systemd.mount-timeout') or '10s')
        self.entry_mount_timeout.set_width_chars(field_width)
        self.entry_mount_timeout.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_mount_timeout)
        systemd_group.add(row)

        pref_page.add(systemd_group)

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

    def _get_option_value(self, option_name: str) -> str | None:
        """Extract value from options like 'key=value' or 'key'."""
        if not hasattr(self.remote, 'options') or not self.remote.options:
            return None
        for opt in self.remote.options:
            if opt.startswith(f'{option_name}='):
                return opt.split('=', 1)[1]
        return None

    def _has_option(self, option_name: str) -> bool:
        """Check if an option exists (for flags without values)."""
        if not hasattr(self.remote, 'options') or not self.remote.options:
            return False
        for opt in self.remote.options:
            if opt == option_name or opt.startswith(f'{option_name}='):
                return True
        return False

    def _on_browse_credentials(self, _button):
        dialog = Gtk.FileDialog()
        dialog.set_title(_('Select credentials file'))
        dialog.open(self.get_root(), None, self._on_credentials_file_selected)

    def _on_credentials_file_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                self.entry_credentials.set_text(file.get_path())
        except Exception:
            pass

    def on_save_clicked(self, _button):
        if not self._validate():
            return

        remote_share_to_update = RemoteShare(
            path=self.entry_mount_path.get_text(),
            remote_path=self.entry_device.get_text(),
        )
        remote_share_to_update.set_options(self._build_options())

        try:
            self._remote_domain.edit_item(self.remote.path, remote_share_to_update)

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

        # Mount path: required, must start with /
        mount_path = self.entry_mount_path.get_text().strip()
        mount_error = not mount_path or not mount_path.startswith('/')
        self._set_row_error(self.entry_mount_path, mount_error)
        if mount_error:
            valid = False

        # Remote address: required, must match //host/share
        device = self.entry_device.get_text().strip()
        device_error = not device or not re.match(r'^//[^/]+/.+$', device)
        self._set_row_error(self.entry_device, device_error)
        if device_error:
            valid = False

        # Filesystem type: required
        fstype = self.entry_fstype.get_text().strip()
        fstype_error = not fstype
        self._set_row_error(self.entry_fstype, fstype_error)
        if fstype_error:
            valid = False

        # UID/GID are now dropdowns, no validation needed

        # Idle timeout: must be a number
        idle = self.entry_idle_timeout.get_text().strip()
        idle_error = idle and not idle.isdigit()
        self._set_row_error(self.entry_idle_timeout, idle_error)
        if idle_error:
            valid = False

        # Device timeout: must match pattern like 10s, 30s
        dev_timeout = self.entry_device_timeout.get_text().strip()
        dev_timeout_error = dev_timeout and not re.match(r'^\d+[smh]?$', dev_timeout)
        self._set_row_error(self.entry_device_timeout, dev_timeout_error)
        if dev_timeout_error:
            valid = False

        # Mount timeout: must match pattern like 10s, 30s
        mnt_timeout = self.entry_mount_timeout.get_text().strip()
        mnt_timeout_error = mnt_timeout and not re.match(r'^\d+[smh]?$', mnt_timeout)
        self._set_row_error(self.entry_mount_timeout, mnt_timeout_error)
        if mnt_timeout_error:
            valid = False

        if not valid:
            self._show_notification(_('There are error during validation'))

        return valid

    

    def _build_options(self) -> list:
        """Build the options list from form values."""
        options = []

        # Credentials
        creds = self.entry_credentials.get_text()
        if creds:
            options.append(f'credentials={creds}')

        # Mount behavior
        if self.combo_mount_behavior.get_selected() == 1:  # Mount on access
            options.append('noauto')
            options.append('x-systemd.automount')
        elif self.combo_mount_behavior.get_selected() == 0:  # Mount on access
            #options.append('noauto')
            options.append('x-systemd.automount')
        

        idle_timeout = self.entry_idle_timeout.get_text()
        if idle_timeout:
            options.append(f'x-systemd.idle-timeout={idle_timeout}')

        device_timeout = self.entry_device_timeout.get_text()
        if device_timeout:
            options.append(f'x-systemd.device-timeout={device_timeout}')

        mount_timeout = self.entry_mount_timeout.get_text()
        if mount_timeout:
            options.append(f'x-systemd.mount-timeout={mount_timeout}')

        # UID/GID from combo boxes
        uid_idx = self.combo_uid.get_selected()
        if uid_idx != Gtk.INVALID_LIST_POSITION and uid_idx < len(self._users):
            uid = self._users[uid_idx][1]
            options.append(f'uid={uid}')

        gid_idx = self.combo_gid.get_selected()
        if gid_idx != Gtk.INVALID_LIST_POSITION and gid_idx < len(self._groups):
            gid = self._groups[gid_idx][1]
            options.append(f'gid={gid}')

        return options
