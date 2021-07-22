from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont, QIcon
from pyunity import config
import pyunity as pyu
import os
import copy
import time


def patch(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            pyu.Logger.LogException(e)
    return inner

class OpenGLFrame(QOpenGLWidget):
    SPACER = None
    def __init__(self, parent):
        super(OpenGLFrame, self).__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.console = None
        self.scene = None
        self.original = None
        self.paused = False
    
    def set_buttons(self, buttons):
        self.buttons = buttons.buttons
        self.buttons[0].clicked.connect(self.start)
        self.buttons[1].clicked.connect(self.pause)
        self.buttons[2].clicked.connect(self.stop)
    
    def initializeGL(self):
        for renderer in self.original.FindComponentsByType(pyu.MeshRenderer):
            renderer.mesh.recompile()
    
    def paintGL(self):
        if self.scene is not None:
            self.scene.update()
        else:
            self.original.mainCamera.Render(self.original.gameObjects)
    
    def resizeGL(self, width, height):
        if self.scene is not None:
            self.scene.mainCamera.Resize(width, height)
        else:
            self.original.mainCamera.Resize(width, height)
        self.update()
    
    @patch
    def start(self, on):
        if self.scene is not None:
            self.stop()
        else:
            self.makeCurrent()
            self.scene = copy.deepcopy(self.original)
            self.scene.Start()
            self.scene.mainCamera.Resize(self.width(), self.height())
            self.buttons[2].setChecked(False)
            print(self.paused)
            if self.console.clear_on_run:
                self.console.clear()
            if not self.paused:
                self.timer.start(1000 / config.fps)
    
    @patch
    def stop(self, on):
        if self.scene is not None:
            self.scene = None
            self.buttons[0].setChecked(False)
            self.buttons[1].setChecked(False)
            self.buttons[2].setChecked(True)
            self.paused = False
            self.update()
            self.timer.stop()
        else:
            self.buttons[2].setChecked(True)
    
    def pause(self, on):
        self.paused = not self.paused
        if self.scene is not None:
            if self.paused:
                self.timer.stop()
            else:
                self.scene.lastFrame = time.time() - 1 / config.fps
                self.timer.start(1000 // config.fps)
    
    def on_switch(self):
        self.console.timer.stop()

class Console(QListWidget):
    SPACER = None
    def __init__(self, parent):
        super(Console, self).__init__(parent)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setIconSize(QSize(100, 100))
        self.entries = []
        self.pending_entries = []
        self.clear_on_run = True

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_switch)
        pyu.Logger.LogLine = self.modded_log(pyu.Logger.LogLine)
    
    def add_entry(self, timestamp, level, text):
        entry = ConsoleEntry(timestamp, level, text)
        self.entries.append(entry)
        self.addItem(entry)
    
    def clear(self):
        num = len(self.entries)
        self.entries = []
        for i in range(num):
            entry = self.takeItem(0)
            entry.deleteLater()
    
    def modded_log(self, func):
        def inner(*args, **kwargs):
            timestamp, msg = func(*args, **kwargs, silent=True)
            if args[0] != pyu.Logger.DEBUG:
                self.pending_entries.append([timestamp, args[0], msg])
            return timestamp, msg
        return inner
    
    def on_switch(self):
        self.pending_entries = self.pending_entries[-100:]
        for entry in self.pending_entries:
            self.add_entry(*entry)
        self.pending_entries = []
        self.timer.start(250)

class ConsoleEntry(QListWidgetItem):
    icon_map = {
        pyu.Logger.ERROR: "error.png",
        pyu.Logger.INFO: "info.png",
        pyu.Logger.OUTPUT: "output.png",
        pyu.Logger.WARN: "warning.png"
    }
    def __init__(self, timestamp, level, text):
        super(ConsoleEntry, self).__init__(
            "|" + level.abbr + "| " + text + "\n" + timestamp)
        self.setFont(QFont("Segoe UI", 14))
        directory = os.path.dirname(os.path.abspath(__file__))
        self.setIcon(QIcon(os.path.join(directory,
            "icons", "console", ConsoleEntry.icon_map[level])))
