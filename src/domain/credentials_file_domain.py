from domain.contract.system_api_contract import SystemApiContract


class CredentialsFileDomain:

    _system_api:SystemApiContract

    def __init__(self,system_api:SystemApiContract):
        self._system_api=system_api
        pass

    def write_file(self,path:str,username:str,password:str):
        content='username='+username+'\n'
        content+='password='+password+''
        self._system_api.write_file(path,content)
        pass