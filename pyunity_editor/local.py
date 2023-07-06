from pathlib import Path
import importlib.util
import sys

packageSpec = importlib.util.find_spec("pyunity")

def importModule(submodule):
    folder = packageSpec.submodule_search_locations[0]
    spec = importlib.util.spec_from_file_location(
        "pyunity." + submodule, Path(folder) / (submodule + ".py"))
    if spec is None:
        raise Exception("Could not load asset resolver")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

logger = importModule("logger")
sys.modules["pyunity.logger"] = logger
sys.modules["pyunity.Logger"] = logger

pyunity = importlib.util.module_from_spec(packageSpec)
sys.modules["pyunity"] = pyunity
resources = importModule("resources")
sys.modules["pyunity.resources"] = resources
loaded = False

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
    return str(resolver.getPath(local))

def fixPackage():
    global loaded
    if loaded:
        return
    packageSpec.loader.exec_module(sys.modules["pyunity"])
    loaded = True
