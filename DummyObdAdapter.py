import random

class DummyObdAdapter:
    """Simuliert einen OBD-Adapter mit zufälligen Werten."""

    def get_data(self, mode="important"):
        """Liefert zufällige Dummy-Daten für OBD-Werte."""
        return {
            "RPM": f"{random.randint(700, 6000)} U/min",
            "SPEED": f"{random.randint(0, 220)} km/h",
            "THROTTLE_POS": f"{random.uniform(5.0, 95.0):.1f} %",
            "COOLANT_TEMP": f"{random.randint(70, 120)} °C",
            "ENGINE_LOAD": f"{random.randint(10, 95)} %",
            "FUEL_LEVEL": f"{random.uniform(5.0, 100.0):.1f} %",
            "MAF": f"{random.uniform(2.0, 20.0):.1f} g/s",
        }

    def get_dtcs(self):
        """Gibt zufällig generierte Fehlercodes zurück oder eine leere Liste."""
        return [
            "P0300 - Random Misfire Detected",
            "P0420 - Catalyst System Efficiency Below Threshold"
        ] if random.choice([True, False]) else []
