from PySide6.QtCore import (
    Signal, Qt, QParallelAnimationGroup, QPropertyAnimation, QAbstractAnimation, QTimer)
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from .smoothScroll import QSmoothListWidget, QSmoothScrollArea
import pyunity as pyu
import re

# test string "clearBoxColor5_3withoutLines"
# turns into "Clear Box Color 5 3 Without Lines"

regex = re.compile("(?<![A-Z])[A-Z][a-z]*|(?<![a-z])[a-z]+|\\d*")
def capitalize(string):
    match = re.findall(regex, string)
    while "" in match:
        match.remove("")
    return " ".join(map(str.capitalize, match))

def isfloat(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

class ComponentFinder(QMenu):
    def __init__(self, parent):
        super(ComponentFinder, self).__init__(parent)
        self.aboutToShow.connect(self.load)

        self.label = QLabel("Select Component", self)
        self.label.setStyleSheet("margin: 5px; margin-bottom: 0px")
        self.labelAction = QWidgetAction(self)
        self.labelAction.setDefaultWidget(self.label)
        self.addAction(self.labelAction)

        self.inputBox = QLineEdit(self)
        self.inputBox.setStyleSheet("margin: 5px; margin-bottom: 0px")
        self.inputBox.textEdited.connect(self.updateSearch)
        self.inputAction = QWidgetAction(self)
        self.inputAction.setDefaultWidget(self.inputBox)
        self.addAction(self.inputAction)

        self.listWidget = QSmoothListWidget(self)
        self.listWidget.setStyleSheet("margin: 5px 5px 10px")
        self.listAction = QWidgetAction(self)
        self.listAction.setDefaultWidget(self.listWidget)
        self.addAction(self.listAction)

        self.components = pyu.Loader.GetComponentMap()
        for name in sorted(self.components):
            self.listWidget.addItem(QListWidgetItem(name))
        self.listWidget.addItem(QListWidgetItem("Create a new Behaviour..."))

    def updateSearch(self, text):
        self.listWidget.clear()
        for name in sorted(self.components):
            if text.lower() in name.lower():
                self.listWidget.addItem(QListWidgetItem(name))
        self.listWidget.addItem(QListWidgetItem("Create a new Behaviour..."))

    def load(self):
        self.inputBox.clear()
        self.inputBox.setFocus()
        QWidget.setTabOrder(self.inputBox, self.listWidget)

class Inspector(QWidget):
    SPACER = True
    props = [pyu.ShowInInspector(str, "", "name"), pyu.ShowInInspector(int, "", "tag")]
    font = QFont("Segoe UI", 12)

    def __init__(self, parent):
        super(Inspector, self).__init__(parent)
        self.baseLayout = QGridLayout(self)
        self.baseLayout.setContentsMargins(0, 0, 0, 0)
        self.baseLayout.setAlignment(Qt.AlignTop)
        self.setLayout(self.baseLayout)
        self.baseWidget = QWidget(self)

        self.vbox_layout = QVBoxLayout(self.baseWidget)
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.vbox_layout.setAlignment(Qt.AlignTop)
        self.baseWidget.setLayout(self.vbox_layout)

        self.scrollArea = QSmoothScrollArea(self)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.baseWidget)
        self.baseLayout.addWidget(self.scrollArea)

        self.sections = []

        self.button = QPushButton("Add Component")
        self.button.setStyleSheet("QPushButton { margin: 10px; }"
                                  "QPushButton::menu-indicator{ image: none; }")
        self.finder = ComponentFinder(self.button)
        self.finder.listWidget.itemDoubleClicked.connect(self.addComponent)
        callback = lambda: self.addComponent(self.finder.listWidget.item(0))
        self.finder.inputBox.returnPressed.connect(callback)
        self.button.setMenu(self.finder)

        self.buffer = self.add_buffer("Select a GameObject in the Hiearchy tab to view its properties.")

    def add_buffer(self, text):
        label = QLabel(text)
        label.setTextFormat(Qt.RichText)
        label.setStyleSheet("margin: 5px")
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
        if isinstance(component, pyu.Component):
            for name, val in component._shown.items():
                section.add_value(name, val, getattr(component, name))
            section.adjustHeight()
        return section

    def load(self, hierarchyItem):
        self.currentItem = None
        self.sections = []
        for i in range(self.vbox_layout.count()):
            item = self.vbox_layout.takeAt(0)
            widget = item.widget()
            self.vbox_layout.removeItem(item)
            if widget not in [self.button]:
                widget.deleteLater()
            else:
                widget.setParent(None)
        if hierarchyItem == []:
            self.buffer = self.add_buffer("Select a single item to view its properties.")
            return
        elif hierarchyItem is None:
            self.buffer = self.add_buffer("Select a GameObject in the Hiearchy tab to view its properties.")
            return
        self.currentItem = hierarchyItem
        self.gameObject = hierarchyItem.gameObject

        self.main_section = self.add_section(self.gameObject)
        self.main_section.component = self.gameObject

        self.name_input = self.main_section.add_value("name", self.props[0], self.gameObject.name)
        self.name_input.edited.connect(hierarchyItem.rename)
        tag_input = self.main_section.add_value("tag", self.props[1], self.gameObject.tag.tag)
        tag_input.prevent_modify = True # temporarily until i implement tag dropdowns
        enabled_input = self.main_section.add_value("enabled", pyu.ShowInInspector(bool, True, "enabled"), True)
        enabled_input.edited.connect(hierarchyItem.toggle)
        self.main_section.adjustHeight()

        for component in self.gameObject.components:
            self.add_section(component)

        self.addComponentButton()

    def addComponentButton(self):
        if self.button in self.vbox_layout.children():
            self.vbox_layout.removeWidget(self.button)
        self.vbox_layout.addWidget(self.button)

    def addComponent(self, item):
        self.finder.close()
        if item.text() == "Create a new Behaviour...":
            pass
        else:
            componentType = self.finder.components[item.text()]
            component = self.gameObject.AddComponent(componentType)
            self.add_section(component)
            self.addComponentButton()
        scrollBar = self.scrollArea.verticalScrollBar()
        QTimer.singleShot(1, lambda: scrollBar.setValue(scrollBar.maximum()))

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

