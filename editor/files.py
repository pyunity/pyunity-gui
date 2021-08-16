from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QFont
from pyunity import Loader, Logger
import os
import glob
import enum

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
