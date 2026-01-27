import subprocess
import tempfile
import os

from domain.contract.system_api_contract import SystemApiContract


class SystemApi(SystemApiContract):

    def read_file(self, path: str):
        return open(path, 'r').read()

    def write_file(self, path: str, content: str):
        open(path, 'w').write(content)

    def write_file_sudo(self, path: str, content: str, password: str):
        """Write file with elevated privileges using sudo."""
        # Write content to a temporary file first
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.nix') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Use sudo -S to copy the temp file to the target path
            process = subprocess.Popen(
                ['sudo', '-S', 'cp', tmp_path, path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=f"{password}\n")

            if process.returncode != 0:
                if "incorrect password" in stderr.lower() or "sorry" in stderr.lower():
                    raise PermissionError("Incorrect password")
                raise PermissionError(f"Failed to write file: {stderr}")
        finally:
            # Clean up temp file
            os.unlink(tmp_path)