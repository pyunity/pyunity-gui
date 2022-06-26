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

if shutil.which("7z.exe") is None:
    raise Exception("7Zip is needed to build the PyUnity Editor.")
if "GITHUB_ACTIONS" in os.environ:
    if shutil.which("cl.exe") is None:
        raise Exception("Microsoft Visual C is needed to build the PyUnity Editor.")
elif shutil.which("gcc.exe") is None:
    raise Exception("MinGW-w64 is needed to build the PyUnity Editor.")

MSVC_RUNTIME = False
version = "3.10.5"
arch = "amd64"
zipoptions = {"compression": zipfile.ZIP_DEFLATED, "compresslevel": 9}
wheels = [
    {
        "pyopengl": "https://files.pythonhosted.org/packages/80/07/003fe74d2af04be917035b42c53c7ea9e3abe1e353753cebccfe792b4e52/PyOpenGL-3.1.6-py3-none-any.whl",
        "pysdl2": "https://files.pythonhosted.org/packages/ea/38/9cd6726c591805f79255310232a912e7c4f57e9e6ad05b74d28dd263b29e/PySDL2-0.9.11-py3-none-any.whl",
    },
    {
        "pyopengl_accelerate": "https://files.pythonhosted.org/packages/f3/a5/ce94f5df7f411b2a44a469859f3a77c8938dc428d229ecbf635fc6358a3f/PyOpenGL_accelerate-3.1.6-cp310-cp310-win_amd64.whl",
        "pysdl2_dll": "https://files.pythonhosted.org/packages/b7/6f/37cdee2957043f0f53b4c49fe819a8c7d3f2e37e6fe452b49cfd5615c344/pysdl2_dll-2.0.20-py2.py3-none-win_amd64.whl",
        "pillow": "https://files.pythonhosted.org/packages/0a/f8/f4a5e9c5f35fbb2e3bfd9b9596d0937e8242ae14ae4172da12dd770c7bdc/Pillow-9.1.1-cp310-cp310-win_amd64.whl",
        "pyglm": "https://files.pythonhosted.org/packages/6f/be/1e68bda30770478e9769190ac0f803221bc55b496491aadd2fe85ea35839/PyGLM-2.5.7-cp310-cp310-win_amd64.whl",
        "pyside6": "https://files.pythonhosted.org/packages/af/fa/233b09b5952c83896ce54987f709ec83050ba1555dd4af54b114bceb2a1f/PySide6-6.3.1-cp36-abi3-win_amd64.whl",
        "shiboken6": "https://files.pythonhosted.org/packages/c0/23/3ce3122a30da4fa8477368627f03ac470daadbd95123b29e7dede83cbb15/shiboken6-6.3.1-cp36-abi3-win_amd64.whl",
        "pyside6_essentials": "https://files.pythonhosted.org/packages/37/4c/dd461414d4ac9716df049f7ab56107eae16b3768049d1feedc3f51550e28/PySide6_Essentials-6.3.1-cp36-abi3-win_amd64.whl",
        "glfw": "https://files.pythonhosted.org/packages/85/c1/42d1cad8a16bba14e2bf3240931cdfa06c3bcb456f2a81636ec7f0a40172/glfw-2.5.3-py2.py27.py3.py30.py31.py32.py33.py34.py35.py36.py37.py38-none-win_amd64.whl",
    }
]

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
        addPackage(zf, "editor", "editor\\**\\*", workdir, "pyunity_editor")

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
