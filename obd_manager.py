import obd
from obd_logger import ObdLogger
from obd_worker import ObdWorker

class ObdManager:
    def __init__(self, obdReader, port="/dev/ttyUSB0"):
        """Verwaltet die OBD-Verbindung und den OBD-Worker."""
        self.port = port
        self.connection = None
        self.logger = ObdLogger()
        self.obdReader = obdReader
        self.obdWorker = None

    def connect(self):
        """Stellt die OBD-Verbindung her."""
        try:
            self.connection = obd.OBD(self.port)
            if self.connection.is_connected():
                self.logger.log_ok("OBD2-Adapter erfolgreich verbunden!")
                return True
            else:
                self.logger.log_error("Verbindung zum OBD2-Adapter fehlgeschlagen.")
                return False
        except Exception as e:
            self.logger.log_error(f"Fehler beim Verbinden: {e}")
            return False

    def start_worker(self, mode="important"):
        """Startet den OBD-Worker im angegebenen Modus."""
        self.stop_worker()  # Falls bereits ein Worker läuft, erst stoppen

        self.logger.log_info(f"Starte OBD-Worker im Modus: {mode}")

        self.obdWorker = ObdWorker(self.obdReader, mode, interval=2000)
        self.obdWorker.start()

    def stop_worker(self):
        """Stoppt den OBD-Worker, falls er läuft."""
        if self.obdWorker and self.obdWorker.isRunning():
            self.obdWorker.stop()
            self.obdWorker.quit()
            self.obdWorker.wait(2000)
            self.logger.log_info("OBD-Worker gestoppt")
