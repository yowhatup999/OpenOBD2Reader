from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

# Farben als Konstanten auslagern
COLOR_PRIMARY = QColor(138, 43, 226, 180)  # Dunkel-Lila
COLOR_BLUE = QColor(30, 144, 255, 170)  # Blau
COLOR_MAGENTA = QColor(255, 20, 147, 160)  # Magenta
COLOR_CYAN = QColor(0, 255, 255, 175)  # Türkis
COLOR_DARK_BG = [
    "background-color: rgba(50,20,80,0.7);",
    "background-color: rgba(30,10,60,0.7);",
    "background-color: rgba(20,5,40,0.7);",
    "background-color: rgba(40,15,70,0.7);"
]

def create_glow_effect(widget, opacity=220):
    """Erzeugt einen leuchtenden Schatten."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(25)
    effect.setOffset(0, 0)
    effect.setColor(QColor(COLOR_PRIMARY.red(), COLOR_PRIMARY.green(), COLOR_PRIMARY.blue(), opacity))
    widget.setGraphicsEffect(effect)
    return effect

def animate_frame_color(effect):
    """Weicher Farbwechsel für den Rahmen."""
    animation = QPropertyAnimation(effect, b"color")
    animation.setDuration(30000)
    animation.setLoopCount(-1)
    animation.setEasingCurve(QEasingCurve.InOutSine)

    animation.setKeyValueAt(0.0, COLOR_PRIMARY)
    animation.setKeyValueAt(0.25, COLOR_BLUE)
    animation.setKeyValueAt(0.5, COLOR_MAGENTA)
    animation.setKeyValueAt(0.75, COLOR_CYAN)
    animation.setKeyValueAt(1.0, COLOR_PRIMARY)

    animation.start()
    return animation

def animate_background_color(widget):
    """Farbwechsel für den Hintergrund."""
    animation = QPropertyAnimation(widget, b"styleSheet")
    animation.setDuration(30000)
    animation.setLoopCount(-1)
    animation.setEasingCurve(QEasingCurve.InOutQuad)

    for i, color in enumerate(COLOR_DARK_BG):
        animation.setKeyValueAt(i / (len(COLOR_DARK_BG) - 1), color)

    animation.start()
    return animation
