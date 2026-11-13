class LocalSambaFileApiContract:

    def get_nix_dict(self)->dict:
        pass

    def get_dedicated_user_list(self)->list:
        """Names of the share-only accounts declared in samba-server.nix."""
        pass

    def convert_local_share_list_to_nix_content(self,local_share_list:list)->str:
        pass

    def get_nix_file_path(self)->str:
        pass
