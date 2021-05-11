from PyQt5.QtWidgets import *
from PyQt5.QtCore import QCoreApplication
import sys

class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle("PyUnity Editor")
        
        self.toolbar = ToolBar(self)
        self.toolbar.add_action("Quit", "File", "Ctrl+Q", "Close the Editor", QCoreApplication.instance().quit)
        self.show()

class ToolBar:
    def __init__(self, instance):
        self.instance = instance
        self.menu_bar = self.instance.menuBar()
        self.menus = {}

        instance.statusBar()
    
    def add_menu(self, name):
        if name in self.menus:
            return
        menu = self.menu_bar.addMenu("&" + name)
        self.menus[name] = menu
        return menu
    
    def add_action(self, name, menu, shortcut, tip, func):
        action = QAction("&" + name, self.instance)
        action.setShortcut(shortcut)
        action.setStatusTip(tip)
        action.triggered.connect(func)

        if menu not in self.menus:
            menuTab = self.add_menu(menu)
        else:
            menuTab = self.menus[menu]
        
        menuTab.addAction(action)

def start():
    return QApplication(sys.argv)