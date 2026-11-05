import os
import sys
import unittest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from domain.contract.network_discovery_api_contract import NetworkDiscoveryApiContract
from domain.entity.samba_host import SambaHost
from domain.network_discovery_domain import NetworkDiscoveryDomain, ShareAccessDeniedError


class MockNetworkDiscoveryApi(NetworkDiscoveryApiContract):

    def __init__(self, hosts=None, shares=None, credentials_files=None, error=None):
        self.hosts = hosts or []
        self.shares = shares or []
        self.credentials_files = credentials_files or {}
        self.error = error
        self.list_shares_calls = []

    def is_host_discovery_available(self) -> bool:
        return True

    def discover_hosts(self) -> list:
        return list(self.hosts)

    def is_share_listing_available(self) -> bool:
        return True

    def list_shares(self, host, username='', password='', workgroup='') -> list:
        self.list_shares_calls.append((host, username, password, workgroup))
        if self.error:
            raise self.error
        return list(self.shares)

    def read_credentials_file(self, path) -> str:
        return self.credentials_files.get(path, '')


class TestNetworkDiscoveryDomain(unittest.TestCase):

    def test_discover_hosts_sorted_by_name(self):
        api = MockNetworkDiscoveryApi(hosts=[
            SambaHost('zeta', 'zeta.local', '192.168.1.3'),
            SambaHost('Alpha', 'alpha.local', '192.168.1.2'),
        ])
        hosts = NetworkDiscoveryDomain(api).discover_hosts()
        self.assertEqual(['Alpha', 'zeta'], [host.name for host in hosts])

    def test_list_shares_hides_special_shares_and_sorts(self):
        api = MockNetworkDiscoveryApi(shares=['photos', 'IPC$', 'Music', 'admin$', 'photos'])
        shares = NetworkDiscoveryDomain(api).list_shares('192.168.1.10')
        self.assertEqual(['Music', 'photos'], shares)

    def test_list_shares_anonymous_without_credentials(self):
        api = MockNetworkDiscoveryApi()
        NetworkDiscoveryDomain(api).list_shares('nas')
        self.assertEqual([('nas', '', '', '')], api.list_shares_calls)

    def test_list_shares_uses_credentials_file(self):
        api = MockNetworkDiscoveryApi(credentials_files={
            '/home/alice/.smb': 'username=alice\npassword=p=ss word\ndomain=HOME\n',
        })
        NetworkDiscoveryDomain(api).list_shares('nas', credentials_file='/home/alice/.smb')
        self.assertEqual([('nas', 'alice', 'p=ss word', 'HOME')], api.list_shares_calls)

    def test_typed_username_has_priority_over_credentials_file(self):
        api = MockNetworkDiscoveryApi(credentials_files={'/creds': 'username=alice\npassword=x\n'})
        NetworkDiscoveryDomain(api).list_shares('nas', '/creds', 'bob', 'secret')
        self.assertEqual([('nas', 'bob', 'secret', '')], api.list_shares_calls)

    def test_domain_in_typed_username(self):
        api = MockNetworkDiscoveryApi()
        NetworkDiscoveryDomain(api).list_shares('nas', username='OFFICE\\bob', password='secret')
        self.assertEqual([('nas', 'bob', 'secret', 'OFFICE')], api.list_shares_calls)

    def test_access_denied_is_propagated(self):
        api = MockNetworkDiscoveryApi(error=ShareAccessDeniedError('denied'))
        with self.assertRaises(ShareAccessDeniedError):
            NetworkDiscoveryDomain(api).list_shares('nas')

    def test_parse_credentials_aliases(self):
        credentials = NetworkDiscoveryDomain.parse_credentials_content('user=alice\npass=secret\nworkgroup=HOME\n# comment\n')
        self.assertEqual({'username': 'alice', 'password': 'secret', 'domain': 'HOME'}, credentials)

    def test_split_remote_address(self):
        self.assertEqual(('192.168.1.10', 'photos'), NetworkDiscoveryDomain.split_remote_address('//192.168.1.10/photos'))
        self.assertEqual(('nas', 'share/sub'), NetworkDiscoveryDomain.split_remote_address('//nas/share/sub'))
        self.assertEqual(('nas', ''), NetworkDiscoveryDomain.split_remote_address('//nas'))
        self.assertEqual(('', ''), NetworkDiscoveryDomain.split_remote_address('nas/share'))
        self.assertEqual(('', ''), NetworkDiscoveryDomain.split_remote_address(''))

    def test_build_remote_address(self):
        self.assertEqual('//nas/photos', NetworkDiscoveryDomain.build_remote_address(' nas ', '/photos/'))


if __name__ == '__main__':
    unittest.main()
