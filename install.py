import requests
import os
import sys
import distutils.util

plat = distutils.util.get_platform()
num = int(plat == "win-amd64")
if plat.startswith("win"):
    job = 0
elif plat.startswith("linux"):
    job = 1
elif plat.startswith("macos"):
    job = 2
ver = sys.version_info.minor


apiUrl = "https://ci.appveyor.com/api"
project = requests.get(f"{apiUrl}/projects/rayzchen/pyunity")
jobId = project.json()["build"]["jobs"][4 * job + 9 - ver]["jobId"]
artifacts = requests.get(f"{apiUrl}/buildjobs/{jobId}/artifacts")
file = f"{apiUrl}/buildjobs/{jobId}/artifacts/{artifacts.json()[num]['fileName']}"
os.system("pip3 uninstall -y pyunity")
os.system("pip3 install -U pyunity@" + file)
