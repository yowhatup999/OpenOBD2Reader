import random
from datetime import datetime
import obd
import subprocess
import time
import platform

from PySide6.QtCore import QObject, Signal, QThread, QTimer

from obd_logger import ObdLogger
from obd_worker import ObdWorker

class ObdReaderThreaded(QObject):
    connectionEstablished = Signal(str)
    dataReceived = Signal(str)
    errorOccurred = Signal(str)
    dtcReceived = Signal(str)
    dtcCleared = Signal(str)
    requestBluetoothReset = Signal()

    def __init__(self, commands_file, commands_imp_file, commands_mil_file, port="/dev/tty.Android-Vlink"):
        super().__init__()
        self.port = port

        self.logger = ObdLogger()
        self.logger.log_info("OBD-Reader wurde gestartet")

        self.commands_all = self.load_commands(commands_file)
        self.commands_important = self.load_commands(commands_imp_file)
        self.commands_mil = self.load_commands(commands_mil_file)
        self.connection = None
        self.ble_serial = None

    def startConnection(self):
        """Verbindet mit dem OBD-II Adapter, falls möglich."""
        self.retry_count = 0
        self.max_retries = 3
        self.connection = None

        if self.retry_count + 1 == self.max_retries:
            self.errorOccurred.emit(f"Letzter Verbindungsversuch {self.retry_count + 1}/{self.max_retries}...")

        # BLE-Serial starten, falls nötig
        self.startBleSerial()

        # Starte den ersten Verbindungsversuch nach 5 Sekunden
        QTimer.singleShot(5000, self.retryConnection)

    def retryConnection(self):
        """Führt einen erneuten Verbindungsversuch aus."""
        if self.retry_count >= self.max_retries:
            self.errorOccurred.emit("Keine OBD2-Verbindung nach mehreren Versuchen.")
            self.askForBluetoothReset()  # Falls keine Verbindung → Bluetooth-Reset anbieten
            return

        self.errorOccurred.emit(f"Verbindungsversuch {self.retry_count + 1}/{self.max_retries}...")

        self.connection = obd.OBD(portstr=self.port, baudrate=9600, timeout=5)

        if self.connection.is_connected():
            self.connectionEstablished.emit("OBD2-Adapter erfolgreich verbunden")
        else:
            self.errorOccurred.emit(
                f"OBD2-Verbindung fehlgeschlagen (Versuch {self.retry_count + 1}/{self.max_retries})")
            self.retry_count += 1
            QTimer.singleShot(5000, self.retryConnection)

    def startBleSerial(self):
        """Startet BLE-Serial, falls es nicht bereits läuft."""
        try:
            self.ble_serial = subprocess.Popen(["ble-serial", "-d", "13:E0:2F:8D:61:3A"],
                                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.errorOccurred.emit("BLE-Serial gestartet. Warte 5 Sekunden auf die Verbindung...")
            QTimer.singleShot(5000, self.checkObdConnection)  # Verbindung nach 5 Sekunden prüfen
        except FileNotFoundError:
            self.errorOccurred.emit("BLE-Serial nicht gefunden. Starte Dummy-Modus.")
            self.startDummyConnection()

    def checkObdConnection(self):
        """Prüft, ob die OBD-Verbindung nach BLE-Serial-Start erfolgreich ist."""
        if self.connection and self.connection.is_connected():
            self.connectionEstablished.emit("OBD2-Verbindung erfolgreich über BLE-Serial!")
        else:
            self.retryConnection()

    def askForBluetoothReset(self):
        """Sendet ein Signal an die GUI, um nach einem Bluetooth-Reset zu fragen."""
        self.errorOccurred.emit("Keine OBD2-Verbindung. Soll Bluetooth neu gestartet werden?")
        self.requestBluetoothReset.emit()

    def restart_bluetooth(self):
        """Startet Bluetooth neu und versucht danach erneut eine Verbindung."""
        try:
            self.error_occurred.emit("Bluetooth wird neu gestartet...")

            if platform.system() == "Linux":
                subprocess.run(["sudo", "systemctl", "restart", "bluetooth"], check=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["sudo", "pkill", "bluetoothd"], check=True)
                subprocess.run(["sudo", "launchctl", "stop", "com.apple.bluetoothd"], check=True)
                subprocess.run(["sudo", "launchctl", "start", "com.apple.bluetoothd"], check=True)

            self.error_occurred.emit("Bluetooth erfolgreich neu gestartet.")
            QTimer.singleShot(5000, self.start_connection)

        except Exception as e:
            self.error_occurred.emit(f"Fehler beim Neustart von Bluetooth: {e}")

    def startDummyConnection(self):
        """Simuliert eine OBD-Verbindung und liefert zufällige Werte."""
        self.logger.log_info("Dummy-Modus wurde aktiviert")
        self.connection = None
        self.connectionEstablished.emit("Dummy-Modus aktiv")

        # Simulierte OBD-Daten
        dummyData = {
            "RPM": f"{random.randint(600, 7000)} U/min",
            "SPEED": f"{random.randint(0, 220)} km/h",
            "THROTTLE_POS": f"{random.uniform(5.0, 95.0):.2f} %",
            "COOLANT_TEMP": f"{random.randint(70, 110)} °C",
            "FUEL_LEVEL": f"{random.uniform(10.0, 90.0):.1f} %",
            "MAF": f"{random.uniform(2.0, 20.0):.2f} g/s",
            "Yo": f"{random.uniform(0.0, 999):.2f} %",
            "what": f"{random.uniform(0.0, 999):.2f} %",
        }

        for cmd, value in dummyData.items():
            message = f"[🟡 Dummy] {cmd}: {value}"
            self.dataReceived.emit(message)
            self.logger.log_info(message)

        # Simulierte Fehlercodes zufällig generieren
        dtc_codes = [
            "P0300 - Random Misfire Detected",
            "P0420 - Catalyst System Efficiency Below Threshold"
        ]

        if random.choice([True, False]):
            dtc_message = "[🟡 Dummy] " + "\n".join(dtc_codes)
            self.dtcReceived.emit(dtc_message)
            self.logger.log_warning(dtc_message)
        else:
            self.dtcReceived.emit("[🟡 Dummy] Keine Fehlercodes gefunden.")
            self.logger.log_info("[🟡 Dummy] Keine Fehlercodes gefunden.")

    def load_commands(self, filename):
        """Lädt OBD-Befehle aus einer Datei."""
        commands = []
        try:
            with open(filename, "r") as file:
                for line in file:
                    cmdName = line.strip()
                    if cmdName and not cmdName.startswith("#"):
                        try:
                            cmd = getattr(obd.commands, cmdName)
                            commands.append(cmd)
                        except AttributeError:
                            self.errorOccurred.emit(f"Unbekannter Befehl: {cmdName}")
        except FileNotFoundError:
            self.errorOccurred.emit(f"Datei {filename} nicht gefunden.")
        return commands

    def readCommands(self, commands):
        """Liest die Werte der angegebenen OBD-Befehle aus und berechnet ggf. den Verbrauch."""
        if not self.connection or not self.connection.is_connected():
            self.errorOccurred.emit("Keine Verbindung zum OBD-II Adapter.")
            return

        maf_value = None
        speed_value = None
        fuel_rate = None

        for cmd in commands:
            if cmd in self.connection.supported_commands:
                response = self.connection.query(cmd)
                value = response.value if response and not response.is_null() else "Keine Daten"
                unit = response.unit if response and not response.is_null() else ""

                self.dataReceived.emit(f"{cmd.name}: {value} {unit}")

                # Werte für Verbrauchsberechnung speichern
                if cmd == obd.commands.MAF and value is not None and isinstance(value, obd.Unit.Quantity):
                    maf_value = value.magnitude
                elif cmd == obd.commands.SPEED and value is not None and isinstance(value, obd.Unit.Quantity):
                    speed_value = value.magnitude
                elif cmd == obd.commands.FUEL_RATE and value is not None and isinstance(value, obd.Unit.Quantity):
                    fuel_rate = value.magnitude
            else:
                self.errorOccurred.emit(f"{cmd.name} wird nicht unterstützt.")

        # Berechnung des Verbrauchs (entweder über MAF oder Fuel Rate)
        consumption = None
        if maf_value is not None and speed_value is not None and speed_value > 0:
            consumption = self.calculateFuelConsumption(maf_value, speed_value)
            self.dataReceived.emit(f"Verbrauch (L/100km): {consumption:.2f} L/100km")

        elif fuel_rate is not None and speed_value is not None and speed_value > 0:
            consumption = fuel_rate * 100 / speed_value
            self.dataReceived.emit(f"Verbrauch (L/100km) [Fuel Rate]: {consumption:.2f} L/100km")

        if speed_value == 0:
            self.dataReceived.emit("Auto steht, Verbrauch nicht berechenbar.")

    def readAll(self):
        """Liest alle verfügbaren OBD-Werte aus."""
        self.readCommands(self.commands_all)

    def readImportant(self):
        """Liest nur die wichtigsten OBD-Werte aus."""
        self.readCommands(self.commands_important)

    def readMIL(self):
        """Liest nur die Service Wichtigen OBD-Werte aus."""
        self.readCommands(self.commands_mil)

    def calculateFuelConsumption(self, maf, speed):
        """ Berechnet den Momentanverbrauch in L/100 km mit MAF """
        if maf is None or speed is None or maf <= 0 or speed <= 0:
            return None

        AFR = 14.7  # Luft-Kraftstoff-Verhältnis für Benziner
        fuelDensity = 0.739  # Dichte von Benzin in kg/L
        fuelFlow = maf / (AFR * fuelDensity)  # Kraftstoffverbrauch in L/s
        consumption = (fuelFlow * 3600 * 100) / speed  # Umrechnung in L/100km

        return consumption

    def checkDTCs(self):
        """Liest Fehlercodes aus."""
        if not self.connection or not self.connection.is_connected():
            self.errorOccurred.emit("Keine Verbindung zum OBD-II Adapter.")
            return

        dtcResponse = self.connection.query(obd.commands.GET_DTC)
        if dtcResponse and not dtcResponse.is_null():
            dtcList = "\n".join([f"{code[0]} - {code[1]}" for code in dtcResponse.value])
            self.dtcReceived.emit(dtcList)
        else:
            self.dtcReceived.emit("Keine Fehlercodes gefunden.")

    def clearDTCs(self):
        """Löscht Fehlercodes."""
        if not self.connection or not self.connection.is_connected():
            self.errorOccurred.emit("Keine Verbindung zum OBD-II Adapter.")
            return

        response = self.connection.query(obd.commands.CLEAR_DTC)
        if response:
            self.dtcCleared.emit("Fehlercodes erfolgreich gelöscht.")
        else:
            self.errorOccurred.emit("Fehler beim Löschen der Fehlercodes.")

    def stopConnection(self):
        """Beendet die OBD-Verbindung und schließt Prozesse."""

        if self.connection:
            self.connection.close()
            self.errorOccurred.emit("OBD-Verbindung geschlossen.")

        if self.ble_serial:
            try:
                subprocess.run(["pkill", "-f", "ble-serial"])
                self.errorOccurred.emit("BLE-Serial-Prozess beendet.")
            except Exception as e:
                self.errorOccurred.emit(f"Fehler beim Beenden von BLE-Serial: {e}")

        self.connectionEstablished.emit("Verbindung beendet.")




