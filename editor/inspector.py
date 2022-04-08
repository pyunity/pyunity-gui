from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import pyunity as pyu
import re

# test string "clearBoxColor5_3withoutLines"
# turns into "Clear Box Color 5 3 Without Lines"

regex = re.compile("(?<![A-Z])[A-Z][a-z]*|(?<![a-z])[a-z]+|\\d*")
def capitalize(string):
    match = re.findall(regex, string)
    while "" in match:
        match.remove("")
    return " ".join(map(lambda a: a.capitalize(), match))

def isfloat(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

class Inspector(QWidget):
    props = [pyu.ShowInInspector(str, "", "name"), pyu.ShowInInspector(int, "", "tag")]
    font = QFont("Segoe UI", 12)
    def __init__(self, parent):
        super(Inspector, self).__init__(parent)
        self.vbox_layout = QVBoxLayout(self)
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vbox_layout)
        self.sections = []

        self.buffer = self.add_buffer("Select a GameObject in the Hiearchy tab to view its properties.")

    def add_buffer(self, text):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setFont(self.__class__.font)
        self.vbox_layout.addWidget(label)
        return label

    def add_section(self, component):
        section = InspectorSection(component.__class__.__name__, self)
        section.component = component
        section.edited.connect(self.on_edit)
        self.sections.append(section)
        self.vbox_layout.addWidget(section)
        return section

    def load(self, hierarchyItem):
        self.currentItem = None
        if len(self.sections):
            list(self.sections[0].fields.keys())[0].edited.disconnect()
        num = len(self.sections)
        self.sections = []
        if self.buffer is not None:
            num += 1
            self.buffer = None
        for i in range(num):
            item = self.vbox_layout.takeAt(0)
            widget = item.widget()
            self.vbox_layout.removeItem(item)
            widget.deleteLater()
        if hierarchyItem == []:
            self.buffer = self.add_buffer("Select a single item to view its properties.")
            return
        elif hierarchyItem is None:
            self.buffer = self.add_buffer("Select a GameObject in the Hiearchy tab to view its properties.")
            return
        self.currentItem = hierarchyItem
        self.gameObject = hierarchyItem.gameObject

        main_section = self.add_section(self.gameObject)
        main_section.component = self.gameObject

        name_input = main_section.add_value("name", self.props[0], self.gameObject.name)
        name_input.edited.connect(hierarchyItem.rename)
        tag_input = main_section.add_value("tag", self.props[1], self.gameObject.tag.tag)
        tag_input.prevent_modify = True # temporarily until i implement tag dropdowns

        enabled_input = main_section.add_value("enabled", pyu.ShowInInspector(bool, True, "enabled"), True)
        enabled_input.edited.connect(hierarchyItem.toggle)

        for component in self.gameObject.components:
            section = self.add_section(component)
            for name, val in component.shown.items():
                section.add_value(name, val, getattr(component, name))

    def on_edit(self, section, item, value, attr):
        if hasattr(item, "prevent_modify") or section.component is None:
            return
        setattr(section.component, attr, value)
        self.currentItem.setBold(True)

    def reset_bold(self):
        for section in self.sections:
            section.reset_bold()

class InspectorInput(QWidget):
    pass

class InspectorTextEdit(QLineEdit, InspectorInput):
    edited = pyqtSignal(object)
    def __init__(self, parent, prop, orig):
        super(InspectorTextEdit, self).__init__(parent)
        self.prop = prop
        self.orig = orig
        self.modified = False
        self.value = ""
        self.editingFinished.connect(self.edit)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            # self.setText(str(self.value))
            self.clearFocus()
        super(InspectorTextEdit, self).keyPressEvent(event)

    def edit(self):
        self.on_edit()

    def on_edit(self, value=None):
        if value is None:
            value = self.text()
        if value != self.value:
            self.modified = True
            font = self.label.font()
            font.setBold(self.modified)
            self.label.setFont(font)
        self.value = value
        self.setText(str(self.value))
        self.edited.emit(self)

    def reset_bold(self):
        self.modified = False
        font = self.label.font()
        font.setBold(self.modified)
        self.label.setFont(font)

    def get(self):
        return self.value

