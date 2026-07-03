from domain.entity.local_share import LocalShare


class LocalShareRepository:

    _local_share_list:list=[]

    def set_list(self,local_share_list:list):
        self._local_share_list=local_share_list

    def get_list(self)->list:
        return self._local_share_list

    def add_item(self,local_share:LocalShare):
        self._local_share_list.append(local_share)

    def edit_item(self,name_to_edit:str,local_share:LocalShare):
        local_share_list:list=[]
        for local_share_loop in self._local_share_list:
            if local_share_loop.name == name_to_edit:
                local_share_list.append(local_share)
            else:
                local_share_list.append(local_share_loop)

        self._local_share_list=local_share_list

    def delete_item(self, name_to_delete: str):
        local_share_list:list=[]
        for local_share_loop in self._local_share_list:
            if local_share_loop.name != name_to_delete:
                local_share_list.append(local_share_loop)

        self._local_share_list=local_share_list

    def load_from_dict(self,samba_settings:dict):
        local_share_list=[]

        for share_name_loop,share_value_loop in samba_settings.items():
            if share_name_loop == 'global':
                continue

            valid_users_raw = share_value_loop.get('valid users','')

            local_share_list.append(LocalShare(
                name=share_name_loop,
                path=share_value_loop.get('path',''),
                comment=share_value_loop.get('comment',''),
                guest_ok=share_value_loop.get('guest ok','no')=='yes',
                read_only=share_value_loop.get('read only','yes')=='yes',
                valid_users=valid_users_raw.split() if valid_users_raw else [],
            ))

        self._local_share_list=local_share_list
