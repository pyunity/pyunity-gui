import os
from PyQt5.QtGui import QIcon, QPixmap
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
    
    def rename(self, textedit):
        text = textedit.value
        self.setText(0, text)
        self.name = text
        assert self.gameObject.name == text

class Hierarchy(QWidget):
    SPACER = None
    def __init__(self, parent):
        super(Hierarchy, self).__init__(parent)
        self.vbox_layout = QVBoxLayout(self)
        self.vbox_layout.setContentsMargins(2, 2, 2, 2)
        self.vbox_layout.setSpacing(2)

        self.hbox_layout = QHBoxLayout()
        self.hbox_layout.setStretch(0, 1)
        icon = QLabel(self)
        icon.setPixmap(QPixmap(os.path.join("icons", "inspector", "logo.png")).scaled(16, 16))
        self.hbox_layout.addWidget(icon, 1)
        self.hbox_layout.addWidget(QLabel("Untitled Scene"))
        self.add_button = QPushButton(self)
        self.add_button.setIcon(QIcon(os.path.join("icons", "inspector", "add.png")))
        self.hbox_layout.addWidget(self.add_button)
        self.vbox_layout.addLayout(self.hbox_layout)

        self.items = []
        self.tree_widget = QTreeWidget(self)
        self.vbox_layout.addWidget(self.tree_widget)
        self.tree_widget.header().setVisible(False)
        self.tree_widget.setIndentation(10)
        self.tree_widget.itemClicked.connect(self.on_click)
        self.inspector = None
    
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
        items = {}
        for gameObject in self.loaded.rootGameObjects:
            items[gameObject] = self.add_item(gameObject)
        for gameObject in self.loaded.gameObjects:
            if gameObject.transform.parent is None:
                continue
            self.add_item(gameObject,
                items[gameObject.transform.parent.gameObject])

    def on_click(self, item, column):
        self.inspector.load(item)
