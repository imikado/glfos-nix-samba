from domain.entity.remote_share import RemoteShare


class RemoteShareRepository:

    _remote_share_list:list=[]

    def set_list(self,remote_share_list:list):
        self._remote_share_list=remote_share_list

    def get_list(self)->list:
        return self._remote_share_list
    
    def add_item(self,remote_share:RemoteShare):
        self._remote_share_list.append(remote_share)

    def edit_item(self,path_to_edit:str,remote_share:RemoteShare):
        remote_share_list:list=[]
        for remote_share_loop in self._remote_share_list:
            if remote_share_loop.path == path_to_edit:
                remote_share_list.append(remote_share)
            else:
                remote_share_list.append(remote_share_loop)

        self._remote_share_list=remote_share_list

    def delete_item(self, path_to_delete: str):
        remote_share_list:list=[]
        for remote_share_loop in self._remote_share_list:
            if remote_share_loop.path != path_to_delete:
                remote_share_list.append(remote_share_loop)

        self._remote_share_list=remote_share_list    

    def load_from_dict(self,nix_dict:dict):
        
        if nix_dict['fileSystems'] is None:
            return[]
        
        remote_list=[]

        for file_system_loop_key in nix_dict['fileSystems']:
            
            file_system_loop = nix_dict['fileSystems'][file_system_loop_key]
            
            if file_system_loop['fsType']=='cifs':
                new_remote_share=RemoteShare(file_system_loop_key,file_system_loop['device'])
                new_remote_share.set_options(file_system_loop['options'])
                remote_list.append(new_remote_share)

        self._remote_share_list=remote_list