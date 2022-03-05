from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont, QIcon
from pyunity import (Logger, SceneManager, KeyCode,
    MouseCode, MeshRenderer, KeyState, Loader, Window, config, render)
import os
import copy
import time

def logPatch(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            Logger.LogException(e)
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
        return SceneManager.windowObject
    
    @winObj.setter
    def winObj(self, val):
        SceneManager.windowObject = val
    
    def set_buttons(self, buttons):
        self.buttons = buttons.buttons
        self.buttons[0].clicked.connect(self.start)
        self.buttons[1].clicked.connect(self.pause)
        self.buttons[2].clicked.connect(self.stop)
    
    def initializeGL(self):
        render.compile_shaders()
        self.original.mainCamera.skybox.compile()
        # self.winObj = WidgetWindow(
        #     self.original.name, self.original.mainCamera.Resize)
        self.original.mainCamera.setup_buffers()
        for renderer in self.original.FindComponentsByType(MeshRenderer):
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
        Qt.LeftButton: MouseCode.Left,
        Qt.RightButton: MouseCode.Right,
        Qt.MiddleButton: MouseCode.Middle,
    }

    keymap = {
        Qt.Key_A: KeyCode.A,
        Qt.Key_B: KeyCode.B,
        Qt.Key_C: KeyCode.C,
        Qt.Key_D: KeyCode.D,
        Qt.Key_E: KeyCode.E,
        Qt.Key_F: KeyCode.F,
        Qt.Key_G: KeyCode.G,
        Qt.Key_H: KeyCode.H,
        Qt.Key_I: KeyCode.I,
        Qt.Key_J: KeyCode.J,
        Qt.Key_K: KeyCode.K,
        Qt.Key_L: KeyCode.L,
        Qt.Key_M: KeyCode.M,
        Qt.Key_N: KeyCode.N,
        Qt.Key_O: KeyCode.O,
        Qt.Key_P: KeyCode.P,
        Qt.Key_Q: KeyCode.Q,
        Qt.Key_R: KeyCode.R,
        Qt.Key_S: KeyCode.S,
        Qt.Key_T: KeyCode.T,
        Qt.Key_U: KeyCode.U,
        Qt.Key_V: KeyCode.V,
        Qt.Key_W: KeyCode.W,
        Qt.Key_X: KeyCode.X,
        Qt.Key_Y: KeyCode.Y,
        Qt.Key_Z: KeyCode.Z,
        Qt.Key_Space: KeyCode.Space,
        Qt.Key_0: KeyCode.Alpha0,
        Qt.Key_1: KeyCode.Alpha1,
        Qt.Key_2: KeyCode.Alpha2,
        Qt.Key_3: KeyCode.Alpha3,
        Qt.Key_4: KeyCode.Alpha4,
        Qt.Key_5: KeyCode.Alpha5,
        Qt.Key_6: KeyCode.Alpha6,
        Qt.Key_7: KeyCode.Alpha7,
        Qt.Key_8: KeyCode.Alpha8,
        Qt.Key_9: KeyCode.Alpha9,
        Qt.Key_F1: KeyCode.F1,
        Qt.Key_F2: KeyCode.F2,
        Qt.Key_F3: KeyCode.F3,
        Qt.Key_F4: KeyCode.F4,
        Qt.Key_F5: KeyCode.F5,
        Qt.Key_F6: KeyCode.F6,
        Qt.Key_F7: KeyCode.F7,
        Qt.Key_F8: KeyCode.F8,
        Qt.Key_F9: KeyCode.F9,
        Qt.Key_F10: KeyCode.F10,
        Qt.Key_F11: KeyCode.F11,
        Qt.Key_F12: KeyCode.F12,
        # Qt.Key_: KeyCode.Keypad0,
        # Qt.Key_: KeyCode.Keypad1,
        # Qt.Key_: KeyCode.Keypad2,
        # Qt.Key_: KeyCode.Keypad3,
        # Qt.Key_: KeyCode.Keypad4,
        # Qt.Key_: KeyCode.Keypad5,
        # Qt.Key_: KeyCode.Keypad6,
        # Qt.Key_: KeyCode.Keypad7,
        # Qt.Key_: KeyCode.Keypad8,
        # Qt.Key_: KeyCode.Keypad9,
        Qt.Key_Up: KeyCode.Up,
        Qt.Key_Down: KeyCode.Down,
        Qt.Key_Left: KeyCode.Left,
        Qt.Key_Right: KeyCode.Right,
    }

    def mouseMoveEvent(self, event):
        super(OpenGLFrame, self).mouseMoveEvent(event)
        if self.winObj is not None:
            self.winObj.mpos = [event.x(), event.y()]
    
    def mousePressEvent(self, event):
        super(OpenGLFrame, self).mousePressEvent(event)
        if self.winObj is not None:
            self.winObj.mbuttons[self.mousemap[event.button()]] = KeyState.DOWN
    
    def mouseReleaseEvent(self, event):
        super(OpenGLFrame, self).mouseReleaseEvent(event)
        if self.winObj is not None:
            self.winObj.mbuttons[self.mousemap[event.button()]] = KeyState.UP
    
    def keyPressEvent(self, event):
        super(OpenGLFrame, self).keyPressEvent(event)
        if self.winObj is not None:
            if event.key() not in self.keymap:
                return
            self.winObj.keys[self.keymap[event.key()]] = KeyState.DOWN
    
    def keyReleaseEvent(self, event):
        super(OpenGLFrame, self).keyReleaseEvent(event)
        if self.winObj is not None:
            if event.key() not in self.keymap:
                return
            self.winObj.keys[self.keymap[event.key()]] = KeyState.UP
    
    @logPatch
    def start(self, on):
        if self.scene is not None:
            self.stop()
        else:
            config.fps = 60
            self.makeCurrent()
            self.scene = copy.deepcopy(self.original)
            self.winObj = WidgetWindow(
                self.scene.name, self.scene.mainCamera.Resize)
            # self.scene.mainCamera.skybox.compile()
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
                self.scene.lastFrame = time.time()
                if config.fps == 0:
                    self.timer.start(1)
                else:
                    self.timer.start(1000 // config.fps)
    
    def save(self):
        Logger.Log(self.original.ids)
        Loader.ResaveScene(self.original, self.file_tracker.project)
    
    def on_switch(self):
        self.console.timer.stop()

class WidgetWindow(Window.ABCWindow):
    def __init__(self, name, resize):
        self.name = name
        self.resize = resize
        self.mpos = [0, 0]
        self.mbuttons = [KeyState.NONE, KeyState.NONE, KeyState.NONE]
        self.keys = [KeyState.NONE for i in range(KeyCode.Right + 1)]

    def check_keys(self):
        for i in range(len(self.keys)):
            if self.keys[i] == KeyState.UP:
                self.keys[i] = KeyState.NONE
            elif self.keys[i] == KeyState.DOWN:
                self.keys[i] = KeyState.PRESS

    def check_mouse(self):
        for i in range(len(self.mbuttons)):
            if self.mbuttons[i] == KeyState.UP:
                self.mbuttons[i] = KeyState.NONE
            elif self.mbuttons[i] == KeyState.DOWN:
                self.mbuttons[i] = KeyState.PRESS

    def get_mouse(self, mousecode, keystate):
        if keystate == KeyState.PRESS:
            if self.mbuttons[mousecode] in [KeyState.PRESS, KeyState.DOWN]:
                return True
        if self.mbuttons[mousecode] == keystate:
            return True
        return False
    
    def get_key(self, keycode, keystate):
        if keystate == KeyState.PRESS:
            if self.keys[keycode] in [KeyState.PRESS, KeyState.DOWN]:
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
        Logger.LogLine = self.modded_log(Logger.LogLine)
    
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
            if args[0] != Logger.DEBUG:
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
        Logger.ERROR: "error.png",
        Logger.INFO: "info.png",
        Logger.OUTPUT: "output.png",
        Logger.WARN: "warning.png"
    }
    def __init__(self, timestamp, level, text):
        super(ConsoleEntry, self).__init__(
            "|" + level.abbr + "| " + text + "\n" + timestamp)
        self.setFont(QFont("Segoe UI", 14))
        directory = os.path.dirname(os.path.abspath(__file__))
        self.setIcon(QIcon(os.path.join(directory,
            "icons", "console", ConsoleEntry.icon_map[level])))
