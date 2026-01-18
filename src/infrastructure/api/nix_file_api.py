import subprocess
import json
import re
from typing import Any

from domain.contract.nix_file_api_contract import NixFileApiContract


class NixFileApi(NixFileApiContract):

    def parse_config_file(self, path: str) -> dict:
        """
        Parse a NixOS module file (a function) by calling it with mock arguments.
        """
        # Create a Nix expression that imports and calls the module function
        nix_expr = f'''
        let
          moduleFn = import {path};
          # Call the module with empty/mock arguments
          result = moduleFn {{
            config = {{}};
            lib = import <nixpkgs/lib>;
            pkgs = import <nixpkgs> {{}};
            modulesPath = "<nixpkgs/nixos/modules>";
          }};
        in result
        '''
        try:
            result = subprocess.run(
                ['nix', 'eval', '--json', '--impure', '--expr', nix_expr],
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise NixParseError(f"Failed to parse NixOS module: {e.stderr}")
        except json.JSONDecodeError as e:
            raise NixParseError(f"Failed to decode Nix output as JSON: {e}")

    def convert_dict_to_string(self, nix_obj: Any) -> str:
        """
        Convert a Python object to a Nix expression string.
        """
        return self._to_nix_string(nix_obj)

    def _to_nix_string(self, obj: Any, indent: int = 0) -> str:
        """
        Recursively convert a Python object to Nix syntax.
        """
        indent_str = '  ' * indent

        if obj is None:
            return 'null'
        elif isinstance(obj, bool):
            return 'true' if obj else 'false'
        elif isinstance(obj, int):
            return str(obj)
        elif isinstance(obj, float):
            return str(obj)
        elif isinstance(obj, str):
            escaped = obj.replace('\\', '\\\\').replace('"', '\\"').replace('${', '\\${')
            return f'"{escaped}"'
        elif isinstance(obj, list):
            if not obj:
                return '[ ]'
            items = [self._to_nix_string(item, indent + 1) for item in obj]
            items_str = '\n'.join(f'{indent_str}  {item}' for item in items)
            return f'[\n{items_str}\n{indent_str}]'
        elif isinstance(obj, dict):
            if not obj:
                return '{ }'
            pairs = []
            for key, value in obj.items():
                key_str = self._format_key(key)
                value_str = self._to_nix_string(value, indent + 1)
                pairs.append(f'{indent_str}  {key_str} = {value_str};')
            pairs_str = '\n'.join(pairs)
            return f'{{\n{pairs_str}\n{indent_str}}}'
        else:
            return f'"{str(obj)}"'

    def _format_key(self, key: str) -> str:
        """
        Format a dictionary key for Nix syntax.
        Simple identifiers don't need quotes, others do.
        """
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_\'-]*$', key):
            return key
        escaped = key.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'


class NixParseError(Exception):
    """Exception raised when Nix parsing fails."""
    pass
