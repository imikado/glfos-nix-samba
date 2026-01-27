from domain.contract.system_api_contract import SystemApiContract


class SystemApi(SystemApiContract):

    def read_file(self,path:str):
        return  open(path,'r').read()
    
    def write_file(self,path:str, content:str):
        open(path,'w').write(content)