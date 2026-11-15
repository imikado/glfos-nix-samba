import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk


ACCESS_MODE_GUEST = 0
ACCESS_MODE_USERS = 1
ACCESS_MODE_DEDICATED = 2


class AccessModeRow(Adw.ComboRow):
    """Short labels in the combo, full description of the selected mode as a (wrapping) subtitle.

    Long labels were ellipsized by Adw.ComboRow without any way to read them.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title(_('Access mode'))
        self.set_subtitle_lines(0)
        self.set_model(Gtk.StringList.new([
            _('Guest'),
            _('Specific users'),
            _('Dedicated account'),
        ]))
        self._description_list = [
            _('Guest access (no login required)'),
            _('Restricted to specific users'),
            _('Dedicated account (this share only)'),
        ]
        self.connect('notify::selected', self._on_selected_changed)
        self._on_selected_changed(self, None)

    def _on_selected_changed(self, _row, _param):
        selected = self.get_selected()
        if 0 <= selected < len(self._description_list):
            self.set_subtitle(self._description_list[selected])
            self.set_tooltip_text(self._description_list[selected])
