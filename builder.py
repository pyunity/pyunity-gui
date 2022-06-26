import textwrap
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

if shutil.which("7z.exe") is None:
    raise Exception("7Zip is needed to build the PyUnity Editor.")
if "GITHUB_ACTIONS" in os.environ:
    if shutil.which("cl.exe") is None:
        raise Exception("Microsoft Visual C is needed to build the PyUnity Editor.")
elif shutil.which("gcc.exe") is None:
    raise Exception("MinGW-w64 is needed to build the PyUnity Editor.")

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
            finder = PackageFinder.create(cls.collector, cls.prefs, target,
                                          use_deprecated_html5lib=False)
            cls.finders[vertuple, platform] = finder
        else:
            finder = cls.finders[vertuple, platform]
        return finder.find_requirement(install_req_from_line(req), False).link._url

MSVC_RUNTIME = False
version = "3.10.5"
arch = "amd64"
zipoptions = {"compression": zipfile.ZIP_DEFLATED, "compresslevel": 9}

wheels = [{}, {}]
for req in ["pyopengl", "pysdl2"]:
    wheels[0][req] = PypiLinkGetter.getLink(version, arch, req)
for req in ["pyopengl_accelerate", "pysdl2_dll", "pillow", "pyglm",
        "pyside6", "shiboken6", "pyside6_essentials", "glfw"]:
    wheels[1][req] = PypiLinkGetter.getLink(version, arch, req)

class PyZipFile(zipfile.PyZipFile):
    """Class to create ZIP archives with Python library files and packages."""

    def __init__(self, file, mode="r", compression=zipfile.ZIP_STORED,
                 allowZip64=True, optimize=-1, compresslevel=None):
        zipfile.ZipFile.__init__(self, file, mode=mode, compression=compression,
                         allowZip64=allowZip64, compresslevel=compresslevel)
        self._optimize = optimize

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
        "__init__.pyc", "QtCore.pyd", "QtGui.pyd", "QtOpenGL.pyd",
        "QtOpenGLWidgets.pyd", "QtWidgets.pyd", "pyside6.abi3.dll",
        "Qt6Core.dll", "Qt6Gui.dll", "Qt6OpenGL.dll",
        "Qt6OpenGLWidgets.dll", "Qt6Widgets.dll", "plugins\\platforms\\qwindows.dll"
    ]
    for dir, subdirs, files in os.walk("Lib\\PySide6\\", topdown=False):
        for name in files:
            path = os.path.join(dir, name)
            if path[12:] not in keep:
                os.remove(path)
        if len(os.listdir(dir)) == 0:
            os.rmdir(dir)

def addPackage(zf, name, path, orig, eggInfo=""):
    print("COMPILE", name, flush=True)
    os.chdir("..\\" + name)
    paths = glob.glob(path, recursive=True)
    if eggInfo:
        paths.extend(glob.glob(eggInfo + ".egg-info\\**\\*", recursive=True))
    for file in paths:
        if file.endswith(".py"):
            py_compile.compile(file, file + "c", file,
                            doraise=True, optimize=1)
            zf.write(file + "c")
        elif not file.endswith(".pyc"):
            zf.write(file)
    os.chdir(orig)

