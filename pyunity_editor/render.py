from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import QFont, QIcon
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from .smoothScroll import QSmoothListWidget
from .files import getPath
from pyunity import (Logger, SceneManager, KeyCode,
    MouseCode, MeshRenderer, KeyState, Loader, Window,
    WaitForUpdate, WaitForRender, WaitForFixedUpdate, PyUnityException,
    EventLoopManager, EventLoop,
    config, render)
from pyunity.scenes.runner import Runner, ChangeScene
import asyncio
import os
import copy
import time

def logPatch(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            Logger.LogException(e, stacklevel=2)
    return inner

class QEventLoopManager(EventLoopManager):
    def start(self):
        if EventLoopManager.current is not None:
            raise PyUnityException("Only one EventLoopManager can be running")
        EventLoopManager.current = self

        self.waiting[self.mainWaitFor] = []

        for loop in self.separateLoops:
            loop.call_soon(loop.stop)
            loop.run_forever() # Run until awaits are encountered
        self.separateLoops.clear()

        self.running = True
        for thread in self.threads:
            thread.start()

        self.mainLoop = EventLoop()
        asyncio.set_event_loop(self.mainLoop)

        def inner():
            if len(EventLoopManager.exceptions):
                if isinstance(EventLoopManager.exceptions[0], ChangeScene):
                    exc = EventLoopManager.exceptions.pop()
                    EventLoopManager.exceptions.clear()
                    raise exc
                elif config.exitOnError:
                    Logger.LogLine(Logger.ERROR,
                                   f"Exception in Scene: {SceneManager.CurrentScene().name!r}")
                    exc = EventLoopManager.exceptions.pop()
                    EventLoopManager.exceptions.clear()
                    raise exc
                else:
                    for exception in EventLoopManager.exceptions:
                        Logger.LogLine(Logger.ERROR,
                                    f"Exception ignored in Scene: {SceneManager.CurrentScene().name!r}")
                        Logger.LogException(exception)
                    EventLoopManager.exceptions.clear()

            for waiter in self.waiting[self.mainWaitFor]:
                waiter.loop.call_soon_threadsafe(waiter.event.set)

            for func in self.updates:
                func(loop)

            for event in self.pending:
                event.trigger()
            self.pending.clear()

            self.mainLoop.call_soon(self.mainLoop.stop)
            self.mainLoop.run_forever()

        return inner

class QRunner(Runner):
    def __init__(self, frame):
        super(QRunner, self).__init__()
        self.frame = frame

    def open(self):
        super(QRunner, self).open()
        os.environ["PYUNITY_GL_CONTEXT"] = "1"
        self.window = WidgetWindow("Editor")

    def load(self):
        if self.scene is None:
            raise PyUnityException("Cannot load runner before setting a scene")
        Logger.LogLine(Logger.DEBUG, "Starting scene")
        self.eventLoopManager = QEventLoopManager()
        self.eventLoopManager.schedule(self.scene.updateFixed, ups=50, waitFor=WaitForFixedUpdate)
        self.eventLoopManager.addLoop(self.scene.startScripts())

        self.eventLoopManager.schedule(
            self.scene.updateScripts, self.window.updateFunc,
            ups=config.fps, waitFor=WaitForUpdate)
        self.eventLoopManager.schedule(
            self.scene.Render, self.window.refresh,
            main=True, waitFor=WaitForRender)
        if self.scene.mainCamera is not None:
            self.window.setResize(self.scene.mainCamera.Resize)
        self.scene.startOpenGL()
        self.scene.startLoop()

    def start(self):
        self.updateFunc = self.eventLoopManager.start()

class OpenGLFrame(QOpenGLWidget):
    SPACER = None
    def __init__(self, parent):
        super(OpenGLFrame, self).__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.console = None
        self.original = None
        self.paused = False
        self.file_tracker = None
        self.runner = QRunner(self)
        SceneManager.runner = self.runner

    def set_buttons(self, buttons):
        self.buttons = buttons.buttons
        self.buttons[0].clicked.connect(self.start)
        self.buttons[1].clicked.connect(self.pause)
        self.buttons[2].clicked.connect(self.stop)

    def initializeGL(self):
        Logger.LogLine(Logger.DEBUG, "Compiling objects")
        Logger.elapsed.tick()
        Logger.LogLine(Logger.INFO, "Compiling shaders")
        render.compileShaders()
        Logger.LogSpecial(Logger.INFO, Logger.ELAPSED_TIME)
        Logger.LogLine(Logger.INFO, "Loading skyboxes")
        render.compileSkyboxes()
        Logger.LogSpecial(Logger.INFO, Logger.ELAPSED_TIME)

        self.original.mainCamera.skybox.compile()
        self.original.mainCamera.setupBuffers()
        for renderer in self.original.FindComponents(MeshRenderer):
            renderer.mesh.compile()
        self.original.Render()

    def paintGL(self):
        if self.runner.opened:
            try:
                self.runner.updateFunc()
            except ChangeScene:
                if self.runner.next is None:
                    raise
                self.runner.eventLoopManager.quit()
                self.runner.scene.cleanUp()
                self.runner.scene = self.runner.next
                self.runner.next = None
                self.runner.load()
                self.runner.start()
        else:
            self.original.Render()

    def resizeGL(self, width, height):
        if self.runner.opened:
            self.runner.scene.mainCamera.Resize(width, height)
        else:
            self.original.mainCamera.Resize(width, height)
        self.update()

    @logPatch
    def start(self, on=None):
        if self.runner.opened:
            self.stop()
        else:
            self.makeCurrent()
            if self.console.clear_on_run:
                self.console.clear()
            self.buttons[2].setChecked(False)
            self.file_tracker.stop()

            self.runner.setScene(copy.deepcopy(self.original))
            if not self.runner.opened:
                self.runner.open()
            self.runner.load()
            self.runner.start()

            self.runner.scene.mainCamera.Resize(self.width(), self.height())
            if not self.paused:
                duration = 0 if config.fps == 0 else 1000 / config.fps
                self.timer.start(duration)
            else:
                self.timer.stop()

    @logPatch
    def stop(self, on=None):
        if self.runner.opened:
            self.runner.quit()
            self.buttons[0].setChecked(False)
            self.buttons[1].setChecked(False)
            self.buttons[2].setChecked(True)
            self.paused = False
            self.update()
            self.file_tracker.start(5)
        else:
            self.buttons[2].setChecked(True)

    def pause(self, on=None):
        self.paused = not self.paused
        if self.runner.opened:
            if self.paused:
                self.timer.stop()
            else:
                self.runner.scene.lastFrame = time.perf_counter()
                self.runner.scene.lastFixedFrame = time.perf_counter()
                duration = 0 if config.fps == 0 else 1000 / config.fps
                self.timer.start(duration)

    def save(self):
        def callback():
            Loader.ResaveScene(self.original, self.file_tracker.project)
            message.done(0)

        message = QMessageBox()
        message.setText("Saving scene...")
        message.setWindowTitle(self.file_tracker.project.name)
        message.setStandardButtons(QMessageBox.StandardButton.NoButton)
        message.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        QTimer.singleShot(2000, callback)
        message.setFont(QFont("Segoe UI", 12))
        message.exec()

    def on_switch(self):
        self.console.timer.stop()

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
        Qt.Key_Up: KeyCode.Up,
        Qt.Key_Down: KeyCode.Down,
        Qt.Key_Left: KeyCode.Left,
        Qt.Key_Right: KeyCode.Right,
    }

    numberkeys = {
        Qt.Key_0: KeyCode.Keypad0,
        Qt.Key_1: KeyCode.Keypad1,
        Qt.Key_2: KeyCode.Keypad2,
        Qt.Key_3: KeyCode.Keypad3,
        Qt.Key_4: KeyCode.Keypad4,
        Qt.Key_5: KeyCode.Keypad5,
        Qt.Key_6: KeyCode.Keypad6,
        Qt.Key_7: KeyCode.Keypad7,
        Qt.Key_8: KeyCode.Keypad8,
        Qt.Key_9: KeyCode.Keypad9,
    }

    def mouseMoveEvent(self, event):
        super(OpenGLFrame, self).mouseMoveEvent(event)
        if hasattr(self.runner, "window"):
            self.runner.window.mpos = [event.x(), event.y()]

    def mousePressEvent(self, event):
        super(OpenGLFrame, self).mousePressEvent(event)
        if hasattr(self.runner, "window"):
            self.runner.window.mbuttons[self.mousemap[event.button()]] = KeyState.DOWN

    def mouseReleaseEvent(self, event):
        super(OpenGLFrame, self).mouseReleaseEvent(event)
        if hasattr(self.runner, "window"):
            self.runner.window.mbuttons[self.mousemap[event.button()]] = KeyState.UP

    def keyPressEvent(self, event):
        super(OpenGLFrame, self).keyPressEvent(event)
        if hasattr(self.runner, "window"):
            if event.key() not in self.keymap:
                return
            if event.key() in self.numberkeys and event.modifiers() & Qt.KeypadModifier:
                self.runner.window.keys[self.numberkeys[event.key()]] = KeyState.DOWN
            else:
                self.runner.window.keys[self.keymap[event.key()]] = KeyState.DOWN

    def keyReleaseEvent(self, event):
        super(OpenGLFrame, self).keyReleaseEvent(event)
        if hasattr(self.runner, "window"):
            if event.key() not in self.keymap:
                return
            if event.key() in self.numberkeys and event.modifiers() & Qt.KeypadModifier:
                self.runner.window.keys[self.numberkeys[event.key()]] = KeyState.UP
            else:
                self.runner.window.keys[self.keymap[event.key()]] = KeyState.UP

