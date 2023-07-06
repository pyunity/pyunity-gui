from pyunity import *

class Oscillator(Behaviour):
    a = 0
    speed = ShowInInspector(int, 5)
    renderer = ShowInInspector(MeshRenderer)
    def Start(self):
        self.renderer.mat = Material(RGB(255, 0, 0))

    def Update(self, dt):
        self.a += dt * self.speed / 10
        self.renderer.mat.color = HSV(self.a % 3 * 360, 100, 100)
