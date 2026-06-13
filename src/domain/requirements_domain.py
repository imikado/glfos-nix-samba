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
    _config_samba_setup_file_path:str='/etc/nixos/customConfig/samba_setup.nix'
    _config_samba_file_path:str='/etc/nixos/customConfig/samba.nix'
    

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

        need_to_create_samba_setup_file=False
        need_to_create_samba=False

        if self._need_fix_all_imports:
            new_content=self.get_content_with_missing_import_block(self._default_nix_content)

            need_to_create_samba_setup_file=True
            need_to_create_samba=True

            
        if len(self._need_fix_missing_list)>0:
            new_content=self.get_content_with_missing_imports(self._default_nix_content,self._need_fix_missing_list)
            
            if self.IMPORT_SAMBA_SETUP in self._need_fix_missing_list:
                need_to_create_samba_setup_file=True
                need_to_create_samba=True

        if need_to_create_samba==True and not self._system_api.file_exists(self._config_samba_file_path):
            samba_content="""{}"""

            self._system_api.write_file_sudo(self._config_samba_file_path,samba_content,password)


        if need_to_create_samba_setup_file==True and not self._system_api.file_exists(self._config_samba_setup_file_path):

            samba_setup_content="""{ pkgs, lib, ... }:
{

  environment.systemPackages = [ pkgs.cifs-utils ];

  # lib.getBin: cifs-utils est multi-output, mount.cifs vit dans `bin`.
  security.wrappers."mount.cifs" = {
    setuid = true;
    owner = "root";
    group = "root";
    source = "${lib.getBin pkgs.cifs-utils}/bin/mount.cifs";
  };
}
"""
            self._system_api.write_file_sudo(self._config_samba_setup_file_path,samba_setup_content,password)

        self._system_api.backup_file_sudo(self._config_file_path,password)

        self._system_api.write_file_sudo(self._config_file_path,new_content,password)

    def get_content_with_missing_import_block(self,content:str):
        new_content=''
        import_block="""
imports=[
    %s
    %s
];

}
""" %(self.IMPORT_SAMBA,self.IMPORT_SAMBA_SETUP)

        if content[-1]=='}':
            new_content=content[:-1]
            new_content+="\n"+import_block

        elif content[-2]=='}':
            new_content=content[:-2]
            new_content+="\n"+import_block
        elif content[-3]=='}':
            new_content=content[:-3]
            new_content+="\n"+import_block
        else:
            print('Error: unable to find end }, last character:'+content[-1])

        return new_content

    def has_samba_imports(self,default_nix_content):

        self._default_nix_content=default_nix_content

        return bool(re.search(r'[./]*samba\.nix', default_nix_content)) \
            or bool(re.search(r'[./]*samba_setup\.nix', default_nix_content))

    def remove_samba_imports(self,password:str):

        new_content=self.get_content_without_imports(self._default_nix_content,[self.IMPORT_SAMBA,self.IMPORT_SAMBA_SETUP])

        self._system_api.backup_file_sudo(self._config_file_path,password)

        self._system_api.write_file_sudo(self._config_file_path,new_content,password)

    def get_content_without_imports(self,content:str,import_list:list):
        new_content=''

        for lineLoop in content.split("\n"):
            stripped_line=lineLoop.strip().rstrip(',')

            if stripped_line in import_list:
                continue

            new_content+=lineLoop+"\n"

        return new_content

    def get_content_with_missing_imports(self,content:str,missing_import_list:list):
        new_content=''
        start_import=False

        lineList=content.split("\n")
        for lineLoop in lineList:

            if re.search('imports',lineLoop) and re.search('=',lineLoop):
                start_import=True

            if start_import and re.search('];',lineLoop):
                new_content+="\n".join(missing_import_list)+"\n"
                start_import=False

            new_content+=lineLoop+"\n"

        return new_content