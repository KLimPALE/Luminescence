import pyvisa
from qcodes_contrib_drivers.drivers.Gentec.Gentec_Maestro import Gentec_Maestro
import time

class PowerMeter:
    def __init__(self):
        self.device = None
        self.connected = False

    def connect(self, com_port=5):
        try:
            self.device = Gentec_Maestro(name="Gentec", address=f'ASRL{com_port}::INSTR')
            self.connected = True
            print(f"Измеритель энергии подключён к COM{com_port}")
            return True
        except Exception as exception:
            print(f"Ошибка подключения измерителя энергии: {exception}")
            return False

    def disconnect(self):
        self.connected = False
        print("Измеритель энергии отключён")

    def set_wavelength(self, nm: int):
        if self.connected:
            self.device.wavelength.set(nm)

    def get_energy(self, n=5) -> float:
        if not self.connected:
            return 0.0
        total = 0.0
        for _ in range(n):
            total += self.device.power.get()
            time.sleep(0.1)
        return total / n

    def get_unit(self) -> str:
        if self.connected:
            return self.device.power.unit
        return "N/A"

    def zero_calibrate(self):
        if self.connected:
            self.device.set_zero_offset()
            self.device.clear_zero_offset()
            print("Калибровка нуля выполнена")

    def is_connected(self):
        return self.connected
