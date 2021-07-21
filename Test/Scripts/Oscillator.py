from pyunity import *
import math

class Oscillator(Behaviour):
    a = 0
    speed = ShowInInspector(int, 5)
    renderer = ShowInInspector(MeshRenderer)

    def Start(self):
        raise Exception

    def Update(self, dt):
        self.a += dt * self.speed / 10
        x = 255 * (1 - abs((self.a % 3 * 2) % 2 - 1))
        period = int(self.a % 3 * 2)
        if period == 0:
            color = Vector3(255, x, 0)
        elif period == 1:
            color = Vector3(x, 255, 0)
        elif period == 2:
            color = Vector3(0, 255, x)
        elif period == 3:
            color = Vector3(0, x, 255)
        elif period == 4:
            color = Vector3(x, 0, 255)
        elif period == 5:
            color = Vector3(255, 0, x)
        self.renderer.mat.color = Color(*color)
        Logger.Log(self.renderer.mat.color)
