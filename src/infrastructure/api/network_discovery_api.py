import importlib.util
import socket
import time

from domain.contract.network_discovery_api_contract import NetworkDiscoveryApiContract
from domain.entity.samba_host import SambaHost
from domain.network_discovery_domain import (
    HostUnreachableError,
    ShareAccessDeniedError,
    ShareListingError,
)


class NetworkDiscoveryApi(NetworkDiscoveryApiContract):
    """Samba network discovery with pure Python libraries.

    - zeroconf: mDNS discovery of `_smb._tcp` services (no avahi daemon needed)
    - pysmb: list the shares of a server (SMB1/SMB2)
    """

    SMB_SERVICE_TYPE = '_smb._tcp.local.'
    DISCOVERY_DURATION = 3  # seconds listening for mDNS announces
    SMB_PORT = 445
    SMB_TIMEOUT = 10
    CLIENT_NAME = 'nix-samba'

    def is_host_discovery_available(self) -> bool:
        return importlib.util.find_spec('zeroconf') is not None

    def discover_hosts(self) -> list:
        from zeroconf import IPVersion, ServiceBrowser, ServiceListener, Zeroconf

        class Listener(ServiceListener):
            def __init__(self):
                self.names = set()

            def add_service(self, zc, type_, name):
                self.names.add(name)

            def update_service(self, zc, type_, name):
                self.names.add(name)

            def remove_service(self, zc, type_, name):
                self.names.discard(name)

        zeroconf = Zeroconf()
        try:
            listener = Listener()
            browser = ServiceBrowser(zeroconf, self.SMB_SERVICE_TYPE, listener)
            time.sleep(self.DISCOVERY_DURATION)
            browser.cancel()

            hosts = []
            for service_name in sorted(listener.names):
                info = zeroconf.get_service_info(self.SMB_SERVICE_TYPE, service_name, timeout=2000)
                if info is None:
                    continue

                name = service_name[:-len('.' + self.SMB_SERVICE_TYPE)] if service_name.endswith(self.SMB_SERVICE_TYPE) else service_name
                hostname = (info.server or '').rstrip('.')
                addresses = info.parsed_addresses(IPVersion.V4Only)
                # IPv6 only: the host name is easier to use than an IPv6 address
                address = addresses[0] if addresses else hostname
                if address:
                    hosts.append(SambaHost(name, hostname or address, address))
            return hosts
        finally:
            zeroconf.close()

    def is_share_listing_available(self) -> bool:
        return importlib.util.find_spec('smb') is not None

    def list_shares(self, host: str, username: str = '', password: str = '', workgroup: str = '') -> list:
        from smb.base import NotConnectedError, NotReadyError, OperationFailure, SharedDevice
        from smb.SMBConnection import SMBConnection

        connection = SMBConnection(
            username, password, self.CLIENT_NAME, host,
            domain=workgroup, use_ntlm_v2=True, is_direct_tcp=True,
        )
        try:
            try:
                connected = connection.connect(host, self.SMB_PORT, timeout=self.SMB_TIMEOUT)
            except NotReadyError as error:
                raise ShareAccessDeniedError(str(error))
            except (socket.timeout, OSError) as error:
                raise HostUnreachableError(str(error))

            if not connected:
                raise ShareAccessDeniedError('Authentication failed')

            try:
                shared_devices = connection.listShares(timeout=self.SMB_TIMEOUT)
            except OperationFailure as error:
                raise ShareAccessDeniedError(str(error))
            except (NotConnectedError, NotReadyError) as error:
                raise ShareListingError(str(error))

            return [
                device.name for device in shared_devices
                if device.type == SharedDevice.DISK_TREE and not device.isSpecial
            ]
        finally:
            connection.close()

    def read_credentials_file(self, path: str) -> str:
        try:
            with open(path, 'r') as file:
                return file.read()
        except OSError:
            return ''
