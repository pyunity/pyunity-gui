from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDoubleValidator, QFont, QIntValidator
import re
import pyunity as pyu

regex = re.compile("(?<![A-Z])[A-Z][a-z]*|(?<![a-z])[a-z]+|\\d*")
def capitalize(string):
    match = re.findall(regex, string)
    while "" in match:
        match.remove("")
    return " ".join(map(lambda a: a.capitalize(), match))

# test string clearBoxColor5_3withoutLines
# turns into Clear Box Color 5 3 Without Lines

def isfloat(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

class Inspector(QWidget):
    def __init__(self, parent):
        super(Inspector, self).__init__(parent)
        self.vbox_layout = QVBoxLayout(self)
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vbox_layout)
        self.sections = []
    
    def add_section(self, name):
        section = InspectorSection(name, self)
        self.sections.append(section)
        self.vbox_layout.addWidget(section)
        return section

    def load(self, gameObject=None):
        num = len(self.sections)
        self.sections = []
        for i in range(num):
            item = self.vbox_layout.takeAt(0)
            widget = item.widget()
            self.vbox_layout.removeItem(item)
            widget.deleteLater()
        if gameObject is None:
            return
        main_section = self.add_section("GameObject")
        main_section.add_value("Name", str)
        main_section.add_value("Tag", int)
        for component in gameObject.components:
            section = self.add_section(component.__class__.__name__)
            for name, val in component.shown.items():
                if val.type in InspectorSection.inputs:
                    section.add_value(name, val.type, getattr(component, name))
                else:
                    section.add_value(name, None)

class InspectorSection(QWidget):
    large_font = QFont("Segoe UI", 12)
    def __init__(self, name, parent):
        super(InspectorSection, self).__init__(parent)
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 2)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)

        self.name = name
        self.header = QLabel(self.name, self)
        self.header.setFont(self.__class__.large_font)
        self.grid_layout.addWidget(self.header)
        self.grid_layout.addWidget(QWidget(self))
        self.setLayout(self.grid_layout)
        self.fields = {None: None}
    
    def add_value(self, name, type, value=None):
        label = QLabel(capitalize(name), self)
        label.setWordWrap(True)

        if type not in self.__class__.inputs:
            raise ValueError("Cannot create input box of type \"" + type.__name__ + "\"")
        input_box = self.__class__.inputs[type](self)
        if isinstance(input_box, InspectorInput):
            input_box.label = label
            if value is not None:
                input_box.setText(str(value))
        self.fields[name] = [type, input_box]

        self.grid_layout.addWidget(label)
        self.grid_layout.addWidget(input_box)

    def new_str(self):
        return InspectorTextEdit(self, str)
    
    def new_int(self):
        line_edit = InspectorTextEdit(self, int)
        line_edit.setValidator(QIntValidator(self))
        return line_edit
    
    def new_float(self):
        line_edit = InspectorTextEdit(self, float)
        line_edit.setValidator(QDoubleValidator(self))
        return line_edit
    
    def new_misc(self):
        blank = QWidget(self)
        return blank
    
    def new_vector3(self):
        input = InspectorVector3Edit(self)
        return input
    
    inputs = {str: new_str, int: new_int, float: new_float, pyu.Vector3: new_vector3, None: new_misc}

class InspectorInput(QWidget):
    pass

class InspectorTextEdit(QLineEdit, InspectorInput):
    def __init__(self, parent, type):
        super(InspectorTextEdit, self).__init__(parent)
        self.textEdited.connect(self.on_edit)
        self.modified = False
        self.type = type
    
    def on_edit(self, text):
        if not isfloat(text):
            self.setText("0")
            return
        self.modified = True
        font = self.label.font()
        font.setBold(self.modified)
        self.label.setFont(font)
    
    def get(self):
        return self.type(self.text())

class InspectorVector3Edit(InspectorInput):
    def __init__(self, parent):
        super(InspectorVector3Edit, self).__init__(parent)
        self.labels = [QLabel("X", self), QLabel("Y", self), QLabel("Z", self)]
        self.inputs = [QLineEdit(self), QLineEdit(self), QLineEdit(self)]
        for i in range(len(self.inputs)):
            self.inputs[i].setValidator(QDoubleValidator(self.inputs[i]))
            self.inputs[i].editingFinished.connect(self.on_edit(i))
        
        self.hbox_layout = QHBoxLayout(self)
        self.hbox_layout.setSpacing(2)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
        for i in range(3):
            self.hbox_layout.addWidget(self.labels[i])
            self.hbox_layout.addWidget(self.inputs[i])
        
        self.modified = False
    
    def setText(self, vec):
        x, y, z = vec[8: -1].split(", ")
        self.inputs[0].setText(x)
        self.inputs[1].setText(y)
        self.inputs[2].setText(z)
    
    def get(self):
        x = float(self.inputs[0].text())
        y = float(self.inputs[0].text())
        z = float(self.inputs[0].text())
        return pyu.Vector3(x, y, z)
    
    def on_edit(self, input):
        def inner():
            text = self.inputs[input].text()
            if not isfloat(text):
                self.inputs[input].setText("0")
                return
            self.inputs[input].setText(str(float(text)))
            self.modified = True
            font = self.labels[input].font()
            font.setBold(self.modified)
            self.labels[input].setFont(font)
            
            font = self.label.font()
            font.setBold(self.modified)
            self.label.setFont(font)
        return inner

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

class Hierarchy(QTreeWidget):
    SPACER = None
    def __init__(self, parent):
        super(Hierarchy, self).__init__(parent)
        self.items = []
        self.header().setVisible(False)
        self.setIndentation(10)
        self.itemClicked.connect(self.on_click)
        self.inspector = None
    
    def add_item(self, gameObject, parent=None):
        item = HierarchyItem(gameObject)
        if parent is None:
            self.items.append(item)
            self.addTopLevelItem(item)
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
        self.inspector.load(item.gameObject)
