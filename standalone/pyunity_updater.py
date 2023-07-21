import traceback
import py_compile
import zipimport
import tempfile
import zipfile
import urllib.request
import ctypes
import shutil
import glob
import sys
import os

ZIP_OPTIONS = {"compression": zipfile.ZIP_DEFLATED, "compresslevel": 9}

originalFolder = os.getcwd()

class ZipFile(zipfile.ZipFile):
    def remove(self, zinfo_or_arcname):
        """Remove a member from the archive."""

        if self.mode not in ('w', 'x', 'a'):
            raise ValueError("remove() requires mode 'w', 'x', or 'a'")
        if not self.fp:
            raise ValueError(
                "Attempt to write to ZIP archive that was already closed")
        if self._writing:
            raise ValueError(
                "Can't write to ZIP archive while an open writing handle exists"
            )

        # Make sure we have an existing info object
        if isinstance(zinfo_or_arcname, zipfile.ZipInfo):
            zinfo = zinfo_or_arcname
            # make sure zinfo exists
            if zinfo not in self.filelist:
                raise KeyError(
                    'There is no item %r in the archive' % zinfo_or_arcname)
        else:
            # get the info object
            zinfo = self.getinfo(zinfo_or_arcname)

        return self._remove_members({zinfo})

    def _remove_members(self, members, *, remove_physical=True, chunk_size=2**20):
        """Remove members in a zip file.

        All members (as zinfo) should exist in the zip; otherwise the zip file
        will erroneously end in an inconsistent state.
        """
        fp = self.fp
        entry_offset = 0
        member_seen = False

        # get a sorted filelist by header offset, in case the dir order
        # doesn't match the actual entry order
        filelist = sorted(self.filelist, key=lambda x: x.header_offset)
        for i in range(len(filelist)):
            info = filelist[i]
            is_member = info in members

            if not (member_seen or is_member):
                continue

            # get the total size of the entry
            try:
                offset = filelist[i + 1].header_offset
            except IndexError:
                offset = self.start_dir
            entry_size = offset - info.header_offset

            if is_member:
                member_seen = True
                entry_offset += entry_size

                # update caches
                self.filelist.remove(info)
                try:
                    del self.NameToInfo[info.filename]
                except KeyError:
                    pass
                continue

            # update the header and move entry data to the new position
            if remove_physical:
                old_header_offset = info.header_offset
                info.header_offset -= entry_offset
                read_size = 0
                while read_size < entry_size:
                    fp.seek(old_header_offset + read_size)
                    data = fp.read(min(entry_size - read_size, chunk_size))
                    fp.seek(info.header_offset + read_size)
                    fp.write(data)
                    fp.flush()
                    read_size += len(data)

        # Avoid missing entry if entries have a duplicated name.
        # Reverse the order as NameToInfo normally stores the last added one.
        for info in reversed(self.filelist):
            self.NameToInfo.setdefault(info.filename, info)

        # update state
        if remove_physical:
            self.start_dir -= entry_offset
        self._didModify = True

        # seek to the start of the central dir
        fp.seek(self.start_dir)

def errorMessage(msg):
    if sys.stderr is not None:
        sys.stderr.write(msg + "\n")
    else:
        ctypes.windll.user32.MessageBoxW(None, msg, "PyUnity Updater error", 0x10)
    exit(1)

def infoMessage(msg):
    if sys.stdout is not None:
        sys.stdout.write(msg + "\n")
    else:
        ctypes.windll.user32.MessageBoxW(None, msg, "PyUnity Updater message", 0x40)

def fixModulePaths():
    # Replace all relative paths with absolute paths
    # TODO: Use absolute paths in C script instead of setting after Python initialization
    mainDir = os.path.abspath(".")
    for i in range(len(sys.path)):
        if sys.path[i].startswith("Lib\\"):
            sys.path[i] = os.path.join(mainDir, sys.path[i])

    removed = []
    new = {}
    for path, importer in sys.path_importer_cache.items():
        if isinstance(importer, zipimport.zipimporter):
            removed.append(path)
            newPath = os.path.join(mainDir, path)
            importer = zipimport.zipimporter(newPath)
            new[newPath] = importer
    for path in removed:
        sys.path_importer_cache.pop(path)
    for path in new:
        sys.path_importer_cache[path] = new[path]
    
    for module in sys.modules.values():
        if isinstance(module.__loader__, zipimport.zipimporter):
            newPath = os.path.join(mainDir, module.__loader__.archive, module.__loader__.prefix)
            loader = zipimport.zipimporter(newPath)
            module.__loader__ = loader
            module.__spec__.loader = loader
            module.__spec__.origin = os.path.join(mainDir, module.__spec__.origin)
            locations = module.__spec__.submodule_search_locations
            if locations is not None:
                for i in range(len(locations)):
                    locations[i] = os.path.join(mainDir, locations[i])

