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
    _delete_remote_list:list=[]

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
            bookmark_list=[]
            if self._system_api.is_current_desktop_kde():
                bookmark_list=self._system_api.get_kde_bookmark_list()                
            else:
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
        self._delete_remote_list.append(path_to_delete)
        self._need_to_save=True


    def save(self):

        new_content=self._samba_file_api.convert_remote_list_to_nix_content(self.get_list())

        #self._system_api.write_file_sudo(self._samba_file_api.get_nix_file_path(), new_content, password) 
        tmp_samba_nix_path=self._system_api.write_file_tmp( new_content) 

        if self._system_api.is_current_desktop_kde():
            kde_bookmark_list=self._system_api.get_kde_bookmark_list()
            new_kde_bookmark_list=self.get_kde_bookmark_list(kde_bookmark_list,self.get_list())
            self._system_api.write_kde_bookmark_list(new_kde_bookmark_list)
        else:
            gtk_bookmark_list=self._system_api.get_gtk_bookmark_list()
            new_gtk_bookmark_list=self.get_gtk_bookmark_list(gtk_bookmark_list,self.get_list())
            self._system_api.write_gtk_bookmark_list(new_gtk_bookmark_list)

        self._need_to_save=False

        return tmp_samba_nix_path
    
    def get_kde_bookmark_list(self,current_bookmark_list:list,remote_share_list:list)->list:
        target_bookmark_list=[]
        for current_bookmark_loop in current_bookmark_list:
            if not self.is_in_bookmark_list(current_bookmark_loop,remote_share_list) and not self.is_deleted(current_bookmark_loop):
                target_bookmark_list.append(current_bookmark_loop)

        for remote in remote_share_list:
            target_bookmark_list.append('file://' + remote.path + ' ' + remote.label)

        return target_bookmark_list

    def get_gtk_bookmark_list(self,current_bookmark_list:list,remote_share_list:list)->list:
        
        target_bookmark_list=[]
        for current_bookmark_loop in current_bookmark_list:
            if not self.is_in_bookmark_list( current_bookmark_loop,remote_share_list) and not self.is_deleted(current_bookmark_loop):
                target_bookmark_list.append(current_bookmark_loop)

        # Add samba bookmarks
        for remote in remote_share_list:
            target_bookmark_list.append('file://' + remote.path + ' ' + remote.label)

        return target_bookmark_list
    
    def is_deleted(self,bookmark_line:str):
        for path_deleted_loop in self._delete_remote_list:
            if path_deleted_loop in bookmark_line:
                return True
        return False
    
    def is_in_bookmark_list(self,bookmark_line:str,bookmark_list:list)->bool:
        for bookmark_loop in bookmark_list:
            if(bookmark_loop.path in bookmark_line):
                return True
            
        return False