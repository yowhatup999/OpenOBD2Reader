import os
import sys
from datetime import datetime

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QGridLayout, QMenuBar, QMenu
from PySide6.QtCore import QTimer, Qt

from gui.obd_ui import create_status_frame, create_buttons_frame, create_log_console
from gui.obd_styles import STYLE_MAIN
from gui.obd_animations import *

from obd_worker import ObdWorker
from ObdReaderThreaded import ObdReaderThreaded
from obd_logger import ObdLogger


class ObdConsole(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OBD2 Terminal")
        self.resize(1280, 800)
        self.setStyleSheet(STYLE_MAIN)

        self.layoutMain = QVBoxLayout(self)
        self.layoutMain.setSpacing(5)

        self.create_menu()

        self.obdReader = ObdReaderThreaded("commands.txt", "commandsImportant.txt", "commandsMIL.txt")
        self.obdWorker = None
        self.valueLabels = {}

        self.status_frame, self.label_connection, self.label_time = create_status_frame(self)

        self.values_frame = QWidget(self)
        self.values_frame.setObjectName("frameValues")
        self.values_layout = QGridLayout(self.values_frame)
        self.values_layout.setSpacing(10)

        self.buttons_frame = create_buttons_frame(self, self.startObdWorker, self.startObdWorker)

        self.layoutMain.addWidget(self.status_frame, 1)
        self.layoutMain.addWidget(self.values_frame, 6)
        self.layoutMain.addWidget(self.buttons_frame, 1)

        self.obdWorker = None
        self.valueLabels = {}

        # Signale verbinden
        self.obdReader.connectionEstablished.connect(self.updateConnection)
        self.obdReader.dataReceived.connect(self.updateDisplayedValues)
        self.obdReader.errorOccurred.connect(self.logError)
        self.obdReader.dtcReceived.connect(self.logWarning)

        # LOG CONSOLE widget / label etc
        self.logFrame = create_log_console(self)
        self.layoutMain.addWidget(self.logFrame, 2)

        self.logger = ObdLogger(log_console=self.logFrame.log_console)

        self.logger.log_info("Programm gestartet")  # Start-Log

        self.timer_time_update = QTimer()
        self.timer_time_update.timeout.connect(self.updateTime)
        self.timer_time_update.start(1000)

    def create_menu(self):
        """Erstellt die Menüleiste mit Optionen für die Ansicht und das Speichern der Logs."""
        menu_bar = QMenuBar(self)

        # Ansicht-Menü
        view_menu = QMenu("Ansicht", self)
        self.menu_toggle_log = QAction("Konsole einblenden", self, checkable=True)
        self.menu_toggle_log.setChecked(True)
        self.menu_toggle_log.triggered.connect(self.toggle_console)
        view_menu.addAction(self.menu_toggle_log)

        # Log-Menü
        log_menu = QMenu("Log", self)
        self.menu_log_to_file = QAction("Log to File", self)
        self.menu_log_to_file.triggered.connect(self.save_log_to_file)
        log_menu.addAction(self.menu_log_to_file)

        # Menüleiste zur GUI hinzufügen
        menu_bar.addMenu(view_menu)
        menu_bar.addMenu(log_menu)
        self.layoutMain.setMenuBar(menu_bar)

    def startObdWorker(self, mode="important"):
        if self.obdWorker:
            self.obdWorker.stop()
            self.obdWorker.quit()
            self.obdWorker.wait(2000)

        self.logger.log_info(f"Starte OBD-Worker im Modus: {mode}")

        self.obdWorker = ObdWorker(self.obdReader, mode, interval=2000)
        self.obdWorker.start()

        if mode == "dummy":
            self.label_connection.setText("Verbindung: Dummy")
            self.logger.log_info("Dummy-Modus gestartet")
            self.log_message("Dummy-Modus aktiviert. Werte werden simuliert!")
        else:
            self.label_connection.setText("Verbindung: Verbinden...")

    def updateConnection(self, message):
        """Aktualisiert das Status-Label mit der passenden Farbe."""
        if "Dummy" in message:
            color = "yellow"
            emoji = "🟡"
        elif "erfolgreich" in message or "Online" in message:
            color = "green"
            emoji = "🟢"
        else:
            color = "red"
            emoji = "🔴"

        self.label_connection.setText(f"{emoji} {message}")
        self.label_connection.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        self.logger.log_info(f"🔄 Verbindungsstatus: {message}")

    def updateDisplayedValues(self, message):
        """Zeigt empfangene OBD-Werte in der GUI an."""
        key, value = message.split(": ")

        is_dummy = "[🟡 Dummy]" in key
        display_text = key.replace("[🟡 Dummy] ", "") + ":\n" + value

        if key not in self.valueLabels:
            label = QLabel(self)
            label.setObjectName("valueLabel")
            label.setAlignment(Qt.AlignCenter)
            label.setWordWrap(True)

            # Dummy-Werte Gelb machen
            color = "yellow" if is_dummy else "white"
            label.setStyleSheet(f"""
                QLabel#valueLabel {{
                    background: rgba(40, 40, 40, 0.6);
                    color: {color};
                    border-radius: 10px;
                    padding: 15px;
                    border: 2px solid rgba(138, 43, 226, 0.4);
                    font-size: 16px;
                    font-weight: bold;
                }}
            """)

            position = len(self.valueLabels)
            row = position // 4
            col = position % 4
            self.values_layout.addWidget(label, row, col)
            self.valueLabels[key] = label

        self.valueLabels[key].setText(display_text)

    def logError(self, msg):
        self.logger.log_error(msg)

    def logWarning(self, msg):
        self.logger.log_warning(msg)

    def log_message(self, message):
        """Fügt eine Nachricht zur Log-Konsole hinzu."""
        if hasattr(self.logFrame, "log_console"):
            self.logFrame.log_console.appendPlainText(message)
            self.logFrame.log_console.verticalScrollBar().setValue(
                self.logFrame.log_console.verticalScrollBar().maximum()
            )

    def toggle_console(self):
        """Zeigt oder versteckt die Log-Konsole über das Menü."""
        is_visible = self.logFrame.isVisible()
        self.logFrame.setVisible(not is_visible)

        if is_visible:
            self.menu_toggle_log.setText("Konsole einblenden")
        else:
            self.menu_toggle_log.setText("Konsole ausblenden")

    def save_log_to_file(self):
        """Speichert den Log-Text in eine Datei mit Zeitstempel."""
        if not hasattr(self.logFrame, "log_console"):
            self.log_message("Log-Konsole nicht gefunden!")
            return

        log_text = self.logFrame.log_console.toPlainText()

        if not log_text.strip():
            self.log_message("Kein Log zum Speichern vorhanden!")
            return

        # Log-Dateiname mit Datum & Uhrzeit
        log_dir = os.path.join(os.getcwd(), "log_files")
        os.makedirs(log_dir, exist_ok=True)
        log_filename = os.path.join(log_dir, f"log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")

        # Log in Datei schreiben
        with open(log_filename, "w", encoding="utf-8") as log_file:
            log_file.write(log_text)

        # Bestätigung in der GUI anzeigen
        self.log_message(f"Log gespeichert: {log_filename}")

    def updateTime(self):
        self.label_time.setText(f"⏱ {datetime.now().strftime('%H:%M:%S')} UHR")
        font = self.label_time.font()
        self.label_time.setFont(font)

    def closeEvent(self, event):
        if self.obdWorker and self.obdWorker.isRunning():
            self.obdWorker.stop()
            self.obdWorker.quit()
            self.obdWorker.wait(2000)

            self.logger.log_info("OBD-Worker gestoppt")
            self.logger.log_info("OBD-Worker sicher beendet.")

        self.logger.log_info("Programm beendet")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    console = ObdConsole()
    console.show()
    sys.exit(app.exec())
