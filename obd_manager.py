import obd
from obd_logger import ObdLogger

class ObdManager:
    def __init__(self, port="/dev/ttyUSB0"):
        self.port = port
        self.connection = None
        self.logger = ObdLogger()

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

    def get_data(self, mode):
        """Liest OBD-Daten aus."""
        if not self.connection or not self.connection.is_connected():
            return {}

        commands = {
            "important": [obd.commands.RPM, obd.commands.SPEED],
            "dummy": ["Dummy-Werte"]
        }

        data = {}
        for cmd in commands.get(mode, []):
            response = self.connection.query(cmd)
            if response and response.value:
                data[cmd.name] = response.value
            else:
                data[cmd.name] = "N/A"

        return data
