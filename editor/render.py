from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont, QIcon
from pyunity import config
import pyunity as pyu
import copy
import time

class OpenGLFrame(QOpenGLWidget):
    SPACER = None
    def __init__(self):
        super(OpenGLFrame, self).__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.console = None
        self.scene = None
        self.original = None
        self.paused = False
    
    def set_buttons(self, buttons):
        self.buttons = buttons.buttons
        self.buttons[0].clicked.connect(self.start_scene)
        self.buttons[1].clicked.connect(self.pause)
        self.buttons[2].clicked.connect(self.stop)
    
    def initializeGL(self):
        self.original.Start()
        self.timer.start(1000 / config.fps)
    
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
    
    def stop(self):
        if self.scene is not None:
            self.scene = None
            self.buttons[0].setChecked(False)
            self.buttons[1].setChecked(False)
            self.buttons[2].setChecked(True)
            self.paused = False
            if not self.timer.isActive():
                self.timer.start(1000 / config.fps)
        else:
            self.buttons[2].setChecked(True)
    
    def pause(self):
        if self.scene is None:
            self.paused = not self.paused
            return
        if self.timer.isActive():
            self.timer.stop()
            self.paused = True
        else:
            self.scene.lastFrame = time.time() - 1 / config.fps
            self.timer.start(1000 / config.fps)
            self.paused = False
    
    def start_scene(self):
        if self.scene is not None:
            self.stop()
        else:
            self.makeCurrent()
            self.scene = copy.deepcopy(self.original)
            self.scene.Start()
            self.scene.mainCamera.Resize(self.width(), self.height())
            self.buttons[2].setChecked(False)
            if self.paused:
                self.pause()
            self.console.clear()

class Console(QListWidget):
    SPACER = None
    def __init__(self):
        super(Console, self).__init__()
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.entries = []
        self.pending_entries = []
        self.clear_on_run = True
        pyu.Logger.LogLine = self.modded_log(pyu.Logger.LogLine)
    
    def add_entry(self, timestamp, level, text):
        entry = ConsoleEntry(timestamp, level, text)
        self.entries.append(entry)
        self.addItem(entry)
    
    def clear(self):
        if self.clear_on_run:
            num = len(self.entries)
            self.entries = []
            for i in range(num):
                entry = self.takeItem(0)
                del entry
    
    def modded_log(self, func):
        def inner(*args, **kwargs):
            timestamp, msg = func(*args, **kwargs, silent=True)
            self.pending_entries.append([timestamp, args[0], msg])
        return inner
    
    def on_switch(self):
        for entry in self.pending_entries:
            self.add_entry(*entry)
        self.pending_entries = []

class ConsoleEntry(QListWidgetItem):
    def __init__(self, timestamp, level, text):
        super(ConsoleEntry, self).__init__(QIcon(),
            "|" + level.abbr + "| " + text + "\n" + timestamp)
        self.setFont(QFont("Segoe UI", 14))
