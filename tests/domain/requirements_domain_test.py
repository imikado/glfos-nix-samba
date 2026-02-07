import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from domain.requirements_domain import RequirementsDomain
from domain.contract.system_api_contract import SystemApiContract


class MockSystemApi(SystemApiContract):
    """Mock SystemApi for testing."""

    def __init__(self):
        self.written_files = {}

    def read_file(self, path: str) -> str:
        return self.written_files.get(path, '')

    def write_file(self, path: str, content: str):
        self.written_files[path] = content

    def write_file_sudo(self, path: str, content: str, password: str):
        self.written_files[path] = content

    def file_exists(self, path: str) -> bool:
        return path in self.written_files

    def create_dir(self, path: str):
        pass

    def chown_smb_creds_file(self, path: str):
        pass

    def nix_rebuild_sudo(self, password: str):
        pass


class TestRequirementsDomain(unittest.TestCase):

    def setUp(self):
        self.mock_system_api = MockSystemApi()
        self.requirements_domain = RequirementsDomain(self.mock_system_api)

    def test_get_config_file_path(self):
        """Test that config file path returns expected value."""
        self.assertEqual(
            self.requirements_domain.get_config_file_path(),
            '/etc/nixos/customConfig/default.nix'
        )

    def test_is_requirements_valid_no_imports_section(self):
        """Test validation fails when no imports section exists."""
        content = """{
  environment.systemPackages = [];
}"""
        result = self.requirements_domain.is_requirements_valid(content)
        self.assertFalse(result)
        self.assertTrue(self.requirements_domain._need_fix_all_imports)

    def test_is_requirements_valid_missing_samba_nix(self):
        """Test validation fails when samba.nix import is missing."""
        content = """{
  imports = [
    ./samba_setup.nix
  ];
  environment.systemPackages = [];
}"""
        # Reset state
        self.requirements_domain._need_fix_missing_list = []
        self.requirements_domain._need_fix_all_imports = False

        result = self.requirements_domain.is_requirements_valid(content)
        self.assertFalse(result)
        self.assertIn('./samba.nix', self.requirements_domain._need_fix_missing_list)

    def test_is_requirements_valid_missing_samba_setup_nix(self):
        """Test validation fails when samba_setup.nix import is missing."""
        content = """{
  imports = [
    ./samba.nix
  ];
  environment.systemPackages = [];
}"""
        # Reset state
        self.requirements_domain._need_fix_missing_list = []
        self.requirements_domain._need_fix_all_imports = False

        result = self.requirements_domain.is_requirements_valid(content)
        self.assertFalse(result)
        self.assertIn('./samba_setup.nix', self.requirements_domain._need_fix_missing_list)

    def test_is_requirements_valid_missing_both_imports(self):
        """Test validation fails when both imports are missing."""
        content = """{
  imports = [
    ./other.nix
  ];
  environment.systemPackages = [];
}"""
        # Reset state
        self.requirements_domain._need_fix_missing_list = []
        self.requirements_domain._need_fix_all_imports = False

        result = self.requirements_domain.is_requirements_valid(content)
        self.assertFalse(result)
        self.assertIn('./samba.nix', self.requirements_domain._need_fix_missing_list)
        self.assertIn('./samba_setup.nix', self.requirements_domain._need_fix_missing_list)

    def test_is_requirements_valid_all_present(self):
        """Test validation passes when all requirements are met."""
        content = """{
  imports = [
    ./samba.nix
    ./samba_setup.nix
  ];
  environment.systemPackages = [];
}"""
        # Reset state
        self.requirements_domain._need_fix_missing_list = []
        self.requirements_domain._need_fix_all_imports = False

        result = self.requirements_domain.is_requirements_valid(content)
        self.assertTrue(result)
        self.assertFalse(self.requirements_domain._need_fix_all_imports)
        self.assertEqual(len(self.requirements_domain._need_fix_missing_list), 0)

    def test_is_requirements_valid_with_path_prefix(self):
        """Test validation passes with different path formats."""
        content = """{
  imports = [
    samba.nix
    samba_setup.nix
  ];
}"""
        # Reset state
        self.requirements_domain._need_fix_missing_list = []
        self.requirements_domain._need_fix_all_imports = False

        result = self.requirements_domain.is_requirements_valid(content)
        self.assertTrue(result)

    def test_get_content_with_missing_imports(self):
        """Test adding missing imports to existing import block."""
        content = """imports = [
    ./other.nix
];"""
        missing = ['./samba.nix', './samba_setup.nix']

        result = self.requirements_domain.get_content_with_missing_imports(content, missing)

        # Check that missing imports are added before ];
        self.assertIn('./samba.nix', result)
        self.assertIn('./samba_setup.nix', result)

    def test_get_content_with_missing_import_block(self):
        """Test adding import block when no imports section exists."""
        content = """{
  environment.systemPackages = [];
}"""
        result = self.requirements_domain.get_content_with_missing_import_block(content)

        # Check that imports block is added with both required imports
        self.assertIn('imports', result)
        self.assertIn('samba.nix', result)
        self.assertIn('samba_setup.nix', result)

    def test_get_content_with_missing_import_block_with_carriagereturn(self):
        """Test adding import block when no imports section exists."""
        content = """{
  environment.systemPackages = [];
}
"""
        result = self.requirements_domain.get_content_with_missing_import_block(content)

        # Check that imports block is added with both required imports
        self.assertIn('imports', result)
        self.assertIn('samba.nix', result)
        self.assertIn('samba_setup.nix', result)


if __name__ == '__main__':
    unittest.main()
