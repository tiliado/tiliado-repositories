from . import devel
try:
    from . import production
except ImportError:
    production = object()

def get_config(key):
    return getattr(production, key, getattr(devel, key))

PROTOCOL = get_config("PROTOCOL")
HOST = get_config("HOST")
SERVER = "{}://{}/".format(PROTOCOL, HOST)
SIGN_UP_PATH = get_config("SIGN_UP_PATH")
PASSWORD_RESET_PATH = get_config("PASSWORD_RESET_PATH")
API_PATH = get_config("API_PATH")
API_AUTH = get_config("API_AUTH")
