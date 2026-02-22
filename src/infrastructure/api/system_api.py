from genericpath import exists
import subprocess
import tempfile
import os
import datetime
import xml.etree.ElementTree as ET

from domain.contract.system_api_contract import SystemApiContract


class SystemApi(SystemApiContract):

    _password:str

    def read_file(self, path: str):
        return open(path, 'r').read()

    def write_file(self, path: str, content: str):
        open(path, 'w').write(content)

    def backup_file_sudo(self,path:str,password:str):
        self._password=password


        datetime_now = datetime.datetime.now()

        backup_file_path=path+'.nix-samba.back'+datetime_now.strftime('%Y%m%d')

        self.sudo_execute(['sudo','-S','cp',path,backup_file_path])

    def write_file_tmp(self, content: str)->str:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.nix') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        return tmp_path

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

    def execute(self,params:list):
        subprocess.Popen(params)
    
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

    def nix_rebuild_sudo(self,password:str):
        self._password=password
        self.sudo_execute(['sudo', '-S', 'nixos-rebuild','switch'])
        pass

    def chown_smb_creds_file(self,path:str):
        subprocess.Popen(['chmod','600',path])

    def is_current_desktop_kde(self)->bool:
        if self.get_current_desktop() =='kde':
            return True
        return False

    def get_current_desktop(self)->str:
        """Return detected desktop environment: 'gnome', 'kde', or 'unknown'."""
        xdg = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        if 'gnome' in xdg:
            return 'gnome'
        if 'kde' in xdg:
            return 'kde'
        # Fallback: check DESKTOP_SESSION
        session = os.environ.get('DESKTOP_SESSION', '').lower()
        if 'gnome' in session:
            return 'gnome'
        if 'kde' in session or 'plasma' in session:
            return 'kde'
        return 'unknown'

    def get_gtk_bookmark_list(self)->list:
        bookmarks_path = os.path.join(os.path.expanduser('~'), '.config', 'gtk-3.0', 'bookmarks')
        if not os.path.isfile(bookmarks_path):
            return []
        with open(bookmarks_path, 'r') as f:
            return [line.rstrip('\n') for line in f if line.strip()]

    def write_gtk_bookmark_list(self,bookmark_list:list):
        bookmarks_path = os.path.join(os.path.expanduser('~'), '.config', 'gtk-3.0', 'bookmarks')
        current_list = self.get_gtk_bookmark_list()
        if current_list == bookmark_list:
            return
        os.makedirs(os.path.dirname(bookmarks_path), exist_ok=True)
        with open(bookmarks_path, 'w') as f:
            for bookmark in bookmark_list:
                f.write(bookmark + '\n')

    def get_kde_bookmark_list(self)->list:
        """Read ~/.local/share/user-places.xbel and return file:// entries as 'url label' strings."""
        xbel_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'user-places.xbel')
        if not os.path.isfile(xbel_path):
            return []
        try:
            tree = ET.parse(xbel_path)
            root = tree.getroot()
            bookmark_list = []
            for bookmark in root.findall('bookmark'):
                href = bookmark.get('href', '')
                if href.startswith('file://'):
                    title_elem = bookmark.find('title')
                    label = title_elem.text if title_elem is not None and title_elem.text else href
                    bookmark_list.append(href + ' ' + label)
            return bookmark_list
        except Exception:
            return []

    def write_kde_bookmark_list(self,bookmark_list:list):
        """Write file:// entries to ~/.local/share/user-places.xbel preserving non-file:// entries."""
        xbel_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'user-places.xbel')

        # Parse new bookmark urls for quick lookup
        new_urls = set()
        new_entries = {}  # url -> label
        for entry in bookmark_list:
            parts = entry.split(' ', 1)
            url = parts[0]
            label = parts[1] if len(parts) > 1 else url
            new_urls.add(url)
            new_entries[url] = label

        if os.path.isfile(xbel_path):
            ET.register_namespace('bookmark', 'http://www.freedesktop.org/standards/desktop-bookmarks')
            ET.register_namespace('kdeprops', 'http://www.kde.org/standards/kdeprops')
            tree = ET.parse(xbel_path)
            root = tree.getroot()
            # Remove existing file:// bookmarks that are in the new list
            for bookmark in list(root.findall('bookmark')):
                if bookmark.get('href', '') in new_urls:
                    root.remove(bookmark)
        else:
            root = ET.Element('xbel')
            root.set('xmlns:bookmark', 'http://www.freedesktop.org/standards/desktop-bookmarks')
            root.set('xmlns:kdeprops', 'http://www.kde.org/standards/kdeprops')
            root.set('version', '1.0')
            tree = ET.ElementTree(root)

        # Append updated samba bookmarks
        for url, label in new_entries.items():
            bookmark_elem = ET.SubElement(root, 'bookmark')
            bookmark_elem.set('href', url)
            title_elem = ET.SubElement(bookmark_elem, 'title')
            title_elem.text = label

        os.makedirs(os.path.dirname(xbel_path), exist_ok=True)
        tree.write(xbel_path, encoding='unicode', xml_declaration=True)



    def write_rebuild_bash(self,tmp_samba_nix_path:str):

        rebuld_bash_content="""#!/usr/bin/env bash
echo "======================================"
echo "  save samba.nix"
echo "======================================"
echo ""

sudo mv """+tmp_samba_nix_path+""" /etc/nixos/customConfig/samba.nix
        

echo "======================================"
echo "  NIX REBUILD with samba setup"
echo "======================================"
echo ""


echo "nixos-rebuild..."
echo ""

# Detect flake configuration name for --flake flag
FLAKE_ATTR=""
if [ -f /etc/nixos/flake.nix ]; then
    FLAKE_ATTR=$(grep -oP 'nixosConfigurations\\.\\s*"?\\K[^"= ]+' /etc/nixos/flake.nix | head -1)
fi

if [ -n "$FLAKE_ATTR" ]; then
    echo "Configuration flake detectee : $FLAKE_ATTR"
    sudo nixos-rebuild switch --flake "/etc/nixos#$FLAKE_ATTR"
else
    sudo nixos-rebuild switch
fi
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "  REBUILD successfully"
    echo "======================================"
else
    echo ""
    echo "======================================"
    echo "  Error during REBUILD"
    echo "======================================"
fi

echo ""
echo "You can close this terminal window."
"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as tmp:
                tmp.write(rebuld_bash_content)
                self.execute(['chmod','+x',tmp.name])
                return tmp.name