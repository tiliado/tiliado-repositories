import os
import json
from gi.repository import Gtk
from tiliadoweb.api import ApiError

CONFIG_FILENAME = "config.json"

from collections import namedtuple

Release = namedtuple("Release", "name label components")
Component = namedtuple("Component", "name label desc groups")

class Installer:
    def __init__(self, api, config_dir, stack, login_page, repositories_page, components_page):
        self.api = api
        self.stack = stack
        self.config_dir = config_dir
        
        self.login_page = login_page
        stack.add(login_page)
        self.login_page.sign_in_button.connect("clicked", self.on_sign_in_clicked)
        self.login_page.quit_button.connect("clicked", self.on_quit_clicked)
        
        self.repositories_page = repositories_page
        stack.add(repositories_page)
        repositories_page.back_button.connect("clicked", self.on_repositories_back_clicked)
        repositories_page.ok_button.connect("clicked", self.on_repositories_next_clicked)
        
        self.components_page = components_page
        stack.add(components_page)
        components_page.back_button.connect("clicked", self.on_components_back_clicked)
        components_page.ok_button.connect("clicked", self.on_quit_clicked)
        
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
    
    def on_repositories_back_clicked(self, *args):
        self.switch_to_login()
    
    def on_repositories_next_clicked(self, *args):
        self.switch_to_components()
    
    def on_components_back_clicked(self, *args):
        self.stack.set_visible_child(self.repositories_page)
    
    def switch_to_login(self):
        self.stack.set_visible_child(self.login_page)
    
    def switch_to_repositories(self):
        self.repositories_page.set_repositories([repo for repo in self.api.repositories if repo["active"]])
        self.stack.set_visible_child(self.repositories_page)
    
    def switch_to_components(self):
        components = (self.api.component(pk) for pk in self.repositories_page.repo.get("component_set", ()))
        groups = {i["id"]: i for i in self.api.groups}
        releases = {
            i["id"]:
            Release(i["name"], "{} {}".format(self.api.distribution(i["distribution"])["label"], i["label"]), {})
            for i in self.api.repo_releases
        }
        
        for c in components:
            if c["active"]:
                for access in c["access_set"]:
                    access_groups = {g: groups[g]["name"] for g in access["groups"]}
                    component = Component(c["name"], c["label"], c["desc"], access_groups)
                    releases[access["release"]].components[c["name"]] = component
        
        options = {r.name: r for r in releases.values() if r.components}
        del groups, components, releases
        
        self.components_page.set_data(self.api.me["groups"], options)
        self.stack.set_visible_child(self.components_page)
