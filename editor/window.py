from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QFont
import os
from .resources import *

class Window(QMainWindow):
    def __init__(self, app):
        super(Window, self).__init__()
        self.setWindowTitle("PyUnity Editor")
        self.setFocusPolicy(Qt.StrongFocus)
        self.app = app
        self.app.setFont(QFont("Segoe UI", 10))
        self.toolbar = ToolBar(self)
        widget = QWidget(self)
        self.vbox_layout = QVBoxLayout(widget)
        self.vbox_layout.setStretch(0, 0)
        self.vbox_layout.setStretch(1, 1)
        self.vbox_layout.setSpacing(0)
        self.vbox_layout.setContentsMargins(2, 2, 2, 2)
        widget.setLayout(self.vbox_layout)
        self.setCentralWidget(widget)
        
        directory = os.path.dirname(os.path.abspath(__file__))
        self.styles = {}
        with open(os.path.join(directory, "theme", "dark.qss")) as f:
            self.styles["dark"] = f.read()
        with open(os.path.join(directory, "theme", "light.qss")) as f:
            self.styles["light"] = f.read()
        self.app.setStyleSheet(self.styles["dark"])
        self.theme = "dark"
    
    def toggle_theme(self):
        if self.theme == "dark":
            self.theme = "light"
        else:
            self.theme = "dark"
        self.app.setStyleSheet(self.styles[self.theme])
    
    def closeEvent(self, event):
        self.app.quit_wrapper()
        event.ignore()
    
    def set_icon(self, path):
        directory = os.path.dirname(os.path.abspath(__file__))
        self.setWindowIcon(QIcon(os.path.join(directory, path)))
    
    def select_none(self):
        if not isinstance(self.app.focusWidget(), QLineEdit):
            self.app.hierarchy_content.tree_widget.clearSelection()
    
    def rename(self):
        self.app.inspector.tab_widget.setCurrentWidget(self.app.inspector)
        box = list(self.app.inspector_content.sections[0].fields.keys())[0]
        box.setFocus()
        box.selectAll()
    
    def mousePressEvent(self, event):
        focused = self.focusWidget()
        if isinstance(focused, QLineEdit):
            focused.clearFocus()
        super(Window, self).mousePressEvent(event)

class SceneButtons(QWidget):
    def __init__(self, window):
        super(SceneButtons, self).__init__(window)
        self.buttons = []

        self.hbox_layout = QHBoxLayout(self)
        self.hbox_layout.setSpacing(0)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)

        spacer1 = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        spacer2 = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.hbox_layout.addSpacerItem(spacer1)
        self.hbox_layout.addSpacerItem(spacer2)
        self.spacers = [spacer1, spacer2]

        self.directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "buttons")
    
    def add_button(self, icon, tip="", on=False):
        button = QToolButton(self)
        button.setIcon(QIcon(os.path.join(self.directory, icon)))
        button.setStatusTip(tip)
        button.setCheckable(True)
        button.setChecked(on)
        self.buttons.append(button)
        self.hbox_layout.insertWidget(len(self.buttons), button)

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
    
    def add_action(self, name, menu, shortcut, tip, *funcs):
        action = QAction(name, self.instance)
        if shortcut:
            action.setShortcut(shortcut)
        action.setStatusTip(tip)
        for func in funcs:
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
        window.vbox_layout.addWidget(self)
        self.columnWidgets = []

        self.hbox_layout = QHBoxLayout(self)
        self.hbox_layout.setSpacing(0)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.hbox_layout)
    
    def add_tab(self, name, row, column):
        if len(self.columnWidgets) <= column:
            column = len(self.columnWidgets)
            columnWidget = Column(self)
            self.hbox_layout.addWidget(columnWidget)
            self.columnWidgets.append(columnWidget)
        columnWidget = self.columnWidgets[column]
        return columnWidget.add_tab(name, row)
    
    def set_stretch(self, stretch):
        if len(stretch) != len(self.columnWidgets):
            raise ValueError("Argument 1: expected %d length, got %d length" % \
                (len(stretch), len(self.columnWidgets)))
        for i in range(len(stretch)):
            self.hbox_layout.setStretch(i, stretch[i])

class Column(QWidget):
    def __init__(self, parent):
        super(Column, self).__init__(parent)
        self.vbox_layout = QVBoxLayout(self)
        self.vbox_layout.setSpacing(0)
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vbox_layout)
        self.tab_widgets = []
        self.tabs = []
    
    def add_tab(self, name, row):
        if len(self.tabs) <= row:
            row = len(self.tabs)
            tab_widget = TabGroup(self)
            self.vbox_layout.addWidget(tab_widget)
            self.tab_widgets.append(tab_widget)
            self.tabs.append([])
        tab_widget = self.tab_widgets[row]
        tab = Tab(tab_widget, name)
        self.tabs[row].append(tab)
        return tab

class TabGroup(QTabWidget):
    def __init__(self, parent):
        super(TabGroup, self).__init__(parent)
        self.setMovable(True)
        self.currentChanged.connect(self.tab_change)

    def tab_change(self, index):
        widget = self.currentWidget()
        if hasattr(widget, "content") and widget.content is not None:
            if hasattr(widget.content, "on_switch"):
                widget.content.on_switch()

class Tab(QWidget):
    def __init__(self, tab_widget, name):
        super(Tab, self).__init__(tab_widget)
        self.tab_widget = tab_widget
        self.name = name
        
        self.vbox_layout = QVBoxLayout(self)
        self.vbox_layout.setSpacing(0)
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)

        self.spacer = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.vbox_layout.addSpacerItem(self.spacer)
        
        self.tab_widget.addTab(self, self.name)
        self.content = None
    
    def set_window_type(self, window_type):
        self.content = window_type(self)
        self.vbox_layout.insertWidget(0, self.content)
        if hasattr(window_type, "SPACER"):
            self.vbox_layout.removeItem(self.spacer)
            del self.spacer
        return self.content
