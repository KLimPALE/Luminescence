import serial
import time

class Laser:
    def __init__(self):
        self.motor = None
        self.connected = False

    def connect(self, com_port=30):
        try:
            self.motor = serial.Serial(f'COM{com_port}', 115200, timeout=1)
            self.connected = True
            print(f"Лазер (моторы) подключён к COM{com_port}")
            return True
        except Exception as exception:
            print(f"Ошибка подключения лазера: {exception}")
            return False

    def disconnect(self):
        if self.motor:
            self.motor.close()
        self.connected = False
        print("Лазер отключён")

    def go_home(self, motor_id=1):
        if not self.connected:
            print("Лазер не подключён")
            return
        self.motor.write(f'HOM{motor_id}=500\r'.encode())
        self._wait_for_free(motor_id)

    def set_wavelength_motor_steps(self, motor_id: int, steps: int):
        if not self.connected:
            print("Лазер не подключён")
            return
        self.motor.write(f'GA{motor_id}={steps}\r'.encode())
        self._wait_for_free(motor_id)

    def get_position(self, motor_id: int) -> int:
        if not self.connected:
            return -1
        self.motor.write(f'CUR{motor_id}\r'.encode())
        time.sleep(0.1)
        line = self.motor.readline().decode().strip()
        if line.startswith(f'CUR{motor_id}='):
            return int(line.split('=')[1])
        return -1

    def _wait_for_free(self, motor_id: int, timeout=10):
        for _ in range(timeout * 2):
            self.motor.write(f'ST{motor_id}\r'.encode())
            time.sleep(0.1)
            line = self.motor.readline().decode().strip()
            if line.endswith('0'):
                return
            time.sleep(0.5)
        print(f"Предупреждение: мотор {motor_id} не освободился за {timeout} сек")

    def is_connected(self):
        return self.connected