class WidgetWindow(Window.ABCWindow):
    def __init__(self, name):
        self.name = name
        self.mpos = [0, 0]
        self.mbuttons = [KeyState.NONE, KeyState.NONE, KeyState.NONE]
        self.keys = [KeyState.NONE for i in range(KeyCode.Right + 1)]

    def setResize(self, resize):
        self.resize = resize

    def checkKeys(self):
        for i in range(len(self.keys)):
            if self.keys[i] == KeyState.UP:
                self.keys[i] = KeyState.NONE
            elif self.keys[i] == KeyState.DOWN:
                self.keys[i] = KeyState.PRESS

    def checkMouse(self):
        for i in range(len(self.mbuttons)):
            if self.mbuttons[i] == KeyState.UP:
                self.mbuttons[i] = KeyState.NONE
            elif self.mbuttons[i] == KeyState.DOWN:
                self.mbuttons[i] = KeyState.PRESS

    def getMouse(self, mousecode, keystate):
        if keystate == KeyState.PRESS:
            if self.mbuttons[mousecode] in [KeyState.PRESS, KeyState.DOWN]:
                return True
        if self.mbuttons[mousecode] == keystate:
            return True
        return False

    def getKey(self, keycode, keystate):
        if keystate == KeyState.PRESS:
            if self.keys[keycode] in [KeyState.PRESS, KeyState.DOWN]:
                return True
        if self.keys[keycode] == keystate:
            return True
        return False

    def getMousePos(self):
        return self.mpos

    def quit(self):
        pass

    def updateFunc(self):
        pass

    def refresh(self):
        pass

