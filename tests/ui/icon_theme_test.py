"""Run from the development environment with Adwaita and a display available."""
import ast
import gettext
import pathlib
import sys

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

root = pathlib.Path(__file__).resolve().parents[2] / 'src'
sys.path.insert(0, str(root))
gettext.install('nix-samba')
from infrastructure.ui.app_window import AppWindow

Adw.init()
settings = Gtk.Settings.get_default()
theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
# Reproduce a desktop environment without Adwaita on its icon search path.
theme.set_search_path(['/tmp/samba-missing-icon-theme'])
settings.set_property('gtk-icon-theme-name', 'Breeze')
resources = theme.get_resource_path()
app = AppWindow()
app.set_flags(Gio.ApplicationFlags.NON_UNIQUE)
assert app.register(None)
assert theme.get_theme_name() == 'Adwaita'
assert pathlib.Path(theme.get_search_path()[0], 'Adwaita', 'index.theme').is_file()
print('Resource paths:', theme.get_resource_path())
assert set(resources).issubset(theme.get_resource_path())
names = set()
for source in root.rglob('*.py'):
    tree = ast.parse(source.read_text())
    names.update(node.value for node in ast.walk(tree)
                 if isinstance(node, ast.Constant) and isinstance(node.value, str)
                 and node.value.endswith('-symbolic'))
failures = []
for name in sorted(names):
    icon = theme.lookup_icon(name, None, 16, 1, Gtk.TextDirection.LTR,
                             Gtk.IconLookupFlags.FORCE_SYMBOLIC)
    file = icon.get_file()
    if not theme.has_icon(name) or file is None or not file.query_exists(None):
        failures.append(name)
    print(f'{name}: {file.get_uri() if file else "MISSING"}')
assert not failures, failures
print(f'PASS: {len(names)} icons resolved; global Adwaita path active; resource paths preserved')

app.quit()
