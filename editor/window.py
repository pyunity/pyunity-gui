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
        self.columnWidgets = []

        self.hbox_layout = QHBoxLayout(self)
        self.hbox_layout.setSpacing(0)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
        window.setCentralWidget(self)
    
    def add_tab(self, name, row, column):
        if len(self.columnWidgets) <= column:
            column = len(self.columnWidgets)
            columnWidget = Column(column)
            self.hbox_layout.addWidget(columnWidget)
            self.columnWidgets.append(columnWidget)
        columnWidget = self.columnWidgets[column]
        columnWidget.add_tab(name, row)
    
    def set_stretch(self, stretch):
        for i in range(len(stretch)):
            self.hbox_layout.setStretch(i, stretch[i])

class Column(QWidget):
    def __init__(self, column):
        super(Column, self).__init__()
        self.vbox_layout = QVBoxLayout(self)
        self.vbox_layout.setSpacing(0)
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widgets = []
        self.tabs = []
        self.column = column
    
    def add_tab(self, name, row):
        if len(self.tabs) <= row:
            row = len(self.tabs)
            tab_widget = QTabWidget(self)
            self.vbox_layout.addWidget(tab_widget)
            self.tab_widgets.append(tab_widget)
            self.tabs.append([])
        tab_widget = self.tab_widgets[row]
        tab = Tab(tab_widget, name, row, self.column)
        self.tabs[row].append(tab)

class Tab(QWidget):
    def __init__(self, tab_widget, name, row, column):
        super(Tab, self).__init__()
        self.tab_widget = tab_widget
        self.vbox_layout = QVBoxLayout(self)
        self.name = name
        self.row = row
        self.column = column
        
        self.tab_widget.addTab(self, self.name)

def start():
    return QApplication(sys.argv)