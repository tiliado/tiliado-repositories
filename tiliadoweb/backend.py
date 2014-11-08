import os
import sys
import subprocess
from codecs import open

def log(line):
    sys.stdout.write(line)
    sys.stdout.write("\n")
    sys.stdout.flush()

def exec_and_collects(argv, dry_run=False):
    log("+ {}".format(argv))
    if dry_run:
        log("*** Dry run ***")
    else:
        subprocess.check_call(argv, stderr=subprocess.STDOUT)

def write_file(filename, data, dry_run=False):
    log("+ [write '{}']\n{}".format(filename, data))
    if not dry_run:
        with open(filename, "w", "utf-8") as f:
            f.write(data)
    else:
        log("*** Dry run ***\n")

class BaseBackend:
    def __init__(self, verify_ssl=True, dry_run=False):
        self.dry_run = dry_run
        self.verify_ssl = verify_ssl
    
    def prepare(self):
        pass

class DebBackend(BaseBackend):
    DEFAULT_KEY = "40554B8FA5FE6F6A"
    
    def __init__(self, *args, **kwargs):
        BaseBackend.__init__(self, *args, **kwargs)
        self.apt_opts = []
        if not self.verify_ssl:
            log("Warning: ignoring SSL errors!")
            self.apt_opts.extend(('-o', 'Acquire::https::Verify-Peer=false', '-o', 'Acquire::https::Verify-Host=false'))
    
    def install_packages(self, packages):
            argv = ["apt-get", "install", "-y"] + self.apt_opts + packages
            exec_and_collects(argv, dry_run=self.dry_run)
            
    def remove_packages(self, packages):
        argv = ["apt-get", "remove", "-y"] + self.apt_opts + packages
        try:
            exec_and_collects(argv, dry_run=self.dry_run)
        except subprocess.CalledProcessError as e:
            log(str(e))
    
    def add_repositories(self, protocol, server, username, token, products, dist_release, variants):
        protocol = protocol or "https"
        variants = " ".join(variants)
        sources_dir = "/etc/apt/sources.list.d"
        log("+ [makedirs '{}']".format(sources_dir))
        if not self.dry_run:
            os.makedirs(sources_dir, exist_ok=True)
        
        auth = "{}:{}@".format(username, token) if username and token else ""
        for product in products:
            filename = "{}/tiliado-{}.list".format(sources_dir, product)
            apt_line = "deb {protocol}://{auth}{server}/{project}/repository/deb/ {release} {components}\n".format(
                server=server,
                protocol=protocol,
                auth=auth,
                project=product,
                release=dist_release,
                components=variants)
            write_file(filename, apt_line, dry_run=self.dry_run)
    
    def add_key(self, key):
        argv = ["apt-key", "adv", "--keyserver", "keyserver.ubuntu.com", "--recv-keys", key]
        exec_and_collects(argv, dry_run=self.dry_run)
    
    def update_db(self):
        argv = ["apt-get", "update"] + self.apt_opts
        exec_and_collects(argv, dry_run=self.dry_run)

class YumBackend(BaseBackend):
    DEFAULT_KEY = "40554B8FA5FE6F6A"
    
    def __init__(self, *args, **kwargs):
        BaseBackend.__init__(self, *args, **kwargs)
        self.yum_opts = []
        #~ if not self.verify_ssl:
            #~ log("Warning: ignoring SSL errors!")
            #~ self.apt_opts.extend(('-o', 'Acquire::https::Verify-Peer=false', '-o', 'Acquire::https::Verify-Host=false'))
    
    def install_packages(self, packages):
            argv = ["yum", "install", "-y"] + self.yum_opts + packages
            exec_and_collects(argv, dry_run=self.dry_run)
            
    def remove_packages(self, packages):
        argv = ["yum", "remove", "-y"] + self.yum_opts + packages
        try:
            exec_and_collects(argv, dry_run=self.dry_run)
        except subprocess.CalledProcessError as e:
            log(str(e))
    
    def add_repositories(self, protocol, server, username, token, products, dist_release, variants):
        protocol = protocol or "https"
        sources_dir = "/etc/yum.repos.d"
        log("+ [makedirs '{}']".format(sources_dir))
        if not self.dry_run:
            try:
                os.makedirs(sources_dir)
            except OSError as e:
                if e.errno != 17:
                    raise e
        
        arch = os.uname()[4]
        if arch != 'x86_64':
            arch = 'i686'
        
        auth = "{}:{}@".format(username, token) if username and token else ""
        for product in products:
            buffer = []
            for component in variants:
                buffer.append('[{}-{}]'.format(product, component))
                buffer.append('name={} repository, component {} ({} {})'.format(
                    product, component, dist_release, arch))
                buffer.append('baseurl={}://{}{}/{}/repository/rpm/{}/{}/{}/'.format(
                    protocol, auth, server, product, dist_release, arch, component))
                buffer.append('enabled=1')
                buffer.append('gpgcheck=0')
                buffer.append('')
            
            filename = "{}/tiliado-{}.repo".format(sources_dir, product)
            write_file(filename, "\n".join(buffer), dry_run=self.dry_run)
    
    def add_key(self, key):
        argv = ["rpm", "--import", "http://keyserver.ubuntu.com/pks/lookup?search=0x{}&op=get".format(key)]
        exec_and_collects(argv, dry_run=self.dry_run)
    
    def update_db(self):
        argv = ["yum", "makecache", "fast"] + self.yum_opts
        exec_and_collects(argv, dry_run=self.dry_run)

def install(server, protocol, project, distribution, release, variants, username=None, token=None,
    install=None, dry_run=False, no_verify_ssl=False, http_proxy=None, https_proxy=None, **kwd):
    if http_proxy is not None:
        os.environ["http_proxy"] = http_proxy
    if https_proxy is not None:
        os.environ["https_proxy"] = https_proxy
    
    if distribution in ("debian", "ubuntu"):
        backend = DebBackend(verify_ssl = not no_verify_ssl, dry_run=dry_run)
    elif distribution in ("fedora",):
        backend = YumBackend(verify_ssl = not no_verify_ssl, dry_run=dry_run)
    else:
        log("Unsupported distribution: {}".format(distribution))
        sys.exit(2)
    
    try:
        backend.prepare()
        
        if install:
            install = install.split(",")
            backend.remove_packages(install)
        
        backend.add_key(backend.DEFAULT_KEY)
        backend.add_repositories(protocol, server, username, token, project.split(","), release, variants.split(","))
        backend.update_db()
        
        if install:
            backend.install_packages(install)
        
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        log("Subprocess Error: {}".format(e))
        sys.exit(4)
    except OSError as e:
        log("OS Error: {}".format(e))
        sys.exit(3)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Install repository.')
    parser.add_argument('-u', "--username", type=str, required=False)
    parser.add_argument('-t', "--token", type=str, required=False)
    parser.add_argument('-p', "--project", type=str, required=True)
    parser.add_argument('-d', "--distribution", type=str, required=True)
    parser.add_argument('-r', "--release", type=str, required=True)
    parser.add_argument('-v', "--variants", type=str, required=True)
    parser.add_argument("--server", type=str, required=True)
    parser.add_argument("--protocol", type=str, default=None)
    parser.add_argument("--http-proxy", dest="http_proxy", type=str, default=None)
    parser.add_argument("--https-proxy", dest="https_proxy", type=str, default=None)
    parser.add_argument("--dry-run", action='store_true', default=False)
    parser.add_argument('-i', "--install", type=str)
    parser.add_argument('--no-verify-ssl', action="store_true", default=False)
    args = parser.parse_args()
    
    install(**vars(args))

if __name__ == "__main__":
    main()
