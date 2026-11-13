import re

from domain.contract.local_samba_file_api_contract import LocalSambaFileApiContract
from domain.contract.system_api_contract import SystemApiContract
from domain.entity.local_share import LocalShare
from domain.repository.local_share_repository import LocalShareRepository


class LocalShareDomain():

    # Unix user name rules (lowercase, as recommended by useradd)
    DEDICATED_USER_PATTERN=r'^[a-z_][a-z0-9_-]{0,31}$'

    _loaded=False
    _system_api:SystemApiContract
    _local_samba_file_api:LocalSambaFileApiContract
    _local_share_repository:LocalShareRepository
    _need_to_save=False

    def __init__(self,system_api:SystemApiContract,local_samba_file_api:LocalSambaFileApiContract):
        self._system_api=system_api
        self._local_samba_file_api=local_samba_file_api
        self._local_share_repository=LocalShareRepository()
        self._delete_local_share_list=[]
        # Dedicated accounts present in the last saved configuration
        self._saved_dedicated_user_list=[]

    def need_to_save(self)->bool:
        return self._need_to_save

    def mark_as_unsaved(self):
        self._need_to_save=True

    def get_list(self)->list:

        if not self._loaded:
            samba_settings=self._local_samba_file_api.get_nix_dict()
            self._saved_dedicated_user_list=list(self._local_samba_file_api.get_dedicated_user_list())
            self._local_share_repository.load_from_dict(samba_settings,self._saved_dedicated_user_list)
            self._loaded=True

        return self._local_share_repository.get_list()

    def add_item(self, local_share: LocalShare):
        self._local_share_repository.add_item(local_share)
        self._need_to_save=True

    def edit_item(self, name_to_update: str, local_share_to_update: LocalShare):
        self._local_share_repository.edit_item(name_to_update,local_share_to_update)
        self._need_to_save=True

    def delete_item(self, name_to_delete: str):
        self._local_share_repository.delete_item(name_to_delete)
        self._delete_local_share_list.append(name_to_delete)
        self._need_to_save=True

    # --- Dedicated (share-only) accounts -------------------------------------------------

    def is_dedicated_user_name_valid(self, user_name: str) -> bool:
        return bool(re.match(self.DEDICATED_USER_PATTERN, user_name))

    def is_dedicated_user_available(self, user_name: str, share_name_to_ignore: str = None) -> bool:
        """An account is exclusive to one share and must not be an existing system account."""
        for local_share_loop in self.get_list():
            if local_share_loop.name == share_name_to_ignore:
                continue
            if local_share_loop.has_dedicated_user() and local_share_loop.dedicated_user == user_name:
                return False

        # Accounts already managed by this application exist on the system: that's expected
        if user_name in self._saved_dedicated_user_list:
            return True

        return not self._system_api.user_exists(user_name)

    def get_folder_owner(self, path: str) -> str:
        """Unix account used to access the files of a share opened with a dedicated account."""
        return self._system_api.get_path_owner(path)

    def get_dedicated_account_actions(self) -> dict:
        """Privileged operations on Samba accounts to run with the rebuild.

        remove: accounts no longer used (their Samba password entry is deleted)
        passwords: list of (user, password) to set once the account is created
        """
        current_user_list=[]
        password_list=[]
        for local_share_loop in self.get_list():
            if not local_share_loop.has_dedicated_user():
                continue
            current_user_list.append(local_share_loop.dedicated_user)
            if local_share_loop.dedicated_password:
                password_list.append((local_share_loop.dedicated_user,local_share_loop.dedicated_password))

        remove_list=[user for user in self._saved_dedicated_user_list if user not in current_user_list]

        return {'remove':remove_list,'passwords':password_list}

    def confirm_saved(self):
        """Called once the rebuild succeeded: forget the passwords kept in memory."""
        self._saved_dedicated_user_list=[]
        for local_share_loop in self.get_list():
            if local_share_loop.has_dedicated_user():
                self._saved_dedicated_user_list.append(local_share_loop.dedicated_user)
            local_share_loop.dedicated_password=''

    def save(self)->str:
        new_content=self._local_samba_file_api.convert_local_share_list_to_nix_content(self.get_list())

        tmp_samba_server_nix_path=self._system_api.write_file_tmp(new_content)

        self._need_to_save=False

        return tmp_samba_server_nix_path
