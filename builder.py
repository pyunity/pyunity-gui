import traceback
import urllib.request
import tempfile
import zipfile
import subprocess
import glob
import os
import sys
from pathlib import Path
import shutil
import hashlib
import py_compile
from optparse import Values
from pip._internal.index.package_finder import PackageFinder
from pip._internal.index.collector import LinkCollector
from pip._internal.network.session import PipSession
from pip._internal.models.selection_prefs import SelectionPreferences
from pip._internal.models.target_python import TargetPython
from pip._internal.req.constructors import install_req_from_line

archmapArg = {"x64": "amd64", "x86": "win32"}

MSVC_RUNTIME = False
VERSION = os.getenv("PYTHON_VERSION")
if not VERSION:
    VERSION = "3.10.12"
ARCH = archmapArg[os.getenv("PYTHON_ARCHITECTURE")]
if not ARCH:
    ARCH = "amd64"
ZIP_OPTIONS = {"compression": zipfile.ZIP_DEFLATED, "compresslevel": 9}

class PypiLinkGetter:
    session = PipSession()
    collector = LinkCollector.create(session, Values(dict(
        index_url="https://pypi.org/pypi",
        extra_index_urls=[],
        no_index=False,
        find_links=[]
    )))
    prefs = SelectionPreferences(True, False, prefer_binary=True)
    finders = {}
    archmap = {"amd64": "win_amd64", "win32": "win32"}

    @classmethod
    def getLink(cls, version, platform, req):
        print("FIND", req)
        vertuple = tuple(version.split("."))
        if (vertuple, platform) not in cls.finders:
            target = TargetPython([cls.archmap[platform]], vertuple)
            finder = PackageFinder.create(cls.collector, cls.prefs, target)
            cls.finders[vertuple, platform] = finder
        else:
            finder = cls.finders[vertuple, platform]
        return finder.find_requirement(install_req_from_line(req), False).link._url

def checkTools():
    if shutil.which("7z.exe") is None:
        raise Exception("7Zip is needed to build the PyUnity Editor.")
    if "GITHUB_ACTIONS" in os.environ:
        if shutil.which("cl.exe") is None:
            raise Exception("Microsoft Visual C is needed to build the PyUnity Editor.")
        if shutil.which("rc.exe") is None:
            raise Exception("Cannot find 'rc.exe'")
    else:
        if shutil.which("gcc.exe") is None:
            raise Exception("MinGW-w64 is needed to build the PyUnity Editor.")
        if shutil.which("windres.exe") is None:
            raise Exception("Cannot find 'windres.exe'")

wheels = [{}, {}]
for req in ["pyopengl", "pysdl2", "pysidesix-frameless-window"]:
    wheels[0][req] = PypiLinkGetter.getLink(VERSION, ARCH, req)
for req in ["pyopengl_accelerate", "pysdl2_dll", "pillow", "pyglm",
        "pyside6", "shiboken6", "pyside6_essentials", "glfw", "pywin32"]:
    wheels[1][req] = PypiLinkGetter.getLink(VERSION, ARCH, req)

def download(url, dest):
    print("GET", url, "->", os.path.basename(dest), flush=True)
    directory = Path.home() / ".pyunity" / ".builder"
    directory.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(url.encode()).hexdigest()
    path = directory / (digest + ".bin")
    if not path.is_file():
        urllib.request.urlretrieve(url, path)
    shutil.copy(path, dest)

def stripPySide6():
    print("STRIP PySide6", flush=True)
    keep = [
        "__init__.pyc", "QtCore.pyd", "QtGui.pyd", "QtOpenGLWidgets.pyd",
        "QtWidgets.pyd", "QtSvg.pyd", "QtXml.pyd",
        "pyside6.abi3.dll", "Qt6Core.dll", "Qt6Gui.dll", "Qt6OpenGL.dll",
        "Qt6OpenGLWidgets.dll", "Qt6Widgets.dll", "Qt6Svg.dll", "Qt6Xml.dll",
        "plugins\\platforms\\qwindows.dll"
    ]
    for dir, subdirs, files in os.walk("Lib\\PySide6\\", topdown=False):
        for name in files:
            path = os.path.join(dir, name)
            if path[12:] not in keep:
                os.remove(path)
        if len(os.listdir(dir)) == 0:
            os.rmdir(dir)

