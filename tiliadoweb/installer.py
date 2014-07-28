from gi.repository import Gtk
from tiliadoweb.api import ApiError

class Installer:
    def __init__(self, api, login_page):
        self.api = api
        self.login_page = login_page
        self.login_page.sign_in_button.connect("clicked", self.on_sign_in_clicked)
        self.login_page.quit_button.connect("clicked", self.on_quit_clicked)
    
    def on_quit_clicked(self, *args):
        Gtk.main_quit()
    
    def on_sign_in_clicked(self, *args):
        page = self.login_page
        username = page.username_entry.get_text().strip()
        password = page.password_entry.get_text()
        
        try:
            page.set_error("Signing in ...")
            page.set_widgets_sensitive(False)
            self.api.login(username, password)
            page.set_widgets_sensitive(True)
            page.set_error()
        except ApiError as e:
            page.set_error(str(e))
            page.set_widgets_sensitive(True)
