from pathlib import Path
from pyunity.resources import ZipAssetResolver, PackageAssetResolver

directory = Path.home() / ".pyunity" / ".editor"
if not directory.is_dir():
    directory.mkdir(parents=True)

package = Path(__file__).resolve().parent
if package.parent.name.endswith(".zip"):
    package = package.parent
    if not package.is_file():
        raise Exception("Cannot find egg file")
    resolver = ZipAssetResolver(directory, package, __package__)
else:
    resolver = PackageAssetResolver(directory, package)

def getPath(local):
    return str(resolver.getPath(local))
