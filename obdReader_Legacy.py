import os
import sys
from datetime import datetime

import obd
import subprocess
import time

class ObdReader:
    def __init__(self, commandsFile, commandsImpFile, commandsMILFile, port="/dev/tty.Android-Vlink"): # ls /dev/tty.* (falls der port nicht existiert)
        # also "ls /dev/tty.*" in terminal
        # Automatisch ble-serial starten

        self.port = port
        self.mafValue = None
        self.speedValue = None
        self.rpmValue = None
        self.fuelRate = None
        self.consumptionHistory = []
        self.valueHistory = {}

        # Log-Ordner erstellen, falls er nicht existiert
        self.logFolder = os.path.join(os.getcwd(), "logs")
        os.makedirs(self.logFolder, exist_ok=True)

        self.timerConsumption = time.time()

        # BLE-Serial starten (wenn nötig)
        try:
            self.ble_serial = subprocess.Popen(["ble-serial", "-d", "13:E0:2F:8D:61:3A"],
                                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("BLE-Serial gestartet. Warte 5 Sekunden auf die Verbindung...")
            time.sleep(3)
        except FileNotFoundError:
            print("Fehler: BLE-Serial nicht installiert.")
            self.ble_serial = None

        # OBD-Verbindung herstellen
        try:
            self.connection = obd.OBD(portstr=self.port, baudrate=9600, timeout=5)  # Timeout nach 5 Sek.
            if not self.connection.is_connected():
                print("❌ Keine Verbindung zum OBD-II Adapter.")
                self.connection = None  #
            else:
                print("✅ Verbindung erfolgreich hergestellt!")
        except Exception as e:
            print(f"❌ Fehler beim Verbinden: {e}")
            self.connection = None

        # Commands aus Datei laden
        self.commandsAll = self.loadCommands(commandsFile)
        self.commandsImportant = self.loadCommands(commandsImpFile)
        self.commandsMIL = self.loadCommands(commandsMILFile)

    def loadCommands(self, filename):
        """Lädt OBD-Befehle aus einer Datei, aber nur wenn eine Verbindung existiert."""
        if not self.connection or not self.connection.is_connected():
            print(f"⚠️ Keine OBD-Verbindung - Überspringe das Laden von {filename}")
            return []  # Gibt eine leere Liste zurück

        commands = []
        try:
            with open(filename, "r") as file:
                for line in file:
                    cmdName = line.strip()
                    if cmdName and not cmdName.startswith("#"):
                        if hasattr(obd.commands, cmdName):
                            cmd = getattr(obd.commands, cmdName)
                            commands.append(cmd)
                        else:
                            print(f"❌ Unbekannter Befehl: {cmdName}")
        except FileNotFoundError:
            print(f"❌ Datei {filename} nicht gefunden.")
            return []

        return commands

    def handleResponse(self, command):
        """Verarbeitet die OBD-Antworten und speichert sie für das Logging."""
        if not self.connection or not self.connection.is_connected():
            print(f"❌ Keine OBD-Verbindung! Kann {command.name} nicht auslesen.")
            return

        response = self.connection.query(command)

        if response.is_null():
            print(f"{command.name:<20} ❌ Keine Daten empfangen")
            return

        value = response.value
        unit = response.unit

        # Falls der Wert eine physikalische Einheit hat, hole den numerischen Wert
        if isinstance(value, obd.Unit.Quantity):
            value = value.magnitude  # Extrahiert den numerischen Wert

        # **Automatische Umrechnung von kPa → Bar**
        if unit == "kilopascal":
            value = value / 100  # 1 bar = 100 kPa
            unit = "bar"

        print(f"📊 {command.name:<20} = {value} {unit}")  # Debug-Print

        # Werte für Verbrauchsberechnung speichern
        if command == obd.commands.MAF:
            self.mafValue = value
            print(f"✅ MAF-Wert gesetzt: {self.mafValue}")
        elif command == obd.commands.SPEED:
            self.speedValue = value
            print(f"✅ Geschwindigkeitswert gesetzt: {self.speedValue}")
        elif command == obd.commands.RPM:
            self.rpmValue = value

        # Speicherung der Werte in `valueHistory`
        if command.name not in self.valueHistory:
            self.valueHistory[command.name] = []
        self.valueHistory[command.name].append(float(value))  # Speichere Wert für Durchschnitt

        # **Jede 60 Sekunden Durchschnitt berechnen & speichern**
        if time.time() - self.timerConsumption >= 60:
            self.logAverageValues()
            self.timerConsumption = time.time()  # Timer zurücksetzen

    def startReading(self):
        print("\nOptionen:")
        print("1: Alle OBD-Daten auslesen")
        print("2: Wichtige OBD-Daten auslesen")
        print("3: Fehlercodes auslesen und speichern")
        print("4: Fehlercodes löschen")
        print("5: Service wichtige Werte auslesen")
        print("Drücke 'Strg+C', um das Programm zu beenden.\n")
        userInput = input("Eingabe: ")

        if userInput.strip() not in ["1", "2", "3", "4", "5"]:
            print("Ungültige Eingabe. Bitte versuche es erneut.")
            return self.startReading()
        elif userInput.strip() == "1":
            print("======================= Alle Werte =======================")
            print(f"{'Command':<20} {'Value':<15}")
            print("-" * 35)
            self.readAll()
        elif userInput.strip() == "2":
            print("======================= Wichtige Werte =======================")
            print(f"{'Command':<20} {'Value':<15}")
            print("-" * 35)
            self.readImportant()
        elif userInput.strip() == "3":
            print("Lese Fehlercodes...")
            self.checkDTCs()
        elif userInput.strip() == "4":
            print("Lösche Fehlercodes...")
            self.clearDTCs()
        elif userInput.strip() == "5":
            print("Lese Service Werte...")
            self.readMIL()
        else:
            print("Ungültige Eingabe. Programm beendet.")

    def stopReading(self):
        """Beendet die OBD-Verbindung und BLE-Serial-Prozess sicher."""
        if self.connection:
            self.connection.close()
            print("✅ OBD-Verbindung geschlossen.")

        if self.ble_serial:
            try:
                subprocess.run(["killall", "ble-serial"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("✅ BLE-Serial-Prozess beendet.")
            except Exception as e:
                print(f"❌ Fehler beim Beenden von BLE-Serial: {e}")

        print("✅ Programm beendet.")

    def readAll(self):
        print("======================= Alle Werte =======================")
        try:
            while True:
                for cmd in self.commandsAll:
                    self.handleResponse(cmd)

                self.printAndLogConsumption()

                print("-" * 30)
                time.sleep(2)  # 2 sec pause per tic
        except KeyboardInterrupt:
            self.stopReading()

    def readImportant(self):
        print("======================= Wichtige Werte =======================")
        try:
            while True:
                for cmd in self.commandsImportant:
                    self.handleResponse(cmd)

                self.printAndLogConsumption()

                self.checkCatalystHealth()

                print("-" * 30)
                time.sleep(2)  # 2 sec pause per tic
        except KeyboardInterrupt:
            self.stopReading()

    import obd

    def readMIL(self):
        """
        Liest die Service-relevanten OBD-Werte aus.

        Diese Methode fragt regelmäßig alle in `commandsMIL` gespeicherten Standard-PIDs ab.
        Zusätzlich werden zwei Custom PIDs für `FUEL_STATUS` (PID 22 1941) und `OIL_TEMP` (PID 22 1945) abgefragt,
        die spezifisch für Opel-Fahrzeuge getestet werden.

        Die Werte werden in der Konsole ausgegeben. Falls keine Daten verfügbar sind, wird eine Fehlermeldung angezeigt.
        Die Abfrage läuft in einer Endlosschleife und kann mit `Strg+C` gestoppt werden.

        Custom PIDs:
        - `FUEL_STATUS`: Gibt den aktuellen Status des Kraftstoffsystems zurück.
        - `OIL_TEMP`: Gibt die aktuelle Öltemperatur in Grad Celsius zurück.

        Alle Werte werden zusätzlich in `printAndLogConsumption()` geloggt.

        Ausnahmebehandlung:
        - Falls ein Befehl nicht unterstützt wird, wird eine Warnung ausgegeben.
        - Falls `Strg+C` gedrückt wird, wird die Verbindung sicher beendet.

        """
        print("======================= Service-Werte =======================")
        try:
            while True:
                for cmd in self.commandsMIL:
                    self.handleResponse(cmd)  # Originale MIL-Werte ausführen

                # **Custom Fuel Status (PID 22 1941)**
                CMD_FUEL_STATUS = obd.OBDCommand(
                    "FUEL_STATUS",
                    "Fuel Status",
                    b"221941",
                    2,
                    lambda x: int.from_bytes(x, byteorder="big")  # Konvertiert Bytes zu Integer
                )
                response_fuel = self.connection.query(CMD_FUEL_STATUS)
                if response_fuel and not response_fuel.is_null():
                    print(f"✅ FUEL_STATUS: {response_fuel.value}")
                else:
                    print("❌ Keine Daten für FUEL_STATUS verfügbar.")

                # **Custom Oil Temperature (PID 22 1945)**
                CMD_OIL_TEMP = obd.OBDCommand(
                    "OIL_TEMP",
                    "Oil Temperature",
                    b"221945",
                    2,
                    lambda x: int.from_bytes(x, byteorder="big") - 40  # Offset -40 für Öltemperatur
                )
                response_oil = self.connection.query(CMD_OIL_TEMP)
                if response_oil and not response_oil.is_null():
                    print(f"✅ OIL_TEMP: {response_oil.value} °C")
                else:
                    print("❌ Keine Daten für OIL_TEMP verfügbar.")

                self.printAndLogConsumption()  # Verbrauch berechnen und loggen
                print("-" * 30)
                time.sleep(2)  # 2 sec pause pro Abfrage

        except KeyboardInterrupt:
            self.stopReading()

    def readAvailablePIDs(self):
        """
        Liest alle vom Steuergerät unterstützten OBD-PIDs aus und speichert sie in einer Log-Datei.

        Die Methode führt folgende Schritte aus:
        1. Ruft die Fahrzeug-VIN (Fahrgestellnummer) ab.
        2. Fragt die unterstützten PIDs ab (obd.commands.MONITOR_STATUS_SINCE_DTC_CLEAR).
        3. Listet alle unterstützten PIDs in einer log-Datei auf.
        4. Speichert die Daten in einer Datei mit Datum und Uhrzeit.

        Falls eine Verbindung nicht möglich ist, wird eine Fehlermeldung ausgegeben.
        """
        if not self.connection or not self.connection.is_connected():
            print("❌ Keine OBD-Verbindung. Konnte PIDs nicht abrufen.")
            return

        # Erstelle den Log-Ordner, falls nicht vorhanden
        log_folder = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_folder, exist_ok=True)

        # Erstelle den Pfad zur Log-Datei
        log_file = os.path.join(log_folder, f"obd_pid_log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")

        with open(log_file, "w") as log:
            # Schreibe das Datum und die VIN in die Datei
            log.write(f"================= OBD PID-Log =================\n")
            log.write(f"📅 Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            # VIN abrufen
            vin_response = self.connection.query(obd.commands.VIN)
            if vin_response and not vin_response.is_null():
                vin = vin_response.value
                print(f"✅ VIN: {vin}")
                log.write(f"🚗 Fahrzeug VIN: {vin}\n")
            else:
                print("⚠️ VIN konnte nicht ausgelesen werden.")
                log.write("🚗 Fahrzeug VIN: Nicht verfügbar\n")

            log.write("\n🎯 Unterstützte PIDs:\n")
            log.write("=" * 50 + "\n")

            # Alle OBD-Befehle durchgehen und testen
            supported_pids = []
            for cmd in obd.commands.__dict__.values():
                if isinstance(cmd, obd.OBDCommand):  # Nur echte OBD-Befehle berücksichtigen
                    response = self.connection.query(cmd)
                    if response and not response.is_null():
                        supported_pids.append(f"{cmd.name:<25} - {cmd.desc}")

            # Ergebnisse ausgeben und ins Log schreiben
            if supported_pids:
                for pid in supported_pids:
                    print(f"✅ {pid}")
                    log.write(f"{pid}\n")
            else:
                print("❌ Keine unterstützten PIDs gefunden.")
                log.write("Keine unterstützten PIDs gefunden.\n")

            print(f"\n📄 Log-Datei gespeichert unter: {log_file}")

    def checkCatalystHealth(self):
        """Überprüft, ob der Katalysator oder die Lambdasonden defekt sind."""
        if not self.connection or not self.connection.is_connected():
            print("❌ Keine OBD-Verbindung. Katalysator-Check nicht möglich.")
            return

        # Abfrage der Lambdawerte
        sensor_b1s1 = self.connection.query(obd.commands.O2_B1S1)
        sensor_b1s2 = self.connection.query(obd.commands.O2_B1S2)

        # Falls keine Daten vorliegen
        if sensor_b1s1.is_null() or sensor_b1s2.is_null():
            print("⚠️ O2-Sensordaten nicht verfügbar.")
            return

        # Extrahiere Spannungswerte
        voltage_b1s1 = sensor_b1s1.value.magnitude
        voltage_b1s2 = sensor_b1s2.value.magnitude

        # Prüflogik
        status = "⚠️ Unklar"
        if 0.1 <= voltage_b1s1 <= 0.9:
            if abs(voltage_b1s2 - voltage_b1s1) > 0.1:  # Schwankt B1S2 nicht?
                status = "✅ Kat in Ordnung"
            else:
                status = "❌ Kat defekt!"
        else:
            status = "❌ Lambdasonde defekt!"

        # Ausgabe mit Formatierung
        print("\n================= Katalysator-Check =================")
        print(f"🔧 O2_B1S1 (VOR Kat) = {voltage_b1s1:.3f} V")
        print(f"🔧 O2_B1S2 (NACH Kat) = {voltage_b1s2:.3f} V")
        print(f"🔍 Status: {status}")
        print("=====================================================\n")

        # Log in Datei speichern
        log_path = os.path.join(self.logFolder, "catalyst_log.txt")
        with open(log_path, "a") as log:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.write(f"[{timestamp}] O2_B1S1 = {voltage_b1s1:.3f} V, O2_B1S2 = {voltage_b1s2:.3f} V, Status: {status}\n")

    def scanAllPids(self):
        if not self.connection or not self.connection.is_connected():
            print("❌ Keine OBD-Verbindung. Konnte PIDs nicht abrufen.")
            return

        logFolder = os.path.join(os.getcwd(), "logs")
        os.makedirs(logFolder, exist_ok=True)

        logFile = os.path.join(logFolder, f"obd_pid_scan_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")

        with open(logFile, "w") as log:
            log.write(f"================= OBD PID-Scan =================\n")
            log.write(f"📅 Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            vinResponse = self.connection.query(obd.commands.VIN)
            if vinResponse and not vinResponse.is_null():
                vin = vinResponse.value
                print(f"✅ VIN: {vin}")
                log.write(f"🚗 Fahrzeug VIN: {vin}\n")
            else:
                print("⚠️ VIN konnte nicht ausgelesen werden.")
                log.write("🚗 Fahrzeug VIN: Nicht verfügbar\n")

            log.write("\n🎯 Unterstützte PIDs:\n")
            log.write("=" * 50 + "\n")

            for cmd in obd.commands.__dict__.values():
                if isinstance(cmd, obd.OBDCommand):
                    response = self.connection.query(cmd)
                    if response and not response.is_null():
                        log.write(f"✅ {cmd.name:<25} - {cmd.desc} - {response.value}\n")
                        print(f"✅ {cmd.name:<25} - {response.value}")
                    else:
                        log.write(f"❌ {cmd.name:<25} - Nicht unterstützt\n")

            for pid in range(0x0100, 0xFFFF, 0x10):
                hexPid = f"{pid:04X}"
                cmd = obd.OBDCommand(
                    f"PID_{hexPid}",
                    f"Custom PID {hexPid}",
                    bytes.fromhex(f"22{hexPid}"),
                    2,
                    lambda x: int.from_bytes(x, byteorder="big")
                )
                response = self.connection.query(cmd)
                if response and not response.is_null():
                    log.write(f"✅ {cmd.name:<25} - {cmd.desc} - {response.value}\n")
                    print(f"✅ {cmd.name:<25} - {response.value}")
                else:
                    log.write(f"❌ {cmd.name:<25} - Nicht unterstützt\n")

            print(f"\n📄 Log-Datei gespeichert unter: {logFile}")

    def logConsumption(self):
        """Speichert den durchschnittlichen Verbrauch in die Logdatei."""
        if not self.consumptionHistory:
            return

        avgConsumption = sum(self.consumptionHistory) / len(self.consumptionHistory)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        logPath = os.path.join(self.logFolder, "consumption_log.txt")

        with open(logPath, "a") as log:
            log.write(f"[{timestamp}] Durchschnittlicher Verbrauch: {avgConsumption:.2f} L/100km\n")

        print(f"✅ Verbrauchslog gespeichert: {avgConsumption:.2f} L/100km")
        self.consumptionHistory = []  # Verlauf zurücksetzen

    def calculateFuelConsumption(self, maf, speed):
        """ Berechnet den Momentanverbrauch in L/100 km mit MAF. Gibt immer eine gültige Zahl zurück. """
        if maf is None or speed is None:
            print("⚠️ Kein MAF oder keine Geschwindigkeit → Verbrauch auf 0.0 L/100km gesetzt.")
            return 0.0  # Verhindert Fehler durch None-Werte

        if maf <= 0 or speed <= 0:
            print(f"⚠️ Ungültige Werte für Verbrauch: MAF={maf}, Speed={speed}. Setze auf 0.0 L/100km.")
            return 0.0  # Fehler durch Nullwerte verhindern

        AFR = 14.7  # Luft-Kraftstoff-Verhältnis für Benziner
        fuelDensity = 0.739  # Dichte von Benzin in kg/L

        try:
            # Falls MAF in g/s gemessen wird, Umrechnung auf kg/s
            maf_kg_per_s = maf / 1000
            # Berechnung des Kraftstoffflusses in L/s
            fuelFlow = maf_kg_per_s / (AFR * fuelDensity)
            # Verbrauch in L/100km umrechnen
            consumption = ((fuelFlow * 3600 * 100) / speed)

            # Falls der berechnete Verbrauch unplausibel hoch ist, auf 0.0 setzen
            if consumption > 50 or consumption < 0:
                print(f"⚠️ Unplausibler Verbrauch erkannt: {consumption:.2f} L/100km → Setze auf 0.0")
                return 0.0

            return consumption

        except Exception as e:
            print(f"❌ Fehler bei der Verbrauchsberechnung: {e} → Setze Verbrauch auf 0.0")
            return 0.0  # Sicherstellen, dass immer eine gültige Zahl zurückkommt

    def printAndLogConsumption(self):
        """ Berechnet und gibt den Verbrauch einmal pro Durchlauf aus. """
        consumption = self.calculateFuelConsumption(self.mafValue, self.speedValue)
        print(f"\n📊 Momentanverbrauch: {consumption:.2f} L/100km\n")

        # Nur loggen, wenn der Wert > 0.0 ist (damit keine unnötigen Nullwerte gespeichert werden)
        if consumption > 0.0:
            self.consumptionHistory.append(consumption)
            avgConsumption = sum(self.consumptionHistory) / len(self.consumptionHistory)
            self.logConsumption()

    def startReconnectLog(self):
        """Speichert jeden Verbindungsversuch in die Logdatei."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logMessage(f"🔄 Reconnect-Versuch um {timestamp}")

    def logMessage(self, message):
        """Schreibt jede Konsolenausgabe auch ins Logfile."""
        print(message)
        with open("full_log.txt", "a") as log:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.write(f"[{timestamp}] {message}\n")

    def logAverageValues(self):
        """Berechnet und speichert Durchschnittswerte aller gesammelten Messungen."""
        if not self.valueHistory:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        averages = {key: sum(values) / len(values) for key, values in self.valueHistory.items() if values}

        logPath = os.path.join(self.logFolder, "average_log.txt")

        with open(logPath, "a") as log:
            log.write(f"\n[{timestamp}] Durchschnittswerte:\n")
            for key, avg in averages.items():
                log.write(f"{key}: {avg:.2f}\n")
            log.write("\n")

        print(f"✅ Durchschnittswerte gespeichert: {averages}")
        self.valueHistory = {}  # Verlauf zurücksetzen

    def logSingleValues(self):
        """Speichert jede einzelne Messung."""
        if not self.valueHistory:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logPath = os.path.join(self.logFolder, "raw_log.txt")

        with open(logPath, "a") as log:
            log.write(f"[{timestamp}] Messwerte:\n")
            for key, values in self.valueHistory.items():
                log.write(f"{key}: {values[-1]:.2f}\n")  # Letzter Wert wird gespeichert
            log.write("\n")

        print(f"✅ Einzelwerte gespeichert.")

    def restartBluetooth(self):
        """Fragt den User, bevor Bluetooth neu gestartet wird."""
        try:
            confirm = input("❓ Verbindung fehlgeschlagen. Bluetooth zurücksetzen? (y/n): ").strip().lower()
            if confirm != "y":
                print("🔄 Bluetooth bleibt unverändert.")
                return

            print("🔄 Bluetooth wird neu gestartet...")
            subprocess.run(["sudo", "pkill", "bluetoothd"], check=True)
            subprocess.run(["sudo", "launchctl", "stop", "com.apple.bluetoothd"], check=True)
            subprocess.run(["sudo", "launchctl", "start", "com.apple.bluetoothd"], check=True)
            print("✅ Bluetooth erfolgreich neu gestartet.")
        except Exception as e:
            print(f"❌ Fehler beim Neustart von Bluetooth: {e}")

    def checkDTCs(self):
        dtcResponse = self.connection.query(obd.commands.GET_DTC)
        if not dtcResponse.is_null():
            print("Diagnose-Fehlercodes:")
            with open("dtc_log.txt", "a") as log:
                log.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                for code in dtcResponse.value:
                    print(f"{code[0]} - {code[1]}")
                    log.write(f"{code[0]} - {code[1]}\n")
            print("Fehlercodes in dtc_log.txt gespeichert.")
        else:
            print("Keine Fehlercodes gefunden.")

    def clearDTCs(self):
        response = self.connection.query(obd.commands.CLEAR_DTC)
        if response:
            print("Fehlercodes erfolgreich gelöscht.")
        else:
            print("Fehler beim Löschen der Fehlercodes.")

    def logError(self, message):
        """Schreibt Fehler in eine Logdatei."""
        with open("error_log.txt", "a") as log:
            log.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")


# Hauptprogramm
if __name__ == "__main__":
    commandsAllFile = "commands.txt"  # Name der Datei mit ALLEN Commands
    commandsImpFile = "commandsImportant.txt"  # Name der Datei mit WICHTIGEN Commands
    commandsMILFile = "commandsMIL.txt"

    MAX_RETRIES = 3
    retryCount = 0
    reader = None  # Initialisiere reader als None

    while retryCount < MAX_RETRIES:
        print(f"🔄 Verbindungsversuch {retryCount + 1}/{MAX_RETRIES}...")
        reader = ObdReader(commandsAllFile, commandsImpFile, commandsMILFile)
        if reader.connection and reader.connection.is_connected():
            reader.readAvailablePIDs()

        if reader.connection and reader.connection.is_connected():  # Sicherstellen, dass die Verbindung wirklich aktiv ist
            print("\n\n######################################")
            print("✅ OBD2-Adapter erfolgreich verbunden!")
            reader.startReading()  # Starten der OBD-Datenabfrage
            sys.exit(0)  # Erfolgreicher Exit

        retryCount += 1
        time.sleep(5)  # Wartezeit zwischen den Versuchen

    # Falls nach 3 Versuchen keine Verbindung -> Frage nach Bluetooth-Reset
    print("❌ Konnte keine Verbindung zum OBD2-Adapter herstellen.")
    reader.restartBluetooth()  # User kann selbst entscheiden

    print("\n🔄 Starte das Programm neu, um eine neue Verbindung zu versuchen.")
    sys.exit(1)  # Programm mit Fehlerstatus beenden


    # pyside6-uic MainWindow.ui -o ui_mainwindow.py
    # pyqt6-tools designer QtDesiogner öffnen
    # pyside6-designer
    # system_profiler SPBluetoothDataType -> (alle geräte details anzeigen lassen)

    # RESTART BLUETOOTH
    # sudo pkill bluetoothd
    # sudo launchctl stop com.apple.bluetoothd
    # sudo launchctl start com.apple.bluetoothd
