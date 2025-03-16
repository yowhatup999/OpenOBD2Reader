from PySide6.QtCore import QThread, Signal
import time
from obd_logger import ObdLogger


class ObdWorker(QThread):
    """Thread für die regelmäßige OBD-Abfrage."""

    dtcReceived = Signal(str)  # dataReceived entfernt, falls nicht genutzt

    def __init__(self, obdReader, mode="important", interval=2000):
        super().__init__()
        self.obdReader = obdReader
        self.mode = mode
        self.interval = interval / 1000
        self.running = True
        self.logger = ObdLogger()

    def run(self):
        """Startet die periodische OBD-Abfrage."""
        self.logger.log_info(f"OBD-Worker gestartet im Modus: {self.mode}")

        while self.running:
            if self.mode == "dummy":
                self.obdReader.startDummyConnection()
            elif self.mode == "important":
                self.obdReader.readImportant()
            elif self.mode == "all":
                self.obdReader.readAll()
            elif self.mode == "mil":
                self.obdReader.readMIL()
            elif self.mode == "dtc":
                self.obdReader.checkDTCs()
            else:
                self.logger.log_warning(f"Unbekannter Modus: {self.mode}")
                break  # Unbekannter Modus → Loop abbrechen

            time.sleep(self.interval)

        self.logger.log_info("OBD-Worker gestoppt.")

    def stop(self):
        """Stoppt den Worker."""
        if self.running:
            self.logger.log_info("Stop-Signal für OBD-Worker gesendet.")
        self.running = False
