from abc import abstractmethod


class NetworkDiscoveryApiContract:

    @abstractmethod
    def is_host_discovery_available(self) -> bool:
        """True if Samba servers can be discovered on the network (mDNS)."""
        pass

    @abstractmethod
    def discover_hosts(self) -> list:
        """Return the SambaHost announced on the local network."""
        pass

    @abstractmethod
    def is_share_listing_available(self) -> bool:
        """True if the shares of a server can be listed."""
        pass

    @abstractmethod
    def list_shares(self, host: str, username: str = '', password: str = '', workgroup: str = '') -> list:
        """Return the names of the disk shares of host.

        Raise ShareAccessDeniedError, HostUnreachableError or ShareListingError.
        """
        pass

    @abstractmethod
    def read_credentials_file(self, path: str) -> str:
        """Return the content of a credentials file, or '' if it cannot be read."""
        pass
