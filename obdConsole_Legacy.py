import os
import sys
from datetime import datetime

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout, QFrame, \
    QGridLayout, QLabel, QSizePolicy, QGraphicsColorizeEffect, QGraphicsDropShadowEffect
from PySide6.QtGui import QFont, QTextCursor, QIcon, Qt, QColor
from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve

from Gui.styles import STYLE_MAIN
from ObdReaderThreaded import ObdReaderThreaded, ObdWorker


class Obd2Console(QWidget):
    def __init__(self):
        super().__init__()

        # **Gesamtes Fenster-Layout**
        self.setStyleSheet(STYLE_MAIN)
        self.layoutMain = QVBoxLayout()
        self.layoutMain.setContentsMargins(10, 10, 10, 10)
        self.layoutMain.setSpacing(10)

        # **App-Icon setzen**
        iconPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "icons", "OBD2Logo.png"))
        if os.path.isfile(iconPath):
            myIcon = QIcon()
            myIcon.addFile(iconPath)
            self.setWindowIcon(myIcon)
        else:
            self.logError(f"Icon nicht gefunden: {iconPath}")

        # **Status-Frame für Verbindung und Uhrzeit**
        self.frameStatus = QFrame(self)
        self.frameStatus.setObjectName("frameStatus")
        self.frameStatus.setStyleSheet(self.getColoredFrameStyle())  # Bunten Rahmen für das gesamte Frame setzen
        self.layoutStatus = QHBoxLayout(self.frameStatus)
        self.layoutStatus.setContentsMargins(5, 5, 5, 5)  # Weniger Abstand, damit der Rahmen kleiner wirkt
        self.layoutStatus.setSpacing(20)

        self.labelConnection = QLabel("🔴 Verbindung: Offline", self)
        self.labelConnection.setObjectName("labelConnection")
        self.labelConnection.setAlignment(Qt.AlignmentFlag.AlignCenter)  # **Zentrale Ausrichtung**
        self.labelConnection.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.labelTime = QLabel(f"⏱ {self.getCurrentTime()}  UHR", self)
        self.labelTime.setObjectName("labelTime")
        self.labelTime.setAlignment(Qt.AlignmentFlag.AlignCenter)  # **Zentrale Ausrichtung**
        self.labelTime.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.layoutStatus.addWidget(self.labelConnection, 1)
        self.layoutStatus.addWidget(self.labelTime, 1)

        # **Frame für OBD-Werte**
        self.frameValues = QFrame(self)
        self.frameValues.setObjectName("frameValues")
        self.frameValues.setStyleSheet(self.getColoredFrameStyle())  # Bunten Rahmen setzen
        self.layoutValues = QGridLayout(self.frameValues)
        self.valueLabels = {}

        # **Frame für Buttons**
        self.frameButtons = QFrame(self)
        self.frameButtons.setObjectName("frameButtons")
        self.frameButtons.setStyleSheet(self.getColoredFrameStyle())  # Bunten Rahmen setzen
        self.layoutButtons = QHBoxLayout(self.frameButtons)
        self.layoutButtons.setSpacing(10)

        self.btnConnect = QPushButton("🔌 Connect", self)
        self.btnConnect.setObjectName("connectButton")
        self.btnConnect.clicked.connect(lambda: self.startObdWorker("important"))
        self.layoutButtons.addWidget(self.btnConnect)

        self.btnDummy = QPushButton("🛠 Dummy-Simulation", self)
        self.btnDummy.setObjectName("dummyButton")
        self.btnDummy.clicked.connect(lambda: self.startObdWorker("dummy"))
        self.layoutButtons.addWidget(self.btnDummy)

        # **Elemente zum Hauptlayout hinzufügen**
        self.layoutMain.addWidget(self.frameStatus, 0)  # Oben: Statusbereich
        self.layoutMain.addWidget(self.frameValues, 3)  # Mitte: Werte
        self.layoutMain.addWidget(self.frameButtons, 0)  # Unten: Buttons

        # **Benachrichtigungs-Label erstellen (wird als Overlay über dem Layout platziert)**
        self.notificationLabel = QLabel(self)
        self.notificationLabel.setObjectName("notificationLabel")
        self.notificationLabel.setStyleSheet("""
            #notificationLabel {
                background-color: rgba(0, 0, 0, 0.5);  /* Weniger Transparenz */
                color: white;
                padding: 10px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                border: 2px solid rgba(255, 255, 255, 0.6);  /* Hinzugefügter Rahmen */
                word-wrap: break-word;  /* Textumbruch */
            }
        """)
        self.notificationLabel.setVisible(False)  # Startet unsichtbar

        # **Das notificationLabel als Overlay über dem Fenster hinzufügen**
        self.notificationLabel.raise_()  # Setzt das Label nach oben, um es über anderen Widgets zu platzieren.

        # Benachrichtigung wird nicht im Layout hinzugefügt, sondern direkt ins Fenster:
        self.notificationLabel.setGeometry(50, 50, 400, 40)  # Position und Größe des Benachrichtigungs-Labels
        self.setLayout(self.layoutMain)

        # glow effekt
        self.animateFrameBorder()

        # **Initialisierung der Variablen**
        self.obdReader = None
        self.obdWorker = None
        self.retryCount = 0

        # **Timer für Auto-Reconnect**
        self.timerReconnect = QTimer()
        self.timerReconnect.timeout.connect(self.tryConnect)
        self.timerReconnect.start(5000)  # Alle 5 Sekunden prüfen

        # **Timer für Uhrzeit-Update**
        self.timerTimeUpdate = QTimer()
        self.timerTimeUpdate.timeout.connect(self.updateTime)
        self.timerTimeUpdate.start(1000)  # Jede Sekunde aktualisieren


    def tryConnect(self):
        """Versucht eine OBD2-Verbindung aufzubauen, falls nicht vorhanden. Kein automatischer Dummy-Modus mehr."""
        if self.obdReader is None or not self.obdReader.connection or not self.obdReader.connection.is_connected():
            self.retryCount += 1
            self.logWarning(f"🔄 Verbindungsversuch {self.retryCount}...")

            # **Neue OBD-Instanz erstellen**
            self.obdReader = ObdReaderThreaded("commands.txt", "commandsImportant.txt", "commandsMIL.txt")

            if self.obdReader.connection and self.obdReader.connection.is_connected():
                self.updateConnectionStatus(True)  # Verbindung = Online
                self.startObdWorker("important")  # Echte Werte
            else:
                self.logError("❌ Verbindung fehlgeschlagen, bitte manuell Modus wählen.")

    def startObdWorker(self, mode="important"):
        """Startet den OBD-Worker, wenn auf den Button geklickt wird."""
        if self.obdReader is None:
            self.obdReader = ObdReaderThreaded("commands.txt", "commandsImportant.txt", "commandsMIL.txt")

        if self.obdWorker is None:
            self.obdWorker = ObdWorker(self.obdReader, mode, interval=2000)  # Alle 2 Sekunden neue Werte
            self.obdWorker.start()

            # **Signale mit GUI verbinden**
            self.obdReader.connectionEstablished.connect(self.logSuccess)
            self.obdReader.dataReceived.connect(self.logData)
            self.obdReader.errorOccurred.connect(self.logError)
            self.obdReader.dtcReceived.connect(self.logWarning)
            self.obdReader.dtcCleared.connect(self.logSuccess)

            # **Verbindung entsprechend anpassen**
            self.updateConnectionStatus(mode != "dummy")

            self.logSuccess(f"🚀 OBD-Worker gestartet im Modus: {mode.upper()}!")

    def log(self, message, color="D4D4D4"):
        """Aktualisiert bestehende Werte in `frameValues`, mit verbessertem Design."""
        parts = message.split(": ")
        if len(parts) != 2:
            return  # Falls das Format nicht passt, ignorieren

        key, value = parts[0].strip(), parts[1].strip()

        if "OBD-Worker gestartet" in key:
            return  # Diese Zeile wird NICHT mehr angezeigt

        if key in self.valueLabels:
            # **Wert aktualisieren**
            self.valueLabels[key].setText(f"{key}:\n{value}")
        else:
            # **Neues Label mit Glassmorphism-Effekt**
            label = QLabel(f"{key}:\n{value}", self)
            label.setObjectName("obdValueLabel")  # Damit das Stylesheet es erkennt
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)  # Automatischer Zeilenumbruch

            # **Größe automatisch anpassen**
            label.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

            font = QFont()
            font.setPointSize(22)  # **Etwas kleinere Schrift für bessere Lesbarkeit**
            font.setBold(True)
            label.setFont(font)

            label.setStyleSheet("""
                QLabel {
                    padding: 12px;
                    background: rgba(50, 50, 50, 0.2); /* **Sanfte Transparenz, nicht zu viel!** */
                    font-weight: bold;
                    font-family: Helvetica, Arial, sans-serif;
                    color: rgba(255, 255, 255, 0.9); /* **Weißer Text mit leichtem Schimmer** */
                    text-align: center;
                    border-radius: 12px; /* **Runde Ecken für modernes Design** */
                    font-size: 22px;
                    box-shadow: 0 3px 10px rgba(255, 255, 255, 0.1); /* **Dezenter Glow für 3D-Effekt** */
                    backdrop-filter: blur(6px); /* **Fix: Glassmorphism richtig einsetzen!** */
                }
            """)

            row = len(self.valueLabels) // 4  # Maximal 4 Werte pro Reihe
            col = len(self.valueLabels) % 4
            self.layoutValues.addWidget(label, row, col)

            self.valueLabels[key] = label

        # **Nach jeder Aktualisierung die Schriftgröße dynamisch anpassen**
        QTimer.singleShot(100, self.adjustFontSize)  # Verzögert den Aufruf, um die GUI-Layout-Aktualisierung abzuwarten

    def adjustFontSize(self):
        """Passt die Schriftgröße dynamisch an die Größe des Labels an."""
        for label in self.valueLabels.values():
            if not label.text():
                continue

            font = label.font()
            fontSize = 10  # Starte mit einer kleinen Schriftgröße
            labelWidth = label.width()
            labelHeight = label.height()

            while fontSize < 100:  # Maximal bis Schriftgröße 100 erhöhen
                font.setPointSize(fontSize)
                label.setFont(font)

                # Berechne die Textgröße
                textRect = label.fontMetrics().boundingRect(label.text())

                # Falls der Text zu groß für das Label wird, abbrechen
                if textRect.width() > labelWidth * 0.9 or textRect.height() > labelHeight * 0.9:
                    break

                fontSize += 1  # Schriftgröße schrittweise erhöhen

            # Setze die letzte funktionierende Schriftgröße
            font.setPointSize(fontSize - 1)
            label.setFont(font)

    def scrollToBottom(self):
        """Scrollt die Konsole automatisch nach unten."""
        self.console.moveCursor(QTextCursor.MoveOperation.End)

    def logSuccess(self, message):
        """Erfolgsmeldung (Grün) als Benachrichtigung."""
        self.showNotification(f"✅ {message}", "green")

    def logData(self, message):
        """Normale Datenanzeige (Weiß) als Benachrichtigung."""
        self.showNotification(f"📊 {message}", "white")

    def logWarning(self, message):
        """Warnmeldung (Gelb) als Benachrichtigung."""
        self.showNotification(f"⚠️ {message}", "yellow")

    def logError(self, message):
        """Fehlermeldung (Rot) als Benachrichtigung."""
        self.showNotification(f"❌ {message}", "red")

    def showNotification(self, message, color="green"):
        """Zeigt eine Benachrichtigung für eine kurze Zeit an."""
        self.notificationLabel.setText(message)
        self.notificationLabel.setStyleSheet(f"""
            #notificationLabel {{
                background-color: {color}; 
                color: white;
                padding: 10px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }}
        """)

        # Benachrichtigung anzeigen
        self.notificationLabel.setVisible(True)

        # Animationen hinzufügen (Einblenden)
        fadeIn = QPropertyAnimation(self.notificationLabel, b"opacity")
        fadeIn.setDuration(500)  # 0.5 Sekunden für Einblenden
        fadeIn.setStartValue(0)
        fadeIn.setEndValue(1)

        # Animation für Ausblenden (nach kurzer Zeit)
        fadeOut = QPropertyAnimation(self.notificationLabel, b"opacity")
        fadeOut.setDuration(500)  # 0.5 Sekunden für Ausblenden
        fadeOut.setStartValue(1)
        fadeOut.setEndValue(0)

        # Nach 2 Sekunden fadeOut starten
        QTimer.singleShot(2000, lambda: fadeOut.start())  # 2 Sekunden warten

        # Sobald fadeOut beendet ist, Benachrichtigung unsichtbar machen
        fadeOut.finished.connect(lambda: self.notificationLabel.setVisible(False))

        fadeIn.start()

    def getCurrentTime(self):
        """Gibt die aktuelle Uhrzeit als String zurück."""
        return datetime.now().strftime("%H:%M:%S")

    def updateTime(self):
        """Aktualisiert die Uhrzeit-Anzeige mit 'UHR' am Ende."""
        self.labelTime.setText(f"⏱ {self.getCurrentTime()} UHR")

    def getColoredFrameStyle(self):
        """Glassmorphism-Stil mit dezenten Neon-Rändern für alle Frames."""
        return """
            QFrame#frameValues, QFrame#frameStatus, QFrame#frameButtons {
                background: rgba(60, 60, 60, 0.1); /* **Sanfte Transparenz, nicht zu stark** */
                border: 2px solid rgba(138, 43, 226, 0.4); /* **Dünner Lila-Rand, dezent** */
                border-radius: 15px; /* **Etwas rundere Ecken für modernes Design** */
                padding: 10px;
                box-shadow: 0 0 15px rgba(138, 43, 226, 0.2); /* **Leichtes Glow für Tiefe** */
                backdrop-filter: blur(6px); /* **Milchglas-Effekt für mehr Tiefe** */
            }
        """

    def animateFrameBorder(self):
        """Langsame, sanfte Farbwechsel-Animation für den Rand mit weichem Glow."""
        effect = QGraphicsDropShadowEffect(self.frameValues)
        effect.setBlurRadius(18)  # Weicher Glow
        effect.setOffset(0, 0)  # Kein Versatz
        self.frameValues.setGraphicsEffect(effect)

        self.animation = QPropertyAnimation(effect, b"color")
        self.animation.setDuration(30000)  # **30 Sekunden für ultra-sanfte Übergänge**
        self.animation.setLoopCount(-1)  # Endlose Wiederholung

        # **Sehr sanfte Farbverläufe**
        self.animation.setKeyValueAt(0.0, QColor(138, 43, 226, 150))  # Lila (sanft)
        self.animation.setKeyValueAt(0.25, QColor(30, 144, 255, 130))  # Blau (leicht abgedunkelt)
        self.animation.setKeyValueAt(0.5, QColor(255, 20, 147, 120))  # Magenta (dezenter)
        self.animation.setKeyValueAt(0.75, QColor(0, 255, 255, 140))  # Türkis (nicht zu hell)
        self.animation.setKeyValueAt(1.0, QColor(138, 43, 226, 150))  # Zurück zu Lila

        self.animation.setEasingCurve(QEasingCurve.InOutSine)  # **Weicher, natürlicher Übergang**
        self.animation.start()

    def updateConnectionStatus(self, connected):
        """Aktualisiert die Verbindung: Offline (🔴), Dummy (🟡) oder Online (🟢) mit Symbol."""
        if connected:
            self.labelConnection.setText("🟢 Verbindung: Online")
        elif self.obdReader and self.obdReader.connection and self.obdReader.connection.is_connected():
            self.labelConnection.setText("🟡 Verbindung: Dummy")
        else:
            self.labelConnection.setText("🔴 Verbindung: Offline")

        # Rahmen-Farbe anpassen
        self.frameStatus.setStyleSheet(self.getColoredFrameStyle())  # Bunten Rahmen setzen


# **Programmstart**
if __name__ == "__main__":
    app = QApplication(sys.argv)

    console = Obd2Console()
    console.setWindowTitle("OBD2 Terminal")
    console.resize(1280, 800)
    console.show()

    sys.exit(app.exec())
