from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont, QIcon
from pyunity import config
import pyunity as pyu
import os
import copy
import time

def logPatch(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            pyu.Logger.LogException(e)
    return inner

class OpenGLFrame(QOpenGLWidget):
    SPACER = None
    def __init__(self, parent):
        super(OpenGLFrame, self).__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.console = None
        self.scene = None
        self.original = None
        self.paused = False
        self.file_tracker = None
    
    @property
    def winObj(self):
        return pyu.SceneManager.windowObject
    
    @winObj.setter
    def winObj(self, val):
        pyu.SceneManager.windowObject = val
    
    def set_buttons(self, buttons):
        self.buttons = buttons.buttons
        self.buttons[0].clicked.connect(self.start)
        self.buttons[1].clicked.connect(self.pause)
        self.buttons[2].clicked.connect(self.stop)
    
    def initializeGL(self):
        self.winObj = WidgetWindow(
            self.original.name, self.original.mainCamera.Resize)
        self.original.mainCamera.setup_buffers()
        for renderer in self.original.FindComponentsByType(pyu.MeshRenderer):
            renderer.mesh.compile()
    
    def paintGL(self):
        if self.scene is not None:
            self.scene.update()
            self.winObj.check_keys()
            self.winObj.check_mouse()
        else:
            self.original.Render()
    
    def resizeGL(self, width, height):
        if self.scene is not None:
            self.scene.mainCamera.Resize(width, height)
        else:
            self.original.mainCamera.Resize(width, height)
        self.update()
    
    mousemap = {
        Qt.LeftButton: pyu.MouseCode.Left,
        Qt.RightButton: pyu.MouseCode.Right,
        Qt.MiddleButton: pyu.MouseCode.Middle,
    }

    keymap = {
        Qt.Key_A: pyu.KeyCode.A,
        Qt.Key_B: pyu.KeyCode.B,
        Qt.Key_C: pyu.KeyCode.C,
        Qt.Key_D: pyu.KeyCode.D,
        Qt.Key_E: pyu.KeyCode.E,
        Qt.Key_F: pyu.KeyCode.F,
        Qt.Key_G: pyu.KeyCode.G,
        Qt.Key_H: pyu.KeyCode.H,
        Qt.Key_I: pyu.KeyCode.I,
        Qt.Key_J: pyu.KeyCode.J,
        Qt.Key_K: pyu.KeyCode.K,
        Qt.Key_L: pyu.KeyCode.L,
        Qt.Key_M: pyu.KeyCode.M,
        Qt.Key_N: pyu.KeyCode.N,
        Qt.Key_O: pyu.KeyCode.O,
        Qt.Key_P: pyu.KeyCode.P,
        Qt.Key_Q: pyu.KeyCode.Q,
        Qt.Key_R: pyu.KeyCode.R,
        Qt.Key_S: pyu.KeyCode.S,
        Qt.Key_T: pyu.KeyCode.T,
        Qt.Key_U: pyu.KeyCode.U,
        Qt.Key_V: pyu.KeyCode.V,
        Qt.Key_W: pyu.KeyCode.W,
        Qt.Key_X: pyu.KeyCode.X,
        Qt.Key_Y: pyu.KeyCode.Y,
        Qt.Key_Z: pyu.KeyCode.Z,
        Qt.Key_Space: pyu.KeyCode.Space,
        Qt.Key_0: pyu.KeyCode.Alpha0,
        Qt.Key_1: pyu.KeyCode.Alpha1,
        Qt.Key_2: pyu.KeyCode.Alpha2,
        Qt.Key_3: pyu.KeyCode.Alpha3,
        Qt.Key_4: pyu.KeyCode.Alpha4,
        Qt.Key_5: pyu.KeyCode.Alpha5,
        Qt.Key_6: pyu.KeyCode.Alpha6,
        Qt.Key_7: pyu.KeyCode.Alpha7,
        Qt.Key_8: pyu.KeyCode.Alpha8,
        Qt.Key_9: pyu.KeyCode.Alpha9,
        Qt.Key_F1: pyu.KeyCode.F1,
        Qt.Key_F2: pyu.KeyCode.F2,
        Qt.Key_F3: pyu.KeyCode.F3,
        Qt.Key_F4: pyu.KeyCode.F4,
        Qt.Key_F5: pyu.KeyCode.F5,
        Qt.Key_F6: pyu.KeyCode.F6,
        Qt.Key_F7: pyu.KeyCode.F7,
        Qt.Key_F8: pyu.KeyCode.F8,
        Qt.Key_F9: pyu.KeyCode.F9,
        Qt.Key_F10: pyu.KeyCode.F10,
        Qt.Key_F11: pyu.KeyCode.F11,
        Qt.Key_F12: pyu.KeyCode.F12,
        # Qt.Key_: pyu.KeyCode.Keypad0,
        # Qt.Key_: pyu.KeyCode.Keypad1,
        # Qt.Key_: pyu.KeyCode.Keypad2,
        # Qt.Key_: pyu.KeyCode.Keypad3,
        # Qt.Key_: pyu.KeyCode.Keypad4,
        # Qt.Key_: pyu.KeyCode.Keypad5,
        # Qt.Key_: pyu.KeyCode.Keypad6,
        # Qt.Key_: pyu.KeyCode.Keypad7,
        # Qt.Key_: pyu.KeyCode.Keypad8,
        # Qt.Key_: pyu.KeyCode.Keypad9,
        Qt.Key_Up: pyu.KeyCode.Up,
        Qt.Key_Down: pyu.KeyCode.Down,
        Qt.Key_Left: pyu.KeyCode.Left,
        Qt.Key_Right: pyu.KeyCode.Right,
    }

    def mouseMoveEvent(self, event):
        super(OpenGLFrame, self).mouseMoveEvent(event)
        self.winObj.mpos = [event.x(), event.y()]
    
    def mousePressEvent(self, event):
        super(OpenGLFrame, self).mousePressEvent(event)
        self.winObj.mbuttons[self.mousemap[event.button()]] = pyu.KeyState.DOWN
    
    def mouseReleaseEvent(self, event):
        super(OpenGLFrame, self).mouseReleaseEvent(event)
        self.winObj.mbuttons[self.mousemap[event.button()]] = pyu.KeyState.UP
    
    def keyPressEvent(self, event):
        super(OpenGLFrame, self).keyPressEvent(event)
        if event.key() not in self.keymap:
            return
        self.winObj.keys[self.keymap[event.key()]] = pyu.KeyState.DOWN
    
    def keyReleaseEvent(self, event):
        super(OpenGLFrame, self).keyReleaseEvent(event)
        if event.key() not in self.keymap:
            return
        self.winObj.keys[self.keymap[event.key()]] = pyu.KeyState.UP
    
    @logPatch
    def start(self, on):
        if self.scene is not None:
            self.stop()
        else:
            self.makeCurrent()
            self.scene = copy.deepcopy(self.original)
            self.winObj = WidgetWindow(
                self.scene.name, self.scene.mainCamera.Resize)
            self.scene.Start()
            self.scene.mainCamera.Resize(self.width(), self.height())
            self.buttons[2].setChecked(False)
            if self.console.clear_on_run:
                self.console.clear()
            if not self.paused:
                self.timer.start(1000 / config.fps)
            self.file_tracker.stop()
    
    @logPatch
    def stop(self, on):
        if self.scene is not None:
            self.scene = None
            self.buttons[0].setChecked(False)
            self.buttons[1].setChecked(False)
            self.buttons[2].setChecked(True)
            self.paused = False
            self.update()
            self.file_tracker.start(5)
        else:
            self.buttons[2].setChecked(True)
    
    def pause(self, on):
        self.paused = not self.paused
        if self.scene is not None:
            if self.paused:
                self.timer.stop()
            else:
                self.scene.lastFrame = time.time() - 1 / config.fps
                self.timer.start(1000 // config.fps)
    
    def save(self):
        pyu.Logger.Log(self.original.ids)
        pyu.Loader.ResaveScene(self.original, self.file_tracker.project)
    
    def on_switch(self):
        self.console.timer.stop()

class WidgetWindow(pyu.Window.ABCWindow):
    def __init__(self, name, resize):
        self.name = name
        self.resize = resize
        self.mpos = [0, 0]
        self.mbuttons = [pyu.KeyState.NONE, pyu.KeyState.NONE, pyu.KeyState.NONE]
        self.keys = [pyu.KeyState.NONE for i in range(pyu.KeyCode.Right + 1)]

    def check_keys(self):
        for i in range(len(self.keys)):
            if self.keys[i] == pyu.KeyState.UP:
                self.keys[i] = pyu.KeyState.NONE
            elif self.keys[i] == pyu.KeyState.DOWN:
                self.keys[i] = pyu.KeyState.PRESS

    def check_mouse(self):
        for i in range(len(self.mbuttons)):
            if self.mbuttons[i] == pyu.KeyState.UP:
                self.mbuttons[i] = pyu.KeyState.NONE
            elif self.mbuttons[i] == pyu.KeyState.DOWN:
                self.mbuttons[i] = pyu.KeyState.PRESS

    def get_mouse(self, mousecode, keystate):
        if keystate == pyu.KeyState.PRESS:
            if self.mbuttons[mousecode] in [pyu.KeyState.PRESS, pyu.KeyState.DOWN]:
                return True
        if self.mbuttons[mousecode] == keystate:
            return True
        return False
    
    def get_key(self, keycode, keystate):
        if keystate == pyu.KeyState.PRESS:
            if self.keys[keycode] in [pyu.KeyState.PRESS, pyu.KeyState.DOWN]:
                return True
        if self.keys[keycode] == keystate:
            return True
        return False

    def get_mouse_pos(self):
        return self.mpos
    
    def quit(self):
        pass

    def start(self, update_func):
        self.update_func = update_func

class SceneEditor:
    pass

class Console(QListWidget):
    SPACER = None
    def __init__(self, parent):
        super(Console, self).__init__(parent)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setIconSize(QSize(100, 100))
        self.entries = []
        self.pending_entries = []
        self.clear_on_run = True

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_switch)
        pyu.Logger.LogLine = self.modded_log(pyu.Logger.LogLine)
    
    def add_entry(self, timestamp, level, text):
        entry = ConsoleEntry(timestamp, level, text)
        self.entries.append(entry)
        self.addItem(entry)
    
    def clear(self):
        self.entries = []
        super(Console, self).clear()
    
    def modded_log(self, func):
        def inner(*args, **kwargs):
            timestamp, msg = func(*args, **kwargs, silent=True)
            if args[0] != pyu.Logger.DEBUG:
                self.pending_entries.append([timestamp, args[0], msg])
            return timestamp, msg
        return inner
    
    def on_switch(self):
        self.pending_entries = self.pending_entries[-100:]
        for entry in self.pending_entries:
            self.add_entry(*entry)
        self.pending_entries = []
        self.timer.start(250)

class ConsoleEntry(QListWidgetItem):
    icon_map = {
        pyu.Logger.ERROR: "error.png",
        pyu.Logger.INFO: "info.png",
        pyu.Logger.OUTPUT: "output.png",
        pyu.Logger.WARN: "warning.png"
    }
    def __init__(self, timestamp, level, text):
        super(ConsoleEntry, self).__init__(
            "|" + level.abbr + "| " + text + "\n" + timestamp)
        self.setFont(QFont("Segoe UI", 14))
        directory = os.path.dirname(os.path.abspath(__file__))
        self.setIcon(QIcon(os.path.join(directory,
            "icons", "console", ConsoleEntry.icon_map[level])))
