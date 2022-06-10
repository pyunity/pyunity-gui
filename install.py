import urllib.request
import os
import sys
import tempfile
import zipfile
import shutil
import sysconfig

plat = sysconfig.get_platform()
if plat.startswith("win"):
    workflow = "windows"
    name = f"python{sys.version_info.major}.{sys.version_info.minor}"
    if plat == "win-amd64":
        name += "-x64"
    else:
        name += "-x86"
elif plat.startswith("linux"):
    workflow = "unix"
    name = f"ubuntu-latest%20python{sys.version_info.major}.{sys.version_info.minor}"
elif plat.startswith("macos"):
    workflow = "unix"
    name = f"macos-latest%20python{sys.version_info.major}.{sys.version_info.minor}"

print(f"Target artifact: {name}.zip")

tmp = tempfile.mkdtemp()
orig = os.getcwd()
os.chdir(tmp)
urllib.request.urlretrieve(f"https://nightly.link/pyunity/pyunity/workflows/{workflow}/develop/{name}.zip", "artifact.zip")

with zipfile.ZipFile(os.path.join(tmp, "artifact.zip")) as zf:
    files = zf.infolist()
    name = files[0].filename
    print(f"Target wheel: {name}")
    zf.extract(name)

print("Installing wheel")
os.system("pip3 uninstall -y pyunity")
os.system("pip3 install -U " + name)
print("Cleaning up")
os.chdir(orig)
shutil.rmtree(tmp)
