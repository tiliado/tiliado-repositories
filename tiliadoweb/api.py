from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import urlencode, quote as urlquote
import json

LOCAL_SERVER = "http://127.0.0.1:8000/"
LOCAL_ROOT = LOCAL_SERVER + "api/"
LOCAL_API_AUTH = LOCAL_SERVER + "api-auth/obtain-token/"
TEST_USER = "test", "test"

class ApiError(Exception):
    pass

class TiliadoApi:
    def __init__(self, root, username=None, token=None):
        self.root = root
        self.token = token
        self.username = username
    
    def login(self, endpoint, username, password, scope="default"):
        if not username:
            raise ApiError("Username field is empty.")
        if not password:
            raise ApiError("Password field is empty.")
        if not scope:
            raise ApiError("Scope field is empty.")
        
        try:
            data = urlencode({"username": username, "password": password, "scope": scope})
            response = urlopen(endpoint, data.encode("ascii"))
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

def main():
    api = TiliadoApi(LOCAL_ROOT)
    api.login(LOCAL_API_AUTH, *TEST_USER)
    print("Auth: user = '{api.username}', scope = '{api.scope}', token = '{api.token}'".format(api=api))

if __name__ == "__main__":
    main()