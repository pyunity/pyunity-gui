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
            self.scene.lastFrame = time.time()
            self.timer.start(1000 / config.fps)
            self.paused = False
    
    def start_scene(self):
        if self.scene is not None:
            self.stop()
        else:
            self.makeCurrent()
            self.scene = copy.deepcopy(self.original)
            self.scene.Start()
            self.buttons[2].setChecked(False)
            if self.paused:
                self.pause()
