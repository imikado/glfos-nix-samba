import threading

from domain.network_discovery_domain import (
    HostUnreachableError,
    NetworkDiscoveryDomain,
    ShareAccessDeniedError,
)
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, GLib, Gtk


class RemoteBrowseDialog(Adw.Dialog):
    """Interactive dialog to fill a remote address (//server/share).

    Discovers Samba servers on the network (mDNS, zeroconf) and lists the shares
    of the chosen server (pysmb). Both steps fall back to manual input when the
    library is missing.
    """

    def __init__(self, network_discovery_domain: NetworkDiscoveryDomain, current_address: str,
                 credentials_file: str, on_selected, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._domain = network_discovery_domain
        self._credentials_file = credentials_file
        self._on_selected = on_selected
        self._host_rows = []
        self._share_rows = []
        # Incremented on every request: results of an outdated request are ignored
        self._share_request_id = 0
        self._closed = False

        self.set_title(_('Browse network'))
        self.set_content_width(560)
        self.set_content_height(680)
        self.connect('closed', self._on_closed)

        toolbar_view = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()
        header_bar.set_show_end_title_buttons(False)
        header_bar.set_show_start_title_buttons(False)

        cancel_button = Gtk.Button(label=_('Cancel'))
        cancel_button.connect('clicked', lambda _button: self.close())
        header_bar.pack_start(cancel_button)

        self._select_button = Gtk.Button(label=_('Select'))
        self._select_button.add_css_class('suggested-action')
        self._select_button.connect('clicked', self._on_select_clicked)
        header_bar.pack_end(self._select_button)

        toolbar_view.add_top_bar(header_bar)

        pref_page = Adw.PreferencesPage()

        # --- Server ---------------------------------------------------------
        self._server_group = Adw.PreferencesGroup()
        self._server_group.set_title(_('Server'))

        server_suffix = Gtk.Box(spacing=6)
        self._server_spinner = Gtk.Spinner()
        server_suffix.append(self._server_spinner)
        self._refresh_button = Gtk.Button(icon_name='view-refresh-symbolic')
        self._refresh_button.add_css_class('flat')
        self._refresh_button.set_valign(Gtk.Align.CENTER)
        self._refresh_button.set_tooltip_text(_('Search again'))
        self._refresh_button.connect('clicked', lambda _button: self._start_host_discovery())
        server_suffix.append(self._refresh_button)
        self._server_group.set_header_suffix(server_suffix)

        self._entry_host = Adw.EntryRow()
        self._entry_host.set_title(_('Server name or IP address'))
        self._entry_host.connect('changed', self._on_fields_changed)
        self._entry_host.connect('entry-activated', lambda _row: self._start_share_listing())
        self._server_group.add(self._entry_host)

        pref_page.add(self._server_group)

        # --- Authentication -------------------------------------------------
        self._auth_group = Adw.PreferencesGroup()
        self._auth_group.set_title(_('Authentication'))
        if credentials_file:
            self._auth_group.set_description(
                _('Optional, only used to list the shares. Leave empty to use the credentials file: ') + credentials_file)
        else:
            self._auth_group.set_description(
                _('Optional, only used to list the shares. Leave empty for anonymous access.'))

        self._entry_username = Adw.EntryRow()
        self._entry_username.set_title(_('Username'))
        self._auth_group.add(self._entry_username)

        self._entry_password = Adw.PasswordEntryRow()
        self._entry_password.set_title(_('Password'))
        self._entry_password.connect('entry-activated', lambda _row: self._start_share_listing())
        self._auth_group.add(self._entry_password)

        pref_page.add(self._auth_group)

        # --- Share ----------------------------------------------------------
        self._share_group = Adw.PreferencesGroup()
        self._share_group.set_title(_('Share'))

        share_suffix = Gtk.Box(spacing=6)
        self._share_spinner = Gtk.Spinner()
        share_suffix.append(self._share_spinner)
        self._list_shares_button = Gtk.Button(label=_('List shares'))
        self._list_shares_button.set_valign(Gtk.Align.CENTER)
        self._list_shares_button.connect('clicked', lambda _button: self._start_share_listing())
        share_suffix.append(self._list_shares_button)
        self._share_group.set_header_suffix(share_suffix)

        self._entry_share = Adw.EntryRow()
        self._entry_share.set_title(_('Share name'))
        self._entry_share.connect('changed', self._on_fields_changed)
        self._entry_share.connect('entry-activated', self._on_select_clicked)
        self._share_group.add(self._entry_share)

        pref_page.add(self._share_group)

        toolbar_view.set_content(pref_page)
        self.set_child(toolbar_view)

        # Prefill with the current value of the form
        host, share = NetworkDiscoveryDomain.split_remote_address(current_address)
        self._entry_host.set_text(host)
        self._entry_share.set_text(share)
        self._on_fields_changed()

        if not self._domain.is_share_listing_available():
            self._list_shares_button.set_visible(False)
            self._auth_group.set_visible(False)
            self._share_group.set_description(
                _('Share listing unavailable: the pysmb Python library is not installed. Enter the share name.'))

        if self._domain.is_host_discovery_available():
            self._start_host_discovery()
        else:
            self._refresh_button.set_visible(False)
            self._server_group.set_description(
                _('Automatic discovery unavailable: the zeroconf Python library is not installed. Enter the server name or IP address.'))

        if host:
            self._start_share_listing()

    # --- Helpers -------------------------------------------------------------

    def _run_in_thread(self, work, on_done):
        """Run work() in a thread, then on_done(result, error) in the GTK main loop."""
        def target():
            try:
                result, error = work(), None
            except Exception as exception:
                result, error = None, exception
            GLib.idle_add(lambda: (not self._closed and on_done(result, error)) and False)
        threading.Thread(target=target, daemon=True).start()

    def _on_closed(self, _dialog):
        self._closed = True

    def _on_fields_changed(self, *_args):
        has_host = bool(self._entry_host.get_text().strip())
        has_share = bool(self._entry_share.get_text().strip())
        self._select_button.set_sensitive(has_host and has_share)
        self._list_shares_button.set_sensitive(has_host)

    def _replace_rows(self, group, old_rows, new_rows):
        for row in old_rows:
            group.remove(row)
        for row in new_rows:
            group.add(row)
        return new_rows

    def _make_info_row(self, text):
        row = Adw.ActionRow()
        row.set_title(text)
        row.add_css_class('dim-label')
        return row

    # --- Server discovery ----------------------------------------------------

    def _start_host_discovery(self):
        self._refresh_button.set_sensitive(False)
        self._server_spinner.start()
        self._server_group.set_description(_('Searching for Samba servers on the network...'))
        self._run_in_thread(self._domain.discover_hosts, self._on_hosts_discovered)

    def _on_hosts_discovered(self, hosts, error):
        self._server_spinner.stop()
        self._refresh_button.set_sensitive(True)

        rows = []
        if error is not None:
            self._server_group.set_description(_('Search failed: ') + str(error))
        elif not hosts:
            self._server_group.set_description(
                _('No server found. Enter the server name or IP address.'))
        else:
            self._server_group.set_description(_('Choose a server or enter its name or IP address.'))
            for host in hosts:
                row = Adw.ActionRow()
                row.set_title(host.name)
                subtitle = host.address if host.hostname == host.address else host.hostname + ' — ' + host.address
                row.set_subtitle(subtitle)
                row.add_prefix(Gtk.Image.new_from_icon_name('network-server-symbolic'))
                row.add_suffix(Gtk.Image.new_from_icon_name('go-next-symbolic'))
                row.set_activatable(True)
                row.connect('activated', self._on_host_row_activated, host)
                rows.append(row)

        self._host_rows = self._replace_rows(self._server_group, self._host_rows, rows)

    def _on_host_row_activated(self, _row, host):
        self._entry_host.set_text(host.address)
        self._start_share_listing()

    # --- Share listing -------------------------------------------------------

    def _start_share_listing(self):
        host = self._entry_host.get_text().strip()
        if not host or not self._domain.is_share_listing_available():
            return

        self._share_request_id += 1
        request_id = self._share_request_id

        username = self._entry_username.get_text().strip()
        password = self._entry_password.get_text()
        credentials_file = self._credentials_file

        self._share_spinner.start()
        self._list_shares_button.set_sensitive(False)
        self._share_group.set_description(_('Listing shares of ') + host + '...')
        self._share_rows = self._replace_rows(self._share_group, self._share_rows, [])

        self._run_in_thread(
            lambda: self._domain.list_shares(host, credentials_file, username, password),
            lambda shares, error: self._on_shares_listed(request_id, host, shares, error),
        )

    def _on_shares_listed(self, request_id, host, shares, error):
        if request_id != self._share_request_id:
            return  # A newer request is running

        self._share_spinner.stop()
        self._on_fields_changed()

        rows = []
        if isinstance(error, ShareAccessDeniedError):
            self._share_group.set_description(
                _('Access denied: enter a username and password above, then list the shares again. You can also type the share name.'))
        elif isinstance(error, HostUnreachableError):
            self._share_group.set_description(_('Server unreachable: ') + host)
        elif error is not None:
            self._share_group.set_description(_('Unable to list the shares. Enter the share name.'))
            print('Share listing error: ' + str(error))
        elif not shares:
            self._share_group.set_description(_('No share found on this server. Enter the share name.'))
        else:
            self._share_group.set_description(_('Choose a share or enter its name.'))
            for share in shares:
                row = Adw.ActionRow()
                row.set_title(share)
                row.add_prefix(Gtk.Image.new_from_icon_name('folder-remote-symbolic'))
                row.set_activatable(True)
                row.connect('activated', self._on_share_row_activated, share)
                rows.append(row)

        self._share_rows = self._replace_rows(self._share_group, self._share_rows, rows)

    def _on_share_row_activated(self, _row, share):
        self._entry_share.set_text(share)
        self._on_select_clicked()

    # --- Result --------------------------------------------------------------

    def _on_select_clicked(self, *_args):
        host = self._entry_host.get_text().strip()
        share = self._entry_share.get_text().strip()
        if not host or not share:
            return
        self._on_selected(NetworkDiscoveryDomain.build_remote_address(host, share))
        self.close()
