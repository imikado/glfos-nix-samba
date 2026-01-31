from domain.contract.samba_file_api_contract import SambaFileApiContract
from infrastructure.api.nix_file_api import NixFileApi


class SambaFileApi(SambaFileApiContract):

    _nix_file:str='/etc/nixos/customConfig/samba.nix'

    _nix_file_api:NixFileApi

    def __init__(self):
        self._nix_file_api=NixFileApi()
        pass

    def get_nix_dict(self)->dict:
        nix_dict:dict = self._nix_file_api.parse_config_file(self._nix_file)

        if nix_dict['fileSystems'] is None:
            return {}
        
        return nix_dict

    def convert_remote_list_to_nix_content(self,remote_file_list:list)->str:
        file_systems = {}
        for remote in remote_file_list:
            file_systems[remote.path] = remote.get_nixcontent()

        new_content = self._nix_file_api.generate_samba_module(file_systems)

        return new_content