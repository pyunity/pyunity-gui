from pathlib import Path
from datetime import datetime
import os
import zipfile
import shutil

package = Path(__file__).resolve().parent
if not package.exists():
    package = package.parent
    if not package.is_file():
        raise Exception("Cannot find egg file")
    egg = True
else:
    egg = False
directory = Path.home() / ".pyunity" / ".editor"

def getPath(local):
    dest = directory / local
    if egg:
        with zipfile.ZipFile(package) as zf:
            src = (Path(__package__) / local).as_posix()
            if src not in zf.namelist():
                raise Exception(f"No resource at {package / src}")
            if dest.exists():
                ziptime = datetime(*zf.getinfo(src).date_time)
                if ziptime.timestamp() != dest.stat().st_mtime:
                    return dest
            out = zf.extract(src, directory)
            os.makedirs(dest.parent, exist_ok=True)
            shutil.move(out, dest.parent)
            shutil.rmtree(Path(out).parent)
            return str(dest)
    else:
        src = package / local
        if not src.exists():
            raise Exception(f"No resource at {src}")
        if dest.exists() and src.stat().st_mtime != dest.stat().st_mtime:
            return dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)
        return str(dest)