tmp = tempfile.mkdtemp()
orig = os.getcwd() + "\\"
os.chdir(tmp)
try:
    download(f"https://www.python.org/ftp/python/{version}/python-{version}-embed-{arch}.zip",
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
    subprocess.call([sys.executable, "setup.py", "bdist_wheel"],
                    stdout=subprocess.DEVNULL, stderr=sys.stderr,
                    env={**os.environ, "cython": "0"})
    shutil.move(glob.glob("dist/*")[0], "..\\pyunity.whl")
    os.chdir(tmp)

    with zipfile.ZipFile("pyunity.whl") as zf:
        print("EXTRACT pyunity.whl", flush=True)
        zf.extractall("pyunity")

    print("BUILD pyunity-editor", flush=True)
    os.chdir(orig)
    subprocess.call([sys.executable, "setup.py", "bdist_wheel"],
                    stdout=subprocess.DEVNULL, stderr=sys.stderr)
    shutil.move(glob.glob("dist/*")[0], tmp + "\\pyunity-editor.whl")
    os.chdir(tmp)

    with zipfile.ZipFile("pyunity-editor.whl") as zf:
        print("EXTRACT pyunity-editor.whl", flush=True)
        zf.extractall("editor")

    workdir = tmp + "\\" + vername
    os.chdir(workdir)

    zipname = "python" + "".join(version.split(".")[:2])
    with PyZipFile(zipname + ".zip", "a", optimize=1, **zipoptions) as zf:
        addPackage(zf, "pyunity", "pyunity\\**\\*", workdir, "pyunity")
        addPackage(zf, "editor", "pyunity_editor\\**\\*", workdir, "pyunity_editor")

        for name, url in wheels[0].items():
            download(url, "..\\" + name + ".whl")
            with zipfile.ZipFile("..\\" + name + ".whl") as zf2:
                print("EXTRACT " + name + ".whl", flush=True)
                zf2.extractall("..\\" + name)
            addPackage(zf, name, "**\\*", workdir)

    for name, url in wheels[1].items():
        download(url, "..\\" + name + ".whl")
        print("COPY", name, flush=True)
        with zipfile.ZipFile("..\\" + name + ".whl") as zf2:
            zf2.extractall("Lib")

    print("COMPILE Lib")
    os.chdir("Lib")
    for file in glob.glob("**\\*.py", recursive=True):
        py_compile.compile(file, file + "c", optimize=1, quiet=0)
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
        download("https://files.pythonhosted.org/packages/6d/4a/602120a9e6625169fbddbdd036fe5559af638986dc0c3c3b602d3d60f95e/msvc_runtime-14.29.30133-cp310-cp310-win_amd64.whl", "..\\msvc_runtime.whl")
        with zipfile.ZipFile("..\\msvc_runtime.whl") as zf:
            print("EXTRACT msvc_runtime.whl", flush=True)
            zf.extractall("..\\msvc_runtime")
        datafolder = glob.glob("..\\msvc_runtime\\*.data\\data\\")[0]
        print("COPY msvc_runtime", flush=True)
        for file in os.listdir(datafolder):
            if file.endswith(".dll"):
                shutil.copy(os.path.join(datafolder, file), ".")

    print("WRITE pyunity-editor.c", flush=True)
    with open("pyunity-editor.c", "w+") as f:
        f.write(textwrap.dedent("""
        #define PY_SSIZE_T_CLEAN
        #define Py_LIMITED_API 0x03060000
        #include <Python.h>
        #include <string.h>
        #define CHECK(n) if (n == NULL) { PyErr_Print(); exit(1); }

        int main(int argc, char **argv) {
            wchar_t *path = Py_DecodeLocale("Lib\\\\python.zip;Lib", NULL);
            Py_SetPath(path);
            wchar_t **program = (wchar_t**)malloc(sizeof(wchar_t**) * argc);
            for (int i = 0; i < argc; i++) {
                program[i] = Py_DecodeLocale(argv[i], NULL);
            }
            if (program[0] == NULL) {
                fprintf(stderr, "Fatal error: cannot decode argv[0]\\n");
                exit(1);
            }
            Py_SetProgramName(program[0]);
            Py_Initialize();
            PySys_SetArgvEx(argc, program, 0);

            PyObject *editor = PyImport_ImportModule("pyunity_editor.cli");
            CHECK(editor)
            #ifdef NOCONSOLE
            PyObject *func = PyObject_GetAttrString(editor, "gui");
            #else
            PyObject *func = PyObject_GetAttrString(editor, "run");
            #endif
            CHECK(func)

            PyObject *res = PyObject_CallFunction(func, NULL);
            CHECK(res)

            if (Py_FinalizeEx() < 0) {
                exit(1);
            }
            for (int i = 0; i < argc; i++) {
                free((void*)program[i]);
            }
            free((void*)program);
            free((void*)path);
            return 0;
        }

        #ifdef NOCONSOLE
        #include <windows.h>
        int __stdcall WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance,
                char* pCmdLine, int nShowCmd) {
            return main(__argc, __argv);
        }
        #endif
        """))

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
            "/Tcpyunity-editor.c", "/Fo..\\pyunity-editor.obj",
            f"/I{sys.base_prefix}\\include", "/DNOCONSOLE",
            "/link", "..\\icons.res", "..\\version.res", "/subsystem:windows",
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
            "-o", "pyunity-editor.exe", "pyunity-editor.c", "..\\icons.o", "..\\version.o",
            "-L.", f"-l{zipname}", f"-I{sys.base_prefix}\\include",
        ], stdout=sys.stdout, stderr=sys.stderr)
    os.remove("pyunity-editor.c")

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