def setupPyWin32(zf):
    os.makedirs("Lib/win32", exist_ok=True)
    files = [
        "win32/win32api.pyd", "win32/win32gui.pyd", "win32/win32print.pyd",
        "win32/lib/win32con.py", "pywin32_system32/pywintypes310.dll"
    ]
    for file in zf.filelist:
        if file.filename in files:
            filename = os.path.basename(file.filename)
            with open("Lib/win32/" + filename, "wb+") as f:
                with zf.open(file) as f2:
                    shutil.copyfileobj(f2, f)
            zf.extract("win32/" + filename, "Lib")
        elif ".dist-info/" in file.filename:
            zf.extract(file, "Lib")

def addPackage(zf, name, path, orig, distInfo=False):
    print("COMPILE", name, flush=True)
    os.chdir("..\\" + name)
    paths = glob.glob(path, recursive=True)
    if distInfo:
        paths.extend(glob.glob("*.dist-info\\**\\*", recursive=True))
    for file in paths:
        if file.endswith(".py"):
            py_compile.compile(file, file + "c", file,
                            doraise=True)
            zf.write(file + "c")
        elif not file.endswith(".pyc"):
            zf.write(file)
    os.chdir(orig)

tmp = tempfile.mkdtemp()
orig = os.getcwd() + "\\"
os.chdir(tmp)
print("Working directory:", os.getcwd())
try:
    download(f"https://www.python.org/ftp/python/{VERSION}/python-{VERSION}-embed-{ARCH}.zip",
             "embed.zip")
    vername = f"pyunity-editor"
    os.makedirs(vername, exist_ok=True)
    with zipfile.ZipFile("embed.zip") as zf:
        print("EXTRACT embed.zip", flush=True)
        zf.extractall(vername)

    url = "https://github.com/pyunity/pyunity/archive/refs/heads/develop.zip"
    print("GET", url, "-> pyunity.zip", flush=True)
    urllib.request.urlretrieve(url, "pyunity.zip")
    with zipfile.ZipFile("pyunity.zip") as zf:
        print("EXTRACT pyunity.zip", flush=True)
        zf.extractall()

    print("BUILD pyunity", flush=True)
    os.chdir("pyunity-develop")
    subprocess.call([sys.executable, "-m", "build"],
                    stdout=subprocess.DEVNULL, stderr=sys.stderr,
                    env={**os.environ, "cython": "0"})
    shutil.move(glob.glob("dist/*.whl")[0], "..\\pyunity.whl")
    os.chdir(tmp)

    with zipfile.ZipFile("pyunity.whl") as zf:
        print("EXTRACT pyunity.whl", flush=True)
        zf.extractall("pyunity")

    print("BUILD pyunity-editor", flush=True)
    os.chdir(orig)
    subprocess.call([sys.executable, "-m", "build"],
                    stdout=subprocess.DEVNULL, stderr=sys.stderr)
    shutil.move(glob.glob("dist/*.whl")[0], tmp + "\\pyunity-editor.whl")
    os.chdir(tmp)

    with zipfile.ZipFile("pyunity-editor.whl") as zf:
        print("EXTRACT pyunity-editor.whl", flush=True)
        zf.extractall("editor")

    workdir = tmp + "\\" + vername
    os.chdir(workdir)

    zipname = "python" + "".join(VERSION.split(".")[:2])
    with zipfile.ZipFile(zipname + ".zip", "a", **ZIP_OPTIONS) as zf:
        addPackage(zf, "pyunity", "pyunity\\**\\*", workdir, True)
        addPackage(zf, "editor", "pyunity_editor\\**\\*", workdir, True)

        for name, url in wheels[0].items():
            if url.endswith(".tar.gz"):
                download(url, "..\\" + name + ".tar.gz")
                subprocess.call([sys.executable, "-m", "pip", "wheel",
                                 "--no-deps", "..\\" + name + ".tar.gz"])
                shutil.move(glob.glob("*.whl")[0], "..\\" + name + ".whl")
            else:
                download(url, "..\\" + name + ".whl")
            with zipfile.ZipFile("..\\" + name + ".whl") as zf2:
                print("EXTRACT " + name + ".whl", flush=True)
                zf2.extractall("..\\" + name)
            addPackage(zf, name, "**\\*", workdir)

    for name, url in wheels[1].items():
        download(url, "..\\" + name + ".whl")
        print("COPY", name, flush=True)
        with zipfile.ZipFile("..\\" + name + ".whl") as zf2:
            if name == "pywin32":
                setupPyWin32(zf2)
            else:
                zf2.extractall("Lib")

    print("COMPILE Lib")
    os.chdir("Lib")
    for file in glob.glob("**\\*.py", recursive=True):
        py_compile.compile(file, file + "c", quiet=0)
        os.remove(file)
    os.chdir(workdir)

    stripPySide6()

    print("MOVE *.pyd", flush=True)
    for file in glob.glob("*.pyd"):
        shutil.move(file, "Lib")

    os.remove("python.exe")
    os.remove("python.cat")
    os.remove("pythonw.exe")
    os.remove(zipname + "._pth")
    shutil.move(zipname + ".zip", "Lib\\python.zip")

    if MSVC_RUNTIME:
        download(PypiLinkGetter.getLink(VERSION, ARCH, "msvc-runtime"), "..\\msvc_runtime.whl")
        with zipfile.ZipFile("..\\msvc_runtime.whl") as zf:
            print("EXTRACT msvc_runtime.whl", flush=True)
            zf.extractall("..\\msvc_runtime")
        datafolder = glob.glob("..\\msvc_runtime\\*.data\\data\\")[0]
        print("COPY msvc_runtime", flush=True)
        for file in os.listdir(datafolder):
            if file.endswith(".dll"):
                shutil.copy(os.path.join(datafolder, file), ".")

    shutil.copy(orig + "\\standalone\\pyunity-editor.c", "..")
    shutil.copy(orig + "\\standalone\\icons.ico", "..")
    shutil.copy(orig + "\\standalone\\icons.rc", "..")
    shutil.copy(orig + "\\standalone\\version.rc", "..")

    if "GITHUB_ACTIONS" in os.environ:
        print("COMPILE icons.o", flush=True)
        subprocess.call([
            "rc.exe", "/fo..\\icons.res", "..\\icons.rc"
        ], stdout=sys.stdout, stderr=sys.stderr)
        print("COMPILE version.o", flush=True)
        subprocess.call([
            "rc.exe", "/fo..\\version.res", "..\\version.rc"
        ], stdout=sys.stdout, stderr=sys.stderr)

        print("COMPILE pyunity-editor.exe", flush=True)
        subprocess.call([
            "cl.exe", "/nologo", "/O2", "/Wall",
            "/Tc..\\pyunity-editor.c", "/Fo..\\pyunity-editor.obj",
            f"/I{sys.base_prefix}\\include", "/DNOCONSOLE",
            "/link", "..\\icons.res", "..\\version.res", "user32.lib",
            "/subsystem:windows",
            f"/libpath:{sys.base_prefix}\\libs",
            "/out:pyunity-editor.exe"
        ], stdout=sys.stdout, stderr=sys.stderr)
    else:
        print("COMPILE icons.o", flush=True)
        subprocess.call([
            "windres.exe", "-O", "coff",
            "..\\icons.rc", "..\\icons.o"
        ], stdout=sys.stdout, stderr=sys.stderr)
        print("COMPILE version.o", flush=True)
        subprocess.call([
            "windres.exe", "-O", "coff",
            "..\\version.rc", "..\\version.o"
        ], stdout=sys.stdout, stderr=sys.stderr)

        print("COMPILE pyunity-editor.exe", flush=True)
        subprocess.call([
            "gcc.exe", "-O2", "-Wall", "-mwindows", "-DNOCONSOLE",
            "-o", "pyunity-editor.exe", "..\\pyunity-editor.c", "..\\icons.o", "..\\version.o",
            "-L.", f"-l{zipname}", f"-I{sys.base_prefix}\\include",
        ], stdout=sys.stdout, stderr=sys.stderr)

    print(f"ZIP pyunity-editor.zip", flush=True)
    os.chdir(tmp)
    subprocess.call([
        "7z.exe", "a", "-mx=9",
        f"pyunity-editor.zip", vername
    ], stdout=sys.stdout, stderr=sys.stderr)
    shutil.copy(f"pyunity-editor.zip", orig)

    print(f"7Z pyunity-editor.7z", flush=True)
    subprocess.call([
        "7z.exe", "a", "-mx=9",
        f"pyunity-editor.7z", vername
    ], stdout=sys.stdout, stderr=sys.stderr)
    shutil.copy(f"pyunity-editor.7z", orig)

    print("SFX pyunity-editor.exe", flush=True)
    with open("pyunity-editor-install.exe", "wb+") as f1:
        with open(orig + "\\standalone\\7z.sfx", "rb") as f2:
            shutil.copyfileobj(f2, f1)
        with open("pyunity-editor.7z", "rb") as f2:
            shutil.copyfileobj(f2, f1)
    shutil.copy("pyunity-editor-install.exe", orig)

    if "GITHUB_ACTIONS" not in os.environ:
        input("Press Enter to continue ...")
except BaseException as e:
    print("".join(traceback.format_exception(e)), flush=True)
    raise SystemExit
finally:
    print("Cleaning up", flush=True)
    os.chdir(orig)
    shutil.rmtree(tmp)
