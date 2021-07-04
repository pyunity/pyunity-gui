from pyunity import Behaviour, SceneManager, Vector3

class Rotator(Behaviour):
    def Update(self, dt):
        self.transform.eulerAngles += Vector3(0, 90, 0) * dt

scene = SceneManager.AddScene("Main Scene")
scene.mainCamera.AddComponent(Rotator)