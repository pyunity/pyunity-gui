__all__ = ["SmoothMode", "QAbstractSmoothScrollArea", "QSmoothScrollArea", "QSmoothListWidget"]

from PyQt5.QtCore import QTimer, Qt, QDateTime, QPoint
from PyQt5.QtWidgets import QAbstractScrollArea, QApplication, QScrollArea, QListWidget
from PyQt5.QtGui import QWheelEvent
import math
import enum

class SmoothMode(enum.Enum):
    NO_SMOOTH = enum.auto()
    CONSTANT = enum.auto()
    LINEAR = enum.auto()
    QUADRATIC = enum.auto()
    COSINE = enum.auto()

class QAbstractSmoothScrollArea(QAbstractScrollArea):
    def __init__(self, parent=None):
        super(QAbstractSmoothScrollArea, self).__init__(parent)
        self.lastWheelEvent = 0
        self.smoothMoveTimer = QTimer(self)
        self.smoothMoveTimer.timeout.connect(self.slotSmoothMove)

        self.fps = 60
        self.duration = 400
        self.smoothMode = SmoothMode.COSINE
        self.acceleration = 2.5

        self.smallStepModifier = Qt.SHIFT
        self.smallStepRatio = 1/5
        self.bigStepModifier = Qt.ALT
        self.bigStepRatio = 5

        self.scrollStamps = []
        self.stepsLeftQueue = []

    def wheelEvent(self, event):
        if self.smoothMode == SmoothMode.NO_SMOOTH:
            super(QAbstractSmoothScrollArea, self).wheelEvent(event)
            return

        now = QDateTime.currentDateTime().toMSecsSinceEpoch()
        self.scrollStamps.append(now)
        while now - self.scrollStamps[0] > 500:
            self.scrollStamps.pop(0)
        accelerationRatio = min(len(self.scrollStamps) / 15, 1)

        if not self.lastWheelEvent:
            self.lastWheelEvent = QWheelEvent(event)
        else:
            self.lastWheelEvent = event

        self.stepsTotal = self.fps * self.duration // 1000
        multiplier = 1
        if QApplication.keyboardModifiers() & self.smallStepModifier:
            multiplier *= self.smallStepRatio
        if QApplication.keyboardModifiers() & self.bigStepModifier:
            multiplier *= self.bigStepRatio
        delta = event.angleDelta().y() * multiplier
        if self.acceleration > 0:
            delta += delta * self.acceleration * accelerationRatio

        self.stepsLeftQueue.append([delta, self.stepsTotal])
        self.smoothMoveTimer.start(1000 // self.fps)

    def slotSmoothMove(self):
        totalDelta = 0
        for pair in self.stepsLeftQueue:
            totalDelta += self.subDelta(*pair)
            pair[1] -= 1

        while len(self.stepsLeftQueue) and self.stepsLeftQueue[0][1] == 0:
            self.stepsLeftQueue.pop(0)

        event = QWheelEvent(
            self.lastWheelEvent.pos(),
            self.lastWheelEvent.globalPos(),
            QPoint(0, 0),
            QPoint(0, round(totalDelta)),
            self.lastWheelEvent.buttons(),
            Qt.NoModifier,
            self.lastWheelEvent.phase(),
            self.lastWheelEvent.inverted(),
            self.lastWheelEvent.source()
        )
        QApplication.sendEvent(self.verticalScrollBar(), event)

        if not self.stepsLeftQueue:
            self.smoothMoveTimer.stop()

    def subDelta(self, delta, stepsLeft):
        assert self.smoothMode != SmoothMode.NO_SMOOTH

        m = self.stepsTotal / 2
        x = abs(self.stepsTotal - stepsLeft - m)

        if self.smoothMode == SmoothMode.CONSTANT:
            return delta / self.stepsTotal
        elif self.smoothMode == SmoothMode.LINEAR:
            return 2 * delta / self.stepsTotal * (m - x) / m
        elif self.smoothMode == SmoothMode.QUADRATIC:
            return 0.75 / m * (1 - x * x / m / m) * delta
        elif self.smoothMode == SmoothMode.COSINE:
            return (math.cos(x * math.pi / m) + 1) / (2 * m) * delta
        return 0

class QSmoothScrollArea(QScrollArea, QAbstractSmoothScrollArea):
    def __init__(self, parent=None):
        QAbstractSmoothScrollArea.__init__(self, parent)
        QScrollArea.__init__(self, parent)

class QSmoothListWidget(QListWidget, QAbstractSmoothScrollArea):
    def __init__(self, parent=None):
        QAbstractSmoothScrollArea.__init__(self, parent)
        QListWidget.__init__(self, parent)
