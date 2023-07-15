import traceback
import urllib.request
import tempfile
import zipfile
import subprocess
import glob
import os
import sys
import atexit
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
from pip._vendor.packaging.version import parse

argArchmap = {"x64": "amd64", "x86": "win32"}
MSVC_RUNTIME = False
VERSION = os.getenv("PYTHON_VERSION")
if not VERSION:
    VERSION = "3.10.11"
ARCH = argArchmap.get(os.getenv("PYTHON_ARCHITECTURE"), "")
if not ARCH:
    ARCH = "amd64"
ZIP_OPTIONS = {"compression": zipfile.ZIP_DEFLATED, "compresslevel": 9}

originalFolder = os.getcwd() + "\\"
mainFolder = "pyunity-editor"
zipName = "python" + "".join(VERSION.split(".")[:2])

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

def getPackageLinks():
    compressedReqs = ["pyopengl", "pysdl2", "pysidesix-frameless-window"]
    extensionReqs = ["pyopengl-accelerate", "pysdl2-dll", "pillow", "pyglm",
        "pyside6", "shiboken6", "pyside6-essentials", "pywin32"]

    if parse(VERSION) < parse("3.9"):
        compressedReqs.append("importlib-metadata")
    if parse(VERSION) >= parse("3.9"):
        extensionReqs.append("numpy")

    packages = [{}, {}]
    for req in compressedReqs:
        packages[0][req] = PypiLinkGetter.getLink(VERSION, ARCH, req)
    for req in extensionReqs:
        packages[1][req] = PypiLinkGetter.getLink(VERSION, ARCH, req)
    return packages

def download(url, dest):
    print("GET", url, "->", os.path.basename(dest), flush=True)
    directory = os.path.expanduser("~/.pyunity/.builder")
    os.makedirs(directory, exist_ok=True)
    digest = hashlib.sha256(url.encode()).hexdigest()
    path = os.path.join(directory, digest + ".bin")
    if not os.path.isfile(path):
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

def stripNumpy():
    print("STRIP numpy", flush=True)
    for folder in glob.glob("Lib/numpy/*/tests"):
        shutil.rmtree(folder)

def setupPillow():
    download("https://download.lfd.uci.edu/pythonlibs/archived/libraqm-0.7.1.dll.zip", "../raqm.zip")
    with zipfile.ZipFile("../raqm.zip") as zf:
        zf.extractall("../raqm-dlls")
    for file in glob.glob("../raqm-dlls/*/x64/*"):
        shutil.move(file, "Lib")

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
        elif ".dist-info/" in file.filename:
            zf.extract(file, "Lib")

def addPackage(zf, name, path, orig, distInfo=True):
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

def getEmbedPackage():
    download(f"https://www.python.org/ftp/python/{VERSION}/python-{VERSION}-embed-{ARCH}.zip",
             "embed.zip")
    os.makedirs(mainFolder, exist_ok=True)
    with zipfile.ZipFile("embed.zip") as zf:
        print("EXTRACT embed.zip", flush=True)
        zf.extractall(mainFolder)

def getPyUnity():
    # Do not cache
    url = "https://github.com/pyunity/pyunity/archive/refs/heads/develop.zip"
    print("GET", url, "-> pyunity.zip", flush=True)
    urllib.request.urlretrieve(url, "pyunity.zip")
    with zipfile.ZipFile("pyunity.zip") as zf:
        print("EXTRACT pyunity.zip", flush=True)
        zf.extractall()

def buildSrcPackage(name, directory, outDir):
    print("BUILD", name, flush=True)
    with open(os.path.join(originalFolder, "build.log"), "a+") as log:
        subprocess.call([sys.executable, "-m", "build", directory],
                         stdout=log, stderr=sys.stderr,
                         env={**os.environ, "cython": "0"})
    shutil.move(glob.glob(directory + "/dist/*.whl")[0], name + ".whl")

    with zipfile.ZipFile(name + ".whl") as zf:
        print("EXTRACT",  name + ".whl", flush=True)
        zf.extractall(outDir)

def getBinaryPackage(name, url):
    if url.endswith(".tar.gz"):
        download(url, "..\\" + name + ".tar.gz")
        subprocess.call([sys.executable, "-m", "pip", "wheel",
                            "--no-deps", "..\\" + name + ".tar.gz"])
        shutil.move(glob.glob("*.whl")[0], "..\\" + name + ".whl")
    else:
        download(url, "..\\" + name + ".whl")

def installLibraries(directory):
    with zipfile.ZipFile(zipName + ".zip", "a", **ZIP_OPTIONS) as zf:
        addPackage(zf, "pyunity-package", "pyunity\\**\\*", directory)
        addPackage(zf, "editor-package", "pyunity_editor\\**\\*", directory)
    wheels = getPackageLinks()

    for name, url in wheels[0].items():
        getBinaryPackage(name, url)
        with zipfile.ZipFile("..\\" + name + ".whl") as zf2:
            print("EXTRACT " + name + ".whl", flush=True)
            zf2.extractall("..\\" + name)
        with zipfile.ZipFile(zipName + ".zip", "a", **ZIP_OPTIONS) as zf:
            addPackage(zf, name, "**\\*", directory, False)

    for name, url in wheels[1].items():
        getBinaryPackage(name, url)
        print("COPY", name, flush=True)
        with zipfile.ZipFile("..\\" + name + ".whl") as zf2:
            if name == "pywin32":
                setupPyWin32(zf2)
            else:
                zf2.extractall("Lib")

