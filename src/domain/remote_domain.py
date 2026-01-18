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
                remote_list.append(new_remote_share)

        return remote_list