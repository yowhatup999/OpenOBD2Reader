from PySide6.QtWidgets import QFrame
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QConicalGradient, QColor, QPen, QBrush

class GlowingWindowFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0

        self._enabled = True

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.updateGlow)
        self._timer.start(16)

        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.lower()

    def updateGlow(self):
        self._angle = (self._angle + 1) % 360
        self.update()

    def paintEvent(self, event):
        if not self._enabled:
            return super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(20, 20, -20, -20)
        center = rect.center()

        gradient = QConicalGradient(center, -self._angle)
        gradient.setColorAt(0.0, QColor(0, 191, 255, 100))
        gradient.setColorAt(0.25, QColor(186, 85, 211, 100))
        gradient.setColorAt(0.5, QColor(255, 69, 0, 100))
        gradient.setColorAt(0.75, QColor(255, 165, 0, 100))
        gradient.setColorAt(1.0, QColor(0, 191, 255, 100))

        # weiche "Aura"
        pen = QPen(QBrush(gradient), 80)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)

        painter.setPen(pen)
        painter.drawRoundedRect(rect, 60, 60)
