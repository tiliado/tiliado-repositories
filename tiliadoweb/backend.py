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
    def __init__(self, dry_run=False):
        self.dry_run = dry_run

class DebBackend(BaseBackend):
    DEFAULT_KEY = "40554B8FA5FE6F6A"
    
    def install_packages(self, packages):
            argv = ["apt-get", "install", "-y"] + packages
            exec_and_collects(argv, dry_run=self.dry_run)
            
    def remove_packages(self, packages):
        argv = ["apt-get", "remove", "-y"] + packages
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
        
        for product in products:
            filename = "{}/tiliado-{}.list".format(sources_dir, product)
            apt_line = "deb {protocol}://{username}:{token}@{server}/{project}/repository/deb/ {release} {components}\n".format(
                server=server,
                protocol=protocol,
                username=username,
                token=token,
                project=product,
                release=dist_release,
                components=variants)
            write_file(filename, apt_line, dry_run=self.dry_run)
    
    def add_key(self, key):
        argv = ["apt-key", "adv", "--keyserver", "keyserver.ubuntu.com", "--recv-keys", key]
        exec_and_collects(argv, dry_run=self.dry_run)
    
    def update_db(self):
        argv = ["apt-get", "update"]
        exec_and_collects(argv, dry_run=self.dry_run)

def install(server, protocol, username, token, project, distribution, release, variants, install=None, dry_run=False, **kwd):
    if distribution in ("debian", "ubuntu"):
        backend = DebBackend(dry_run=dry_run)
    else:
        log("Unsupported distribution: {}".format(distribution))
        sys.exit(2)
    
    try:
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
    parser.add_argument('-u', "--username", type=str, required=True)
    parser.add_argument('-t', "--token", type=str, required=True)
    parser.add_argument('-p', "--project", type=str, required=True)
    parser.add_argument('-d', "--distribution", type=str, required=True)
    parser.add_argument('-r', "--release", type=str, required=True)
    parser.add_argument('-v', "--variants", type=str, required=True)
    parser.add_argument("--server", type=str, required=True)
    parser.add_argument("--protocol", type=str, default=None)
    parser.add_argument("--dry-run", action='store_true', default=False)
    parser.add_argument('-i', "--install", type=str)
    args = parser.parse_args()
    
    install(**vars(args))

if __name__ == "__main__":
    main()