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
        response = urlopen(request)
        data = response.read() 
        return json.loads(data.decode("utf-8"));
    
    @property
    def me(self):
        return self.make_request("me/")

def main():
    api = TiliadoApi(tiliadoweb.DEVEL_SERVER, tiliadoweb.DEFAULT_API_PATH, tiliadoweb.DEFAULT_API_AUTH)
    api.login(*TEST_USER)
    print("Auth: user = '{api.username}', scope = '{api.scope}', token = '{api.token}'".format(api=api))
    
    print(api.me)

if __name__ == "__main__":
    main()
