class RemoteShare:

    path:str
    remote_path:str
    label:str
    fs_type:str='cifs'
    options:list=[]
    show_on_desktop:bool=False

    def __init__(self,path,remote_path,label,show_on_desktop=False):
        self.path=path
        self.remote_path=remote_path
        self.label=label
        self.show_on_desktop=show_on_desktop
        pass

    def set_options(self,options:list):
        options.append('_netdev')
        options.append('file_mode=0775')
        options.append('dir_mode=0775')
        options.append('nofail')
        options.append('x-gvfs-hide')

        self.options=options


    def get_nixcontent(self)->dict:
        nix_dict:dict={}
        nix_dict['device']=self.remote_path
        nix_dict['fsType']='cifs'
        nix_dict['options']=self.options
        nix_dict['label']=self.label

        return nix_dict
