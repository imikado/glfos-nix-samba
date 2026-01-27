import subprocess

from domain.contract.system_api_contract import SystemApiContract


class SystemApi(SystemApiContract):

    def read_file(self, path: str):
        return open(path, 'r').read()

    def write_file(self, path: str, content: str):
        open(path, 'w').write(content)

    def write_file_sudo(self, path: str, content: str, password: str):
        """Write file with elevated privileges using sudo."""
        # Use sudo -S to read password from stdin, then tee to write the file
        process = subprocess.Popen(
            ['sudo', '-S', 'tee', path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Send password + newline, then the content
        stdout, stderr = process.communicate(input=f"{password}\n{content}")

        if process.returncode != 0:
            if "incorrect password" in stderr.lower() or "sorry" in stderr.lower():
                raise PermissionError("Incorrect password")
            raise PermissionError(f"Failed to write file: {stderr}")