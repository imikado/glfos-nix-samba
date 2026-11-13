class LocalShare:

    name:str
    path:str
    comment:str
    guest_ok:bool
    read_only:bool
    valid_users:list
    # Account created only for this share (system user, cannot log in to the computer)
    dedicated_user:str
    # Samba password of the dedicated account: kept in memory only, never written to Nix
    # (the Nix store is world readable). Empty means "keep the current password".
    dedicated_password:str
    # Unix account used for file access (folder owner), needed by the dedicated account
    force_user:str

    def __init__(self,name,path,comment='',guest_ok=False,read_only=True,valid_users=None,dedicated_user='',dedicated_password='',force_user=''):
        self.name=name
        self.path=path
        self.comment=comment
        self.guest_ok=guest_ok
        self.read_only=read_only
        self.valid_users=valid_users if valid_users is not None else []
        self.dedicated_user=dedicated_user
        self.dedicated_password=dedicated_password
        self.force_user=force_user

    def has_dedicated_user(self)->bool:
        return not self.guest_ok and bool(self.dedicated_user)

    def get_nixcontent(self)->dict:
        nix_dict:dict={}
        nix_dict['path']=self.path
        nix_dict['browseable']='yes'
        nix_dict['read only']='yes' if self.read_only else 'no'
        nix_dict['guest ok']='yes' if self.guest_ok else 'no'

        if self.comment:
            nix_dict['comment']=self.comment

        if self.has_dedicated_user():
            nix_dict['valid users']=self.dedicated_user
            if self.force_user:
                nix_dict['force user']=self.force_user
        elif not self.guest_ok and self.valid_users:
            nix_dict['valid users']=' '.join(self.valid_users)

        return nix_dict
