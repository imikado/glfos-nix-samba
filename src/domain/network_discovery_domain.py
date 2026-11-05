from domain.contract.network_discovery_api_contract import NetworkDiscoveryApiContract


class ShareListingError(Exception):
    """The shares of a server could not be listed."""


class ShareAccessDeniedError(ShareListingError):
    """The server refused the connection: credentials are missing or wrong."""


class HostUnreachableError(ShareListingError):
    """The server could not be reached."""


class NetworkDiscoveryDomain:

    _network_discovery_api: NetworkDiscoveryApiContract

    def __init__(self, network_discovery_api: NetworkDiscoveryApiContract):
        self._network_discovery_api = network_discovery_api

    def is_host_discovery_available(self) -> bool:
        return self._network_discovery_api.is_host_discovery_available()

    def is_share_listing_available(self) -> bool:
        return self._network_discovery_api.is_share_listing_available()

    def discover_hosts(self) -> list:
        hosts = self._network_discovery_api.discover_hosts()
        return sorted(hosts, key=lambda host: host.name.lower())

    def list_shares(self, host: str, credentials_file: str = '', username: str = '', password: str = '') -> list:
        """List the visible disk shares of host.

        Credentials: the username/password typed by the user, else the
        credentials file, else anonymous access.
        """
        workgroup = ''
        if not username and credentials_file:
            credentials = self.parse_credentials_content(
                self._network_discovery_api.read_credentials_file(credentials_file))
            username = credentials.get('username', '')
            password = credentials.get('password', '')
            workgroup = credentials.get('domain', '')

        # DOMAIN\user or user@DOMAIN typed in the username field
        if '\\' in username:
            workgroup, username = username.split('\\', 1)

        shares = self._network_discovery_api.list_shares(host, username, password, workgroup)
        visible_shares = {share for share in shares if share and not share.endswith('$')}
        return sorted(visible_shares, key=str.lower)

    @staticmethod
    def parse_credentials_content(content: str) -> dict:
        """Parse a cifs credentials file (username=, password=, domain=)."""
        credentials = {}
        for line in (content or '').splitlines():
            key, separator, value = line.partition('=')
            key = key.strip().lower()
            if separator and key in ('username', 'user', 'password', 'pass', 'domain', 'workgroup'):
                key = {'user': 'username', 'pass': 'password', 'workgroup': 'domain'}.get(key, key)
                credentials[key] = value.strip() if key != 'password' else value.rstrip('\r\n')
        return credentials

    @staticmethod
    def split_remote_address(remote_address: str) -> tuple:
        """'//host/share/sub' -> ('host', 'share/sub'). Missing parts are empty strings."""
        value = (remote_address or '').strip()
        if not value.startswith('//'):
            return ('', '')
        host, _separator, share = value[2:].partition('/')
        return (host, share)

    @staticmethod
    def build_remote_address(host: str, share: str) -> str:
        return '//' + host.strip().strip('/') + '/' + share.strip().strip('/')
