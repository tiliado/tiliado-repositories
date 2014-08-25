SIGN_UP_PATH = "accounts/signup/"
PASSWORD_RESET_PATH = "accounts/password/reset/"
API_PATH = "api/"
API_AUTH = "api-auth/obtain-token/"
VERIFY_SSL = True

def _join_config():
    import sys
    import os
    from importlib import import_module
    
    config_module = os.environ.get("TILIADO_REPOSITORIES_CONFIG", ".production")
    config = import_module(config_module, __name__)
    self = sys.modules[__name__]
    
    for key in dir(config):
        if not key.startswith("_"):
            setattr(self, key, getattr(config, key))

_join_config()

SERVER = "{}://{}/".format(PROTOCOL, HOST)
