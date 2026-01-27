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

    def update_file_systems(self, original_content: str, file_systems: dict) -> str:
        """
        Update only the fileSystems section in a NixOS config file.
        Removes existing CIFS fileSystems entries and adds new ones.
        """
        lines = original_content.split('\n')
        result_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check if this line starts a fileSystems entry with cifs
            if 'fileSystems.' in line and '=' in line:
                # Look ahead to check if it's a cifs entry
                is_cifs = False
                temp_lines = []
                temp_i = i
                temp_brace_count = 0

                while temp_i < len(lines):
                    temp_line = lines[temp_i]
                    temp_lines.append(temp_line)
                    temp_brace_count += temp_line.count('{') - temp_line.count('}')

                    if 'fsType' in temp_line and 'cifs' in temp_line:
                        is_cifs = True

                    if temp_brace_count <= 0 and temp_i > i:
                        break
                    temp_i += 1

                if is_cifs:
                    # Skip this entire fileSystems entry
                    i = temp_i + 1
                    continue

            result_lines.append(line)
            i += 1

        # Find the position to insert new fileSystems entries (before the closing brace)
        # Look for the last '}' that closes the main module
        insert_position = len(result_lines) - 1
        for j in range(len(result_lines) - 1, -1, -1):
            if result_lines[j].strip() == '}':
                insert_position = j
                break

        # Generate new fileSystems entries
        new_entries = []
        for path, config in file_systems.items():
            entry = self._generate_file_system_entry(path, config)
            new_entries.append(entry)

        # Insert new entries before the closing brace
        for entry in new_entries:
            result_lines.insert(insert_position, entry)

        return '\n'.join(result_lines)

    def _generate_file_system_entry(self, path: str, config: dict) -> str:
        """Generate a single fileSystems entry."""
        lines = [f'  fileSystems."{path}" = {{']

        if 'device' in config:
            lines.append(f'    device = "{config["device"]}";')

        if 'fsType' in config:
            lines.append(f'    fsType = "{config["fsType"]}";')

        if 'options' in config and config['options']:
            options_str = ' '.join(f'"{opt}"' for opt in config['options'])
            lines.append(f'    options = [ {options_str} ];')

        lines.append('  };')
        return '\n'.join(lines)


class NixParseError(Exception):
    """Exception raised when Nix parsing fails."""
    pass
