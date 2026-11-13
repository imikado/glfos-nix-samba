from domain.contract.local_samba_file_api_contract import LocalSambaFileApiContract
from infrastructure.api.nix_file_api import NixFileApi


class LocalSambaFileApi(LocalSambaFileApiContract):

    _nix_file_path:str='/etc/nixos/customConfig/samba-server.nix'

    # Group of the share-only accounts: identifies them when reading samba-server.nix back
    DEDICATED_USER_GROUP:str='nix-samba-share'

    _nix_file_api:NixFileApi

    def __init__(self):
        self._nix_file_api=NixFileApi()
        self._parsed_nix_dict=None

    def _get_parsed_nix_dict(self)->dict:
        if self._parsed_nix_dict is None:
            self._parsed_nix_dict = self._nix_file_api.parse_config_file(self._nix_file_path)
        return self._parsed_nix_dict

    def get_nix_dict(self)->dict:
        nix_dict:dict = self._get_parsed_nix_dict()

        services = nix_dict.get('services')
        if not services or not services.get('samba'):
            return {}

        return services['samba'].get('settings',{})

    def get_dedicated_user_list(self)->list:
        users = (self._get_parsed_nix_dict().get('users') or {}).get('users') or {}
        return [name for name,value in users.items()
                if isinstance(value,dict) and value.get('group') == self.DEDICATED_USER_GROUP]

    def convert_local_share_list_to_nix_content(self,local_share_list:list)->str:
        settings = {
            'global': {
                'workgroup': 'WORKGROUP',
                'server string': 'nix-samba',
                'security': 'user',
                'map to guest': 'Bad User',
            }
        }

        dedicated_users = {}

        for local_share in local_share_list:
            settings[local_share.name] = local_share.get_nixcontent()

            if local_share.has_dedicated_user():
                # System account: no Unix password and nologin shell, so it cannot be used
                # to log in to the computer; only its Samba password (smbpasswd) is set.
                dedicated_users[local_share.dedicated_user] = {
                    'isSystemUser': True,
                    'group': self.DEDICATED_USER_GROUP,
                    'description': 'Samba account for share '+local_share.name+' (nix-samba)',
                }

        return self._nix_file_api.generate_samba_server_module(settings, dedicated_users, self.DEDICATED_USER_GROUP)

    def get_nix_file_path(self)->str:
        return self._nix_file_path
