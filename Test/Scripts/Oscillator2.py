from pyunity import *

class Oscillator2(Behaviour):
    a = 0
    speed = ShowInInspector(int, 10)
    def Update(self, dt):
        self.a += dt * self.speed / 10
        size = Mathf.LerpUnclamped(Mathf.Cos(self.a), 0.75, 1)
        self.transform.localScale = Vector3.one() * size
