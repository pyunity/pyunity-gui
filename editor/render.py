from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from pyunity import config
from pyunity.scenes import Scene
import pyunity as pyu
import copy
import time

class OpenGLFrame(QOpenGLWidget):
    SPACER = None
    def __init__(self):
        super(OpenGLFrame, self).__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
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

class Console(QWidget):
    SPACER = None
    def __init__(self):
        super(Console, self).__init__()
        self.entries = []
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.vbox_layout = QVBoxLayout(self)
        self.setLayout(self.vbox_layout)
    
        self.scroll_area = QScrollArea()
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setWidget(self)
    
    def add_entry(self, timestamp, level, text):
        entry = ConsoleEntry(timestamp, level, text)
        self.entries.append(entry)
        self.vbox_layout.addWidget(entry)
    
    def showEvent(self, event):
        super(Console, self).showEvent(event)
        self.setMaximumHeight(self.height())
        for i in range(10):
            self.add_entry(time.strftime("%Y-%m-%d %H:%M:%S"), pyu.Logger.OUTPUT, "Test")

class ConsoleEntry(QWidget):
    def __init__(self, timestamp, level, text):
        super(ConsoleEntry, self).__init__()
        self.hbox_layout = QHBoxLayout(self)
        self.setLayout(self.hbox_layout)
        self.label = QLabel()
        self.label.setText(timestamp + " |" + level.abbr + "| " + text)
        self.hbox_layout.addWidget(self.label)
