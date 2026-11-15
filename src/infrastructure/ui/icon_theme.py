"""Resolve application icons from Adwaita, including nonstandard install prefixes."""
import os

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gdk, GLib, Gtk


def configure_icon_theme():
    theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
    # A packager can select the exact theme dependency independently of the
    # desktop's paths. Otherwise discover Adwaita through XDG_DATA_DIRS.
    candidates = [os.environ.get('GLFOS_SAMBA_ICON_DIR')]
    candidates.extend(os.path.join(path, 'icons') for path in GLib.get_system_data_dirs())
    adwaita_paths = [path for path in candidates
                     if path and os.path.isfile(os.path.join(path, 'Adwaita', 'index.theme'))]
    # Keep GTK/Libadwaita resource icons and other theme paths available.
    paths = list(dict.fromkeys(adwaita_paths + theme.get_search_path()))
    theme.set_search_path(paths)
    Gtk.Settings.get_default().set_property('gtk-icon-theme-name', 'Adwaita')
