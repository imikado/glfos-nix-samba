class LocalShare:

    name:str
    path:str
    comment:str
    guest_ok:bool
    read_only:bool
    valid_users:list

    def __init__(self,name,path,comment='',guest_ok=False,read_only=True,valid_users=None):
        self.name=name
        self.path=path
        self.comment=comment
        self.guest_ok=guest_ok
        self.read_only=read_only
        self.valid_users=valid_users if valid_users is not None else []

    def get_nixcontent(self)->dict:
        nix_dict:dict={}
        nix_dict['path']=self.path
        nix_dict['browseable']='yes'
        nix_dict['read only']='yes' if self.read_only else 'no'
        nix_dict['guest ok']='yes' if self.guest_ok else 'no'

        if self.comment:
            nix_dict['comment']=self.comment

        if not self.guest_ok and self.valid_users:
            nix_dict['valid users']=' '.join(self.valid_users)

        return nix_dict
