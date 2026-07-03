from domain.contract.local_samba_file_api_contract import LocalSambaFileApiContract
from infrastructure.api.nix_file_api import NixFileApi


class LocalSambaFileApi(LocalSambaFileApiContract):

    _nix_file_path:str='/etc/nixos/customConfig/samba-server.nix'

    _nix_file_api:NixFileApi

    def __init__(self):
        self._nix_file_api=NixFileApi()

    def get_nix_dict(self)->dict:
        nix_dict:dict = self._nix_file_api.parse_config_file(self._nix_file_path)

        services = nix_dict.get('services')
        if not services or not services.get('samba'):
            return {}

        return services['samba'].get('settings',{})

    def convert_local_share_list_to_nix_content(self,local_share_list:list)->str:
        settings = {
            'global': {
                'workgroup': 'WORKGROUP',
                'server string': 'nix-samba',
                'security': 'user',
                'map to guest': 'Bad User',
            }
        }

        for local_share in local_share_list:
            settings[local_share.name] = local_share.get_nixcontent()

        return self._nix_file_api.generate_samba_server_module(settings)

    def get_nix_file_path(self)->str:
        return self._nix_file_path
