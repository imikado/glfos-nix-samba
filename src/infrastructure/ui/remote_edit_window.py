from domain.entity.remote_share import RemoteShare
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


class RemoteEditWindow(Adw.Window):
    def __init__(self, parent, remote:RemoteShare, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.remote = remote

        self.set_title(_('Edit Remote Share'))
        self.set_default_size(500, 600)
        self.set_modal(True)
        self.set_transient_for(parent)

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

        # Mount path (e.g., /media/blender2)
        self.entry_mount_path = Adw.EntryRow()
        self.entry_mount_path.set_title(_('Mount path'))
        self.entry_mount_path.set_text(remote.path or '')
        basic_group.add(self.entry_mount_path)

        # Device/Remote path (e.g., //192.168.1.103/Blender2)
        self.entry_device = Adw.EntryRow()
        self.entry_device.set_title(_('Remote address'))
        self.entry_device.set_text(remote.remote_path or '')
        basic_group.add(self.entry_device)

        # Filesystem type
        self.entry_fstype = Adw.EntryRow()
        self.entry_fstype.set_title(_('Filesystem type'))
        self.entry_fstype.set_text(remote.fs_type or 'cifs')
        basic_group.add(self.entry_fstype)

        pref_page.add(basic_group)

        # Credentials group
        creds_group = Adw.PreferencesGroup()
        creds_group.set_title(_('Credentials'))
        creds_group.set_description(_('Authentication settings'))

        # Credentials file path
        self.entry_credentials = Adw.EntryRow()
        self.entry_credentials.set_title(_('Credentials file'))
        self.entry_credentials.set_text(self._get_option_value('credentials') or '')
        creds_group.add(self.entry_credentials)

        # UID
        self.entry_uid = Adw.EntryRow()
        self.entry_uid.set_title(_('UID'))
        self.entry_uid.set_text(self._get_option_value('uid') or '1000')
        creds_group.add(self.entry_uid)

        # GID
        self.entry_gid = Adw.EntryRow()
        self.entry_gid.set_title(_('GID'))
        self.entry_gid.set_text(self._get_option_value('gid') or '100')
        creds_group.add(self.entry_gid)

        pref_page.add(creds_group)

        # Systemd options group
        systemd_group = Adw.PreferencesGroup()
        systemd_group.set_title(_('Systemd Options'))
        systemd_group.set_description(_('Automount and timeout settings'))

        # Automount switch
        self.switch_automount = Adw.SwitchRow()
        self.switch_automount.set_title(_('Automount'))
        self.switch_automount.set_subtitle(_('Mount automatically when accessed'))
        self.switch_automount.set_active(self._has_option('x-systemd.automount'))
        systemd_group.add(self.switch_automount)

        # Noauto switch
        self.switch_noauto = Adw.SwitchRow()
        self.switch_noauto.set_title(_('No auto mount at boot'))
        self.switch_noauto.set_subtitle(_('Do not mount at system startup'))
        self.switch_noauto.set_active(self._has_option('noauto'))
        systemd_group.add(self.switch_noauto)

        # Idle timeout
        self.entry_idle_timeout = Adw.EntryRow()
        self.entry_idle_timeout.set_title(_('Idle timeout (seconds)'))
        self.entry_idle_timeout.set_text(self._get_option_value('x-systemd.idle-timeout') or '300')
        systemd_group.add(self.entry_idle_timeout)

        # Device timeout
        self.entry_device_timeout = Adw.EntryRow()
        self.entry_device_timeout.set_title(_('Device timeout'))
        self.entry_device_timeout.set_text(self._get_option_value('x-systemd.device-timeout') or '10s')
        systemd_group.add(self.entry_device_timeout)

        # Mount timeout
        self.entry_mount_timeout = Adw.EntryRow()
        self.entry_mount_timeout.set_title(_('Mount timeout'))
        self.entry_mount_timeout.set_text(self._get_option_value('x-systemd.mount-timeout') or '10s')
        systemd_group.add(self.entry_mount_timeout)

        pref_page.add(systemd_group)

        # Save button group
        button_group = Adw.PreferencesGroup()

        button_save = Adw.ButtonRow()
        button_save.set_title(_('Save changes'))
        button_save.set_start_icon_name('document-save-symbolic')
        button_save.connect('activated', self.on_save_clicked)
        button_group.add(button_save)

        pref_page.add(button_group)

        scrolled.set_child(pref_page)
        toolbar_view.set_content(scrolled)
        self.set_content(toolbar_view)

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

    def on_save_clicked(self, _button):
        # Gather all values
        config = {
            'path': self.entry_mount_path.get_text(),
            'device': self.entry_device.get_text(),
            'fsType': self.entry_fstype.get_text(),
            'options': self._build_options()
        }
        print(f"Saving config: {config}")
        self.close()

    def _build_options(self) -> list:
        """Build the options list from form values."""
        options = []

        # Credentials
        creds = self.entry_credentials.get_text()
        if creds:
            options.append(f'credentials={creds}')

        # Systemd options
        if self.switch_automount.get_active():
            options.append('x-systemd.automount')

        if self.switch_noauto.get_active():
            options.append('noauto')

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
