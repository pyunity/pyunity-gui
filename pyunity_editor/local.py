from pathlib import Path
import importlib.util
import sys

# Problem: Need to import `pyunity.resources` for splash
# image fetching, but that will load the entirety of
# pyunity and take a long time.
# Solution: Get the module of `pyunity` but don't execute
# it. Import `pyunity.resources` and `pyunity.logger`
# then reset and execute `pyunity` correctly later.

packageSpec = importlib.util.find_spec("pyunity")

def importModule(submodule):
    folder = packageSpec.submodule_search_locations[0]
    module = None
    for suffix in [".py", ".pyc"]:
        spec = importlib.util.spec_from_file_location(
            "pyunity." + submodule, Path(folder) / (submodule + suffix))
        if spec is None:
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            break
        except FileNotFoundError:
            module = None
    return module

# Import `pyunity.logger` into `pyunity.Logger` for
# use by `pyunity.resources`
logger = importModule("logger")
if logger is None:
    raise Exception("Could not load asset resolver: pyunity.logger failed to load")
sys.modules["pyunity.logger"] = logger
sys.modules["pyunity.Logger"] = logger

# Get module but don't execute `pyunity`
pyunity = importlib.util.module_from_spec(packageSpec)
sys.modules["pyunity"] = pyunity
resources = importModule("resources")
if resources is None:
    raise Exception("Could not load asset resolver: pyunity.resources failed to load")
sys.modules["pyunity.resources"] = resources
loaded = False

# Code for asset resolver
directory = Path.home() / ".pyunity" / ".editor"
if not directory.is_dir():
    directory.mkdir(parents=True)

package = Path(__file__).resolve().parent
if package.parent.name.endswith(".zip"):
    package = package.parent
    if not package.is_file():
        raise Exception("Cannot find egg file")
    resolver = resources.ZipAssetResolver(directory, package, __package__)
else:
    resolver = resources.PackageAssetResolver(directory, package)

def getPath(local):
    # Most Qt functions cannot take Path arguments
    return str(resolver.getPath(local))

def fixPackage():
    # Only load once
    global loaded
    if loaded:
        return
    sys.modules.pop("pyunity.Logger")
    packageSpec.loader.exec_module(sys.modules["pyunity"])
    loaded = True
