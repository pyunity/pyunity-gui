from PyQt5.QtCore import QTimer
import os
import glob
import enum

class FileState(enum.Enum):
    CREATED = enum.auto()
    MODIFIED = enum.auto()
    DELETED = enum.auto()

class FileTracker:
    def __init__(self, path):
        self.path = path
        self.files = set(glob.glob(os.path.join(self.path, "**/*"), recursive=True))
        self.times = {file: os.stat(file)[8] for file in self.files}
        self.changed = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.check)
    
    def check(self):
        files2 = set(glob.glob(os.path.join(self.path, "**/*"), recursive=True))
        for file in self.files:
            if file not in files2:
                print("Removed " + file)
                self.changed.append((file, FileState.DELETED))
            elif self.times[file] < os.stat(file)[8]:
                print("Modified " + file)
                self.changed.append((file, FileState.MODIFIED))
                self.times[file] = os.stat(file)[8]
        for file in files2 - self.files:
            print("Created " + file)
            self.changed.append((file, FileState.CREATED))
            self.times[file] = os.stat(file)[8]
        self.files = files2
    
    def start(self, delay):
        self.timer.start(delay * 1000)
