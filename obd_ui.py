from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QGridLayout, QPlainTextEdit
from PySide6.QtCore import Qt, QPropertyAnimation
from Gui.Console.obd_animations import create_glow_effect, animate_frame_color, animate_background_color

def create_status_frame(parent):
    frame = QFrame(parent)
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

    effect = create_glow_effect(frame)
    animate_frame_color(effect)

    return frame, label_connection, label_time

def create_values_frame(parent):
    frame = QFrame(parent)
    layout = QGridLayout(frame)

    effect = create_glow_effect(frame)
    animate_frame_color(effect)
    animate_background_color(frame)  # Hier wird der sanfte Farbwechsel gestartet

    return frame, layout

def create_buttons_frame(parent, connect_callback, dummy_callback):
    frame = QFrame(parent)
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

    effect = create_glow_effect(frame)
    animate_frame_color(effect)

    return frame

def create_log_console(parent):
    """Erstellt eine Log-Konsole mit Titel und Einklapp-Funktion."""
    frame = QFrame(parent)
    frame.setObjectName("logFrame")
    frame.setStyleSheet("""
        QFrame#logFrame {
            border: 1px solid rgba(138, 43, 226, 0.3);
            border-radius: 5px;
        }
    """)

    layout = QVBoxLayout(frame)
    layout.setContentsMargins(5, 5, 5, 5)

    # Titel-Leiste mit „Log“ Label und Minimize-Button
    title_bar = QHBoxLayout()
    title_label = QLabel("Log", parent)
    title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")

    btn_toggle = QPushButton("━", parent)  # Windows-Style Minimize Symbol
    btn_toggle.setFixedSize(25, 25)  # Knopf hat eine Höhe von 25px
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
            font-family: monospace;
            font-size: 14px;
            border-radius: 5px;
            padding: 5px;
            border: 1px solid rgba(138, 43, 226, 0.3);
        }
    """)
    log_console.setMaximumHeight(120)

    layout.addLayout(title_bar)
    layout.addWidget(log_console)

    # Animation für Einklappen
    animation = QPropertyAnimation(frame, b"maximumHeight")
    animation.setDuration(200)
    animation.setStartValue(130)  # Volle Höhe mit Log
    animation.setEndValue(40)  # Min-Höhe = Höhe des Buttons
    frame.setMinimumHeight(30)  # Mindestens 30px, damit der Button passt!

    def toggle_log():
        """Blendet die Konsole ein oder aus."""
        if log_console.isVisible():
            log_console.setVisible(False)
            animation.setDirection(QPropertyAnimation.Forward)
            btn_toggle.setText("━")  # Windows Minimize-Button
        else:
            log_console.setVisible(True)
            animation.setDirection(QPropertyAnimation.Backward)
            btn_toggle.setText("━")
        animation.start()

    btn_toggle.clicked.connect(toggle_log)

    frame.log_console = log_console  # Speichern, damit wir von außen darauf zugreifen können
    return frame
