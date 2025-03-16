from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

# Farbkonstanten für den Glow-Effekt
COLOR_PRIMARY = QColor(138, 43, 226, 120)  # Dunkel-Lila (leicht transparent)
COLOR_BLUE = QColor(30, 144, 255, 100)  # Blau (sanfte Intensität)
COLOR_MAGENTA = QColor(255, 20, 147, 90)  # Magenta (leichte Deckkraft)
COLOR_CYAN = QColor(0, 255, 255, 100)  # Türkis (dezenter Farbton)

def create_glow_effect(widget):
    """Erzeugt einen subtilen Rand-Glow."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(20)  # Kleinerer Radius für schwächeren Glow
    effect.setOffset(0, 0)  # Glow bleibt um das Element herum
    effect.setColor(COLOR_PRIMARY)  # Startfarbe
    widget.setGraphicsEffect(effect)
    return effect

def animate_glow_color(effect):
    """Farbwechsel für den Glow mit sanften Übergängen."""
    animation = QPropertyAnimation(effect, b"color")
    animation.setDuration(25000)  # Langsame Farbwechsel
    animation.setLoopCount(-1)
    animation.setEasingCurve(QEasingCurve.InOutSine)

    # Sanfte Farbverläufe mit niedriger Opacity
    animation.setKeyValueAt(0.0, COLOR_PRIMARY)
    animation.setKeyValueAt(0.3, COLOR_BLUE)
    animation.setKeyValueAt(0.6, COLOR_MAGENTA)
    animation.setKeyValueAt(0.9, COLOR_CYAN)
    animation.setKeyValueAt(1.0, COLOR_PRIMARY)

    animation.start()
    return animation
