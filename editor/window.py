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

class Editor(QWidget):
    def __init__(self, window):
        super(Editor, self).__init__(window)
        self.tabs = []
        self.tab_widgets = []

        self.grid_layout = QGridLayout(self)
        self.grid_layout.setSpacing(0)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        window.setCentralWidget(self)
    
    def add_tab(self, name, row, column):
        if len(self.tabs) <= column:
            column = len(self.tabs)
            self.tabs.append([])
            self.tab_widgets.append([])
            span = int(len(self.tabs[column]) == 0) + 1
            self.tab_widgets[column].append(tab_widget := QTabWidget(self))
            self.grid_layout.addWidget(tab_widget, row, column, 1, span)
        if len(self.tabs[column]) <= row:
            row = len(self.tabs[column])
            self.tabs[column].append([])
            self.tab_widgets[column].append(tab_widget := QTabWidget(self))
            span = int(len(self.tabs[column]) == 0) + 1
            self.grid_layout.addWidget(tab_widget, row, column, 1, span)
        else:
            tab_widget = self.tab_widgets[column][row]
        print(self.tabs, row, column)
        tab = Tab(tab_widget, name, row, column)
        self.tabs[column][row].append(tab)

class Tab(QWidget):
    def __init__(self, tab_widget, name, row, column):
        super(Tab, self).__init__()
        self.tab_widget = tab_widget
        self.name = name
        self.row = row
        self.column = column
        
        self.tab_widget.addTab(self, self.name)

def start():
    return QApplication(sys.argv)