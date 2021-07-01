from PyQt5.QtWidgets import *
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
        t = threading.Timer(5, lambda: SceneManager.LoadSceneByIndex(0))
        t.start()
    
    def paintGL(self):
        if window is not None:
            window.update_func()

class Window:
    def __init__(self, name, resize):
        global window
        window = self
        self.resize = resize

    def quit(self):
        pass

    def start(self, update_func):
        self.update_func = update_func
        clock = Clock()
        clock.Start(config.fps)
        self.done = False
        while not self.done:
            frame.update()
            clock.Maintain()

        self.quit()
