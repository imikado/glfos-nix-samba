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