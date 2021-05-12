from PyQt5.QtWidgets import *
import sys

class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("PyUnity Editor")
        
        self.toolbar = ToolBar(self)

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
        if shortcut:
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