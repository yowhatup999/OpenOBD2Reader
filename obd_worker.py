from PySide6.QtCore import QThread, Signal
import time

class ObdWorker(QThread):
    dataReceived = Signal(dict)
    dtcReceived = Signal(str)

    def __init__(self, obdReader, mode="important", interval=2000):
        super().__init__()
        self.obdReader = obdReader
        self.mode = mode
        self.interval = interval / 1000
        self.running = True

    def run(self):
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

            time.sleep(self.interval)

    def stop(self):
        self.running = False
