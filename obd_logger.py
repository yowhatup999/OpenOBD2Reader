import os
from datetime import datetime

class ObdLogger:
    def __init__(self, log_console=None):
        self.log_folder = "logs"
        os.makedirs(self.log_folder, exist_ok=True)
        self.log_file = os.path.join(self.log_folder, "obd_log.txt")
        self.log_console = log_console

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}\n"

        if self.log_console:
            self.log_console.appendPlainText(log_message.strip())

        with open(self.log_file, "a") as f:
            f.write(log_message)

    def log_info(self, message):
        self.log(message, "INFO")

    def log_warning(self, message):
        self.log(message, "WARNING")

    def log_error(self, message):
        self.log(message, "ERROR")

    def log_ok(self, message):
        self.log(message, "OK")
