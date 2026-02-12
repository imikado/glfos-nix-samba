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
    _need_to_save=False

    def __init__(self,system_api:SystemApiContract,samba_file_api:SambaFileApiContract):
        self._system_api=system_api
        self._samba_file_api=samba_file_api
        self._remote_share_repository=RemoteShareRepository()
        pass

    def need_to_save(self)->bool:
        return self._need_to_save

    def get_list(self)->list:

        if not self._loaded:

            nix_dict=self._samba_file_api.get_nix_dict()
            bookmark_list=self._system_api.get_gtk_bookmark_list()
            self._remote_share_repository.load_from_dict_and_bookmark_list(nix_dict,bookmark_list)
            self._loaded=True

        return self._remote_share_repository.get_list()
    
    def add_item(self, remote_share: RemoteShare):

        self._remote_share_repository.add_item(remote_share)
        self._need_to_save=True

    def edit_item(self, path_to_update: str, remote_share_to_update: RemoteShare):

        self._remote_share_repository.edit_item(path_to_update,remote_share_to_update)
        self._need_to_save=True

    def delete_item(self, path_to_delete: str):
        self._remote_share_repository.delete_item(path_to_delete)
        self._need_to_save=True


    def save(self, password: str):

        new_content=self._samba_file_api.convert_remote_list_to_nix_content(self.get_list())

        self._system_api.write_file_sudo(self._samba_file_api.get_nix_file_path(), new_content, password) 

        gtk_bookmark_list=self._system_api.get_gtk_bookmark_list()
        new_gtk_bookmark_list=self.get_gtk_bookmark_list(gtk_bookmark_list,self.get_list())

        self._system_api.write_gtk_bookmark_list(new_gtk_bookmark_list)

        self._need_to_save=False

    def get_gtk_bookmark_list(self,current_bookmark_list:list,new_bookmark_list:list)->list:
        target_bookmark_list=[]
        for current_bookmark_loop in current_bookmark_list:
            if ' ' not in current_bookmark_loop:
                target_bookmark_list.append(current_bookmark_loop)
        
        for new_bookmark_loop in new_bookmark_list:
            target_bookmark_list.append(new_bookmark_loop)

        return target_bookmark_list