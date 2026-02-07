import re

from domain.contract.system_api_contract import SystemApiContract


class RequirementsDomain:

    _system_api:SystemApiContract
    _default_nix_content:str

    _need_fix_all_imports=False
    _need_fix_missing_list:list=[]

    IMPORT_SAMBA='./samba.nix'
    IMPORT_SAMBA_SETUP='./samba_setup.nix'

    _config_file_path:str='/etc/nixos/customConfig/default.nix'

    def __init__(self,system_api:SystemApiContract):
        self._system_api=system_api

    def get_config_file_path(self):
        return self._config_file_path

    def is_requirements_valid(self,default_nix_content):
        
        self._default_nix_content=default_nix_content

        _is_valid=True
        
        if not re.search(r'imports', self._default_nix_content):
            self._need_fix_all_imports=True
            return False

        if not re.search(r'[./]*samba\.nix', self._default_nix_content):
            self._need_fix_missing_list.append(self.IMPORT_SAMBA)
            _is_valid=False


        if not re.search(r'[./]*samba_setup\.nix', self._default_nix_content):
            self._need_fix_missing_list.append(self.IMPORT_SAMBA_SETUP)
            _is_valid=False

        return _is_valid


    def fix_requirements(self,password:str):
        if self._need_fix_all_imports:
            new_content=self.get_content_with_missing_import_block(self._default_nix_content)
            print('need import block')

        if len(self._need_fix_missing_list)>0:
            new_content=self.get_content_with_missing_imports(self._default_nix_content,self._need_fix_missing_list)
            print('nee missing import')

        print(new_content)
        exit()

        self._system_api.write_file_sudo(self._config_file_path,new_content,password)

    def get_content_with_missing_import_block(self,content:str):
        new_content=''
        if content[-1]=='}':
            new_content=content[::-1]
            new_content+="""
imports=[
    ./samba.nix
    ./samba-setup.nix
];
"""
        else:
            print('Error: unable to find end }')

        return new_content

    def get_content_with_missing_imports(self,content:str,missing_import_list:list):
        new_content=''
        start_import=False
        for line in content.split("\n"):
            if re.search('imports',line) and re.search('=',line):
                start_import=True

            if start_import and re.search('];',line):
                line="\n".join(missing_import_list)+"\n"+line

            new_content+=line+"\"n"

        return new_content