class SceneEditor:
    pass

class Console(QSmoothListWidget):
    SPACER = None
    def __init__(self, parent):
        super(Console, self).__init__(parent)
        self.scrollRatio = 0.5
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setIconSize(QSize(50, 50))
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
        self.pending_entries = []
        super(Console, self).clear()

    def modded_log(self, func):
        def inner(*args, **kwargs):
            timestamp, msg = func(*args, **kwargs)
            if args[0] != Logger.DEBUG:
                self.pending_entries.append([timestamp, args[0], msg])
            return timestamp, msg
        return inner

    def on_switch(self):
        self.pending_entries = self.pending_entries[-100:]
        if len(self.pending_entries) == 100:
            self.clear()
        for entry in self.pending_entries:
            self.add_entry(*entry)
        self.pending_entries = []
        self.timer.start(100)

class ConsoleEntry(QListWidgetItem):
    icon_map = {
        Logger.ERROR: "error.png",
        Logger.INFO: "info.png",
        Logger.OUTPUT: "output.png",
        Logger.WARN: "warning.png"
    }
    def __init__(self, timestamp, level, text):
        super(ConsoleEntry, self).__init__(text + "\n" + timestamp)
        self.setFont(QFont("Segoe UI", 12))
        self.setIcon(QIcon(getPath(
            "icons/console/" + ConsoleEntry.icon_map[level])))
