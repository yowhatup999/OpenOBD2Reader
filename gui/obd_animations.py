from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

def create_glow_effect(widget, opacity=220):
    """Erzeugt einen leuchtenden RGB-Rahmen."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(25)
    effect.setOffset(0, 0)
    effect.setColor(QColor(138, 43, 226, opacity))  # Dunkles Lila als Grundfarbe
    widget.setGraphicsEffect(effect)
    return effect

def animate_frame_color(effect):
    """Weicher Farbwechsel für den Frame-Rand."""
    animation = QPropertyAnimation(effect, b"color")
    animation.setDuration(30000)  # 30 Sekunden für sanfte Übergänge
    animation.setLoopCount(-1)

    # Farbverlauf für modernes RGB-Styling
    animation.setKeyValueAt(0.0, QColor(138, 43, 226, 180))  # Dunkel-Lila
    animation.setKeyValueAt(0.25, QColor(30, 144, 255, 170))  # Blau
    animation.setKeyValueAt(0.5, QColor(255, 20, 147, 160))  # Magenta
    animation.setKeyValueAt(0.75, QColor(0, 255, 255, 175))  # Türkis
    animation.setKeyValueAt(1.0, QColor(138, 43, 226, 180))  # Zurück zu Dunkel-Lila

    animation.setEasingCurve(QEasingCurve.InOutSine)
    animation.start()
    return animation

def animate_background_color(widget):
    """Sanfter Farbwechsel für den Hintergrund von valuesFrame."""
    animation = QPropertyAnimation(widget, b"styleSheet")
    animation.setDuration(30000)  # Langsamer, sanfter Übergang
    animation.setLoopCount(-1)

    # Weicher Übergang zwischen dunklen und neonartigen Farben
    animation.setKeyValueAt(0.0, "background-color: rgba(50, 20, 80, 0.7);")  # Tiefes Lila
    animation.setKeyValueAt(0.25, "background-color: rgba(30, 10, 60, 0.7);")  # Dunkles Blau-Lila
    animation.setKeyValueAt(0.5, "background-color: rgba(20, 5, 40, 0.7);")  # Fast Schwarz mit Hauch von Lila
    animation.setKeyValueAt(0.75, "background-color: rgba(40, 15, 70, 0.7);")  # Etwas heller Lila-Blau
    animation.setKeyValueAt(1.0, "background-color: rgba(50, 20, 80, 0.7);")  # Zurück zu tiefem Lila

    animation.setEasingCurve(QEasingCurve.InOutQuad)
    animation.start()
    return animation
