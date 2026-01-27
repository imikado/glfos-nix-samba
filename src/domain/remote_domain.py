from domain.contract.nix_file_api_contract import NixFileApiContract
from domain.contract.system_api_contract import SystemApiContract
from domain.entity.remote_share import RemoteShare


class RemoteDomain():

    _nix_file:str='/etc/nixos/hardware-configuration.nix'

    _system_api:SystemApiContract
    _nix_file_api:NixFileApiContract

    def __init__(self,system_api:SystemApiContract,nix_file_api:NixFileApiContract):
        self._system_api=system_api
        self._nix_file_api=nix_file_api

        pass


    def get_list(self):

        nix_dict:dict = self._nix_file_api.parse_config_file(self._nix_file)

        if nix_dict['fileSystems'] is None:
            return[]
        
        remote_list=[]

        for file_system_loop_key in nix_dict['fileSystems']:
            
            file_system_loop = nix_dict['fileSystems'][file_system_loop_key]
            
            if file_system_loop['fsType']=='cifs':
                new_remote_share=RemoteShare(file_system_loop_key,file_system_loop['device'])
                new_remote_share.set_options(file_system_loop['options'])
                remote_list.append(new_remote_share)

        return remote_list
    
    def add_item(self):
        pass

    def edit_item(self, path_to_update: str, remote_share_to_update: RemoteShare, password: str):
        new_remote_list = []
        for remote_list_loop in self.get_list():
            if remote_list_loop.path == path_to_update:
                new_remote_list.append(remote_share_to_update)
            else:
                new_remote_list.append(remote_list_loop)

        self.save_list(new_remote_list, password)

    def save_list(self, remote_list: list, password: str):
        nix_dict: dict = self._nix_file_api.parse_config_file(self._nix_file)

        for remote_list_loop in remote_list:
            nix_dict['fileSystems'][remote_list_loop.path] = remote_list_loop.get_nixcontent()

        nix_content = self._nix_file_api.convert_dict_to_string(nix_dict)

        self._system_api.write_file_sudo(self._nix_file, nix_content, password) 