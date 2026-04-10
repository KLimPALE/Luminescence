import serial
import serial.tools.list_ports
import time


class LaserSource:
    def __init__(self):
        self.connection = None
        self.is_connected = False
        self.port_name = None


    def connect(self, com_port = None, baudrate: int = 115200) -> bool:
        connection_status = False

        if com_port is None:
            available_ports = list(serial.tools.list_ports.comports())

            for port in available_ports:
                try:
                    temporary_connection = serial.Serial(port.device, baudrate, timeout=1)
                    time.sleep(0.5)
                    temporary_connection.write("?\r".encode())
                    time.sleep(0.3)

                    response_lines = []

                    for _ in range(5):
                        line = temporary_connection.readline().decode().strip()

                        if not line:
                            break

                        response_lines.append(line)

                    temporary_connection.close()
                    full_response = " ".join(response_lines)

                    if "OPO" in full_response or "CU-2350" in full_response:
                        com_port = port.device

                        break
                except:
                    continue

        if com_port is None:
            return connection_status

        try:
            if isinstance(com_port, int):
                com_port = f"COM{com_port}"

            self.connection = serial.Serial(com_port, baudrate, timeout=1)
            time.sleep(0.5)
            self.port_name = com_port
            self.is_connected = True
            connection_status = True
        except Exception as error:
            connection_status = False

        return connection_status


    def disconnect(self):
        if self.connection and self.connection.is_open:
            self.connection.close()

        self.is_connected = False


    def send_command(self, command_string: str) -> str:
        response_string = ""

        if self.is_connected:
            try:
                self.connection.write(f"{command_string}\r".encode())
                time.sleep(0.3)

                first_response = self.connection.readline().decode().strip()

                if self.connection.in_waiting:
                    second_response = self.connection.readline().decode().strip()

                    if second_response:
                        response_string = second_response
                    else:
                        response_string = first_response
                else:
                    response_string = first_response
            except:
                response_string = ""

        return response_string


    def send_command_multi(self, command_string: str) -> str:
        response_string = ""

        if self.is_connected:
            try:
                self.connection.write(f"{command_string}\r".encode())
                time.sleep(0.3)

                response_lines = []

                for _ in range(20):
                    line = self.connection.readline().decode().strip()

                    if not line:
                        break

                    response_lines.append(line)

                    if ">" in line:
                        break

                response_string = "\n".join(response_lines)
            except:
                response_string = ""

        return response_string


    def parse_value(self, response_string: str, parameter_name: str) -> str:
        result_string = ""

        if "=" in response_string:
            parts = response_string.split("=")

            if len(parts) > 1:
                result_string = parts[1].split(";")[0].strip()

        return result_string


    def get_model(self) -> str:
        response_string = self.send_command_multi("?")
        model_string = "OPO 2350"

        for line in response_string.split("\n"):
            if "NAME=" in line:
                parts = line.split("=")

                if len(parts) > 1:
                    model_string = parts[1].split(";")[0].strip().strip("'")
                    
                    return model_string

        for line in response_string.split("\n"):
            if "OPO" in line:
                if "'" in line:
                    model_string = line.split("'")[0]
                else:
                    model_string = line.strip()
                
                return model_string

        return model_string


    def get_position(self, motor_number: int = 1) -> int:
        position_value = 0
        response_string = self.send_command(f"CUR{motor_number}?")
        value_string = self.parse_value(response_string, f"CUR{motor_number}")

        if value_string:
            try:
                position_value = int(value_string)
            except:
                position_value = 0

        return position_value


    def get_status(self, motor_number: int = 1) -> int:
        status_value = -1
        response_string = self.send_command(f"ST{motor_number}?")
        value_string = self.parse_value(response_string, f"ST{motor_number}")

        if value_string:
            try:
                status_value = int(value_string)
            except:
                status_value = -1

        return status_value


    def is_ready(self, motor_number: int = 1) -> bool:
        status_value = self.get_status(motor_number)
        ready_status = status_value == 0

        return ready_status


    def set_absolute_position(self, motor_number: int = 1, position_steps: int = 0) -> bool:
        operation_status = False

        if self.is_connected:
            response_string = self.send_command(f"GA{motor_number}={position_steps}")

            if f"GA{motor_number}={position_steps}" in response_string or "OK" in response_string:
                operation_status = True

        return operation_status


    def set_relative_position(self, motor_number: int = 1, position_steps: int = 0) -> bool:
        operation_status = False

        if self.is_connected:
            response_string = self.send_command(f"GR{motor_number}={position_steps}")

            if f"GR{motor_number}={position_steps}" in response_string or "OK" in response_string:
                operation_status = True

        return operation_status


    def enable_motor(self, motor_number: int = 1) -> bool:
        operation_status = False

        if self.is_connected:
            response_string = self.send_command(f"ENB{motor_number}")

            if "OK" in response_string:
                operation_status = True

        return operation_status


    def disable_motor(self, motor_number: int = 1) -> bool:
        operation_status = False

        if self.is_connected:
            response_string = self.send_command(f"DSB{motor_number}")

            if "OK" in response_string:
                operation_status = True

        return operation_status


    def get_speed(self, motor_number: int = 1) -> int:
        speed_value = 0
        response_string = self.send_command(f"SPD{motor_number}?")
        value_string = self.parse_value(response_string, f"SPD{motor_number}")

        if value_string:
            try:
                speed_value = int(value_string)
            except:
                speed_value = 0

        return speed_value


    def set_shutter(self, shutter_number: int = 1, open_status: bool = True) -> bool:
        operation_status = False

        if self.is_connected:
            if shutter_number == 1:
                command_string = "SHUTTER=1" if open_status else "SHUTTER=0"
            else:
                command_string = "SHUTTER2=1" if open_status else "SHUTTER2=0"

            response_string = self.send_command(command_string)

            if f"{command_string.split('=')[0]}={1 if open_status else 0}" in response_string:
                operation_status = True

        return operation_status


    def get_shutter(self, shutter_number: int = 1) -> bool:
        shutter_status = False

        if shutter_number == 1:
            response_string = self.send_command("SHUTTER?")
        else:
            response_string = self.send_command("SHUTTER2?")

        value_string = self.parse_value(response_string, f"SHUTTER{'' if shutter_number == 1 else '2'}")

        if value_string:
            try:
                shutter_status = int(value_string) == 1
            except:
                shutter_status = False

        return shutter_status


    def set_wavelength(self, wavelength_nanometers: float) -> bool:
        operation_status = self.set_absolute_position(1, int(wavelength_nanometers))

        return operation_status


    def get_wavelength(self) -> float:
        wavelength_value = self.get_position(1)
        wavelength_float = float(wavelength_value)

        return wavelength_float


    def reset(self) -> bool:
        operation_status = False

        if self.is_connected:
            response_string = self.send_command("RESET")

            if "OK" in response_string:
                operation_status = True

        return operation_status
