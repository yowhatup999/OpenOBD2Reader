from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect
from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor

class GlowingFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(10, 10, 10, 10)

        # setup shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(40)
        self.shadow.setOffset(0, 0)
        self.shadow.setColor(QColor(255, 0, 0, 160))  # startfarbe
        self.setGraphicsEffect(self.shadow)

        # rainbow-farbverlauf
        self.colors = [
            QColor(0, 191, 255, 160),     # blue
            QColor(186, 85, 211, 160),    # purple
            QColor(255, 69, 0, 160),      # red-orange
            QColor(255, 165, 0, 160),     # orange
            QColor(0, 255, 127, 160),     # greenish
            QColor(0, 191, 255, 160),     # back to blue
        ]
        self.color_index = 0

        # animation
        self.animation = QPropertyAnimation(self.shadow, b"color")
        self.animation.setDuration(1200)
        self.animation.setEasingCurve(QEasingCurve.InOutSine)
        self.animation.setLoopCount(1)

        # timer für rotation
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotateGlow)
        self.timer.start(1200)

    def rotateGlow(self):
        current_color = self.shadow.color()
        next_color = self.colors[self.color_index]
        self.animation.stop()
        self.animation.setStartValue(current_color)
        self.animation.setEndValue(next_color)
        self.animation.start()

        self.color_index = (self.color_index + 1) % len(self.colors)
