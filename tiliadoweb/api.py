from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import urlencode, quote as urlquote
from base64 import b64encode
import json

import tiliadoweb

TEST_USER = "test", "test"

class ApiError(Exception):
    pass

class TiliadoApi:
    def __init__(self, server, api_path, api_auth, username=None, token=None):
        self.root = server + api_path
        self.api_auth = server + api_auth
        self.token = token
        self.username = username
        self._groups = None
        self._distributions = None
        self._repo_releases = None
    
    def login(self, username, password, scope="default"):
        if not username:
            raise ApiError("Username field is empty.")
        if not password:
            raise ApiError("Password field is empty.")
        if not scope:
            raise ApiError("Scope field is empty.")
        
        try:
            data = urlencode({"username": username, "password": password, "scope": scope})
            response = urlopen(self.api_auth, data.encode("ascii"))
        except HTTPError as e:
            if e.code == 400:
                raise ApiError("Unable to login with provided credentials.")
            print("Server has returned an error: %s." % e.read().decode("utf-8"))
            raise ApiError("Server has returned an error: %s." % str(e.reason).lower())
        
        data = response.read() 
        try:
            token = json.loads(data.decode("utf-8"))["token"];
        except Exception as e:
            print("Failed to read response from server. %s" % e)
            raise ApiError("Failed to read response from server.")
        
        self.username = username
        self.scope = scope
        self.token = token
    
    def make_request(self, path, params=None, data=None, headers=None):
        headers = headers or {}
        
        if self.token and self.username:
            #Authorization: Token  base64(username) 401f7ac837da42b97f613d789819ff93537bee6a
            headers["Authorization"] = "Token %s %s" % (b64encode(self.username.encode("utf-8")).decode("ascii"), self.token)
        
        if params:
            path = "{}?{}".format(path, urlencode(params))
        
        request = Request(self.root + path, data, headers)
        try:
            response = urlopen(request)
            data = response.read() 
            return json.loads(data.decode("utf-8"));
        except HTTPError as e:
            print("Server has returned an error: %s." % e.read().decode("utf-8"))
            raise ApiError("Server has returned an error: %s." % str(e.reason).lower())
    
    @property
    def me(self):
        return self.make_request("me/")
    
    @property
    def repositories(self):
        return self.make_request("repository/repositories/")
    
    @property
    def repo_releases(self):
        return self.make_request("repository/releases/")
    
    def repo_release(self, key):
        if self._repo_releases is None:
            self._repo_releases = {i["id"]: i for i in self.repo_releases}
        try:
            return self._repo_releases[key]
        except KeyError:
            repo_release = self._repo_releases[key] = self.make_request("repository/releases/".format(key))
            return repo_release
   
    @property
    def distributions(self):
        return self.make_request("repository/distributions/")
    
    def distribution(self, key):
        if self._distributions is None:
            self._distributions = {i["id"]: i for i in self.distributions}
        try:
            return self._distributions[key]
        except KeyError:
            distribution = self._distributions[key] = self.make_request("repository/distributions/".format(key))
            return distribution
    
    def component(self, identifier):
        return self.make_request("repository/components/{}/".format(identifier))
    
    @property
    def groups(self):
        return self.make_request("auth/groups/")
        
    def group(self, key):
        if self._groups is None:
            self._groups = {group["id"]: group for group in self.groups}
        try:
            return self._groups[key]
        except KeyError:
            group = self._groups[key] = self.make_request("auth/groups/".format(key))
            return group
    
    @property
    def all_products(self):
        return self.make_request("repository/products/")
    
    def list_products(self, **params):
        return self.make_request("repository/products/", params=params)
        
    def list_packages(self, **params):
        return self.make_request("repository/packages/", params=params)
    
def main():
    api = TiliadoApi(tiliadoweb.DEVEL_SERVER, tiliadoweb.DEFAULT_API_PATH, tiliadoweb.DEFAULT_API_AUTH)
    api.login(*TEST_USER)
    print("Auth: user = '{api.username}', scope = '{api.scope}', token = '{api.token}'".format(api=api))
    
    print(api.me)
    
    for product in api.all_products:
        print("Product: {}".format(product))
    
    repositories = api.repositories
    for repo in repositories:
        print("Repo: {}".format(repo))
        product = None
        for product in api.list_products(repository=repo["id"]):
            print("Product: {}".format(product))
        
        for pk in repo.get("component_set", ()):
            component = api.component(pk)
            print("Component: {}".format(component))
            for access in component["access_set"]:
                print("Access: {}".format(access))
                for group_pk in access["groups"]:
                    group = api.group(group_pk)
                    print("Group {}: {}".format(group_pk, group))
                release = access["release"]
                if product:
                    for pkg_name in product["packages"].split(","):
                        packages = api.list_packages(repository=repo["id"], component=pk, release=release, name=pkg_name)
                        for package in packages:
                            print("Package: {}".format(package["id"]))

    for distribution in api.distributions:
        print("Distribution {}: {}".format(distribution["id"], api.distribution(distribution["id"])))
         
    for release in api.repo_releases:
        print("Repo release {}: {}".format(release["id"], api.repo_release(release["id"])))
    
if __name__ == "__main__":
    main()
