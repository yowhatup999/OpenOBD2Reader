from PySide6.QtWidgets import QFrame
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QConicalGradient, QColor, QPen, QBrush

class GlowingAnimatedFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update_animation)
        self._timer.start(16)  # ~60fps
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setContentsMargins(10, 10, 10, 10)

    def update_animation(self):
        self._angle = (self._angle + 1) % 360
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(5, 5, -5, -5)
        center = rect.center()

        # Apple-like rotierender Farbverlauf
        gradient = QConicalGradient(center, -self._angle)
        gradient.setColorAt(0.0, QColor(0, 191, 255, 200))    # cyan
        gradient.setColorAt(0.25, QColor(186, 85, 211, 200))  # lila
        gradient.setColorAt(0.5, QColor(255, 69, 0, 200))     # rot
        gradient.setColorAt(0.75, QColor(255, 165, 0, 200))   # orange
        gradient.setColorAt(1.0, QColor(0, 191, 255, 200))    # cyan (loop)

        # Dünner animierter Rand
        pen = QPen(QBrush(gradient), 2.5)  # dünner rand!
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 12, 12)
