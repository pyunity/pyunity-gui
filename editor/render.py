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
        self.default = SceneManager.AddScene("Scene")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
    
    def initializeGL(self):
        global frame
        frame = self
        self.default.Start()
    
    def paintGL(self):
        if window is not None:
            window.update_func()
        else:
            self.default.update()
    
    def resizeGL(self, width, height):
        if window is not None:
            window.resize(width, height)
        else:
            self.default.mainCamera.Resize(width, height)
        self.update()
    
    def stop(self):
        window.timer.stop()
    
    def start_scene(self, scene):
        SceneManager.LoadScene(scene)

class Window:
    def __init__(self, name, resize):
        global window
        window = self
        self.resize = resize

    def quit(self):
        global window
        del window

    def start(self, update_func):
        frame.makeCurrent()
        self.update_func = update_func
        frame.timer.start(1000 / config.fps)
