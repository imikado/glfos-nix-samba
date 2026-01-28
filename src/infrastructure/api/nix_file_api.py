import subprocess
import json
import re
from typing import Any

from domain.contract.nix_file_api_contract import NixFileApiContract
from infrastructure.api.system_api import SystemApi


class NixFileApi(NixFileApiContract):

    def parse_config_file(self, path: str) -> dict:
        """Parse the samba.nix config file managed by this application."""
        system_api = SystemApi()
        if not system_api.file_exists(path):
            return {"fileSystems":{}}

        # Since samba.nix is a NixOS module function ({ config, lib, pkgs, ... }: { ... })
        # but doesn't use any of those args, we pass empty mock values.
        # This avoids importing nixpkgs which is very slow.
        nix_expr = f'''
        let
          moduleFn = import {path};
          result = moduleFn {{
            config = {{}};
            lib = {{}};
            pkgs = {{}};
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
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise NixParseError(f"Failed to parse samba config: {e.stderr}")
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


    def generate_samba_module(self, file_systems: dict) -> str:





        """
        Generate a complete samba.nix NixOS module and format it with nixfmt.
        """


  

        

        # Build the module body with fileSystems entries
        body = self._to_nix_string({"fileSystems": file_systems}, indent=0)

        # Wrap in NixOS module function
        raw_nix = f'''{{
  lib,
  config,
  pkgs,
  ...
}}:
{body}
'''
        # Format with nixfmt
        try:
            result = subprocess.run(
                ['nixfmt'],
                input=raw_nix,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except FileNotFoundError:
            # nixfmt not installed, return unformatted
            return raw_nix
        except subprocess.CalledProcessError:
            # formatting failed, return unformatted
            return raw_nix


class NixParseError(Exception):
    """Exception raised when Nix parsing fails."""
    pass
