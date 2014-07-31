import subprocess

def guess_dist():
    try:
        dist = subprocess.check_output(["lsb_release", "-sc"], universal_newlines=True).strip()
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print("Failed to guess distribution: %s" % e)
        dist = None
    
    return dist
