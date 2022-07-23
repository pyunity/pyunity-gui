from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QFont
from pyunity import Loader, Logger, Scripts, SceneManager
import os
import glob

class FileTracker:
    font = QFont("Segoe UI", 12)
    states = {
        "modified": "Modifying",
        "deleted": "Deleting",
        "created": "Creating"
    }

    def __init__(self, app, path):
        self.app = app
        self.path = os.path.normpath(path)
        self.files = set(glob.glob(os.path.join(self.path, "**/*"), recursive=True))
        self.times = {file: os.stat(file)[8] for file in self.files}
        self.changed = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.check)
        self.project = Loader.LoadProject(self.path)

    def check(self):
        files2 = set(glob.glob(os.path.join(self.path, "**/*"), recursive=True))
        for file in self.files:
            if file not in files2:
                Logger.Log("Removed " + file)
                self.changed.append((file, "deleted"))
            elif self.times[file] < os.stat(file)[8]:
                Logger.Log("Modified " + file)
                self.changed.append((file, "modified"))
                self.times[file] = os.stat(file)[8]
        for file in files2 - self.files:
            Logger.Log("Created " + file)
            self.changed.append((file, "created"))
            self.times[file] = os.stat(file)[8]
        self.files = files2

        if self.app.activeWindow() is not None:
            scripts = []
            for file in self.changed:
                if file[0].endswith(".py"):
                    scripts.append(file[0])
                message = QMessageBox()
                message.setText(self.states[file[1]] + " " + file[0])
                message.setWindowTitle("Importing files...")
                message.setStandardButtons(QMessageBox.StandardButton.NoButton)
                message.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)
                QTimer.singleShot(2000, lambda: message.done(0))
                message.setFont(self.font)
                message.exec()

            if len(self.changed):
                if len(scripts):
                    Scripts.Reset()
                    Scripts.GenerateModule()
                    for file in self.project.filePaths:
                        if file.endswith(".py"):
                            fullpath = self.project.path / os.path.normpath(file)
                            Scripts.LoadScript(fullpath)
                selected = self.app.hierarchy_content.tree_widget.selectedItems()
                if len(selected):
                    prevIDs = []
                    for item in selected:
                        prevIDs.append(self.project._ids[item.gameObject])
                else:
                    prevIDs = None
                file = self.project.fileIDs[self.project._ids[self.app.loaded]].path
                SceneManager.RemoveScene(self.app.loaded)
                scene = Loader.LoadScene(self.project.path / file, self.project)
                self.app.loadScene(scene, prevIDs)

            self.changed = []

    def start(self, delay):
        self.check()
        self.timer.start(int(delay * 1000))

    def stop(self):
        self.timer.stop()
