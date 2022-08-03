import urllib.request
import os
import sys
import tempfile
import zipfile
import shutil
import sysconfig
import subprocess

plat = sysconfig.get_platform()
if plat.startswith("win"):
    workflow = "windows"
    name = f"python{sys.version_info.major}.{sys.version_info.minor}"
    if plat == "win-amd64":
        name += "-x64"
    else:
        name += "-x86"
elif plat.startswith("linux"):
    workflow = "linux"
    arch = plat.split("-", 1)[1]
    name = f"python{sys.version_info.major}.{sys.version_info.minor}-{arch}"
elif plat.startswith("macos"):
    workflow = "macos"
    name = f"python{sys.version_info.major}.{sys.version_info.minor}"

print(f"Target artifact: {name}.zip")

tmp = tempfile.mkdtemp()
orig = os.getcwd()
os.chdir(tmp)
try:
    urllib.request.urlretrieve(f"https://nightly.link/pyunity/pyunity/workflows/{workflow}/develop/{name}.zip", "artifact.zip")

    with zipfile.ZipFile(os.path.join(tmp, "artifact.zip")) as zf:
        files = zf.infolist()
        name = files[0].filename
        print(f"Target wheel: {name}")
        zf.extract(name)

    print("Installing wheel")
    subprocess.call([sys.executable, "-m", "pip", "uninstall", "-y", "pyunity"],
                    stdout=sys.stdout, stderr=sys.stderr)
    subprocess.call([sys.executable, "-m", "pip", "install", "-U", name],
                    stdout=sys.stdout, stderr=sys.stderr)
finally:
    print("Cleaning up")
    os.chdir(orig)
    shutil.rmtree(tmp)
