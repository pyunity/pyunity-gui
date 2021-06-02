from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication
from .window import Editor, Window
import sys
import os

class Application(QApplication):
    def __init__(self):
        def testing(string):
            def inner():
                print(string)
            return inner
        super(Application, self).__init__(sys.argv)

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dark.qss")) as f:
            style = f.read()
        self.setStyleSheet(style)

        self.window = Window()
        
        self.window.toolbar.add_action("New", "File", "Ctrl+N", "Create a new project", testing("new"))
        self.window.toolbar.add_action("Open", "File", "Ctrl+O", "Open an existing project", testing("open"))
        self.window.toolbar.add_action("Save", "File", "Ctrl+S", "Save the current Scene", testing("save"))
        self.window.toolbar.add_action("Save As", "File", "Ctrl+Shift+S", "Save the current Scene as new file", testing("save as"))
        self.window.toolbar.add_action("Save a Copy As", "File", "Ctrl+Alt+S", "Save a copy of the current Scene", testing("save copy as"))
        self.window.toolbar.add_separator("File")
        self.window.toolbar.add_action("Close Scene", "File", "Ctrl+W", "Closes the current Scene", testing("close"))
        self.window.toolbar.add_action("Close All", "File", "Ctrl+Shift+W", "Closes all opened Scene", testing("close all"))
        self.window.toolbar.add_separator("File")
        self.window.toolbar.add_action("Quit", "File", "Ctrl+Q", "Close the Editor", QCoreApplication.instance().quit)
        
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
        
        self.editor = Editor(self.window)
        self.editor.add_tab("Scene", 0, 0)
        self.editor.add_tab("Game", 1, 0)
        self.editor.add_tab("Console", 1, 0)
        self.editor.add_tab("Hierarchy", 0, 1)
        self.editor.add_tab("Files", 1, 1)
        self.editor.add_tab("Audio Mixer", 1, 1)
        self.editor.add_tab("Inspector", 0, 2)
        self.editor.add_tab("Navigation", 0, 2)

    def start(self):
        self.window.showMaximized()
        self.exec_()