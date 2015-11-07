import os
from gi.repository import Gio


def set_proxy_from_gsettings():
    if "http_proxy" in os.environ:
        print("HTTP proxy environ:", os.environ["http_proxy"])
        return
    if "https_proxy" in os.environ:
        print("HTTPS proxy environ:", os.environ["https_proxy"])
        return
    
    PROXY_SCHEMA_ID = "org.gnome.system.proxy"
    HTTP_PROXY_SCHEMA_ID = "org.gnome.system.proxy.http"
    HTTPS_PROXY_SCHEMA_ID = "org.gnome.system.proxy.https"
    schemas = frozenset(Gio.Settings.list_schemas())
    
    if PROXY_SCHEMA_ID in schemas:
        proxy_mode = Gio.Settings.new(PROXY_SCHEMA_ID).get_string("mode")
        if proxy_mode in ("none", "auto"):
            return
    
    http_proxy = ""
    https_proxy = ""
    
    if HTTP_PROXY_SCHEMA_ID in schemas:
        gs_proxy = Gio.Settings.new(HTTP_PROXY_SCHEMA_ID)
        host = gs_proxy.get_string("host")
        port = gs_proxy.get_int("port")
        if host and port > 0:
            http_proxy = "http://{0}:{1}/".format(host, port)
    
    if HTTPS_PROXY_SCHEMA_ID in schemas:
        gs_proxy = Gio.Settings.new(HTTPS_PROXY_SCHEMA_ID)
        host = gs_proxy.get_string("host")
        port = gs_proxy.get_int("port")
        if host and port > 0:
            https_proxy = "http://{0}:{1}/".format(host, port)
    
    print("HTTP  proxy from gsettings:", http_proxy)
    print("HTTPS proxy from gsettings:", https_proxy)
    
    if http_proxy:
        os.environ["http_proxy"] = http_proxy
        if not https_proxy:
            os.environ["https_proxy"] = http_proxy
        
    if https_proxy:
        os.environ["https_proxy"] = https_proxy