class AutoSelectLineEdit(QLineEdit):
    def __init__(self, parent):
        super(AutoSelectLineEdit, self).__init__(parent)
        self.readyToEdit = True

    def setText(self, text):
        super(AutoSelectLineEdit, self).setText(text)
        self.setCursorPosition(0)

    def mouseReleaseEvent(self, event):
        super(AutoSelectLineEdit, self).mouseReleaseEvent(event)
        if not self.selectedText():
            if self.readyToEdit:
                self.selectAll()
                self.readyToEdit = False
        else:
            self.readyToEdit = False

    def focusOutEvent(self, e):
        super(AutoSelectLineEdit, self).focusOutEvent(e)
        self.readyToEdit = True
        self.setCursorPosition(0)

class InspectorTextEdit(AutoSelectLineEdit, InspectorInput):
    edited = Signal(object)
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
    edited = Signal(object)
    def __init__(self, parent, prop, orig):
        super(InspectorIntEdit, self).__init__(parent, prop, orig)
        self.value = 0
        self.setText("0")
        self.setValidator(QIntValidator(self))

    def on_edit(self):
        super(InspectorIntEdit, self).on_edit(int(self.text()))

class InspectorFloatEdit(InspectorTextEdit):
    edited = Signal(object)
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
    edited = Signal(object)
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
    edited = Signal(object)
    def __init__(self, parent, prop, orig):
        super(InspectorVector3Edit, self).__init__(parent)
        self.prop = prop
        self.orig = orig
        self.labels = [QLabel("X", self), QLabel("Y", self), QLabel("Z", self)]
        self.inputs = [AutoSelectLineEdit(self), AutoSelectLineEdit(self), AutoSelectLineEdit(self)]
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
    edited = Signal(object)
    def __init__(self, parent, prop, orig):
        super(InspectorQuaternionEdit, self).__init__(parent)
        self.prop = prop
        self.orig = orig
        self.labels = [QLabel("X", self), QLabel("Y", self), QLabel("Z", self)]
        self.inputs = [AutoSelectLineEdit(self), AutoSelectLineEdit(self), AutoSelectLineEdit(self)]
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
        q = pyu.Quaternion.Euler(pyu.Vector3(x, y, z))
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
    largeFont = QFont("Segoe UI", 12)
    edited = Signal(object, object, object, str)

    def __init__(self, name, parent):
        super(InspectorSection, self).__init__(parent)
        self.toggleButton = QToolButton(self)
        self.toggleButton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.toggleButton.setFont(self.largeFont)
        self.toggleButton.setStyleSheet("QToolButton { margin: 0px; border: none; }")
        self.toggleButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggleButton.setArrowType(Qt.DownArrow)
        self.toggleButton.setText(name)
        self.toggleButton.setCheckable(True)
        self.toggleButton.setChecked(False)
        self.toggleButton.clicked.connect(self.toggle)

        self.contentArea = QFrame(self)
        self.contentArea.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.contentArea.setMaximumHeight(0)
        self.contentArea.setMinimumHeight(0)

        self.toggleAnimation = QParallelAnimationGroup(self)
        self.toggleAnimation.addAnimation(QPropertyAnimation(self, b"minimumHeight"))
        self.toggleAnimation.addAnimation(QPropertyAnimation(self, b"maximumHeight"))
        self.toggleAnimation.addAnimation(
            QPropertyAnimation(self.contentArea, b"maximumHeight"))

        self.opened = True
        self.mainLayout = QGridLayout(self)
        self.mainLayout.setVerticalSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.toggleButton, 0, 0, 1, 1, Qt.AlignLeft)
        self.mainLayout.addWidget(self.contentArea, 1, 0, 1, 2, Qt.AlignLeft)
        self.setLayout(self.mainLayout)

        self.grid_layout = QGridLayout(self.contentArea)
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 2)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)

        self.name = name
        self.component = None
        self.prevent_modify = False
        self.fields = {}

        self.label = QLabel("No properties", self)
        self.grid_layout.addWidget(self.label, 0, 0, 1, 2)

        self.contentArea.setLayout(self.grid_layout)
        self.adjustHeight()

    def toggle(self):
        if not self.opened:
            self.toggleButton.setArrowType(Qt.DownArrow)
            self.toggleAnimation.setDirection(QAbstractAnimation.Forward)
            self.opened = True
        else:
            self.toggleButton.setArrowType(Qt.RightArrow)
            self.toggleAnimation.setDirection(QAbstractAnimation.Backward)
            self.opened = False
        self.toggleButton.setChecked(False)
        self.toggleAnimation.start()

    def adjustHeight(self):
        collapsedHeight = self.sizeHint().height() - self.contentArea.maximumHeight()
        contentHeight = self.contentArea.sizeHint().height()
        for i in range(self.toggleAnimation.animationCount() - 1):
            anim = self.toggleAnimation.animationAt(i)
            anim.setDuration(300)
            anim.setStartValue(collapsedHeight)
            anim.setEndValue(collapsedHeight + contentHeight)
        contentAnimation = self.toggleAnimation.animationAt(
            self.toggleAnimation.animationCount() - 1)
        contentAnimation.setDuration(300)
        contentAnimation.setStartValue(0)
        contentAnimation.setEndValue(contentHeight)

        # Open section
        self.toggleAnimation.setCurrentTime(300)
        self.setMinimumHeight(collapsedHeight + contentHeight)
        self.setMaximumHeight(collapsedHeight + contentHeight)
        self.contentArea.setMaximumHeight(contentHeight)

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
