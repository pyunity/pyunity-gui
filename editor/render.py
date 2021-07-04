from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from pyunity import config
from pyunity.scenes import Scene
import pyunity as pyu
import copy

class OpenGLFrame(QOpenGLWidget):
    SPACER = None
    def __init__(self):
        super(OpenGLFrame, self).__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.scene = None

        self.default = Scene("Default Scene")
    
    def set_buttons(self, buttons):
        buttons.buttons[0].clicked.connect(
            lambda: self.start_scene(pyu.SceneManager.GetSceneByIndex(0)))
        buttons.buttons[2].clicked.connect(self.stop)
    
    def initializeGL(self):
        self.default.Start()
        self.timer.start(1000 / config.fps)
    
    def paintGL(self):
        if self.scene is not None:
            self.scene.update()
        else:
            self.default.mainCamera.Render(self.default.gameObjects)
    
    def resizeGL(self, width, height):
        if self.scene is not None:
            self.scene.mainCamera.Resize(width, height)
        else:
            self.default.mainCamera.Resize(width, height)
        self.update()
    
    def stop(self):
        self.scene = None
    
    def start_scene(self, scene):
        self.makeCurrent()
        self.default = scene
        self.scene = copy.deepcopy(scene)
        self.scene.Start()
        self.timer.start(1000 / config.fps)