class InspectorIntEdit(InspectorTextEdit):
    edited = pyqtSignal(object)
    def __init__(self, parent, prop, orig):
        super(InspectorIntEdit, self).__init__(parent, prop, orig)
        self.value = 0
        self.setText("0")
        self.setValidator(QIntValidator(self))

    def on_edit(self):
        super(InspectorIntEdit, self).on_edit(int(self.text()))

class InspectorFloatEdit(InspectorTextEdit):
    edited = pyqtSignal(object)
    def __init__(self, parent, prop, orig):
        super(InspectorFloatEdit, self).__init__(parent, prop, orig)
        self.value = 0
        self.setText("0.0")
        self.setValidator(FloatValidator(self))

    def on_edit(self):
        super(InspectorFloatEdit, self).on_edit(float(self.text()))

class FloatValidator(QValidator):
    regex = re.compile("[-+]?((?:[0-9]*[.])?[0-9]+)([eE][-+]?\\d+)?")
    regexes = [
        (re.compile("[-+]?"), "0.0"), # "-" or "+" or ""
        (re.compile("[-+]?[.]"), "0.0"), # "-."
        (re.compile("([-+]?((?:[0-9]*[.])?[0-9]+))[eE]"), "\\1"), # "-5.e" turns into "-5."
        (re.compile("([-+]?((?:[0-9]*[.])?[0-9]+))[eE][-+]"), "\\1") # "-5.e+" turns into "-5."
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

class InspectorBoolEdit(QCheckBox, InspectorInput):
    edited = pyqtSignal(object)
    def __init__(self, parent, prop, orig):
        super(InspectorBoolEdit, self).__init__(parent)
        self.setStyleSheet("QCheckBox{color: rgba(0,0,0,0);}")
        self.prop = prop
        self.orig = orig
        self.value = True
        self.label = None
        self.stateChanged.connect(self.on_edit)
        self.setChecked(True)

    def on_edit(self, state):
        value = state == Qt.Checked
        if value != self.value:
            self.modified = True
            font = self.label.font()
            font.setBold(self.modified)
            self.label.setFont(font)
        self.value = value
        self.setChecked(self.value)
        self.edited.emit(self)

    def reset_bold(self):
        self.modified = False
        font = self.label.font()
        font.setBold(self.modified)
        self.label.setFont(font)

    def setText(self, text):
        super(InspectorBoolEdit, self).setText(text)
        self.value = text == "True"
        self.setChecked(self.value)

    def get(self):
        return self.value

class InspectorVector3Edit(InspectorInput):
    edited = pyqtSignal(object)
    def __init__(self, parent, prop, orig):
        super(InspectorVector3Edit, self).__init__(parent)
        self.prop = prop
        self.orig = orig
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
        y = float(self.inputs[1].text())
        z = float(self.inputs[2].text())
        return pyu.Vector3(x, y, z)

    def on_edit(self, input):
        def inner():
            text = float(self.inputs[input].text())
            if text != self.value[input]:
                self.modified = True
                font = self.label.font()
                font.setBold(self.modified)
                self.label.setFont(font)

                self.inputs[input].modified = True
                font = self.inputs[input].label.font()
                font.setBold(self.inputs[input].modified)
                self.inputs[input].label.setFont(font)
            vec = list(self.get())
            vec[input] = text
            self.value = pyu.Vector3(vec)
            self.setText(str(self.value))
            self.edited.emit(self)
        return inner

    def reset_bold(self):
        self.modified = False
        font = self.label.font()
        font.setBold(self.modified)
        self.label.setFont(font)

        for input in self.inputs:
            input.modified = False
            font = input.label.font()
            font.setBold(input.modified)
            input.label.setFont(font)

class InspectorQuaternionEdit(InspectorInput):
    edited = pyqtSignal(object)
    def __init__(self, parent, prop, orig):
        super(InspectorQuaternionEdit, self).__init__(parent)
        self.prop = prop
        self.orig = orig
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

    def setText(self, quat):
        w, x, y, z = list(map(float, quat[11: -1].split(", ")))
        x, y, z = pyu.Quaternion(w, x, y, z).eulerAngles
        self.inputs[0].setText(str(float(x)))
        self.inputs[1].setText(str(float(y)))
        self.inputs[2].setText(str(float(z)))

    def setVec(self, vec):
        x, y, z = vec
        self.inputs[0].setText(str(float(x)))
        self.inputs[1].setText(str(float(y)))
        self.inputs[2].setText(str(float(z)))

    def get(self):
        x = float(self.inputs[0].text())
        y = float(self.inputs[1].text())
        z = float(self.inputs[2].text())
        q = pyu.Quaternion.identity()
        q.SetBackward(pyu.Vector3(x, y, z))
        return q

    def getVec(self):
        x = float(self.inputs[0].text())
        y = float(self.inputs[1].text())
        z = float(self.inputs[2].text())
        return pyu.Vector3(x, y, z)

    def on_edit(self, input):
        def inner():
            text = float(self.inputs[input].text())
            if text != self.value[input]:
                self.modified = True
                font = self.label.font()
                font.setBold(self.modified)
                self.label.setFont(font)

                self.inputs[input].modified = True
                font = self.inputs[input].label.font()
                font.setBold(self.inputs[input].modified)
                self.inputs[input].label.setFont(font)
            vec = list(self.getVec())
            vec[input] = text
            self.value = pyu.Vector3(vec)
            self.setVec(self.value)
            self.edited.emit(self)
        return inner

    def reset_bold(self):
        self.modified = False
        font = self.label.font()
        font.setBold(self.modified)
        self.label.setFont(font)

        for input in self.inputs:
            input.modified = False
            font = input.label.font()
            font.setBold(input.modified)
            input.label.setFont(font)

class InspectorSection(QWidget):
    large_font = QFont("Segoe UI", 12)
    edited = pyqtSignal(object, object, object, str)
    def __init__(self, name, parent):
        super(InspectorSection, self).__init__(parent)
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 2)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)

        self.name = name
        self.component = None
        self.prevent_modify = False

        self.header = QLabel(self.name, self)
        self.header.setFont(self.__class__.large_font)
        self.grid_layout.addWidget(self.header)
        self.grid_layout.addWidget(QWidget(self))

        self.label = QLabel("No properties", self)
        self.grid_layout.addWidget(self.label, 1, 0, 1, 2)

        self.setLayout(self.grid_layout)
        self.fields = {}

    def add_value(self, orig, prop, value=None):
        if len(self.fields) == 0:
            self.grid_layout.removeWidget(self.label)
            self.label.deleteLater()
        label = QLabel(capitalize(prop.name), self)
        label.setWordWrap(True)

        if prop.type not in self.__class__.inputs:
            input_box = QWidget(self)
        else:
            input_box = self.__class__.inputs[prop.type](self, prop, orig)
        if isinstance(input_box, InspectorInput):
            input_box.label = label
            if value is not None:
                input_box.setText(str(value))
            input_box.edited.connect(self.on_edit)
        self.fields[input_box] = [prop.name, prop.type]

        self.grid_layout.addWidget(label)
        self.grid_layout.addWidget(input_box)
        return input_box

    inputs = {
        str: InspectorTextEdit,
        int: InspectorIntEdit,
        float: InspectorFloatEdit,
        bool: InspectorBoolEdit,
        pyu.Vector3: InspectorVector3Edit,
        pyu.Quaternion: InspectorQuaternionEdit,
    }

    def on_edit(self, input):
        value = input.get()
        attr = self.fields[input][0]
        self.edited.emit(self, input, value, attr)

    def reset_bold(self):
        for box in self.fields:
            if isinstance(box, InspectorInput):
                box.reset_bold()
