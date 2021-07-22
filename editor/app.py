import os
from editor.files import FileTracker
from PyQt5.QtWidgets import QApplication, QMessageBox
from .window import Editor, SceneButtons, Window
from .views import Inspector, Hierarchy
from .render import OpenGLFrame, Console
from pyunity import Loader, SceneManager, Logger
import sys
import subprocess
import time

def testing(string):
    def inner():
        print(string)
    return inner

class Application(QApplication):
    def __init__(self, path):
        super(Application, self).__init__(sys.argv)
        self.project = Loader.LoadProject(path)

        self.window = Window(self)
        self.window.set_icon("icons/icon.png")
        
        self.window.toolbar.add_action("New", "File", "Ctrl+N", "Create a new project", testing("new"))
        self.window.toolbar.add_action("Open", "File", "Ctrl+O", "Open an existing project", self.open)
        self.window.toolbar.add_action("Save", "File", "Ctrl+S", "Save the current Scene", testing("save"))
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
        self.window.toolbar.add_action("Rename", "Edit", "F2", "Renames the selected item", testing("rename"))
        self.window.toolbar.add_action("Duplicate", "Edit", "Ctrl+D", "Duplicates the selected item(s)", testing("duplicate"))
        self.window.toolbar.add_action("Delete", "Edit", "Delete", "Deletes item", testing("delete"))
        self.window.toolbar.add_separator("Edit")
        self.window.toolbar.add_action("Select All", "Edit", "Ctrl+A", "Selects all items in the current Scene", testing("select all"))
        self.window.toolbar.add_action("Select None", "Edit", "Escape", "Deselects all items", testing("select none"))
        
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
        
        self.window.toolbar.add_action("Toggle Theme", "Window", "Ctrl+L", "Toggle theme between light and dark", self.window.toggle_theme)

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
        
        self.editor.set_stretch((4, 1, 1))

        inspector_content = self.inspector.set_window_type(Inspector)
        section = inspector_content.add_section("Testing")
        section.add_value("Name", str)
        section.add_value("Value", int)
        section.add_value("Price", float)

        game_content = self.game.set_window_type(OpenGLFrame)
        game_content.original = SceneManager.GetSceneByIndex(self.project.firstScene)
        game_content.set_buttons(self.buttons)

        hierarchy_content = self.hierarchy.set_window_type(Hierarchy)
        hierarchy_content.load_scene(game_content.original)
        hierarchy_content.inspector = inspector_content
        
        console_content = self.console.set_window_type(Console)
        for i in range(10):
            console_content.add_entry(time.strftime("%Y-%m-%d %H:%M:%S"), Logger.OUTPUT, "Test")
        game_content.console = console_content

        self.file_tracker = FileTracker(path)
        self.file_tracker.start(5)

    def start(self):
        self.window.showMaximized()
        os.environ["PYUNITY_EDITOR_LOADED"] = "1"
        self.exec_()
    
    def open(self):
        print("Choosing folder...")
        # Get opened project
        subprocess.Popen(["py", "cli.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.quit()
    
    def quit_wrapper(self):
        message_box = QMessageBox(QMessageBox.Information, "Quit", "Are you sure you want to quit?", parent=self.window)
        message_box.setInformativeText("You may lose unsaved changes.")
        message_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        message_box.setDefaultButton(QMessageBox.Cancel)
        ret = message_box.exec()
        if ret == QMessageBox.Ok:
            self.quit()
