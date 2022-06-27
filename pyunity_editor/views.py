import os
import pyunity as pyu
# from PySide6.QtCore import QItemSelectionModel, QModelIndex
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import *
from .smoothScroll import QSmoothTreeWidget
from .files import getPath

class HierarchyItem(QTreeWidgetItem):
    def __init__(self, gameObject):
        super(HierarchyItem, self).__init__()
        self.setFlags(self.flags() | Qt.ItemIsEditable)
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
        self.hbox_layout.setStretch(0, 1)
        self.title = QLabel("Untitled Scene")
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.vbox_layout.setSpacing(0)
        self.hbox_layout.addWidget(self.title)

        self.add_button = QToolButton(self)
        self.add_button.setIcon(QIcon(getPath("icons/inspector/add.png")))
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
        self.tree_widget.itemChanged.connect(self.rename)
        self.tree_widget.itemSelectionChanged.connect(self.on_click)
        self.inspector = None
        self.preview = None

    def new(self):
        new = pyu.GameObject("GameObject")
        self.loaded.Add(new)
        newitem = self.add_item(new)
        self.tree_widget.clearSelection()
        newitem.setSelected(True)

    def new_child(self):
        item = self.tree_widget.currentItem()
        if item is None:
            return self.new()
        parent = item.gameObject
        new = pyu.GameObject("GameObject", parent)
        self.loaded.Add(new)
        newitem = self.add_item(new, item)
        self.tree_widget.clearSelection()
        item.setExpanded(True)
        newitem.setSelected(True)
        newitem.setSelected(True)

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
        newitem = self.add_item(new, item)
        self.tree_widget.clearSelection()
        newitem.setSelected(True)

    def remove(self):
        items = self.tree_widget.selectedItems()
        if len(items) == 0:
            pyu.Logger.Log("Nothing selected")
            return

        for item in items:
            item.selectAll()
        items = self.tree_widget.selectedItems()
        self.items = []
        for item in items:
            pyu.Logger.Log("Removing", item.gameObject.name)
            if item.parent() is not None:
                item.parent().removeChild(item)
            else:
                idx = self.tree_widget.indexOfTopLevelItem(item)
                self.tree_widget.takeTopLevelItem(idx)
            if self.loaded.Has(item.gameObject):
                self.loaded.Destroy(item.gameObject)
        self.preview.update()

    def reparent(self, items):
        for item in items:
            index = self.tree_widget.indexFromItem(item).row()
            parent = item.parent()
            if parent is None:
                item.gameObject.transform.ReparentTo(None)
                print("Move", item.gameObject.name, "to root, index", index)
            else:
                print("Move", item.gameObject.name, "under", parent.gameObject.name, "index", index)
                parent.setExpanded(True)
                transform = item.gameObject.transform
                parentTransform = parent.gameObject.transform
                transform.ReparentTo(parentTransform)
                parentTransform.children.remove(transform)
                parentTransform.children.insert(index, transform)

    def rename(self, item, column):
        self.inspector.name_input.setText(item.text(column))
        item.gameObject.name = item.text(column)

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

class CustomTreeWidget(QSmoothTreeWidget):
    def __init__(self, parent):
        super(CustomTreeWidget, self).__init__(parent)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.header().setVisible(False)
        self.setAnimated(True)
        self.setIndentation(10)
        self.hierarchy = parent

        self.setDragEnabled(True)
        self.setDragDropOverwriteMode(False)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    def selectAll(self):
        item = self.invisibleRootItem()
        for i in range(self.invisibleRootItem().childCount()):
            child = item.child(i)
            child.selectAll()

    def dropEvent(self, event):
        items = self.selectedItems()
        super(CustomTreeWidget, self).dropEvent(event)
        for item in items:
            item.setSelected(True)
        self.hierarchy.reparent(items)

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
