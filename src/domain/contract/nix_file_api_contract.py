from abc import abstractmethod
from typing import Any


class NixFileApiContract:

    @abstractmethod
    def parse_config_file(path:str)-> dict:
        pass

    @abstractmethod
    def convert_dict_to_string(self, nix_obj: Any) -> str:
        pass