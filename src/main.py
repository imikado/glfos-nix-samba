#!/usr/bin/env python3

from infrastructure.ui.app_window import AppWindow

import gettext
import os
import subprocess


def _compile_mo_if_needed(localedir: str, appname: str):
    """Compile .po to .mo if .mo is missing or older than .po."""
    for lang_dir in os.listdir(localedir):
        lc_dir = os.path.join(localedir, lang_dir, 'LC_MESSAGES')
        po_file = os.path.join(lc_dir, appname + '.po')
        mo_file = os.path.join(lc_dir, appname + '.mo')
        if os.path.isfile(po_file):
            if not os.path.isfile(mo_file) or os.path.getmtime(po_file) > os.path.getmtime(mo_file):
                try:
                    subprocess.run(['msgfmt', po_file, '-o', mo_file], check=True, capture_output=True)
                except Exception:
                    pass


def main():
    appname = 'nix-samba'
    # Use absolute path relative to this file, regardless of working directory
    localedir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'infrastructure', 'locales')

    _compile_mo_if_needed(localedir, appname)

    # Detect OS language from environment variables (GNOME/NixOS sets LANG or LANGUAGE)
    lang = 'en'
    for var in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        val = os.environ.get(var, '')
        if val:
            lang = val.split(':')[0].split('_')[0].split('.')[0]
            break
    
    print('language chosen: '+lang)

    translation = gettext.translation(appname, localedir, fallback=True, languages=[lang, 'en'])
    translation.install()


    app = AppWindow()
    app.run(None)


if __name__ == "__main__":
    main()
