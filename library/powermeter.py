import serial
import serial.tools.list_ports
import time


class Powermeter:
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
                    temporary_connection.write("*VER\r\n".encode())
                    time.sleep(0.2)
                    response_string = temporary_connection.readline().decode().strip()
                    temporary_connection.close()

                    if "Maestro" in response_string or "Gentec" in response_string:
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
                self.connection.write(f"{command_string}\r\n".encode())
                time.sleep(0.1)
                response_string = self.connection.readline().decode().strip()
            except:
                response_string = ""

        return response_string


    def get_version(self) -> str:
        version_string = self.send_command("*VER")

        return version_string


    def get_status(self) -> str:
        status_string = self.send_command("*STS")

        return status_string


    def get_extended_status(self) -> str:
        extended_status_string = self.send_command("*ST2")

        return extended_status_string


    def set_scale(self, scale_index: int) -> bool:
        operation_status = False

        if self.is_connected and 0 <= scale_index <= 41:
            command_string = f"*SCS{scale_index:02d}"
            response_string = self.send_command(command_string)

            if "OK" in response_string.upper():
                operation_status = True

        return operation_status


    def set_scale_up(self) -> bool:
        operation_status = False
        response_string = self.send_command("*SSU")

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def set_scale_down(self) -> bool:
        operation_status = False
        response_string = self.send_command("*SSD")

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def get_current_scale_index(self) -> int:
        scale_index = 0
        response_string = self.send_command("*GCR")

        try:
            scale_index = int(response_string)
        except:
            scale_index = 0

        return scale_index


    def set_autoscale(self, enable_status: bool) -> bool:
        operation_status = False
        command_string = "*SAS1" if enable_status else "*SAS0"
        response_string = self.send_command(command_string)

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def get_autoscale(self) -> bool:
        autoscale_status = False
        response_string = self.send_command("*GAS")

        if response_string == "1":
            autoscale_status = True

        return autoscale_status


    def get_valid_scales(self) -> str:
        valid_scales_string = self.send_command("*DVS")

        return valid_scales_string


    def set_trigger_level(self, trigger_level_percent: float) -> bool:
        operation_status = False

        if 0.1 <= trigger_level_percent <= 99.9:
            command_string = f"*STL{trigger_level_percent:04.1f}"
            response_string = self.send_command(command_string)

            if "OK" in response_string.upper():
                operation_status = True

        return operation_status


    def get_trigger_level(self) -> float:
        trigger_level = 0.0
        response_string = self.send_command("*GTL")

        if ":" in response_string:
            parts = response_string.split(":")

            if len(parts) > 1:
                try:
                    trigger_level = float(parts[1].strip())
                except:
                    trigger_level = 0.0

        return trigger_level


    def get_measure_mode(self) -> int:
        measure_mode = 0
        response_string = self.send_command("*GMD")

        if ":" in response_string:
            parts = response_string.split(":")

            if len(parts) > 1:
                try:
                    measure_mode = int(parts[1].strip())
                except:
                    measure_mode = 0

        return measure_mode


    def get_power(self) -> float:
        power_value = 0.0
        response_string = self.send_command("*CVU")

        if response_string:
            try:
                if response_string.startswith(":"):
                    hex_value = response_string[1:]
                    power_value = int(hex_value, 16) / 1000000.0
                else:
                    power_value = float(response_string)
            except:
                power_value = 0.0

        return power_value


    def get_energy(self) -> float:
        energy_value = self.get_power()

        return energy_value


    def start_continuous_transmission(self) -> bool:
        operation_status = False
        response_string = self.send_command("*CAU")

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def start_continuous_with_frequency(self) -> bool:
        operation_status = False
        response_string = self.send_command("*CEU")

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def get_current_with_frequency(self):
        energy_value = 0.0
        frequency_value = 0.0
        response_string = self.send_command("*CTU")

        parts = response_string.split(",")

        if len(parts) >= 2:
            try:
                energy_value = float(parts[0])
                frequency_value = float(parts[1])
            except:
                energy_value = 0.0
                frequency_value = 0.0

        return energy_value, frequency_value


    def stop_continuous_transmission(self) -> bool:
        operation_status = False
        response_string = self.send_command("*CSU")

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def is_new_value_ready(self) -> bool:
        new_value_ready = False
        response_string = self.send_command("*NVU")

        if "available" in response_string.lower() and "not" not in response_string.lower():
            new_value_ready = True

        return new_value_ready


    def get_laser_frequency(self) -> float:
        frequency_value = 0.0
        response_string = self.send_command("*GRR")

        try:
            frequency_value = float(response_string)
        except:
            frequency_value = 0.0

        return frequency_value


    def set_binary_mode(self, enable_status: bool) -> bool:
        operation_status = False
        command_string = "*SS11" if enable_status else "*SS10"
        response_string = self.send_command(command_string)

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def get_binary_mode(self) -> bool:
        binary_mode_status = False
        response_string = self.send_command("*GBM")

        if response_string == "1":
            binary_mode_status = True

        return binary_mode_status


    def set_wavelength_nanometers(self, wavelength_nanometers: int) -> bool:
        operation_status = False
        command_string = f"*PWC{wavelength_nanometers:05d}"
        response_string = self.send_command(command_string)

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def set_wavelength_microns(self, wavelength_microns: float) -> bool:
        operation_status = False
        command_string = f"*PWM{wavelength_microns:05.1f}"
        response_string = self.send_command(command_string)

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def get_wavelength(self) -> int:
        wavelength_value = 0
        response_string = self.send_command("*GWL")

        if ":" in response_string:
            parts = response_string.split(":")

            if len(parts) > 1:
                try:
                    wavelength_value = int(parts[1].strip())
                except:
                    wavelength_value = 0

        return wavelength_value


    def set_anticipation(self, enable_status: bool) -> bool:
        operation_status = False
        command_string = "*ANT1" if enable_status else "*ANT0"
        response_string = self.send_command(command_string)

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def get_anticipation(self) -> bool:
        anticipation_status = False
        response_string = self.send_command("*GAN")

        if response_string == "1":
            anticipation_status = True

        return anticipation_status


    def set_noise_suppression(self, average_size: int) -> bool:
        operation_status = False

        if 0 <= average_size <= 999:
            command_string = f"*AVG{average_size:03d}"
            response_string = self.send_command(command_string)

            if "OK" in response_string.upper():
                operation_status = True

        return operation_status


    def set_zero_offset(self) -> bool:
        operation_status = False
        response_string = self.send_command("*SOU")

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def clear_zero_offset(self) -> bool:
        operation_status = False
        response_string = self.send_command("*COU")

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def get_zero_offset(self) -> bool:
        zero_offset_status = False
        response_string = self.send_command("*GZO")

        if response_string == "1":
            zero_offset_status = True

        return zero_offset_status


    def set_diode_zero_offset(self) -> bool:
        operation_status = False
        response_string = self.send_command("*SDZ")

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def set_user_multiplier(self, multiplier: float) -> bool:
        operation_status = False
        command_string = f"*MUL{multiplier:.6e}"
        response_string = self.send_command(command_string)

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def get_user_multiplier(self) -> float:
        multiplier_value = 1.0
        response_string = self.send_command("*GUM")

        if ":" in response_string:
            parts = response_string.split(":")

            if len(parts) > 1:
                try:
                    multiplier_value = float(parts[1].strip())
                except:
                    multiplier_value = 1.0

        return multiplier_value


    def set_user_offset(self, offset: float) -> bool:
        operation_status = False
        command_string = f"*OFF{offset:.6e}"
        response_string = self.send_command(command_string)

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def get_user_offset(self) -> float:
        offset_value = 0.0
        response_string = self.send_command("*GUO")

        if ":" in response_string:
            parts = response_string.split(":")

            if len(parts) > 1:
                try:
                    offset_value = float(parts[1].strip())
                except:
                    offset_value = 0.0

        return offset_value


    def set_single_shot_energy_mode(self, enable_status: bool) -> bool:
        operation_status = False
        command_string = "*SSE1" if enable_status else "*SSE0"
        response_string = self.send_command(command_string)

        if "OK" in response_string.upper():
            operation_status = True

            if operation_status:
                time.sleep(2)

        return operation_status


    def set_attenuator(self, enable_status: bool) -> bool:
        operation_status = False
        command_string = "*ATT1" if enable_status else "*ATT0"
        response_string = self.send_command(command_string)

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def get_attenuator(self) -> bool:
        attenuator_status = False
        response_string = self.send_command("*GAT")

        if response_string == "1":
            attenuator_status = True

        return attenuator_status


    def set_external_trigger(self, enable_status: bool) -> bool:
        operation_status = False
        command_string = "*ET1" if enable_status else "*ET0"
        response_string = self.send_command(command_string)

        if "OK" in response_string.upper():
            operation_status = True

        return operation_status


    def set_baud_rate(self, baud_rate_index: int) -> bool:
        operation_status = False
        baud_rates = {0: 9600, 1: 19200, 2: 38400, 3: 57600, 4: 115200}

        if baud_rate_index in baud_rates:
            command_string = f"*BPS{baud_rate_index}"
            response_string = self.send_command(command_string)

            if "OK" in response_string.upper():
                operation_status = True

        return operation_status


    def get_average_power(self, number_of_measurements: int = 10, delay_seconds: float = 0.1) -> float:
        total_value = 0.0

        for measurement_index in range(number_of_measurements):
            total_value = total_value + self.get_power()
            time.sleep(delay_seconds)

        average_value = total_value / number_of_measurements

        return average_value


    def get_average_energy(self, number_of_measurements: int = 10, delay_seconds: float = 0.1) -> float:
        total_value = 0.0

        for measurement_index in range(number_of_measurements):
            total_value = total_value + self.get_energy()
            time.sleep(delay_seconds)

        average_value = total_value / number_of_measurements

        return average_value
