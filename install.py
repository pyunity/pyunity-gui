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
project = requests.get(f"{apiUrl}/projects/pyunity/pyunity")
jobId = project.json()["build"]["jobs"][3 * job + 10 - ver]["jobId"]
artifacts = requests.get(f"{apiUrl}/buildjobs/{jobId}/artifacts")
if len(artifacts.json()) <= num:
    print("No artifact found, check https://ci.appveyor.com/project/pyunity/pyunity for details")
    exit(1)
file = f"{apiUrl}/buildjobs/{jobId}/artifacts/{artifacts.json()[num]['fileName']}"
os.system("pip3 uninstall -y pyunity")
os.system("pip3 install -U pyunity@" + file)
