#!/usr/bin/env python3

from infrastructure.ui.app_window import AppWindow

import gettext
import locale


def main():
    appname = 'nix-samba'
    localedir = './infrastructure/locales'

    # Detect OS language (e.g. 'fr_FR.UTF-8' -> 'fr')
    lang_code, _ = locale.getlocale()
    lang = lang_code.split('_')[0] if lang_code else 'en'

    translation = gettext.translation(appname, localedir, fallback=True, languages=[lang, 'en'])
    translation.install()


    app = AppWindow()
    app.run(None)


if __name__ == "__main__":
    main()
