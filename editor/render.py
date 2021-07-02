from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from pyunity import config
from pyunity.scenes import Scene
import pyunity as pyu

class OpenGLFrame(QOpenGLWidget):
    SPACER = None
    def __init__(self):
        super(OpenGLFrame, self).__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.scene = None
        
        # class Rotator(pyu.Behaviour):
        #     def Update(self, dt):
        #         self.transform.eulerAngles += pyu.Vector3(0, 90, 0) * dt

        self.default = Scene("Default Scene")
        # self.default.mainCamera.AddComponent(Rotator)
    
    def initializeGL(self):
        self.default.Start()
    
    def paintGL(self):
        if self.scene is not None:
            self.scene.update()
        else:
            self.default.update()
    
    def resizeGL(self, width, height):
        if self.scene is not None:
            self.scene.mainCamera.Resize(width, height)
        else:
            self.default.mainCamera.Resize(width, height)
        self.update()
    
    def stop(self):
        self.timer.stop()
        self.scene = False
    
    def start_scene(self, scene):
        self.scene = scene
        scene.Start()
        self.timer.start(1000 / config.fps)
