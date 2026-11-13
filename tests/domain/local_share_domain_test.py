import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from domain.entity.local_share import LocalShare
from domain.local_share_domain import LocalShareDomain


class MockSystemApi:

    def __init__(self, existing_user_list=None):
        self.existing_user_list = existing_user_list or []

    def user_exists(self, user_name: str) -> bool:
        return user_name in self.existing_user_list

    def get_path_owner(self, path: str) -> str:
        return 'alice'

    def write_file_tmp(self, content: str) -> str:
        return '/tmp/fake.nix'


class MockLocalSambaFileApi:

    def __init__(self, samba_settings=None, dedicated_user_list=None):
        self.samba_settings = samba_settings or {}
        self.dedicated_user_list = dedicated_user_list or []

    def get_nix_dict(self) -> dict:
        return dict(self.samba_settings)

    def get_dedicated_user_list(self) -> list:
        return list(self.dedicated_user_list)

    def convert_local_share_list_to_nix_content(self, local_share_list: list) -> str:
        return ''


class TestLocalShareDomainDedicatedAccount(unittest.TestCase):

    def _create_domain(self, existing_user_list=None):
        samba_settings = {
            'global': {},
            'Docs': {'path': '/srv/docs', 'guest ok': 'no', 'valid users': 'docshare', 'force user': 'alice'},
            'Family': {'path': '/srv/family', 'guest ok': 'no', 'valid users': 'alice bob'},
        }
        system_api = MockSystemApi((existing_user_list or []) + ['docshare'])
        domain = LocalShareDomain(system_api, MockLocalSambaFileApi(samba_settings, ['docshare']))
        domain._local_share_repository._local_share_list = []
        return domain

    def test_load_detects_dedicated_account(self):
        domain = self._create_domain()
        docs, family = domain.get_list()

        self.assertEqual(docs.dedicated_user, 'docshare')
        self.assertEqual(docs.force_user, 'alice')
        self.assertEqual(docs.valid_users, [])
        self.assertFalse(family.has_dedicated_user())
        self.assertEqual(family.valid_users, ['alice', 'bob'])

    def test_nix_content_uses_dedicated_account(self):
        share = LocalShare('Docs', '/srv/docs', dedicated_user='docshare', force_user='alice', valid_users=['bob'])
        nix_content = share.get_nixcontent()

        self.assertEqual(nix_content['valid users'], 'docshare')
        self.assertEqual(nix_content['force user'], 'alice')

    def test_user_name_validation(self):
        domain = self._create_domain()

        self.assertTrue(domain.is_dedicated_user_name_valid('docs-share_1'))
        self.assertFalse(domain.is_dedicated_user_name_valid('Docs'))
        self.assertFalse(domain.is_dedicated_user_name_valid('1docs'))
        self.assertFalse(domain.is_dedicated_user_name_valid('doc share'))
        self.assertFalse(domain.is_dedicated_user_name_valid(''))

    def test_user_availability(self):
        domain = self._create_domain(existing_user_list=['alice'])

        # Existing login account: refused
        self.assertFalse(domain.is_dedicated_user_available('alice'))
        # Account of another share: refused
        self.assertFalse(domain.is_dedicated_user_available('docshare', 'Family'))
        # Account of the edited share: allowed even though it exists on the system
        self.assertTrue(domain.is_dedicated_user_available('docshare', 'Docs'))
        self.assertTrue(domain.is_dedicated_user_available('newshare'))

    def test_account_actions_and_confirm(self):
        domain = self._create_domain()
        domain.get_list()

        domain.edit_item('Docs', LocalShare('Docs', '/srv/docs', dedicated_user='docs2', dedicated_password='secret'))
        actions = domain.get_dedicated_account_actions()

        self.assertEqual(actions['remove'], ['docshare'])
        self.assertEqual(actions['passwords'], [('docs2', 'secret')])

        domain.confirm_saved()
        actions = domain.get_dedicated_account_actions()

        self.assertEqual(actions['remove'], [])
        self.assertEqual(actions['passwords'], [])
        self.assertTrue(domain.is_dedicated_user_available('docs2', 'Docs'))


if __name__ == '__main__':
    unittest.main()
