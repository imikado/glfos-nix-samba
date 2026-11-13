from genericpath import exists
import shlex
import shutil
import subprocess
import tempfile
import os
import datetime
import getpass
import pwd
import xml.etree.ElementTree as ET

from domain.contract.system_api_contract import SystemApiContract


class SystemApi(SystemApiContract):

    def read_file(self, path: str):
        return open(path, 'r').read()

    def write_file(self, path: str, content: str):
        open(path, 'w').write(content)

    def write_file_tmp(self, content: str)->str:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.nix') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        return tmp_path

    def user_exists(self,user_name:str)->bool:
        try:
            pwd.getpwnam(user_name)
            return True
        except KeyError:
            return False

    def get_path_owner(self,path:str)->str:
        """Owner name of path, or the current user if it cannot be found."""
        try:
            return pwd.getpwuid(os.stat(path).st_uid).pw_name
        except (OSError, KeyError):
            return getpass.getuser()

    def _write_secret_tmp(self, content: str)->str:
        """Temporary file readable only by the current user (and root), removed after use."""
        fd, tmp_path = tempfile.mkstemp(prefix='nix-samba-', suffix='.secret')
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(content)
        self._secret_tmp_file_list = getattr(self, '_secret_tmp_file_list', []) + [tmp_path]
        return tmp_path

    def remove_secret_tmp_files(self):
        """Remove the password files left if the rebuild script did not run (pkexec cancelled)."""
        for tmp_path in getattr(self, '_secret_tmp_file_list', []):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        self._secret_tmp_file_list = []

    def execute(self,params:list):
        subprocess.Popen(params)
    
    def file_exists(self,path:str)->bool:
        return exists(path)
    
    def create_dir(self,path:str):
        os.mkdir(path, mode=0o777,)

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
        if 'kde' in xdg or 'plasma' in xdg:
            return 'kde'
        # Fallback: check DESKTOP_SESSION
        session = os.environ.get('DESKTOP_SESSION', '').lower()
        if 'gnome' in session:
            return 'gnome'
        if 'kde' in session or 'plasma' in session:
            return 'kde'
        # KDE-specific env vars
        if os.environ.get('KDE_FULL_SESSION') or os.environ.get('KDE_SESSION_VERSION'):
            return 'kde'
        # Fallback: check KDE/GNOME specific config files
        home = os.path.expanduser('~')
        kde_markers = [
            os.path.join(home, '.local', 'share', 'user-places.xbel'),
            os.path.join(home, '.config', 'plasma-org.kde.plasma.desktop-appletsrc'),
            os.path.join(home, '.config', 'kwinrc'),
        ]
        if any(os.path.isfile(p) for p in kde_markers):
            return 'kde'
        gnome_markers = [
            os.path.join(home, '.config', 'gnome-shell'),
            os.path.join(home, '.local', 'share', 'gnome-shell'),
        ]
        if any(os.path.exists(p) for p in gnome_markers):
            return 'gnome'
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

    def _kde_is_system_item(self, bookmark_elem) -> bool:
        """Return True if this XBEL bookmark has <isSystemItem>true</isSystemItem>."""
        for metadata in bookmark_elem.findall('.//metadata'):
            if metadata.get('owner') == 'http://www.kde.org':
                is_system = metadata.find('isSystemItem')
                if is_system is not None and is_system.text == 'true':
                    return True
        return False

    def get_kde_bookmark_list(self)->list:
        """Read user-added (non-system) file:// bookmarks from ~/.local/share/user-places.xbel."""
        xbel_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'user-places.xbel')
        if not os.path.isfile(xbel_path):
            return []
        try:
            tree = ET.parse(xbel_path)
            root = tree.getroot()
            bookmark_list = []
            for bookmark in root.findall('bookmark'):
                href = bookmark.get('href', '')
                if href.startswith('file://') and not self._kde_is_system_item(bookmark):
                    title_elem = bookmark.find('title')
                    label = title_elem.text if title_elem is not None and title_elem.text else href
                    bookmark_list.append(href + ' ' + label)
            return bookmark_list
        except Exception:
            return []

    def write_kde_bookmark_list(self,bookmark_list:list):
        """Replace non-system bookmarks in user-places.xbel with bookmark_list. System items are preserved."""
        xbel_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'user-places.xbel')

        # Register namespaces to avoid ns0: rewriting by ElementTree
        ET.register_namespace('bookmark', 'http://www.freedesktop.org/standards/desktop-bookmarks')
        ET.register_namespace('kdepriv', 'http://www.kde.org/kdepriv')
        ET.register_namespace('mime', 'http://www.freedesktop.org/standards/shared-mime-info')

        if os.path.isfile(xbel_path):
            tree = ET.parse(xbel_path)
            root = tree.getroot()
            # Remove all non-system bookmarks (we will re-add the merged list)
            for bookmark in list(root.findall('bookmark')):
                if not self._kde_is_system_item(bookmark):
                    root.remove(bookmark)
        else:
            root = ET.Element('xbel')
            root.set('xmlns:bookmark', 'http://www.freedesktop.org/standards/desktop-bookmarks')
            root.set('xmlns:kdepriv', 'http://www.kde.org/kdepriv')
            root.set('version', '1.0')
            tree = ET.ElementTree(root)

        # Append bookmarks with folder-network icon
        for entry in bookmark_list:
            parts = entry.split(' ', 1)
            url = parts[0]
            label = parts[1] if len(parts) > 1 else url
            bookmark_elem = ET.SubElement(root, 'bookmark')
            bookmark_elem.set('href', url)
            title_elem = ET.SubElement(bookmark_elem, 'title')
            title_elem.text = label
            info_elem = ET.SubElement(bookmark_elem, 'info')
            fd_meta = ET.SubElement(info_elem, 'metadata')
            fd_meta.set('owner', 'http://freedesktop.org')
            icon_elem = ET.SubElement(fd_meta, '{http://www.freedesktop.org/standards/desktop-bookmarks}icon')
            icon_elem.set('name', 'folder-network')

        os.makedirs(os.path.dirname(xbel_path), exist_ok=True)
        tree.write(xbel_path, encoding='unicode', xml_declaration=True)



    def get_desktop_dir(self)->str:
        """Return the user's Desktop directory, honoring xdg-user-dirs if available."""
        try:
            result = subprocess.run(['xdg-user-dir', 'DESKTOP'], capture_output=True, text=True, check=True)
            desktop_dir = result.stdout.strip()
            if desktop_dir:
                return desktop_dir
        except Exception:
            pass
        return os.path.join(os.path.expanduser('~'), 'Desktop')

    def _desktop_shortcut_path(self,mount_path:str)->str:
        filename = mount_path.strip('/').replace('/', '-') + '.desktop'
        return os.path.join(self.get_desktop_dir(), filename)

    def has_desktop_shortcut(self,mount_path:str)->bool:
        return os.path.isfile(self._desktop_shortcut_path(mount_path))

    def create_desktop_shortcut(self,mount_path:str,label:str):
        desktop_dir = self.get_desktop_dir()
        os.makedirs(desktop_dir, exist_ok=True)

        shortcut_path = self._desktop_shortcut_path(mount_path)
        content = (
            '[Desktop Entry]\n'
            'Version=1.0\n'
            'Type=Link\n'
            f'Name={label}\n'
            'Icon=folder-remote\n'
            f'URL=file://{mount_path}\n'
        )
        with open(shortcut_path, 'w') as f:
            f.write(content)
        os.chmod(shortcut_path, 0o755)
        # Mark as trusted so Nautilus/Files runs it without a warning banner.
        subprocess.run(['gio', 'set', shortcut_path, 'metadata::trusted', 'true'], capture_output=True)

    def remove_desktop_shortcut(self,mount_path:str):
        shortcut_path = self._desktop_shortcut_path(mount_path)
        if os.path.isfile(shortcut_path):
            os.remove(shortcut_path)

    def write_rebuild_bash(self,tmp_samba_nix_path:str,tmp_samba_server_nix_path:str=None,file_write_list:list=None,samba_account_actions:dict=None):
        """Write the rebuild script, meant to run as root through pkexec (see get_rebuild_command).

        file_write_list: extra privileged writes applied first, as dicts {path, content, backup}
        (e.g. fixes of /etc/nixos/customConfig/default.nix).
        samba_account_actions: {remove: [user], passwords: [(user, password)]} for the
        share-only accounts (see LocalShareDomain.get_dedicated_account_actions).
        """

        samba_account_actions=samba_account_actions or {}

        save_steps=self._get_file_write_steps(file_write_list or [])
        save_steps+=self._get_samba_account_remove_steps(samba_account_actions.get('remove',[]))
        password_steps=self._get_samba_account_password_steps(samba_account_actions.get('passwords',[]))

        save_steps+="""echo "======================================"
echo "  save samba.nix"
echo "======================================"
echo ""

install -m 644 -o root -g root '"""+tmp_samba_nix_path+"""' /etc/nixos/customConfig/samba.nix || exit 1
rm -f '"""+tmp_samba_nix_path+"""'
"""

        if tmp_samba_server_nix_path:
            save_steps+="""
echo "======================================"
echo "  save samba-server.nix"
echo "======================================"
echo ""

install -m 644 -o root -g root '"""+tmp_samba_server_nix_path+"""' /etc/nixos/customConfig/samba-server.nix || exit 1
rm -f '"""+tmp_samba_server_nix_path+"""'
"""

        rebuld_bash_content="""#!/usr/bin/env bash
# pkexec runs with a minimal environment: restore the NixOS one (PATH, NIX_PATH...)
if [ -f /etc/set-environment ]; then
    . /etc/set-environment
fi
export PATH="/run/wrappers/bin:/run/current-system/sw/bin:$PATH"

"""+save_steps+"""

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
    nixos-rebuild switch --flake "/etc/nixos#$FLAKE_ATTR"
else
    nixos-rebuild switch
fi
EXIT_CODE=$?
"""+password_steps+"""
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

exit $EXIT_CODE
"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as tmp:
            tmp.write(rebuld_bash_content)
        os.chmod(tmp.name, 0o700)
        return tmp.name

    def _get_file_write_steps(self,file_write_list:list)->str:
        backup_suffix='.nix-samba.back'+datetime.datetime.now().strftime('%Y%m%d')
        steps=''
        for file_write in file_write_list:
            path=file_write['path']
            tmp_path=self.write_file_tmp(file_write['content'])
            steps+='echo "======================================"\n'
            steps+='echo '+shlex.quote('  update '+path)+'\n'
            steps+='echo "======================================"\n'
            steps+='echo ""\n\n'
            if file_write.get('backup'):
                steps+='if [ -f '+shlex.quote(path)+' ]; then cp -p '+shlex.quote(path)+' '+shlex.quote(path+backup_suffix)+' || exit 1; fi\n'
            steps+='install -m 644 -o root -g root '+shlex.quote(tmp_path)+' '+shlex.quote(path)+' || exit 1\n'
            steps+='rm -f '+shlex.quote(tmp_path)+'\n\n'
        return steps

    def _get_samba_account_remove_steps(self,user_list:list)->str:
        if not user_list:
            return ''
        steps='echo "======================================"\n'
        steps+='echo "  remove unused Samba share accounts"\n'
        steps+='echo "======================================"\n'
        steps+='echo ""\n\n'
        for user in user_list:
            # The Unix account itself is removed by nixos-rebuild (no longer declared)
            steps+='pdbedit -x -u '+shlex.quote(user)+' >/dev/null 2>&1 && echo '+shlex.quote('  '+user+' removed')+'\n'
        return steps+'\n'

    def _get_samba_account_password_steps(self,password_list:list)->str:
        if not password_list:
            return ''
        steps='\necho ""\n'
        steps+='echo "======================================"\n'
        steps+='echo "  set Samba share account passwords"\n'
        steps+='echo "======================================"\n'
        steps+='echo ""\n\n'
        for user,password in password_list:
            # smbpasswd -s reads the new password twice on stdin; never put it on the command line
            password_path=self._write_secret_tmp(password+'\n'+password+'\n')
            quoted_user=shlex.quote(user)
            quoted_path=shlex.quote(password_path)
            steps+='if id -u '+quoted_user+' >/dev/null 2>&1; then\n'
            steps+='    if smbpasswd -s -a '+quoted_user+' < '+quoted_path+' >/dev/null; then\n'
            steps+='        echo '+shlex.quote('  password set for '+user)+'\n'
            steps+='    else\n'
            steps+='        echo '+shlex.quote('  ERROR: unable to set the password of '+user)+'\n'
            steps+='        EXIT_CODE=1\n'
            steps+='    fi\n'
            steps+='else\n'
            steps+='    echo '+shlex.quote('  ERROR: account '+user+' was not created')+'\n'
            steps+='    EXIT_CODE=1\n'
            steps+='fi\n'
            steps+='rm -f '+quoted_path+'\n'
        return steps

    def get_rebuild_command(self,rebuild_bash_path:str)->list:
        """Command running the rebuild script as root, authenticated by polkit (graphical prompt)."""
        bash_path = shutil.which('bash') or '/run/current-system/sw/bin/bash'
        return ['pkexec', bash_path, rebuild_bash_path]
