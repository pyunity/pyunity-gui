from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import pyunity as pyu
import re

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
        main_section.add_value("Name", str, gameObject.name)
        main_section.add_value("Tag", int, gameObject.tag.tag)
        for component in gameObject.components:
            section = self.add_section(component.__class__.__name__)
            for name, val in component.shown.items():
                if val.type in InspectorSection.inputs:
                    section.add_value(val.name, val.type, getattr(component, name))
                else:
                    section.add_value(val.name, None)

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
        return InspectorTextEdit(self)
    
    def new_int(self):
        line_edit = InspectorIntEdit(self)
        return line_edit
    
    def new_float(self):
        line_edit = InspectorFloatEdit(self)
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
    def __init__(self, parent):
        super(InspectorTextEdit, self).__init__(parent)
        self.editingFinished.connect(self.on_edit)
        self.modified = False
        self.value = ""
    
    def on_edit(self, text):
        if text != self.value:
            self.modified = True
            font = self.label.font()
            font.setBold(self.modified)
            self.label.setFont(font)
        self.value = text
        self.setText(str(self.value))
    
    def get(self):
        return self.value

class InspectorIntEdit(InspectorTextEdit):
    def __init__(self, parent):
        super(InspectorIntEdit, self).__init__(parent)
        self.value = 0
        self.setText("0")
        self.setValidator(QIntValidator(self))
    
    def on_edit(self):
        super(InspectorIntEdit, self).on_edit(int(self.text()))

class InspectorFloatEdit(InspectorTextEdit):
    def __init__(self, parent):
        super(InspectorFloatEdit, self).__init__(parent)
        self.value = 0
        self.setText("0.0")
        self.setValidator(FloatValidator(self))
    
    def on_edit(self):
        super(InspectorFloatEdit, self).on_edit(float(self.text()))

class FloatValidator(QValidator):
    regex = re.compile("[-+]?((?:[0-9]*[.])?[0-9]+)([eE][-+]?\\d+)?")
    regexes = [
        (re.compile("[-+]?"), "0.0"),
        (re.compile("[-+]?[.]"), "0.0"),
        (re.compile("([-+]?((?:[0-9]*[.])?[0-9]+))[eE]"), "\\1"),
        (re.compile("([-+]?((?:[0-9]*[.])?[0-9]+))[eE][-+]"), "\\1")
    ]
    def validate(self, input, pos):
        if not isfloat(input):
            if self.check(input) is not None:
                return QValidator.Intermediate, input, pos
            return QValidator.Invalid, input, pos
        return QValidator.Acceptable, input, pos
    
    def fixup(self, input):
        new = self.check(input)
        if new is not None:
            return new
        return input
    
    def check(self, string):
        for regex, replace in self.__class__.regexes:
            match = re.match(regex, string)
            if match is not None and match.group(0) == string:
                return re.sub(regex, replace, string, 1)

class InspectorVector3Edit(InspectorInput):
    def __init__(self, parent):
        super(InspectorVector3Edit, self).__init__(parent)
        self.labels = [QLabel("X", self), QLabel("Y", self), QLabel("Z", self)]
        self.inputs = [QLineEdit(self), QLineEdit(self), QLineEdit(self)]
        for i in range(len(self.inputs)):
            self.inputs[i].modified = False
            self.inputs[i].value = 0
            self.inputs[i].label = self.labels[i]
            self.inputs[i].setValidator(FloatValidator(self.inputs[i]))
            self.inputs[i].editingFinished.connect(self.on_edit(i))
        
        self.hbox_layout = QHBoxLayout(self)
        self.hbox_layout.setSpacing(2)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
        for i in range(3):
            self.hbox_layout.addWidget(self.labels[i])
            self.hbox_layout.addWidget(self.inputs[i])
        
        self.modified = False
        self.value = pyu.Vector3.zero()
    
    def setText(self, vec):
        x, y, z = vec[8: -1].split(", ")
        self.inputs[0].setText(str(float(x)))
        self.inputs[1].setText(str(float(y)))
        self.inputs[2].setText(str(float(z)))
    
    def get(self):
        x = float(self.inputs[0].text())
        y = float(self.inputs[0].text())
        z = float(self.inputs[0].text())
        return pyu.Vector3(x, y, z)
    
    def on_edit(self, input):
        def inner():
            text = float(self.inputs[input].text())
            print(text, self.value)
            if text != self.value[input]:
                self.modified = True
                font = self.label.font()
                font.setBold(self.modified)
                self.label.setFont(font)
                
                self.inputs[input].modified = True
                font = self.inputs[input].label.font()
                font.setBold(self.inputs[input].modified)
                self.inputs[input].label.setFont(font)
            vec = list(self.value)
            vec[input] = text
            self.value = pyu.Vector3(vec)
            self.setText(str(self.value))
        return inner
