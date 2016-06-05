import subprocess
import os
import re

def guess_dist():
    FEDORA_RELEASE_FILE = "/etc/fedora-release"
    if os.path.exists(FEDORA_RELEASE_FILE):
        try:
            with open(FEDORA_RELEASE_FILE, "r", encoding="utf-8", errors='surrogateescape') as f:
                fedora_release = f.read().strip()
                m = re.match(r"fedora\s+release\s+(\d+)", fedora_release.lower())
                if m:
                    return "fc" + m.group(1)
        except Exception as e:
            print("Failed to parse {}: {}".format(FEDORA_RELEASE_FILE, e))
    try:
        dist = subprocess.check_output(["lsb_release", "-sc"], universal_newlines=True).strip()
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print("Failed to guess distribution: %s" % e)
        dist = None
    
    return dist
