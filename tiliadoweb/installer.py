import os
import sys
import json
from urllib.error import HTTPError
from queue import Queue, Empty
from gi.repository import Gtk, GLib
from tiliadoweb.config import PROTOCOL, HOST, VERIFY_SSL
from tiliadoweb.api import ApiError
from tiliadoweb.worker import run_command

CONFIG_FILENAME = "config2.json"

from collections import namedtuple

Release = namedtuple("Release", "name distribution label components")
Component = namedtuple("Component", "name label desc groups")

class Installer:
    def __init__(self, api, installer, config_dir, stack, login_page, repositories_page, components_page,
            products_page, summary_page, progress_page):
        self.api = api
        self.installer = installer
        self.stack = stack
        self.config_dir = config_dir
        self.authorized = False
        
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
        components_page.ok_button.connect("clicked", self.on_components_next_clicked)
       
        self.products_page = products_page
        stack.add(products_page)
        products_page.back_button.connect("clicked", self.on_products_back_clicked)
        products_page.ok_button.connect("clicked", self.on_products_next_clicked)
        
        self.summary_page = summary_page
        stack.add(summary_page)
        summary_page.back_button.connect("clicked", self.on_summary_back_clicked)
        summary_page.ok_button.connect("clicked", self.on_summary_next_clicked)
        
        self.progress_page = progress_page
        stack.add(progress_page)
        progress_page.back_button.connect("clicked", self.on_progress_back_clicked)
        progress_page.quit_button.connect("clicked", self.on_quit_clicked)
        
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
            try:
                self.switch_to_repositories()
            except HTTPError:
                self.switch_to_login()
    
    def save_config(self):
        with open(os.path.join(self, self.config_dir, CONFIG_FILENAME), "wt") as f:
            json.dump(self.config, f)
    
    def on_quit_clicked(self, *args):
        Gtk.main_quit()
    
    def on_sign_in_clicked(self, *args):
        page = self.login_page
        if not page.option_account.get_active():
            self.authorized = False
            self.switch_to_repositories()
        else:
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
                self.authorized = True
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
    
    def on_components_next_clicked(self, *args):
        self.switch_to_products()
    
    def on_products_back_clicked(self, *args):
        self.stack.set_visible_child(self.components_page)
    
    def on_products_next_clicked(self, *args):
        self.switch_to_summary()
        
    def on_summary_back_clicked(self, *args):
        if self.products:
            self.stack.set_visible_child(self.products_page)
        else:
            self.stack.set_visible_child(self.components_page)
    
    def on_summary_next_clicked(self, *args):
        self.switch_to_progress()
    
    def on_progress_back_clicked(self, *args):
        self.stack.set_visible_child(self.summary_page)
    
    def switch_to_login(self):
        self.stack.set_visible_child(self.login_page)
    
    def switch_to_repositories(self):
        self.repositories_page.set_repositories([repo for repo in self.api.repositories if repo["active"]])
        self.stack.set_visible_child(self.repositories_page)
    
    def switch_to_components(self):
        components = (self.api.component(pk) for pk in self.repositories_page.repo.get("component_set", ()))
        self.components_id = {}
        groups = {i["id"]: i for i in self.api.groups}
        releases = {
            i["id"]:
            Release(i["name"], self.api.distribution(i["distribution"])["name"], "{} {}".format(self.api.distribution(i["distribution"])["label"], i["label"]), {})
            for i in self.api.repo_releases
        }
        
        self.releases_id = {r.name: r_id for (r_id, r) in releases.items()}
        self.releases_dists = {r.name: r.distribution for  r in releases.values()}
        
        for c in components:
            if c["active"]:
                self.components_id[c["name"]] = c["id"]
                for access in c["access_set"]:
                    access_groups = {g: groups[g]["name"] for g in access["groups"]}
                    component = Component(c["name"], c["label"], c["desc"], access_groups)
                    releases[access["release"]].components[c["name"]] = component
        
        options = {r.name: r for r in releases.values() if r.components}
        
        del groups, components, releases
        
        self.components_page.set_data(self.api.me["groups"], options)
        self.stack.set_visible_child(self.components_page)
    
    def switch_to_products(self):
        available_products = []
        repo_id = self.repositories_page.repo["id"]
        release_id = self.releases_id[self.components_page.dist]
        
        for product in self.api.list_products(repository=repo_id):
            for pkg_name in product["packages"].split(","):
                for component in self.components_page.enabled_components:
                    component_id = self.components_id[component]
                    packages = self.api.list_packages(repository=repo_id, component=component_id, release=release_id, name=pkg_name)
                    if packages:
                        # Success: Package found, no need to examine other components
                        break
                else:
                    # Failure: Package not found in any component, no need to examine other packages
                    break
            else:
                # Success: All packages checks were successful
                available_products.append(product)
        
        self.products = {p["id"]: p for p in available_products}
        self.products_page.set_data(available_products)
        if available_products:
            self.stack.set_visible_child(self.products_page)
        else:
            self.switch_to_summary()
        
    def switch_to_summary(self):
        products = [self.products[p]["name"] for p in self.products_page.selected_products]
        self.summary_page.set_data(self.repositories_page.repo["label"], products)
        self.stack.set_visible_child(self.summary_page)
    
    def switch_to_progress(self):
        self.progress_page.clear()
        self.stack.set_visible_child(self.progress_page)
        self._queue = Queue()
        GLib.idle_add(self._process_queue)
        self.progress_page.set_sensitive(False)
        
        release = self.components_page.dist
        distribution = self.releases_dists[release]
        variants = ",".join(self.components_page.enabled_components)
        project = self.repositories_page.repo["project"]
        packages = ",".join(self.products[p]["packages"] for p in self.products_page.selected_products)
        
        args = [
            "pkexec",
            self.installer,
            "-d", distribution,
            "-r", release,
            "-v", variants,
            "-p", project,
            "-i", packages,
            "--server", HOST,
            "--protocol", PROTOCOL,
        ]
        
        if self.api.username and self.api.token:
            args.extend(("-u", self.api.username,  "-t", self.api.token))
        
        for key in ("http_proxy", "https_proxy"):
            proxy = os.environ.get(key)
            if proxy is not None:
                args.append("--{0}".format(key.replace("_", "-")))
                args.append(proxy)
        
        if not VERIFY_SSL:
            args.append("--no-verify-ssl")
        
        self._worker = run_command(args, self.on_progress_output, self.on_progress_done)
        
    def on_progress_output(self, worker, line):
        self._queue.put((True, line))
    
    def on_progress_done(self, worker, status):
        self._queue.put((False, status))
    
    def _process_queue(self):
        running = True
        try:
            while True:
                running, data = self._queue.get_nowait()
                if hasattr(data, "encode"):
                    data = data.encode("utf-8", errors='backslashreplace').decode("utf-8")
                
                if running:
                    sys.stdout.write(data)
                    sys.stdout.flush()
                    self.progress_page.write(data)
                else:
                    self.progress_page.write("+ [Return code = {}]".format(data))
                    self.progress_page.set_sensitive(True)
                    
                    if data == 0:
                        self.progress_page.set_message("<b>Installation has been successfully finished. You can close this window.</b>")
                    elif data == 127:
                        self.progress_page.set_message("<b>Installation has failed because of authorization error.</b>")
                    elif data == 126:
                        self.progress_page.set_message("<b>Installation has failed because of cancelled authorization.</b>")
                    else:
                        self.progress_page.set_message("<b>Installation has failed. <a href=\"https://github.com/tiliado/tiliado-repositories/issues/new\">File a bug report</a> with the log bellow:</b>")
        except Empty:
            pass
        
        return running
