import os
os.environ["PYUNITY_DEBUG_MODE"] = "1"
from editor.files import FileTracker
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMessageBox
from .window import Editor, SceneButtons, Window
from .views import Hierarchy
from .inspector import Inspector
from .render import OpenGLFrame, Console
from pyunity import SceneManager, Logger
import io
import sys
import subprocess
import contextlib

def testing(string):
    def inner():
        Logger.Log(string)
    return inner

class VersionWorker(QObject):
    finished = pyqtSignal()

    def run(self):
        from pyunity.__main__ import version
        r = io.StringIO()
        with contextlib.redirect_stdout(r):
            version()
        self.lines = r.getvalue().rstrip().split("\n")[3:]
        self.finished.emit()

class Application(QApplication):
    def __init__(self, path):
        super(Application, self).__init__(sys.argv)

        self.window = Window(self)
        self.window.set_icon("icons/icon.png")

        self.buttons = SceneButtons(self.window)
        self.buttons.add_button("play.png", "Run the scene")
        self.buttons.add_button("pause.png", "Pause the scene")
        self.buttons.add_button("stop.png", "Stop the current running scene", True)
        self.window.vbox_layout.addWidget(self.buttons)

        self.editor = Editor(self.window)
        self.scene = self.editor.add_tab("Scene", 0, 0)
        self.game = self.editor.add_tab("Game", 1, 0)
        self.console = self.editor.add_tab("Console", 1, 0)
        self.hierarchy = self.editor.add_tab("Hierarchy", 0, 1)
        self.files = self.editor.add_tab("Files", 1, 1)
        self.mixer = self.editor.add_tab("Audio Mixer", 1, 1)
        self.inspector = self.editor.add_tab("Inspector", 0, 2)
        self.navigation = self.editor.add_tab("Navigation", 0, 2)

        self.editor.set_stretch((7, 2, 2))

        self.inspector_content = self.inspector.set_window_type(Inspector)

        self.game_content = self.game.set_window_type(OpenGLFrame)
        self.game_content.set_buttons(self.buttons)
        self.game_content.file_tracker = FileTracker(self, path)
        self.game_content.file_tracker.start(1)
        self.game_content.original = SceneManager.GetSceneByIndex(
            # 0)
            self.game_content.file_tracker.project.firstScene)

        self.hierarchy_content = self.hierarchy.set_window_type(Hierarchy)
        self.hierarchy_content.load_scene(self.game_content.original)
        self.hierarchy_content.inspector = self.inspector_content
        self.hierarchy_content.preview = self.game_content

        self.console_content = self.console.set_window_type(Console)
        self.game_content.console = self.console_content

        self.setup_toolbar()

    def start(self):
        self.window.showMaximized()
        os.environ["PYUNITY_EDITOR_LOADED"] = "1"
        self.exec_()

    def open(self):
        Logger.Log("Choosing folder...")
        # Get opened project
        subprocess.Popen(["py", "cli.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.quit()

    def save(self):
        self.game_content.save()
        self.inspector_content.reset_bold()
        self.hierarchy_content.reset_bold()

    def quit_wrapper(self):
        message_box = QMessageBox(QMessageBox.Information, "Quit", "Are you sure you want to quit?", parent=self.window)
        message_box.setInformativeText("You may lose unsaved changes.")
        message_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        message_box.setDefaultButton(QMessageBox.Cancel)
        ret = message_box.exec()
        if ret == QMessageBox.Ok:
            self.quit()

    def showVersion(self):
        if self.worker is not None:
            return
        self.worker = VersionWorker()
        self.vThread = QThread()
        self.worker.moveToThread(self.vThread)
        self.vThread.started.connect(self.worker.run)
        self.worker.finished.connect(self.vThread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.vThread.finished.connect(self.cleanUpWorker)
        self.vThread.finished.connect(self.vThread.deleteLater)
        self.vThread.start()

    def cleanUpWorker(self):
        msg = QMessageBox()
        msg.setText("PyUnity Version Info")
        msg.setInformativeText("\n".join(
            [x for x in self.worker.lines if not x.startswith("Warning: ")]))
        msg.setWindowTitle("PyUnity information")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

        self.worker = None
        self.vThread = None

    def setup_toolbar(self):
        self.window.toolbar.add_action("New", "File", "Ctrl+N", "Create a new project", testing("new"))
        self.window.toolbar.add_action("Open", "File", "Ctrl+O", "Open an existing project", self.open)
        self.window.toolbar.add_action("Save", "File", "Ctrl+S", "Save the current Scene", self.save)
        self.window.toolbar.add_action("Save As", "File", "Ctrl+Shift+S", "Save the current Scene as new file", testing("save as"))
        self.window.toolbar.add_action("Save a Copy As", "File", "Ctrl+Alt+S", "Save a copy of the current Scene", testing("save copy as"))
        self.window.toolbar.add_separator("File")
        self.window.toolbar.add_action("Close Scene", "File", "Ctrl+W", "Closes the current Scene", testing("close"))
        self.window.toolbar.add_action("Close All", "File", "Ctrl+Shift+W", "Closes all opened Scene", testing("close all"))
        self.window.toolbar.add_separator("File")
        self.window.toolbar.add_action("Quit", "File", "Ctrl+Q", "Close the Editor", self.quit_wrapper)

        self.window.toolbar.add_action("Undo", "Edit", "Ctrl+Z", "Undo the last action", testing("undo"))
        self.window.toolbar.add_action("Redo", "Edit", "Ctrl+Shift+Z", "Redo the last action", testing("redo"))
        self.window.toolbar.add_separator("Edit")
        self.window.toolbar.add_action("Cut", "Edit", "Ctrl+X", "Deletes item and adds to clipboard", testing("cut"))
        self.window.toolbar.add_action("Copy", "Edit", "Ctrl+C", "Adds item to clipboard", testing("copy"))
        self.window.toolbar.add_action("Paste", "Edit", "Ctrl+V", "Pastes item from clipboard", testing("paste"))
        self.window.toolbar.add_separator("Edit")
        self.window.toolbar.add_action("Rename", "Edit", "F2", "Renames the selected item", self.window.rename)
        self.window.toolbar.add_action("Duplicate", "Edit", "Ctrl+D", "Duplicates the selected item(s)", testing("duplicate"))
        self.window.toolbar.add_action("Delete", "Edit", "Delete", "Deletes item", self.hierarchy_content.remove)
        self.window.toolbar.add_separator("Edit")
        self.window.toolbar.add_action("Select All", "Edit", "Ctrl+A", "Selects all items in the current Scene", self.hierarchy_content.tree_widget.selectAll)
        self.window.toolbar.add_action("Select None", "Edit", "Escape", "Deselects all items", self.window.select_none)

        self.window.toolbar.add_sub_action("Start/Stop", "View", "Game", "Ctrl+Return", "Starts and stops the game", self.buttons.buttons[0].click)
        self.window.toolbar.add_sub_action("Pause/Unpause", "View", "Game", "Space", "Toggles the pause state", self.game_content.buttons[1].click)

        self.window.toolbar.add_sub_action("Folder", "Assets", "Create", "", "", testing("new folder"))
        self.window.toolbar.add_sub_action("File", "Assets", "Create", "", "", testing("new file"))
        self.window.toolbar.add_sub_separator("Assets", "Create")
        self.window.toolbar.add_sub_action("Script", "Assets", "Create", "", "", testing("new script"))
        self.window.toolbar.add_sub_separator("Assets", "Create")
        self.window.toolbar.add_sub_action("Scene", "Assets", "Create", "", "", testing("new scene"))
        self.window.toolbar.add_sub_action("Prefab", "Assets", "Create", "", "", testing("new prefab"))
        self.window.toolbar.add_sub_action("Material", "Assets", "Create", "", "", testing("new mat"))
        self.window.toolbar.add_sub_separator("Assets", "Create")
        self.window.toolbar.add_sub_action("Physic Material", "Assets", "Create", "", "", testing("new phys mat"))

        self.window.toolbar.add_action("Open", "Assets", "", "Opens the selected asset", testing("open asset"))
        self.window.toolbar.add_action("Delete", "Assets", "", "Deletes the selected asset", testing("del asset"))

        self.worker = None
        self.vThread = None
        self.window.toolbar.add_action("Show PyUnity information", "Window", "", "Show information about PyUnity, the PyUnity Editor and all its dependencies.", self.showVersion)
        self.window.toolbar.add_action("Toggle Theme", "Window", "Ctrl+L", "Toggle theme between light and dark", self.window.toggle_theme)

