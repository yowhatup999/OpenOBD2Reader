from PySide6.QtWidgets import (
    QFrame, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QGridLayout, QPlainTextEdit
)
from PySide6.QtCore import Qt, QPropertyAnimation

from gui.obd_animations import animate_hue_shift
from gui.GlowingAnimatedFrame import GlowingAnimatedFrame
from gui.GlowingFrame import GlowingFrame


def create_status_frame(parent):
    frame = GlowingAnimatedFrame(parent)
    frame.setObjectName("frameStatus")  # Objektname setzen
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(5, 5, 5, 5)
    layout.setSpacing(20)

    label_connection = QLabel("🔴 Verbindung: Offline", parent)
    label_connection.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label_connection.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")

    label_time = QLabel("⏱ --:-- UHR", parent)
    label_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label_time.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")

    layout.addWidget(label_connection, 1)
    layout.addWidget(label_time, 1)

    return frame, label_connection, label_time

def create_values_frame(parent):
    frame = QFrame(parent)
    frame.setObjectName("frameValues")
    layout = QGridLayout(frame)

    # Starte den Farbwechsel
    animate_hue_shift(frame)

    return frame, layout

def create_buttons_frame(parent, connect_callback, dummy_callback):
    frame = GlowingAnimatedFrame(parent)
    frame.setObjectName("frameButtons")  # Objektname setzen
    layout = QHBoxLayout(frame)
    layout.setSpacing(10)

    btn_connect = QPushButton("🔌 Connect", parent)
    btn_connect.setStyleSheet("font-size: 14px; color: white;")
    btn_connect.clicked.connect(lambda: connect_callback("important"))

    btn_dummy = QPushButton("🛠 Dummy-Simulation", parent)
    btn_dummy.setStyleSheet("font-size: 14px; color: white;")
    btn_dummy.clicked.connect(lambda: dummy_callback("dummy"))

    layout.addWidget(btn_connect)
    layout.addWidget(btn_dummy)

    return frame

def create_log_console(parent):
    """Erstellt eine Log-Konsole mit Titel und Einklapp-Funktion."""
    frame = QFrame(parent)
    frame.setObjectName("logFrame")
    frame.setStyleSheet("""
        QFrame#logFrame {
            border: 1px solid rgba(138, 43, 226, 0.3);
            border-radius: 12px;
        }
    """)

    layout = QVBoxLayout(frame)
    layout.setContentsMargins(5, 5, 5, 5)

    title_bar = QHBoxLayout()
    title_label = QLabel("Log", parent)
    title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")

    btn_toggle = QPushButton("━", parent)
    btn_toggle.setFixedSize(25, 25)
    btn_toggle.setStyleSheet("""
        QPushButton {
            background-color: rgba(138, 43, 226, 0.3);
            color: white;
            font-size: 14px;
            font-weight: bold;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: rgba(138, 43, 226, 0.6);
        }
    """)

    title_bar.addWidget(title_label)
    title_bar.addStretch()
    title_bar.addWidget(btn_toggle)

    log_console = QPlainTextEdit(parent)
    log_console.setReadOnly(True)
    log_console.setStyleSheet("""
        QPlainTextEdit {
            background-color: rgb(30, 30, 30);
            color: white;
            font-family: Consolas, Courier, monospace;
            font-size: 14px;
            border-radius: 5px;
            padding: 5px;
            border: 1px solid rgba(138, 43, 226, 0.3);
        }
    """)
    log_console.setMaximumHeight(200)  # Mehr Platz für Logs

    layout.addLayout(title_bar)
    layout.addWidget(log_console)

    # Animation für Einklappen
    animation = QPropertyAnimation(frame, b"maximumHeight")
    animation.setDuration(200)
    animation.setStartValue(200)  # Volle Höhe mit Log
    animation.setEndValue(55)  # Min-Höhe des eingeklappten Fensters
    frame.setMinimumHeight(55)  # Mindestens 80px, damit der Button passt!

    def toggle_log():
        """Minimiert oder maximiert das Log-Fenster in der UI."""
        if log_console.isVisible():
            log_console.setVisible(False)
            animation.setDirection(QPropertyAnimation.Forward)
            btn_toggle.setText("━")
        else:
            log_console.setVisible(True)
            animation.setDirection(QPropertyAnimation.Backward)
            btn_toggle.setText("━")
        animation.start()

    btn_toggle.clicked.connect(toggle_log)

    frame.log_console = log_console  # WICHTIG: Damit der Zugriff in obdConsole.py funktioniert
    return frame