def getPyUnity():
    url = "https://nightly.link/pyunity/pyunity/workflows/windows/develop/purepython.zip"
    print("GET", url, "-> pyunity-artifact.zip", flush=True)
    urllib.request.urlretrieve(url, "pyunity-artifact.zip")
    with zipfile.ZipFile("pyunity-artifact.zip") as zf:
        print("EXTRACT pyunity-artifact.zip", flush=True)
        zf.extractall("pyunity-artifact")
    file = glob.glob("pyunity-artifact/*.whl")[0]
    with zipfile.ZipFile(file) as zf:
        print("EXTRACT", os.path.basename(file), flush=True)
        zf.extractall("pyunity-package")

def getPyUnityEditor():
    url = "https://nightly.link/pyunity/pyunity-gui/workflows/wheel/master/purepython.zip"
    print("GET", url, "-> editor-artifact.zip", flush=True)
    urllib.request.urlretrieve(url, "editor-artifact.zip")
    with zipfile.ZipFile("editor-artifact.zip") as zf:
        print("EXTRACT editor-artifact.zip", flush=True)
        zf.extractall("editor-artifact")
    file = glob.glob("editor-artifact/*.whl")[0]
    with zipfile.ZipFile(file) as zf:
        print("EXTRACT", os.path.basename(file), flush=True)
        zf.extractall("editor-package")

# copied from builder.py
def addPackage(zf, name, path, orig, distInfo=True):
    print("COMPILE", name, flush=True)
    os.chdir("..\\" + name)
    paths = glob.glob(path, recursive=True)
    if distInfo:
        paths.extend(glob.glob("*.dist-info\\**\\*", recursive=True))
    for file in paths:
        if file.endswith(".py"):
            py_compile.compile(file, file + "c", file, doraise=True)
            zf.write(file + "c")
        elif not file.endswith(".pyc"):
            zf.write(file)
    os.chdir(orig)

def updatePackages(workdir):
    getPyUnity()
    getPyUnityEditor()
    with ZipFile(os.path.dirname(__file__), "a", **ZIP_OPTIONS) as zf:
        removed = set()
        for file in zf.filelist:
            for folder in ["pyunity/", "pyunity-", "pyunity_editor/", "pyunity_editor-"]:
                if file.filename.startswith(folder):
                    removed.add(file)
                    break
        zf._remove_members(removed)

        os.chdir(os.path.join(workdir, "pyunity-package"))
        addPackage(zf, "pyunity-package", "pyunity\\**\\*", workdir)
        os.chdir(os.path.join(workdir, "editor-package"))
        addPackage(zf, "editor-package", "pyunity_editor\\**\\*", workdir)

def main():
    if not os.path.isfile("Lib\\python.zip"):
        errorMessage("Zip file not locatable")

    fixModulePaths()

    workdir = tempfile.mkdtemp()
    os.chdir(workdir)
    try:
        updatePackages(workdir)
        infoMessage("Updated packages successfully")
    except Exception as e:
        errorMessage("".join(traceback.format_exception(type(e), e, e.__traceback__)))
    finally:
        os.chdir(originalFolder)
        shutil.rmtree(workdir)

def installIntoZip():
    source = os.path.abspath(__file__)
    filename = os.path.basename(__file__)
    os.chdir(os.path.dirname(source))
    if not os.path.isfile("Lib\\python.zip"):
        errorMessage("Zip file not locatable")

    try:
        py_compile.compile(filename, filename + "c")
        with zipfile.ZipFile("Lib\\python.zip", "a") as zf:
            zf.write(filename + "c")
    except Exception as e:
        errorMessage("".join(traceback.format_exception(type(e), e, e.__traceback__)))
    else:
        infoMessage("Installed script successfully")
    finally:
        if os.path.isfile(filename + "c"):
            os.remove(filename + "c")

if __name__ == "__main__":
    source = os.path.abspath(__file__)
    if os.path.dirname(source).endswith(".zip"):
        main()
    else:
        installIntoZip()
