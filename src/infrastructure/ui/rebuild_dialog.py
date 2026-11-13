import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib, Gtk


# pkexec exit codes: authentication dialog dismissed / not authorized
PKEXEC_CANCELLED_CODES = (126, 127)


class RebuildDialog(Adw.Dialog):
    """Run the NixOS rebuild command and show its live log with a spinner.

    The dialog cannot be closed while the command is running. `on_finished(success, cancelled)`
    is called once the command exits.
    """

    def __init__(self, command: list, on_finished=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._command = command
        self._on_finished = on_finished
        self._running = False
        self._script_started = False

        self.set_title(_('NixOS rebuild'))
        self.set_content_width(720)
        self.set_content_height(480)
        self.set_can_close(False)

        toolbar_view = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()
        toolbar_view.add_top_bar(header_bar)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        # Status line: spinner while running, then a result icon
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._spinner = Gtk.Spinner()
        status_box.append(self._spinner)
        self._status_icon = Gtk.Image()
        self._status_icon.set_visible(False)
        status_box.append(self._status_icon)
        self._status_label = Gtk.Label(xalign=0)
        self._status_label.set_hexpand(True)
        self._status_label.set_wrap(True)
        status_box.append(self._status_label)
        box.append(status_box)

        self._progress_bar = Gtk.ProgressBar()
        box.append(self._progress_bar)

        # Log view
        self._buffer = Gtk.TextBuffer()
        self._end_mark = self._buffer.create_mark(None, self._buffer.get_end_iter(), False)
        self._text_view = Gtk.TextView(buffer=self._buffer)
        self._text_view.set_editable(False)
        self._text_view.set_cursor_visible(False)
        self._text_view.set_monospace(True)
        self._text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._text_view.set_top_margin(6)
        self._text_view.set_bottom_margin(6)
        self._text_view.set_left_margin(6)
        self._text_view.set_right_margin(6)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add_css_class('card')
        scrolled.set_child(self._text_view)
        box.append(scrolled)

        self._close_button = Gtk.Button(label=_('Close'))
        self._close_button.set_halign(Gtk.Align.END)
        self._close_button.add_css_class('pill')
        self._close_button.set_sensitive(False)
        self._close_button.connect('clicked', lambda _button: self.force_close())
        box.append(self._close_button)

        toolbar_view.set_content(box)
        self.set_child(toolbar_view)

    def is_running(self) -> bool:
        return self._running

    def start(self):
        self._set_running(True)
        self._status_label.set_label(_('Waiting for authentication…'))

        try:
            self._process = Gio.Subprocess.new(
                self._command,
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE,
            )
        except GLib.Error as e:
            self._append_line(str(e.message))
            self._finish(False, False, _('Unable to start the rebuild (is polkit/pkexec available?)'))
            return

        self._stream = Gio.DataInputStream.new(self._process.get_stdout_pipe())
        self._stream.read_line_async(GLib.PRIORITY_DEFAULT, None, self._on_line_read)
        self._process.wait_async(None, self._on_process_exited)

    def _set_running(self, running: bool):
        self._running = running
        self._spinner.set_visible(running)
        self._spinner.set_spinning(running)
        if running:
            self._pulse_source = GLib.timeout_add(120, self._on_pulse)
        elif getattr(self, '_pulse_source', None):
            GLib.source_remove(self._pulse_source)
            self._pulse_source = None
        self._close_button.set_sensitive(not running)
        self.set_can_close(not running)

    def _on_pulse(self):
        self._progress_bar.pulse()
        return GLib.SOURCE_CONTINUE

    def _on_line_read(self, stream, result):
        try:
            raw_line, _length = stream.read_line_finish(result)
        except GLib.Error:
            raw_line = None
        if raw_line is None:
            return  # end of output
        line = raw_line.decode('utf-8', errors='replace')
        if line.startswith('====='):
            self._script_started = True  # authentication passed, the script is running as root
        if self._status_label.get_label() == _('Waiting for authentication…'):
            self._status_label.set_label(_('Rebuilding the system, this may take a few minutes…'))
        self._append_line(line.split('\r')[-1])
        stream.read_line_async(GLib.PRIORITY_DEFAULT, None, self._on_line_read)

    def _append_line(self, line: str):
        self._buffer.insert(self._buffer.get_end_iter(), line + '\n')
        self._buffer.move_mark(self._end_mark, self._buffer.get_end_iter())
        self._text_view.scroll_mark_onscreen(self._end_mark)

    def _on_process_exited(self, process, result):
        try:
            process.wait_finish(result)
        except GLib.Error:
            pass
        exit_status = process.get_exit_status() if process.get_if_exited() else -1

        if exit_status == 0:
            self._finish(True, False, _('System rebuilt successfully'))
        elif exit_status in PKEXEC_CANCELLED_CODES and not self._script_started:
            self._finish(False, True, _('Authentication cancelled: nothing was saved'))
        else:
            self._finish(False, False, _('Error during rebuild, see the log above'))

    def _finish(self, success: bool, cancelled: bool, message: str):
        self._set_running(False)
        self._progress_bar.set_fraction(1.0 if success else 0.0)
        self._status_icon.set_from_icon_name(
            'emblem-ok-symbolic' if success else 'dialog-warning-symbolic' if cancelled else 'dialog-error-symbolic')
        self._status_icon.remove_css_class('success')
        self._status_icon.remove_css_class('error')
        self._status_icon.add_css_class('success' if success else 'error')
        self._status_icon.set_visible(True)
        self._status_label.set_label(message)
        self._close_button.grab_focus()

        if self._on_finished:
            self._on_finished(success, cancelled)
