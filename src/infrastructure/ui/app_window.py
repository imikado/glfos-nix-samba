from domain.credentials_file_domain import CredentialsFileDomain
from domain.remote_domain import RemoteDomain
import gi
from infrastructure.api.samba_file_api import SambaFileApi
from infrastructure.api.system_api import SystemApi
from infrastructure.ui.create_creds_file_page import CreateCredsFilePage

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from infrastructure.ui.remote_list_page import RemoteListPage
from infrastructure.ui.remote_add_page import RemoteAddPage


class MainWindow(Adw.ApplicationWindow):

    _remote_domain:RemoteDomain=None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._remote_domain=RemoteDomain(SystemApi(),SambaFileApi())

        self.set_title("Nix Samba")
        self.set_default_size(800, 600)

        # Create toast overlay for notifications
        self._toast_overlay = Adw.ToastOverlay()
        self.set_content(self._toast_overlay)

        # Create navigation view for in-window navigation
        self.navigation_view = Adw.NavigationView()
        self._toast_overlay.set_child(self.navigation_view)

        # Create and push the home page
        home_page = self._create_home_page()
        self.navigation_view.push(home_page)

        self.navigation_view.connect('popped', self._on_page_popped)

        # Handle close request to prompt for unsaved changes
        self.connect('close-request', self._on_close_request)


    def _create_home_page(self):
        page = Adw.NavigationPage.new(self._create_home_content(), _('Nix Samba'))
        return page

    def _create_home_content(self):
        # Create toolbar view with header bar
        toolbar_view = Adw.ToolbarView()
        header_bar = Adw.HeaderBar()

        # Save button in header bar
        save_button = Gtk.Button()
        save_button.set_icon_name('media-floppy-symbolic')
        save_button.set_label(_('Save on disk'))
        save_button.set_tooltip_text(_('Save on disk'))
        save_button.connect('clicked', self.on_save_clicked)
        save_button.add_css_class('destructive-action')
        save_button.set_sensitive(False)

        self.save_button=save_button

        header_bar.pack_end(save_button)

        toolbar_view.add_top_bar(header_bar)

        # Create preferences page
        pref_page_remote = Adw.PreferencesPage()
        pref_page_remote.set_title(_('Remote share'))

        # First group
        pref_group_remote = Adw.PreferencesGroup()
        pref_group_remote.set_title(_('Remote share'))
        pref_group_remote.set_description(_('Mange your remote samba shares'))

        # List remote shares button
        button_remote_list = Adw.ButtonRow()
        button_remote_list.set_title(_('List remote shares'))
        button_remote_list.set_start_icon_name('view-list-symbolic')
        button_remote_list.connect('activated', self.on_list_remote_clicked)
        pref_group_remote.add(button_remote_list)

        # Add remote share button
        button_remote_add = Adw.ButtonRow()
        button_remote_add.set_title(_('Add remote share'))
        button_remote_add.set_start_icon_name('list-add-symbolic')
        button_remote_add.connect('activated', self.on_add_remote_clicked)
        pref_group_remote.add(button_remote_add)

        # Add create credentials button
        button_create_creds_file = Adw.ButtonRow()
        button_create_creds_file.set_title(_('Create credentials file'))
        button_create_creds_file.set_start_icon_name('document-save-symbolic')
        button_create_creds_file.connect('activated', self.on_create_creds_file)
        pref_group_remote.add(button_create_creds_file)


        pref_page_remote.add(pref_group_remote)
        toolbar_view.set_content(pref_page_remote)



        return toolbar_view
    
    def _on_page_popped(self, _navigation_view, _page):
        self.save_button.set_sensitive(self._remote_domain.need_to_save())

    def _on_close_request(self, _window):
        if self._remote_domain.need_to_save():
            dialog = Adw.AlertDialog()
            dialog.set_heading(_('Unsaved Changes'))
            dialog.set_body(_('You have modifications not saved. Are you sure you want to quit without saving?'))
            dialog.add_response('cancel', _('Cancel'))
            dialog.add_response('quit', _('Quit without saving'))
            dialog.set_response_appearance('quit', Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response('cancel')
            dialog.set_close_response('cancel')
            dialog.connect('response', self._on_close_dialog_response)
            dialog.present(self)
            return True  # Prevent window from closing
        return False  # Allow window to close

    def _on_close_dialog_response(self, dialog, response):
        if response == 'quit':
            self.destroy()

    def on_list_remote_clicked(self, _button):
        page = RemoteListPage(self._remote_domain,self.navigation_view,self.show_notification,self.on_save_clicked)
        self.navigation_view.push(page)

    def on_add_remote_clicked(self, _button):
        page = RemoteAddPage(self._remote_domain,self.navigation_view,self.show_notification)
        self.navigation_view.push(page)

    def on_create_creds_file(self,_button):

        credentials_file_domain=CredentialsFileDomain(SystemApi())
        page= CreateCredsFilePage(credentials_file_domain,self.navigation_view,self.show_notification)
        self.navigation_view.push(page)


    def on_save_clicked(self, _button):
        # Show password dialog
        dialog = Adw.AlertDialog()
        dialog.set_heading(_('Authentication Required'))
        dialog.set_body(_('Enter your password to save changes to system configuration.'))

        password_entry = Gtk.PasswordEntry()
        password_entry.set_show_peek_icon(True)
        password_entry.set_hexpand(True)
        dialog.set_extra_child(password_entry)

        dialog.add_response('cancel', _('Cancel'))
        dialog.add_response('save', _('Save'))
        dialog.set_response_appearance('save', Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response('save')
        dialog.set_close_response('cancel')

        self._password_entry = password_entry
        dialog.connect('response', self._on_save_password_response)
        dialog.present(self)

    def _on_save_password_response(self, dialog, response):
        if response != 'save':
            return

        password = self._password_entry.get_text()

        try:
            self._remote_domain.save(password)

            system_api=SystemApi()

            rebuild_bash_path=system_api.write_rebuild_bash(password)

            print(rebuild_bash_path+' created')

            # Open terminal to run nixos-rebuild switch
            import subprocess
            import shutil
            cmd = rebuild_bash_path+'; echo "Press Enter to close..."; read'

            # Try different terminal emulators (including NixOS common ones)
            if shutil.which('kgx'):  # GNOME Console
                subprocess.Popen(['kgx', '--', 'bash', '-c', cmd])
            elif shutil.which('gnome-terminal'):
                subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', cmd])
            elif shutil.which('konsole'):
                subprocess.Popen(['konsole', '-e', 'bash', '-c', cmd])
            elif shutil.which('foot'):  # Common on NixOS/Sway
                subprocess.Popen(['foot', 'bash', '-c', cmd])
            elif shutil.which('alacritty'):
                subprocess.Popen(['alacritty', '-e', 'bash', '-c', cmd])
            elif shutil.which('kitty'):
                subprocess.Popen(['kitty', 'bash', '-c', cmd])
            elif shutil.which('xfce4-terminal'):
                subprocess.Popen(['xfce4-terminal', '-e', f'bash -c "{cmd}"'])
            elif shutil.which('tilix'):
                subprocess.Popen(['tilix', '-e', f'bash -c "{cmd}"'])
            elif shutil.which('xterm'):
                subprocess.Popen(['xterm', '-e', 'bash', '-c', cmd])
            else:
                # Fallback: run in background without terminal
                subprocess.Popen(['bash', '-c', rebuild_bash_path])

            self.save_button.set_sensitive(False)

            self.show_notification(_('Configuration saved - rebuilding in terminal'))


        except PermissionError as e:
            error_dialog = Adw.AlertDialog()
            error_dialog.set_heading(_('Error'))
            error_dialog.set_body(str(e))
            error_dialog.add_response('ok', _('OK'))
            error_dialog.present(self)

    def show_notification(self,text:str):
        toast = Adw.Toast.new(text)
        toast.set_timeout(3)
        self._toast_overlay.add_toast(toast)


class AppWindow(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.dupot.glfosnixsamba")

    def do_activate(self):
        win = MainWindow(application=self)
        win.present()
