from genericpath import exists
import subprocess
import tempfile
import os

from domain.contract.system_api_contract import SystemApiContract


class SystemApi(SystemApiContract):

    _password:str

    def read_file(self, path: str):
        return open(path, 'r').read()

    def write_file(self, path: str, content: str):
        open(path, 'w').write(content)

    def write_file_sudo(self, path: str, content: str, password: str):

        self._password=password
        
        """Write file with elevated privileges using sudo."""
        # Write content to a temporary file first
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.nix') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            if False==exists(path):

                self.sudo_execute(['sudo', '-S', 'touch', path])
                self.sudo_execute(['sudo', '-S', 'chmod','644', path])

                
            self.sudo_execute(['sudo', '-S', 'cp', tmp_path, path])
        finally:
            # Clean up temp file
            os.unlink(tmp_path)

    def sudo_execute(self,params:list):
        process = subprocess.Popen(
                params,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        stdout, stderr = process.communicate(input=f"{self._password}\n")

        if process.returncode != 0:
            if "incorrect password" in stderr.lower() or "sorry" in stderr.lower():
                raise PermissionError("Incorrect password")
            raise PermissionError(f"Failed to excute commands: {stderr}")

    def file_exists(self,path:str)->bool:
        return exists(path)
    
    def create_dir(self,path:str):
        os.mkdir(path, mode=0o777,)