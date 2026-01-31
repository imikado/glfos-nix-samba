import re

from domain.entity.remote_share import RemoteShare
from domain.remote_domain import RemoteDomain
import gi
from infrastructure.api.nix_file_api import NixFileApi
from infrastructure.api.system_api import SystemApi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


class RemoteAddPage(Adw.NavigationPage):

    _remote_domain:RemoteDomain
    _navigation_view:Adw.NavigationView


    def __init__(self, remote_domain:RemoteDomain,navigation_view:Adw.NavigationView, show_notification, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._navigation_view=navigation_view

        self._show_notification=show_notification

        self._remote_domain = remote_domain
        self.set_title(_('Add Remote Share'))

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
        self.entry_mount_path.set_text('/media/')
        self.entry_mount_path.set_width_chars(field_width)
        self.entry_mount_path.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_mount_path)
        basic_group.add(row)

        row = Adw.ActionRow()
        row.set_title(_('Remote address'))
        self.entry_device = Gtk.Entry()
        self.entry_device.set_placeholder_text('//192.168.1.100/Share')
        self.entry_device.set_width_chars(field_width)
        self.entry_device.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_device)
        basic_group.add(row)

        row = Adw.ActionRow()
        row.set_title(_('Filesystem type'))
        self.entry_fstype = Gtk.Entry()
        self.entry_fstype.set_placeholder_text('cifs')
        self.entry_fstype.set_text('cifs')
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
        self.entry_credentials.set_width_chars(field_width)
        self.entry_credentials.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_credentials)
        creds_group.add(row)

        row = Adw.ActionRow()
        row.set_title(_('UID (user id)'))
        self.entry_uid = Gtk.Entry()
        self.entry_uid.set_placeholder_text('1000')
        self.entry_uid.set_text('1000')
        self.entry_uid.set_width_chars(field_width)
        self.entry_uid.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_uid)
        creds_group.add(row)

        row = Adw.ActionRow()
        row.set_title(_('GID (Group id)'))
        self.entry_gid = Gtk.Entry()
        self.entry_gid.set_placeholder_text('1000')
        self.entry_gid.set_text('1000')
        self.entry_gid.set_width_chars(field_width)
        self.entry_gid.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_gid)
        creds_group.add(row)

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
        self.combo_mount_behavior.set_selected(0)
        systemd_group.add(self.combo_mount_behavior)

        row = Adw.ActionRow()
        row.set_title(_('Idle timeout (seconds)'))
        self.entry_idle_timeout = Gtk.Entry()
        self.entry_idle_timeout.set_placeholder_text('300')
        self.entry_idle_timeout.set_text('300')
        self.entry_idle_timeout.set_width_chars(field_width)
        self.entry_idle_timeout.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_idle_timeout)
        systemd_group.add(row)

        row = Adw.ActionRow()
        row.set_title(_('Device timeout'))
        self.entry_device_timeout = Gtk.Entry()
        self.entry_device_timeout.set_placeholder_text('10s')
        self.entry_device_timeout.set_text('10s')
        self.entry_device_timeout.set_width_chars(field_width)
        self.entry_device_timeout.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_device_timeout)
        systemd_group.add(row)

        row = Adw.ActionRow()
        row.set_title(_('Mount timeout'))
        self.entry_mount_timeout = Gtk.Entry()
        self.entry_mount_timeout.set_placeholder_text('10s')
        self.entry_mount_timeout.set_text('10s')
        self.entry_mount_timeout.set_width_chars(field_width)
        self.entry_mount_timeout.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.entry_mount_timeout)
        systemd_group.add(row)

        pref_page.add(systemd_group)

        # Add button group
        button_group = Adw.PreferencesGroup()

        button_add = Adw.ButtonRow()
        button_add.set_title(_('Add share'))
        button_add.set_start_icon_name('list-add-symbolic')
        button_add.connect('activated', self.on_add_clicked)
        button_group.add(button_add)

        pref_page.add(button_group)

        scrolled.set_child(pref_page)
        toolbar_view.set_content(scrolled)
        self.set_child(toolbar_view)

    def on_add_clicked(self, _button):
        if not self._validate():
            return

        remote_share = RemoteShare(
            path=self.entry_mount_path.get_text(),
            remote_path=self.entry_device.get_text(),
        )
        remote_share.set_options(self._build_options())

        try:
            self._remote_domain.add_item(remote_share)
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

        # UID: must be a number
        uid = self.entry_uid.get_text().strip()
        uid_error = uid and not uid.isdigit()
        self._set_row_error(self.entry_uid, uid_error)
        if uid_error:
            valid = False

        # GID: must be a number
        gid = self.entry_gid.get_text().strip()
        gid_error = gid and not gid.isdigit()
        self._set_row_error(self.entry_gid, gid_error)
        if gid_error:
            valid = False

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
        elif self.combo_mount_behavior.get_selected() == 0:  # Auto mount at boot
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

        # UID/GID
        uid = self.entry_uid.get_text()
        if uid:
            options.append(f'uid={uid}')

        gid = self.entry_gid.get_text()
        if gid:
            options.append(f'gid={gid}')

        return options
