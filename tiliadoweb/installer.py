from gi.repository import Gtk
from tiliadoweb.api import ApiError

class Installer:
    def __init__(self, api, stack, login_page, repositories_page):
        self.api = api
        self.stack = stack
        
        self.login_page = login_page
        stack.add(login_page)
        self.login_page.sign_in_button.connect("clicked", self.on_sign_in_clicked)
        self.login_page.quit_button.connect("clicked", self.on_quit_clicked)
        
        self.repositories_page = repositories_page
        stack.add(repositories_page)
        repositories_page.back_button.connect("clicked", self.on_quit_clicked)
        repositories_page.ok_button.connect("clicked", self.on_quit_clicked)
    
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
            self.switch_to_repositories()
        except ApiError as e:
            page.set_error(str(e))
            page.set_widgets_sensitive(True)
    
    def switch_to_repositories(self):
        self.repositories_page.set_repositories([repo for repo in self.api.repositories if repo["active"]])
        self.stack.set_visible_child(self.repositories_page)
