import os
import json
from gi.repository import Gtk
from tiliadoweb.api import ApiError

CONFIG_FILENAME = "config.json"
class Installer:
    def __init__(self, api, config_dir, stack, login_page, repositories_page):
        self.api = api
        self.stack = stack
        self.config_dir = config_dir
        
        self.login_page = login_page
        stack.add(login_page)
        self.login_page.sign_in_button.connect("clicked", self.on_sign_in_clicked)
        self.login_page.quit_button.connect("clicked", self.on_quit_clicked)
        
        self.repositories_page = repositories_page
        stack.add(repositories_page)
        repositories_page.back_button.connect("clicked", self.on_quit_clicked)
        repositories_page.ok_button.connect("clicked", self.on_quit_clicked)
        
        try:
            with open(os.path.join(config_dir, CONFIG_FILENAME), "rt") as f:
                self.config = json.load(f)
        except OSError as e:
            self.config = {}
        except ValueError as e:
            print(e)
            self.config = {}
        
        api.username = self.config.get("username")
        api.token = self.config.get("token")
        if api.username and api.token:
            self.switch_to_repositories()
    
    def save_config(self):
        with open(os.path.join(self, self.config_dir, CONFIG_FILENAME), "wt") as f:
            json.dump(self.config, f)
    
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
            self.config["username"] = self.api.username
            self.config["token"] = self.api.token
            self.save_config()
            self.switch_to_repositories()
        except ApiError as e:
            page.set_error(str(e))
            page.set_widgets_sensitive(True)
    
    def switch_to_repositories(self):
        self.repositories_page.set_repositories([repo for repo in self.api.repositories if repo["active"]])
        self.stack.set_visible_child(self.repositories_page)
