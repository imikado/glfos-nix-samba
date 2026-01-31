from domain.contract.nix_file_api_contract import NixFileApiContract
from domain.contract.samba_file_api_contract import SambaFileApiContract
from domain.contract.system_api_contract import SystemApiContract
from domain.entity.remote_share import RemoteShare
from domain.repository.remote_share_repository import RemoteShareRepository


class RemoteDomain():

    _loaded=False
    _system_api:SystemApiContract
    _samba_file_api:SambaFileApiContract
    _remote_share_repository:RemoteShareRepository

    def __init__(self,system_api:SystemApiContract,samba_file_api:SambaFileApiContract):
        self._system_api=system_api
        self._samba_file_api=samba_file_api
        self._remote_share_repository=RemoteShareRepository()
        pass


    def get_list(self)->list:

        if not self._loaded:

            nix_dict=self._samba_file_api.get_nix_dict()
            self._remote_share_repository.load_from_dict(nix_dict)
            self._loaded=True

        return self._remote_share_repository.get_list()
    
    def add_item(self, remote_share: RemoteShare):

        self._remote_share_repository.add_item(remote_share)

    def edit_item(self, path_to_update: str, remote_share_to_update: RemoteShare):

        self._remote_share_repository.edit_item(path_to_update,remote_share_to_update)


    def save(self, password: str):

        new_content=self._samba_file_api.convert_remote_list_to_nix_content(self.get_list())

        self._system_api.write_file_sudo(self._nix_file, new_content, password) 