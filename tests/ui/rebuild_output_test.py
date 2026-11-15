"""Run inside the package's nix-shell with a display (Xvfb is sufficient).

Usage: python tests/ui/rebuild_output_test.py
Run from the repository root with GTK4/Libadwaita and a display available.
Only simulated commands run; no system configuration is changed.
"""
import gettext
from pathlib import Path
import sys
import time

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, GLib

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
gettext.install('nix-samba')
from infrastructure.ui.rebuild_dialog import RebuildDialog

Adw.init()
window = Adw.Window()
window.set_default_size(800, 600)
window.present()
context = GLib.MainContext.default()


def pump(duration):
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        context.iteration(False)
        time.sleep(0.001)


cases = [
    (b'', 0),
    (b'Finished at 19:11:17 after 4s\n', 0),
    (b'first\n\nlast', 0),
    (b'\x1b[32mOK\x1b[0m\ninvalid: \xff\n', 0),
    (b'log line\n' * 2000, 0),
    (b'failed\n', 1),
    (b'locked\n', 75),
    (b'', 126),
]
try:
    for payload, code in cases:
        finished = []
        command = [sys.executable, '-c',
                   f'import sys; sys.stdout.buffer.write({payload!r}); sys.exit({code})']
        dialog = RebuildDialog(command, lambda *result: finished.append(result))
        dialog.present(window)
        dialog.start()
        deadline = time.monotonic() + 10
        while dialog.is_running() and time.monotonic() < deadline:
            pump(0.01)
        assert not dialog.is_running(), ('completion timeout', code)
        pump(0.3)  # Detect EOF callbacks continuing to append empty lines.
        text = dialog._buffer.get_text(*dialog._buffer.get_bounds(), True)
        expected = payload.decode('utf-8', errors='replace').replace('\x1b[32m', '').replace('\x1b[0m', '')
        if expected and not expected.endswith('\n'):
            expected += '\n'
        assert text == expected, (code, len(text), len(expected))
        assert finished == [(code == 0, code == 126)], finished
        assert dialog._close_button.get_sensitive()
        assert dialog._reboot_button.get_visible() == (code == 0)
        count = dialog._buffer.get_line_count()
        pump(0.2)
        assert dialog._buffer.get_line_count() == count, 'Log keeps growing after EOF'
        dialog.force_close()
        print(f'PASS: {len(payload)} bytes, exit {code}, log stable and dialog closable', flush=True)
finally:
    window.destroy()
