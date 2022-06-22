import textwrap
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

def download(url, dest):
    print("GET", url, "->", os.path.basename(dest))
    directory = Path.home() / ".pyunity" / ".builder"
    directory.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(url.encode()).hexdigest()
    path = directory / (digest + ".bin")
    if not path.is_file():
        urllib.request.urlretrieve(url, path)
    shutil.copy(path, dest)

tmp = tempfile.mkdtemp()
orig = os.getcwd() + "\\"
os.chdir(tmp)
try:
    download(f"https://www.python.org/ftp/python/{version}/python-{version}-embed-{arch}.zip",
             "embed.zip")
    vername = f"pyunity-editor"
    os.makedirs(vername, exist_ok=True)
    with zipfile.ZipFile("embed.zip") as zf:
        print("EXTRACT embed.zip")
        zf.extractall(vername)

    urllib.request.urlretrieve("https://github.com/pyunity/pyunity/archive/refs/heads/develop.zip", "pyunity.zip")
    with zipfile.ZipFile("pyunity.zip") as zf:
        print("EXTRACT pyunity.zip")
        zf.extractall()
    print("BUILD pyunity")
    os.chdir("pyunity-develop")
    subprocess.call([sys.executable, "setup.py", "bdist_wheel"],
                    stdout=subprocess.DEVNULL, stderr=sys.stderr,
                    env={**os.environ, "cython": "0"})
    shutil.copy(glob.glob("dist/*")[0], "..\\pyunity.whl")

    os.chdir(tmp + "\\" + vername)
    zipname = "python" + "".join(version.split(".")[:2]) + ".zip"
    with zipfile.PyZipFile(zipname, "a", optimize=1) as zf:
        with zipfile.ZipFile("..\\pyunity.whl") as zf2:
            print("EXTRACT pyunity.whl")
            zf2.extractall("..\\pyunity")
        print("COMPILE", "pyunity")
        zf.writepy("..\\pyunity\\pyunity")
        for file in glob.glob("..\\pyunity\\**\\*", recursive=True):
            if file.endswith(".py") or file.endswith(".pyc"):
                continue
            zf.write(file, file[11:])

        print("COMPILE editor")
        zf.writepy(orig + "editor")
        for file in glob.glob(orig + "\\editor\\**\\*", recursive=True) + \
                glob.glob(orig + "\\pyunity_editor.egg-info\\**\\*", recursive=True):
            if file.endswith(".py") or file.endswith(".pyc"):
                continue
            zf.write(file, file[len(orig):])

        for name, url in wheels[0].items():
            download(url, "..\\" + name + ".whl")
            with zipfile.ZipFile("..\\" + name + ".whl") as zf2:
                print("EXTRACT " + name + ".whl")
                zf2.extractall("..\\" + name)
            for package in glob.glob("..\\" + name + "\\*\\__init__.py"):
                print("COMPILE", package[4 + len(name):-12].replace("\\", "."))
                zf.writepy(os.path.dirname(package))
            for file in glob.glob("..\\" + name + "\\**\\*", recursive=True):
                if file.endswith(".py") or file.endswith(".pyc"):
                    continue
                zf.write(file, file[len(name) + 4:])

    for name, url in wheels[1].items():
        download(url, "..\\" + name + ".whl")
        print("COPY", name)
        with zipfile.ZipFile("..\\" + name + ".whl") as zf2:
            zf2.extractall("Lib")

    with open("python" + "".join(version.split(".")[:2]) + "._pth") as f:
        contents = f.read()
    with open("python" + "".join(version.split(".")[:2]) + "._pth", "w") as f:
        f.write(".\\Lib\n" + contents)

    print("WRITE pyunity-editor.c")
    with open("pyunity-editor.c", "w+") as f:
        f.write(textwrap.dedent("""
        #define PY_SSIZE_T_CLEAN
        #define Py_LIMITED_API 0x03060000
        #include <Python.h>
        #include <string.h>

        int main(int argc, char **argv) {
            Py_Initialize();
            wchar_t **program = (wchar_t**)PyMem_Malloc(sizeof(wchar_t**) * argc);
            for (int i = 0; i < argc; i++) {
                program[i] = Py_DecodeLocale(argv[i], NULL);
            }
            if (program[0] == NULL) {
                fprintf(stderr, "Fatal error: cannot decode argv[0]\n");
                exit(1);
            }
            Py_SetProgramName(program[0]);  /* optional but recommended */
            PySys_SetArgvEx(argc, program, 0);

            PyObject *editor = PyImport_ImportModule("editor.cli");
            PyObject *func = PyObject_GetAttrString(editor, "run");

            PyObject *res = PyObject_CallFunction(func, NULL);
            if (res == NULL) {
                PyErr_Print();
                exit(1);
            }

            if (Py_FinalizeEx() < 0) {
                exit(1);
            }
            for (int i = 0; i < argc; i++) {
                PyMem_Free((void*)program[i]);
            }
            return 0;
        }
        """))

    print("COMPILE pyunity-editor.exe")
    if "GITHUB_ACTIONS" in os.environ:
        subprocess.call([
            "cl.exe", "/nologo", "/O2", "/Wall",
            "/Tcpyunity-editor.c", "/Fepyunity-editor.exe",
            f"/I{sys.base_prefix}\\include",
            "/link", f"/LIBPATH:{sys.base_prefix}\\libs"
        ], stdout=sys.stdout, stderr=sys.stderr)
    else:
        subprocess.call([
            "gcc.exe", "-O2", "-Wall",
            "-o", "pyunity-editor.exe", "pyunity-editor.c",
            "-L.", "-lpython310", f"-I{sys.base_prefix}\\include",
        ], stdout=sys.stdout, stderr=sys.stderr)
    os.remove("pyunity-editor.c")

    print(f"ZIP pyunity-editor.zip")
    os.chdir(tmp)
    subprocess.call([
        "7z.exe", "a", "-mx=9",
        f"pyunity-editor.zip", vername
    ], stdout=sys.stdout, stderr=sys.stderr)
    shutil.copy(f"pyunity-editor.zip", orig)

    print(f"7Z pyunity-editor.7z")
    subprocess.call([
        "7z.exe", "a", "-mx=9",
        f"pyunity-editor.7z", vername
    ], stdout=sys.stdout, stderr=sys.stderr)
    shutil.copy(f"pyunity-editor.7z", orig)

    if "GITHUB_ACTIONS" not in os.environ:
        input("Press Enter to continue ...")
finally:
    print("Cleaning up")
    os.chdir(orig)
    shutil.rmtree(tmp)
