from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QFont
from pyunity import Loader, Logger
from pathlib import Path
import os
import glob
import enum
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
    if dest.exists():
        return str(dest)
    if egg:
        with zipfile.ZipFile(package) as zf:
            src = str(Path(__package__) / local)
            if src not in zf.namelist():
                raise Exception(f"No resource at {package / src}")
            out = zf.extract(src, directory)
            shutil.move(out, dest)
            shutil.rmtree(Path(out).parent)
            return str(dest)
    else:
        src = package / local
        if not src.exists():
            raise Exception(f"No resource at {src}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)
        return str(dest)

class FileState(enum.Enum):
    CREATED = enum.auto()
    MODIFIED = enum.auto()
    DELETED = enum.auto()

class FileTracker:
    font = QFont("Segoe UI", 12)
    def __init__(self, app, path):
        self.app = app
        self.path = path
        self.files = set(glob.glob(os.path.join(self.path, "**/*"), recursive=True))
        self.times = {file: os.stat(file)[8] for file in self.files}
        self.changed = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.check)
        self.project = Loader.LoadProject(path)

    def check(self):
        files2 = set(glob.glob(os.path.join(self.path, "**/*"), recursive=True))
        for file in self.files:
            if file not in files2:
                Logger.Log("Removed " + file)
                self.changed.append((file, FileState.DELETED))
            elif self.times[file] < os.stat(file)[8]:
                Logger.Log("Modified " + file)
                self.changed.append((file, FileState.MODIFIED))
                self.times[file] = os.stat(file)[8]
        for file in files2 - self.files:
            Logger.Log("Created " + file)
            self.changed.append((file, FileState.CREATED))
            self.times[file] = os.stat(file)[8]
        self.files = files2

        if self.app.activeWindow() is not None:
            for file in self.changed:
                message = QMessageBox()
                message.setText(
                    file[1].name.lower().capitalize().replace("ed", "ing") + \
                        " " + file[0])
                message.setWindowTitle("Importing files...")
                message.setStandardButtons(QMessageBox.StandardButton.NoButton)
                message.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)
                QTimer.singleShot(2000, lambda: message.done(0))
                message.setFont(self.font)
                message.exec()
            self.changed = []

    def start(self, delay):
        self.check()
        self.timer.start(delay * 1000)

    def stop(self):
        self.timer.stop()
