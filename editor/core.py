from PyQt5.QtWidgets import *
from PyQt5.QtCore import QCoreApplication
import sys

def testing(string):
    def inner():
        print(string)
    return inner

class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("PyUnity Editor")
        
        self.toolbar = ToolBar(self)
        
        self.toolbar.add_action("New", "File", "Ctrl+N", "Create a new project", testing("new"))
        self.toolbar.add_action("Open", "File", "Ctrl+O", "Open an existing project", testing("open"))
        self.toolbar.add_action("Save", "File", "Ctrl+S", "Save the current Scene", testing("save"))
        self.toolbar.add_action("Save As", "File", "Ctrl+Shift+S", "Save the current Scene as new file", testing("save as"))
        self.toolbar.add_action("Save a Copy As", "File", "Ctrl+Alt+S", "Save a copy of the current Scene", testing("save copy as"))
        self.toolbar.add_separator("File")
        self.toolbar.add_action("Close Scene", "File", "Ctrl+W", "Closes the current Scene", testing("close"))
        self.toolbar.add_action("Close All", "File", "Ctrl+Shift+W", "Closes all opened Scene", testing("close all"))
        self.toolbar.add_separator("File")
        self.toolbar.add_action("Quit", "File", "Ctrl+Q", "Close the Editor", QCoreApplication.instance().quit)
        
        self.toolbar.add_action("Undo", "Edit", "Ctrl+Z", "Undo the last action", testing("undo"))
        self.toolbar.add_action("Redo", "Edit", "Ctrl+Shift+Z", "Redo the last action", testing("redo"))
        self.toolbar.add_separator("Edit")
        self.toolbar.add_action("Cut", "Edit", "Ctrl+X", "Deletes item and adds to clipboard", testing("cut"))
        self.toolbar.add_action("Copy", "Edit", "Ctrl+C", "Adds item to clipboard", testing("copy"))
        self.toolbar.add_action("Paste", "Edit", "Ctrl+V", "Pastes item from clipboard", testing("paste"))
        self.toolbar.add_separator("Edit")
        self.toolbar.add_action("Rename", "Edit", "F2", "Renames the selected item", testing("rename"))
        self.toolbar.add_action("Duplicate", "Edit", "Ctrl+D", "Duplicates the selected item(s)", testing("duplicate"))
        self.toolbar.add_action("Delete", "Edit", "Delete", "Deletes item", testing("delete"))
        self.toolbar.add_separator("Edit")
        self.toolbar.add_action("Select All", "Edit", "Ctrl+A", "Selects all items in the current Scene", testing("select all"))
        self.toolbar.add_action("Select None", "Edit", "Escape", "Deselects all items", testing("select none"))
        
        self.toolbar.add_sub_action("Folder", "Assets", "Create", None, "", testing("new folder"))
        self.toolbar.add_sub_action("File", "Assets", "Create", None, "", testing("new file"))
        self.toolbar.add_sub_separator("Assets", "Create")
        self.toolbar.add_sub_action("Script", "Assets", "Create", None, "", testing("new script"))
        self.toolbar.add_sub_separator("Assets", "Create")
        self.toolbar.add_sub_action("Scene", "Assets", "Create", None, "", testing("new scene"))
        self.toolbar.add_sub_action("Prefab", "Assets", "Create", None, "", testing("new prefab"))
        self.toolbar.add_sub_action("Material", "Assets", "Create", None, "", testing("new mat"))
        self.toolbar.add_sub_separator("Assets", "Create")
        self.toolbar.add_sub_action("Physic Material", "Assets", "Create", None, "", testing("new phys mat"))
        
        self.toolbar.add_action("Open", "Assets", None, "Opens the selected asset", testing("open asset"))
        self.toolbar.add_action("Delete", "Assets", None, "Deletes the selected asset", testing("del asset"))
        
        self.showMaximized()

class ToolBar:
    def __init__(self, instance):
        self.instance = instance
        self.menu_bar = self.instance.menuBar()
        self.menus = {}
        self.sub_menus = {}

        instance.statusBar()
    
    def add_menu(self, name):
        if name in self.menus:
            return
        menu = self.menu_bar.addMenu("&" + name)
        self.menus[name] = menu
        self.sub_menus[name] = {}
        return menu
    
    def add_action(self, name, menu, shortcut, tip, func):
        action = QAction(name, self.instance)
        action.setShortcut(shortcut)
        action.setStatusTip(tip)
        action.triggered.connect(func)

        if menu not in self.menus:
            menu_tab = self.add_menu(menu)
        else:
            menu_tab = self.menus[menu]
        
        menu_tab.addAction(action)
    
    def add_sub_menu(self, name, menu):
        if menu not in self.menus:
            menu_tab = self.add_menu(menu)
        else:
            menu_tab = self.menus[menu]
        sub_menu = menu_tab.addMenu(name)
        self.sub_menus[menu][name] = sub_menu
        return sub_menu
    
    def add_sub_action(self, name, menu, sub_menu, shortcut, tip, func):
        action = QAction(name, self.instance)
        if shortcut is not None:
            action.setShortcut(shortcut)
        action.setStatusTip(tip)
        action.triggered.connect(func)

        if menu not in self.menus:
            menu_tab = self.add_sub_menu(sub_menu, menu)
        else:
            menu_tab = self.sub_menus[menu][sub_menu]
        
        menu_tab.addAction(action)
    
    def add_separator(self, menu):
        if menu in self.menus:
            self.menus[menu].addSeparator()
    
    def add_sub_separator(self, menu, sub):
        if menu in self.menus and sub in self.sub_menus[menu]:
            self.sub_menus[menu][sub].addSeparator()

def start():
    return QApplication(sys.argv)