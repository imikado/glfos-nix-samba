class RemoteShare:

    path:str
    remote_path:str
    fs_type:str='cifs'
    options:list=[]

    def __init__(self,path,remote_path):
        self.path=path
        self.remote_path=remote_path
        pass

    def set_options(self,options:list):
        self.options=options

    def get_nixcontent(self)->dict:
        nix_dict:dict={}
        nix_dict['device']=self.remote_path
        nix_dict['fsType']='cifs'
        nix_dict['options']=self.options

        return nix_dict
