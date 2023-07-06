from PySide6.QtCore import Qt
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon, QPixmap, QAction, QFont
from PIL import Image
from qframelesswindow import FramelessMainWindow
import os
from .local import getPath
from .resources import qInitResources
qInitResources()

class Window(FramelessMainWindow):
    def __init__(self, app):
        super(Window, self).__init__()
        self.setStyleSheet("Window:focus {border: none;}")
        self.setWindowTitle("PyUnity Editor")
        self.titleBar.raise_()
        self.setFocusPolicy(Qt.StrongFocus)

        self.statusBar()
        self.app = app
        self.toolbar = ToolBar(self)
        self.titleBar.layout().insertWidget(0, self.toolbar, 0, Qt.AlignLeft)
        self.titleBar.layout().insertStretch(1, 1)
        self.setMenuWidget(self.titleBar)

        self.mainWidget = QWidget(self)
        self.mainWidget.setObjectName("main-widget")
        self.mainWidget.setStyleSheet("#main-widget:focus {border: none;}")
        self.vbox_layout = QVBoxLayout(self.mainWidget)
        self.vbox_layout.setStretch(0, 0)
        self.vbox_layout.setStretch(1, 1)
        self.vbox_layout.setSpacing(0)
        self.vbox_layout.setContentsMargins(2, 2, 2, 2)

        self.colors = {
            "dark": "#485057",
            "light": "#d4d7d9"
        }
        self.styles = {}
        for style in ["dark", "light"]:
            with open(getPath(f"theme/{style}.qss")) as f:
                self.styles[style] = f.read()
        self.setTheme("dark")

        self.icon = QIcon()
        for size in [16, 24, 32, 48, 64, 128, 256]:
            filename = f"icon{size}x{size}.png"
            fullPath = os.path.join("icons", "window", filename)
            img = Image.open(getPath(fullPath))
            pixmap = QPixmap()
            pixmap.loadFromData(img.tobytes())
            self.icon.addPixmap(pixmap)
        self.setWindowIcon(self.icon)

    def toggle_theme(self):
        if self.theme == "dark":
            self.setTheme("light")
        else:
            self.setTheme("dark")

    def setTheme(self, theme):
        self.theme = theme
        self.app.setStyleSheet(self.styles[self.theme])
        self.titleBar.setStyleSheet(f"background-color: {self.colors[self.theme]};")

    def closeEvent(self, event):
        self.app.quit_wrapper()
        event.ignore()

    def select_none(self):
        if not isinstance(self.app.focusWidget(), QLineEdit):
            self.app.hierarchy_content.tree_widget.clearSelection()

    def rename(self):
        self.app.hierarchy.tab_widget.setCurrentWidget(self.app.hierarchy)
        items = self.app.hierarchy_content.tree_widget.selectedItems()
        if len(items) == 1:
            self.app.hierarchy_content.tree_widget.editItem(items[0])

    def mousePressEvent(self, event):
        focused = self.focusWidget()
        if isinstance(focused, QLineEdit):
            focused.clearFocus()
        super(Window, self).mousePressEvent(event)

    def resizeEvent(self, event):
        super(Window, self).resizeEvent(event)
        padding = self.statusBar().height() + self.titleBar.height()
        self.mainWidget.resize(self.width(), self.height() - padding)
        self.mainWidget.move(0, self.titleBar.height())
        self.titleBar.raise_()
        self.app.editor.readjust()

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

    def add_button(self, icon, tip="", on=False):
        button = QToolButton(self)
        button.setIcon(QIcon(getPath("icons/buttons/" + icon)))
        button.setStatusTip(tip)
        button.setCheckable(True)
        button.setChecked(on)
        self.buttons.append(button)
        self.hbox_layout.insertWidget(len(self.buttons), button)

class ToolBar(QMenuBar):
    def __init__(self, instance):
        super(ToolBar, self).__init__(instance)
        self.setStyleSheet("ToolBar {vertical-align: middle; padding: 4px;}")
        self.setFont(QFont("Segoe UI", 10))
        self.instance = instance
        self.menus = {}
        self.sub_menus = {}

    def add_menu(self, name):
        if name in self.menus:
            return
        menu = self.addMenu("&" + name)
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

class Editor(QSplitter):
    def __init__(self, window):
        super(Editor, self).__init__(Qt.Horizontal, window)
        self.setHandleWidth(2)
        self.setChildrenCollapsible(False)
        self.columnWidgets = []
        self.stretch = []
        self.splitterMoved.connect(self.setWidth)

    def readjust(self):
        part = self.width() / sum(self.stretch)
        self.setSizes([int(stretch * part) for stretch in self.stretch])

        for column in self.columnWidgets:
            column.readjust()

    def setWidth(self, pos, index):
        part = self.height() / sum(self.stretch)
        original = self.stretch[index - 1] * part
        diff = (pos - original) / part
        self.stretch[index - 1] += diff
        self.stretch[index] -= diff

    def add_tab(self, name, row, column):
        if len(self.columnWidgets) <= column:
            column = len(self.columnWidgets)
            columnWidget = Column(self)
            self.addWidget(columnWidget)
            self.stretch.append(1)
            self.columnWidgets.append(columnWidget)
        else:
            columnWidget = self.columnWidgets[column]
        return columnWidget.add_tab(name, row)

    def set_stretch(self, stretch):
        if len(stretch) != len(self.columnWidgets):
            raise ValueError("Argument 1: expected %d length, got %d length" % \
                (len(stretch), len(self.columnWidgets)))
        self.stretch = list(stretch)

class Column(QSplitter):
    def __init__(self, parent):
        super(Column, self).__init__(Qt.Vertical, parent)
        self.setHandleWidth(2)
        self.setChildrenCollapsible(False)
        self.tab_widgets = []
        self.tabs = []
        self.stretch = []
        self.splitterMoved.connect(self.setWidth)

    def readjust(self):
        part = self.height() / sum(self.stretch)
        self.setSizes([int(stretch * part) for stretch in self.stretch])

    def setWidth(self, pos, index):
        part = self.height() / sum(self.stretch)
        original = self.stretch[index - 1] * part
        diff = (pos - original) / part
        self.stretch[index - 1] += diff
        self.stretch[index] -= diff

    def add_tab(self, name, row):
        if len(self.tabs) <= row:
            row = len(self.tabs)
            tab_widget = TabGroup(self)
            self.addWidget(tab_widget)
            self.stretch.append(1)
            self.tab_widgets.append(tab_widget)
            self.tabs.append([])
        else:
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
        self.setLayout(self.vbox_layout)

        self.spacer = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.vbox_layout.addSpacerItem(self.spacer)

        self.tab_widget.addTab(self, self.name)
        self.content = None

    def set_window(self, content):
        self.content = content
        self.content.setParent(self)
        self.vbox_layout.insertWidget(0, self.content)
        if hasattr(type(content), "SPACER"):
            self.vbox_layout.removeItem(self.spacer)
            del self.spacer
        return self.content
