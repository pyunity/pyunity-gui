import os
import pyunity as pyu
from PyQt5.QtCore import QItemSelectionModel, QModelIndex
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *

class HierarchyItem(QTreeWidgetItem):
    def __init__(self, gameObject):
        super(HierarchyItem, self).__init__()
        self.setText(0, gameObject.name)
        self.name = gameObject.name
        self.gameObject = gameObject
        self.children = []
    
    def add_child(self, child):
        self.children.append(child)
        self.addChild(child)
    
    def selectAll(self):
        self.setSelected(True)
        for child in self.children:
            child.selectAll()
    
    def rename(self, textedit):
        text = textedit.value
        self.setText(0, text)
        self.name = text
        assert self.gameObject.name == text

    def toggle(self):
        self.gameObject.enabled = not self.gameObject.enabled

    def setBold(self, bold):
        font = self.font(0)
        font.setBold(bold)
        self.setFont(0, font)

class Hierarchy(QWidget):
    SPACER = None
    def __init__(self, parent):
        super(Hierarchy, self).__init__(parent)
        self.vbox_layout = QVBoxLayout(self)
        self.vbox_layout.setContentsMargins(2, 2, 2, 2)
        self.vbox_layout.setSpacing(2)

        self.hbox_layout = QHBoxLayout()
        # self.hbox_layout.setStretch(0, 1)
        self.title = QLabel("Untitled Scene")
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.vbox_layout.setSpacing(0)
        self.hbox_layout.addWidget(self.title)

        self.add_button = QToolButton(self)
        self.add_button.setIcon(QIcon(os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "icons", "inspector", "add.png")))
        self.add_button.setStyleSheet("padding: 3px;")
        self.add_button.setPopupMode(QToolButton.InstantPopup)
        self.add_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.menu = QMenu()
        self.menu.addAction("New Root GameObject", self.new)
        self.menu.addAction("New Child GameObject", self.new_child)
        self.menu.addAction("New Sibling GameObject", self.new_sibling)
        self.add_button.setMenu(self.menu)

        self.hbox_layout.addWidget(self.add_button)
        self.vbox_layout.addLayout(self.hbox_layout)

        self.items = []
        self.tree_widget = CustomTreeWidget(self)
        self.vbox_layout.addWidget(self.tree_widget)
        self.tree_widget.itemSelectionChanged.connect(self.on_click)
        self.inspector = None
    
    def new(self):
        new = pyu.GameObject("GameObject")
        self.loaded.Add(new)
        self.add_item(new)

    def new_child(self):
        item = self.tree_widget.currentItem()
        if item is None:
            return self.new()
        parent = item.gameObject
        new = pyu.GameObject("GameObject", parent)
        self.loaded.Add(new)
        self.add_item(new, item)
    
    def new_sibling(self):
        sibling = self.tree_widget.currentItem()
        if sibling is None:
            return self.new()
        item = sibling.parent()
        if item is None:
            return self.new()
        parent = item.gameObject
        new = pyu.GameObject("GameObject", parent)
        self.loaded.Add(new)
        self.add_item(new, item)
    
    def remove(self):
        items = self.tree_widget.selectedItems()
        if len(items) == 0:
            print("Nothing selected")
            return
        
        for item in items:
            item.selectAll()
        items = self.tree_widget.selectedItems()
        for item in items:
            print("Removing", item.gameObject.name)
            if self.loaded.Has(item.gameObject):
                self.loaded.Remove(item.gameObject)

    def add_item(self, gameObject, parent=None):
        item = HierarchyItem(gameObject)
        if parent is None:
            self.items.append(item)
            self.tree_widget.addTopLevelItem(item)
        else:
            parent.add_child(item)
        return item
    
    def add_item_pos(self, gameObject, *args):
        item = HierarchyItem(gameObject)
        parent = self.items[args[0]]
        pos = args[1:]
        for num in pos:
            parent = parent.children[num]
        parent.add_child(item)
        return item
    
    def load_scene(self, scene):
        self.loaded = scene
        self.title.setText(scene.name)
        items = {}
        for gameObject in self.loaded.rootGameObjects:
            items[gameObject] = self.add_item(gameObject)
        for gameObject in self.loaded.gameObjects:
            if gameObject.transform.parent is None:
                continue
            self.add_item(gameObject,
                items[gameObject.transform.parent.gameObject])

    def on_click(self):
        items = self.tree_widget.selectedItems()
        if len(items) > 1:
            self.inspector.load([])
        elif len(items) == 0:
            self.inspector.load(None)
        else:
            self.inspector.load(items[0])
    
    def reset_bold(self):
        for item in self.items:
            item.setBold(False)

class CustomTreeWidget(QTreeWidget):
    def __init__(self, parent):
        super(CustomTreeWidget, self).__init__(parent)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.header().setVisible(False)
        self.setDragEnabled(True)
        # self.viewport().setAcceptDrops(True)
        # self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setIndentation(10)
        self.hierarchy = parent
    
    def selectAll(self):
        item = self.invisibleRootItem()
        for i in range(self.invisibleRootItem().childCount()):
            child = item.child(i)
            child.selectAll()
    
    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.addAction("New Root GameObject", self.hierarchy.new)
        menu.addAction("New Child GameObject", self.hierarchy.new_child)
        menu.addAction("New Sibling GameObject", self.hierarchy.new_sibling)

        num = len(self.selectedItems())
        if num > 0:
            menu.addSeparator()
            if num == 1:
                menu.addAction("Delete GameObject", self.hierarchy.remove)
            else:
                menu.addAction("Delete GameObjects", self.hierarchy.remove)

        menu.exec(event.globalPos())
        super(CustomTreeWidget, self).contextMenuEvent(event)

    # def mousePressEvent(self, event):
    #     item = self.indexAt(event.pos())
    #     super(CustomTreeWidget, self).mousePressEvent(event)
    #     if item.row() == -1 and item.column() == -1:
    #         self.clearSelection()
    #         self.selectionModel().setCurrentIndex(QModelIndex(), QItemSelectionModel.Select)

    def mouseMoveEvent(self, event):
        event.accept()
