from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer
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

def animate_hue_shift(widget):
    """Erstellt eine sanfte Hintergrund-Farbanimation im HUE-Farbspektrum"""
    animation = QPropertyAnimation(widget, b"styleSheet")
    animation.setDuration(5000)  # Dauer eines Farbwechsels
    animation.setLoopCount(-1)  # Endlos wiederholen
    animation.setEasingCurve(QEasingCurve.InOutQuad)

    colors = [
        "background-color: rgb(255, 0, 0);",   # Rot
        "background-color: rgb(255, 165, 0);", # Orange
        "background-color: rgb(255, 255, 0);", # Gelb
        "background-color: rgb(0, 255, 0);",   # Grün
        "background-color: rgb(0, 255, 255);", # Türkis
        "background-color: rgb(0, 0, 255);",   # Blau
        "background-color: rgb(128, 0, 128);"  # Lila
    ]

    for i, color in enumerate(colors):
        animation.setKeyValueAt(i / (len(colors) - 1), color)

    animation.start()

    # Timer erstellen, um das StyleSheet zu aktualisieren
    def update_style():
        widget.setStyleSheet(colors[0])  # Setzt den ersten Farbwert als Startfarbe

    timer = QTimer()
    timer.timeout.connect(update_style)
    timer.start(5000)  # Aktualisiert alle 5 Sekunden

    return animation