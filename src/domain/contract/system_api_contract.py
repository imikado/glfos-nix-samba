from abc import abstractmethod


class SystemApiContract:

    @abstractmethod
    def read_file(path: str) -> str:
        pass

    @abstractmethod
    def write_file(path: str, content: str):
        pass

    @abstractmethod
    def write_file_sudo(path: str, content: str, password: str):
        """Write file with elevated privileges using sudo."""
        pass