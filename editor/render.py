from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from pyunity import SceneManager, config, Clock
import sys
import threading

config.windowProvider = sys.modules[__name__]
frame = None
window = None

class OpenGLFrame(QOpenGLWidget):
    SPACER = None
    def __init__(self):
        super(OpenGLFrame, self).__init__()
        self.scene = SceneManager.AddScene("Scene")
    
    def initializeGL(self):
        global frame
        frame = self
        SceneManager.LoadSceneByIndex(0)
    
    def paintGL(self):
        if window is not None:
            window.update_func()
    
    def resizeGL(self, width, height):
        if window is not None:
            window.resize(width, height)
            self.update()

class Window:
    def __init__(self, name, resize):
        global window
        window = self
        self.resize = resize

    def quit(self):
        pass

    def start(self, update_func):
        frame.makeCurrent()
        self.update_func = update_func
        self.timer = QTimer(frame)
        self.timer.timeout.connect(frame.update)
        self.timer.start(config.fps)
