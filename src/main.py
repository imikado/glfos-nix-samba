#!/usr/bin/env python3

from infrastructure.ui.app_window import AppWindow

import gettext
import os


def main():
    appname = 'nix-samba'
    # Use absolute path relative to this file, regardless of working directory
    localedir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'infrastructure', 'locales')

    # Detect OS language from environment variables (GNOME/NixOS sets LANG or LANGUAGE)
    lang = 'en'
    for var in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        val = os.environ.get(var, '')
        if val:
            lang = val.split(':')[0].split('_')[0].split('.')[0]
            break

    translation = gettext.translation(appname, localedir, fallback=True, languages=[lang, 'en'])
    translation.install()


    app = AppWindow()
    app.run(None)


if __name__ == "__main__":
    main()
