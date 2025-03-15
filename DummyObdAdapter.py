import random

class DummyObdAdapter:
    def get_data(self, mode="important"):
        """Liefert Dummy-OBD-Daten."""
        return {
            "RPM": f"{random.randint(700, 6000)} U/min",
            "SPEED": f"{random.randint(0, 220)} km/h",
            "THROTTLE_POS": f"{random.uniform(5.0, 95.0):.2f} %",
            "COOLANT_TEMP": f"{random.randint(70, 120)} °C",
            "ENGINE_LOAD": f"{random.randint(10, 95)} %",
            "FUEL_LEVEL": f"{random.uniform(5.0, 100.0):.1f} %",
            "MAF": f"{random.uniform(2.0, 20.0):.2f} g/s",
        }

    def get_data(self, mode="important"):
        """Dummy-Daten liefern."""
        return self.get_dummy_data()

    def get_dummy_data(self):
        return {
            "RPM": f"{random.randint(700, 6000)} U/min",
            "SPEED": f"{random.randint(0, 220)} km/h",
            "THROTTLE_POS": f"{random.uniform(5.0, 95.0):.2f} %",
            "COOLANT_TEMP": f"{random.randint(70, 120)} °C",
            "ENGINE_LOAD": f"{random.randint(10, 95)} %",
            "FUEL_LEVEL": f"{random.uniform(5.0, 100.0):.2f} %",
            "MAF": f"{random.uniform(2.0, 20.0):.2f} g/s",
        }

    def get_dtcs(self):
        if random.choice([True, False]):
            return [
                "P0300 - Random Misfire Detected",
                "P0420 - Catalyst System Efficiency Below Threshold"
            ]
        else:
            return []
