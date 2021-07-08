from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QFont
import os
from . import resources

class Window(QMainWindow):
    def __init__(self, app):
        super(Window, self).__init__()
        self.setWindowTitle("PyUnity Editor")
        self.app = app
        self.toolbar = ToolBar(self)
        self.vbox_layout = QVBoxLayout()
        self.vbox_layout.setStretch(0, 0)
        self.vbox_layout.setStretch(1, 1)
        self.vbox_layout.setSpacing(0)
        self.vbox_layout.setContentsMargins(2, 2, 2, 2)
        widget = QWidget()
        widget.setFont(QFont("Segoe UI"))
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
        self.setWindowIcon(QIcon(path))

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
        window.vbox_layout.addWidget(self)
        self.columnWidgets = []

        self.hbox_layout = QHBoxLayout(self)
        self.hbox_layout.setSpacing(0)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
    
    def add_tab(self, name, row, column):
        if len(self.columnWidgets) <= column:
            column = len(self.columnWidgets)
            columnWidget = Column()
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
    def __init__(self):
        super(Column, self).__init__()
        self.vbox_layout = QVBoxLayout(self)
        self.vbox_layout.setSpacing(0)
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widgets = []
        self.tabs = []
    
    def add_tab(self, name, row):
        if len(self.tabs) <= row:
            row = len(self.tabs)
            tab_widget = QTabWidget(self)
            self.vbox_layout.addWidget(tab_widget)
            self.tab_widgets.append(tab_widget)
            self.tabs.append([])
        tab_widget = self.tab_widgets[row]
        tab = Tab(tab_widget, name)
        self.tabs[row].append(tab)
        return tab

class Tab(QWidget):
    def __init__(self, tab_widget, name):
        super(Tab, self).__init__()
        self.tab_widget = tab_widget
        self.name = name
        
        self.vbox_layout = QVBoxLayout(self)
        self.vbox_layout.setSpacing(0)
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)

        self.spacer = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.vbox_layout.addSpacerItem(self.spacer)
        
        self.tab_widget.addTab(self, self.name)
    
    def set_window_type(self, window_type):
        self.content = window_type()
        self.vbox_layout.insertWidget(0, self.content)
        if hasattr(window_type, "SPACER"):
            self.vbox_layout.removeItem(self.spacer)
            del self.spacer
        return self.content

class Values(QWidget):
    def __init__(self):
        super(Values, self).__init__()
        self.grid_layout = QGridLayout()
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 2)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self.setLayout(self.grid_layout)
        self.fields = {}
    
    def add_value(self, name, type):
        label = QLabel()
        label.setText(name)
        label.setWordWrap(True)

        if type not in self.__class__.inputs:
            raise ValueError("Cannot create input box of type \"" + type.__name__ + "\"")
        input_box = self.__class__.inputs[type](self)
        self.fields[name] = [type, input_box]

        self.grid_layout.addWidget(label, len(self.fields) - 1, 0)
        self.grid_layout.addWidget(input_box, len(self.fields) - 1, 1)

    def new_str(self):
        return QLineEdit(self)
    
    def new_int(self):
        line_edit = QLineEdit(self)
        line_edit.setValidator(QIntValidator(self))
        return line_edit
    
    def new_float(self):
        line_edit = QLineEdit(self)
        line_edit.setValidator(QDoubleValidator(self))
        return line_edit
    
    inputs = {str: new_str, int: new_int, float: new_float}

class HierarchyItem(QTreeWidgetItem):
    def __init__(self, name):
        super(HierarchyItem, self).__init__()
        self.setText(0, name)
        self.name = name
        self.children = []
    
    def add_child(self, child):
        self.children.append(child)
        self.addChild(child)

class Hierarchy(QTreeWidget):
    SPACER = None
    def __init__(self):
        super(Hierarchy, self).__init__()
        self.items = []
        self.header().setVisible(False)
        self.setIndentation(10)
    
    def add_item(self, name, parent=None):
        item = HierarchyItem(name)
        if parent is None:
            self.items.append(item)
            self.addTopLevelItem(item)
        else:
            parent.add_child(item)
        return item
    
    def add_item_pos(self, name, *args):
        item = HierarchyItem(name)
        parent = self.items[args[0]]
        pos = args[1:]
        for num in pos:
            parent = parent.children[num]
        parent.add_child(item)
        return item

    def load_scene(self, scene):
        items = {}
        for gameObject in scene.rootGameObjects:
            items[gameObject] = self.add_item(gameObject.name)
        for gameObject in scene.gameObjects:
            print(gameObject.transform.parent)
            if gameObject.transform.parent is None:
                continue
            self.add_item(gameObject.name,
                items[gameObject.transform.parent.gameObject])