def setupLibraries(directory):
    print("COMPILE Lib")
    os.chdir("Lib")
    for file in glob.glob("**\\*.py", recursive=True):
        py_compile.compile(file, file + "c", quiet=0)
        os.remove(file)
    os.chdir(directory)

    print("REMOVE *.pyi *.pxd")
    files = glob.glob("Lib/**/*.pyi", recursive=True) + \
        glob.glob("Lib/**/*.pxd", recursive=True)
    for file in files:
        os.remove(file)

    stripPySide6()
    stripNumpy()
    setupPillow()

def cleanPackageRoot():
    print("MOVE *.pyd", flush=True)
    for file in glob.glob("*.pyd"):
        shutil.move(file, "Lib")

    print("CLEAN", mainFolder)
    os.remove("python.exe")
    os.remove("python.cat")
    os.remove("pythonw.exe")
    os.remove(zipName + "._pth")
    shutil.move(zipName + ".zip", "Lib\\python.zip")

def getRuntimeDlls():
    download(PypiLinkGetter.getLink(VERSION, ARCH, "msvc-runtime"), "..\\msvc-runtime.whl")
    with zipfile.ZipFile("..\\msvc-runtime.whl") as zf:
        print("EXTRACT msvc-runtime.whl", flush=True)
        zf.extractall("..\\msvc-runtime")
    print("COPY msvc-runtime", flush=True)
    datafolder = glob.glob("..\\msvc-runtime\\*.data\\data\\")[0]
    for file in os.listdir(datafolder):
        if file.endswith(".dll"):
            shutil.copy(os.path.join(datafolder, file), ".")

def copyExeInfoFiles():
    shutil.copy(originalFolder + "\\standalone\\pyunity-editor.c", "..")
    shutil.copy(originalFolder + "\\standalone\\icons.ico", "..")
    shutil.copy(originalFolder + "\\standalone\\icons.rc", "..")
    shutil.copy(originalFolder + "\\standalone\\version.rc", "..")

def compileMsvc():
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

def compileMinGW():
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
        "-L.", f"-l{zipName}", f"-I{sys.base_prefix}\\include",
    ], stdout=sys.stdout, stderr=sys.stderr)

def archiveFolder():
    print(f"ZIP pyunity-editor.zip", flush=True)
    subprocess.call([
        "7z.exe", "a", "-mx=9",
        f"pyunity-editor.zip", mainFolder
    ], stdout=sys.stdout, stderr=sys.stderr)
    shutil.copy(f"pyunity-editor.zip", originalFolder)

    print(f"7Z pyunity-editor.7z", flush=True)
    subprocess.call([
        "7z.exe", "a", "-mx=9",
        f"pyunity-editor.7z", mainFolder
    ], stdout=sys.stdout, stderr=sys.stderr)
    shutil.copy(f"pyunity-editor.7z", originalFolder)

    print("SFX pyunity-editor.exe", flush=True)
    with open("pyunity-editor-install.exe", "wb+") as f1:
        with open(originalFolder + "\\standalone\\7z.sfx", "rb") as f2:
            shutil.copyfileobj(f2, f1)
        with open("pyunity-editor.7z", "rb") as f2:
            shutil.copyfileobj(f2, f1)
    shutil.copy("pyunity-editor-install.exe", originalFolder)

def main():
    workingDir = tempfile.mkdtemp()
    atexit.register(shutil.rmtree, workingDir)
    os.chdir(workingDir)
    print("Working directory:", workingDir)

    getEmbedPackage()
    getPyUnity()
    buildSrcPackage("pyunity", "pyunity-develop", "pyunity-package")
    buildSrcPackage("pyunity-editor", originalFolder, "editor-package")

    packageDir = os.path.join(workingDir, mainFolder)
    os.chdir(packageDir)
    installLibraries(packageDir)
    setupLibraries(packageDir)
    cleanPackageRoot()
    if MSVC_RUNTIME:
        getRuntimeDlls()

    copyExeInfoFiles()
    if "GITHUB_ACTIONS" in os.environ:
        compileMsvc()
    else:
        compileMinGW()

    os.chdir(workingDir)
    archiveFolder()
    if "GITHUB_ACTIONS" not in os.environ:
        input("Press Enter to continue ...")

if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        tracebackLines = traceback.format_exception(type(e), e, e.__traceback__)
        print("".join(tracebackLines), flush=True)
        raise SystemExit
    finally:
        print("Cleaning up", flush=True)
        os.chdir(originalFolder)
