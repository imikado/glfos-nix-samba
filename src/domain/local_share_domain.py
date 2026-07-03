from domain.contract.local_samba_file_api_contract import LocalSambaFileApiContract
from domain.contract.system_api_contract import SystemApiContract
from domain.entity.local_share import LocalShare
from domain.repository.local_share_repository import LocalShareRepository


class LocalShareDomain():

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

    def need_to_save(self)->bool:
        return self._need_to_save

    def get_list(self)->list:

        if not self._loaded:
            samba_settings=self._local_samba_file_api.get_nix_dict()
            self._local_share_repository.load_from_dict(samba_settings)
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

    def save(self)->str:
        new_content=self._local_samba_file_api.convert_local_share_list_to_nix_content(self.get_list())

        tmp_samba_server_nix_path=self._system_api.write_file_tmp(new_content)

        self._need_to_save=False

        return tmp_samba_server_nix_path
