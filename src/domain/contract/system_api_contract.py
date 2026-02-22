from abc import abstractmethod


class SystemApiContract:

    @abstractmethod
    def read_file(path: str) -> str:
        pass

    @abstractmethod
    def write_file(path: str, content: str):
        pass

    @abstractmethod
    def write_file_tmp(self, content: str)->str:
        pass

    @abstractmethod
    def backup_file_sudo(self,path:str,password:str):
        pass

    @abstractmethod
    def write_file_sudo(path: str, content: str, password: str):
        """Write file with elevated privileges using sudo."""
        pass

    @abstractmethod
    def file_exists(self,path:str)->bool:
        pass

    @abstractmethod
    def create_dir(self,path:str):
        pass

    @abstractmethod
    def chown_smb_creds_file(self,path:str):
        pass

    @abstractmethod
    def is_current_desktop_kde(self)->bool:
        pass

    @abstractmethod
    def get_current_desktop(self)->str:
        pass

    @abstractmethod
    def get_gtk_bookmark_list(self)->list:
        pass

    @abstractmethod
    def write_gtk_bookmark_list(self,bookmark_list:list):
        pass

    @abstractmethod
    def get_kde_bookmark_list(self)->list:
        pass

    @abstractmethod
    def write_kde_bookmark_list(self,bookmark_list:list):
        pass

    @abstractmethod
    def nix_rebuild_sudo(self,password:str):
        pass