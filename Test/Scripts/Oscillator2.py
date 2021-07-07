from pyunity import *
import math

class Oscillator2(Behaviour):
    a = 0
    speed = ShowInInspector(int, 10)
    def Update(self, dt):
        self.a += dt * self.speed / 10
        self.transform.localScale = Vector3.one() * (0.75 + math.sin(self.a) / 4)
