import numpy
import pyvisa
import time

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple


class Oscilloscope:
    def __init__(self):
        self.instrument = None
        self.resource_manager = None
        self.is_connected = False
        self.timeout_milliseconds = 5000


    def connect(self, resource_string: str = None) -> bool:
        status = False

        try:
            self.resource_manager = pyvisa.ResourceManager('@py')

            if resource_string:
                self.instrument = self.resource_manager.open_resource(resource_string)
            else:
                available_resources = self.resource_manager.list_resources()

                for single_resource in available_resources:
                    if 'USB' in single_resource:
                        try:
                            temporary_instrument = self.resource_manager.open_resource(single_resource)
                            temporary_instrument.timeout = self.timeout_milliseconds
                            temporary_instrument.read_termination = '\n'
                            temporary_instrument.write_termination = '\n'
                            
                            temporary_instrument.write('*IDN?')
                            time.sleep(0.2)
                            identification_string = temporary_instrument.read()

                            if any(brand in identification_string.upper() for brand in ['AGILENT', 'KEYSIGHT', 'RIGOL', 'TEKTRONIX', 'SIGLENT', 'ROHDE', 'SCHWARZ']):
                                self.instrument = temporary_instrument

                                break
                            else:
                                temporary_instrument.close()
                        except Exception as error:
                            continue

            if self.instrument is not None:
                self.is_connected = True
                status = True
        except Exception as error:
            pass

        return status


    def disconnect(self):
        if self.instrument:
            self.instrument.close()

        if self.resource_manager:
            self.resource_manager.close()

        self.is_connected = False


    def set_timeout(self, milliseconds: int):
        self.timeout_milliseconds = milliseconds

        if self.instrument:
            self.instrument.timeout = milliseconds


    def identification(self) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write('*IDN?')
        time.sleep(0.2)
        identification_string = self.instrument.read()

        return identification_string


    def reset(self):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write('*RST')
        time.sleep(0.1)


    def self_test(self) -> bool:
        if not self.is_connected or self.instrument is None:
            return False

        self.instrument.write('*TST?')
        time.sleep(0.2)
        test_result = self.instrument.read() == '0'

        return test_result


    def clear_status(self):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write('*CLS')


    def get_error(self) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write(':SYSTem:ERRor?')
        time.sleep(0.2)
        error_message = self.instrument.read()

        return error_message


    def wait_for_operation_complete(self):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write('*OPC?')
        time.sleep(0.2)
        self.instrument.read()


    def set_channel_display(self, channel_number: int, enable_status: bool):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':CHANnel{channel_number}:DISPlay {1 if enable_status else 0}')


    def get_channel_display(self, channel_number: int) -> bool:
        if not self.is_connected or self.instrument is None:
            return False

        self.instrument.write(f':CHANnel{channel_number}:DISPlay?')
        time.sleep(0.2)
        display_status = self.instrument.read() == '1'

        return display_status


    def set_channel_scale(self, channel_number: int, scale_volts: float):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':CHANnel{channel_number}:SCALe {scale_volts}')


    def get_channel_scale(self, channel_number: int) -> float:
        if not self.is_connected or self.instrument is None:
            return 0.0

        self.instrument.write(f':CHANnel{channel_number}:SCALe?')
        time.sleep(0.2)
        scale_value = float(self.instrument.read())

        return scale_value


    def set_channel_offset(self, channel_number: int, offset_volts: float):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':CHANnel{channel_number}:OFFSet {offset_volts}')


    def get_channel_offset(self, channel_number: int) -> float:
        if not self.is_connected or self.instrument is None:
            return 0.0

        self.instrument.write(f':CHANnel{channel_number}:OFFSet?')
        time.sleep(0.2)
        offset_value = float(self.instrument.read())

        return offset_value


    def set_channel_coupling(self, channel_number: int, coupling_type: str):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':CHANnel{channel_number}:COUPling {coupling_type}')


    def get_channel_coupling(self, channel_number: int) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write(f':CHANnel{channel_number}:COUPling?')
        time.sleep(0.2)
        coupling_value = self.instrument.read().strip()

        return coupling_value


    def set_channel_impedance(self, channel_number: int, impedance_ohms: float):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':CHANnel{channel_number}:IMPedance {impedance_ohms}')


    def get_channel_impedance(self, channel_number: int) -> float:
        if not self.is_connected or self.instrument is None:
            return 0.0

        self.instrument.write(f':CHANnel{channel_number}:IMPedance?')
        time.sleep(0.2)
        impedance_value = float(self.instrument.read())

        return impedance_value


    def set_channel_probe(self, channel_number: int, attenuation_factor: float):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':CHANnel{channel_number}:PROBe {attenuation_factor}')


    def get_channel_probe(self, channel_number: int) -> float:
        if not self.is_connected or self.instrument is None:
            return 0.0

        self.instrument.write(f':CHANnel{channel_number}:PROBe?')
        time.sleep(0.2)
        attenuation_value = float(self.instrument.read())

        return attenuation_value


    def set_channel_invert(self, channel_number: int, invert_status: bool):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':CHANnel{channel_number}:INVert {1 if invert_status else 0}')


    def get_channel_invert(self, channel_number: int) -> bool:
        if not self.is_connected or self.instrument is None:
            return False

        self.instrument.write(f':CHANnel{channel_number}:INVert?')
        time.sleep(0.2)
        invert_status = self.instrument.read() == '1'

        return invert_status


    def set_channel_bandwidth(self, channel_number: int, bandwidth_limit: str):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':CHANnel{channel_number}:BANDwidth {bandwidth_limit}')


    def get_channel_bandwidth(self, channel_number: int) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write(f':CHANnel{channel_number}:BANDwidth?')
        time.sleep(0.2)
        bandwidth_value = self.instrument.read().strip()

        return bandwidth_value


    def set_channel_label(self, channel_number: int, label_text: str):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':CHANnel{channel_number}:LABel "{label_text}"')


    def get_channel_label(self, channel_number: int) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write(f':CHANnel{channel_number}:LABel?')
        time.sleep(0.2)
        label_value = self.instrument.read().strip().strip('"')

        return label_value


    def auto_scale(self):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(':AUToscale')
        time.sleep(1)


    def set_timebase_scale(self, seconds_per_division: float):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':TIMebase:SCALe {seconds_per_division}')


    def get_timebase_scale(self) -> float:
        if not self.is_connected or self.instrument is None:
            return 0.0

        self.instrument.write(':TIMebase:SCALe?')
        time.sleep(0.2)
        scale_value = float(self.instrument.read())

        return scale_value


    def set_timebase_delay(self, delay_seconds: float):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':TIMebase:DELay {delay_seconds}')


    def get_timebase_delay(self) -> float:
        if not self.is_connected or self.instrument is None:
            return 0.0

        self.instrument.write(':TIMebase:DELay?')
        time.sleep(0.2)
        delay_value = float(self.instrument.read())

        return delay_value


    def set_timebase_reference(self, reference_position: str):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':TIMebase:REFerence {reference_position}')


    def get_timebase_reference(self) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write(':TIMebase:REFerence?')
        time.sleep(0.2)
        reference_value = self.instrument.read().strip()

        return reference_value


    def set_timebase_mode(self, mode_type: str):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':TIMebase:MODE {mode_type}')


    def get_timebase_mode(self) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write(':TIMebase:MODE?')
        time.sleep(0.2)
        mode_value = self.instrument.read().strip()

        return mode_value


    def run_acquisition(self):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(':RUN')


    def stop_acquisition(self):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(':STOP')


    def single_acquisition(self):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(':SINGle')


    def force_trigger(self):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(':TRIGger:FORCe')


    def set_trigger_source(self, source_channel: str):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':TRIGger:SOURce {source_channel}')


    def get_trigger_source(self) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write(':TRIGger:SOURce?')
        time.sleep(0.2)
        source_value = self.instrument.read().strip()

        return source_value


    def set_trigger_level(self, level_volts: float):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':TRIGger:LEVel {level_volts}')


    def get_trigger_level(self) -> float:
        if not self.is_connected or self.instrument is None:
            return 0.0

        self.instrument.write(':TRIGger:LEVel?')
        time.sleep(0.2)
        level_value = float(self.instrument.read())

        return level_value


    def set_trigger_slope(self, slope_direction: str):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':TRIGger:SLOPe {slope_direction}')


    def get_trigger_slope(self) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write(':TRIGger:SLOPe?')
        time.sleep(0.2)
        slope_value = self.instrument.read().strip()

        return slope_value


    def set_trigger_mode(self, mode_type: str):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':TRIGger:MODE {mode_type}')


    def get_trigger_mode(self) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write(':TRIGger:MODE?')
        time.sleep(0.2)
        mode_value = self.instrument.read().strip()

        return mode_value


    def set_trigger_coupling(self, coupling_type: str):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':TRIGger:COUPling {coupling_type}')


    def get_trigger_coupling(self) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write(':TRIGger:COUPling?')
        time.sleep(0.2)
        coupling_value = self.instrument.read().strip()

        return coupling_value


    def set_trigger_holdoff(self, holdoff_seconds: float):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':TRIGger:HOLDoff {holdoff_seconds}')


    def get_trigger_holdoff(self) -> float:
        if not self.is_connected or self.instrument is None:
            return 0.0

        self.instrument.write(':TRIGger:HOLDoff?')
        time.sleep(0.2)
        holdoff_value = float(self.instrument.read())

        return holdoff_value


    def set_acquire_type(self, acquisition_type: str):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':ACQuire:TYPE {acquisition_type}')


    def get_acquire_type(self) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write(':ACQuire:TYPE?')
        time.sleep(0.2)
        type_value = self.instrument.read().strip()

        return type_value


    def set_acquire_type_normal(self):
        self.set_acquire_type('NORMal')


    def set_acquire_type_average(self):
        self.set_acquire_type('AVERage')


    def set_acquire_type_peak(self):
        self.set_acquire_type('PEAK')


    def set_acquire_type_high_resolution(self):
        self.set_acquire_type('HRESolution')


    def set_average_count(self, number_of_averages: int):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':ACQuire:COUNt {number_of_averages}')


    def get_average_count(self) -> int:
        if not self.is_connected or self.instrument is None:
            return 0

        self.instrument.write(':ACQuire:COUNt?')
        time.sleep(0.2)
        count_value = int(self.instrument.read())

        return count_value


    def set_acquire_complete(self, completion_percent: int = 100):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':ACQuire:COMPlete {completion_percent}')


    def get_acquire_complete(self) -> int:
        if not self.is_connected or self.instrument is None:
            return 0

        self.instrument.write(':ACQuire:COMPlete?')
        time.sleep(0.2)
        percent_value = int(self.instrument.read())

        return percent_value


    def measure(self, parameter_name: str, channel_number: int = 1, timeout_milliseconds: int = 5000) -> Optional[float]:
        result_value = None

        valid_parameters = [
            'VPP',
            'VMAX',
            'VMIN',
            'VRMS',
            'FREQuency',
            'PERiod',
            'RISetime',
            'FALLtime',
            'PWIDth',
            'NWIDth',
            'DUTYcycle',
            'MEAN',
            'RMS',
            'OVERS',
            'PREShoot',
            'DELay',
            'PHASe'
        ]

        if parameter_name.upper() in valid_parameters:
            try:
                old_timeout = self.instrument.timeout
                self.instrument.timeout = timeout_milliseconds
                self.instrument.write(f':MEASure:{parameter_name}? CHAN{channel_number}')
                time.sleep(0.2)

                measurement_result = self.instrument.read()
                result_value = float(measurement_result) if measurement_result else None

                self.instrument.timeout = old_timeout
            except:
                result_value = None

        return result_value


    def measure_peak_to_peak(self, channel_number: int = 1) -> Optional[float]:
        result_value = self.measure('VPP', channel_number)

        return result_value


    def measure_maximum(self, channel_number: int = 1) -> Optional[float]:
        result_value = self.measure('VMAX', channel_number)

        return result_value


    def measure_minimum(self, channel_number: int = 1) -> Optional[float]:
        result_value = self.measure('VMIN', channel_number)

        return result_value


    def measure_rms(self, channel_number: int = 1) -> Optional[float]:
        result_value = self.measure('VRMS', channel_number)

        return result_value


    def measure_frequency(self, channel_number: int = 1) -> Optional[float]:
        result_value = self.measure('FREQuency', channel_number)

        return result_value


    def measure_period(self, channel_number: int = 1) -> Optional[float]:
        result_value = self.measure('PERiod', channel_number)

        return result_value


    def measure_rise_time(self, channel_number: int = 1) -> Optional[float]:
        result_value = self.measure('RISetime', channel_number)

        return result_value


    def measure_fall_time(self, channel_number: int = 1) -> Optional[float]:
        result_value = self.measure('FALLtime', channel_number)

        return result_value


    def measure_positive_width(self, channel_number: int = 1) -> Optional[float]:
        result_value = self.measure('PWIDth', channel_number)

        return result_value


    def measure_negative_width(self, channel_number: int = 1) -> Optional[float]:
        result_value = self.measure('NWIDth', channel_number)

        return result_value


    def measure_duty_cycle(self, channel_number: int = 1) -> Optional[float]:
        result_value = self.measure('DUTYcycle', channel_number)

        return result_value


    def measure_mean(self, channel_number: int = 1) -> Optional[float]:
        result_value = self.measure('MEAN', channel_number)

        return result_value


    def measure_rms_ac(self, channel_number: int = 1) -> Optional[float]:
        result_value = self.measure('RMS', channel_number)

        return result_value


    def measure_phase(self, source_one: str = 'CHAN1', source_two: str = 'CHAN2') -> Optional[float]:
        result_value = None

        try:
            self.instrument.write(f':MEASure:PHASe? {source_one},{source_two}')
            time.sleep(0.2)
            phase_result = self.instrument.read()
            result_value = float(phase_result) if phase_result else None
        except:
            result_value = None

        return result_value


    def measure_delay(self, source_one: str = 'CHAN1', source_two: str = 'CHAN2') -> Optional[float]:
        result_value = None

        try:
            self.instrument.write(f':MEASure:DELay? {source_one},{source_two}')
            time.sleep(0.2)
            delay_result = self.instrument.read()
            result_value = float(delay_result) if delay_result else None
        except:
            result_value = None

        return result_value


    def set_cursor_mode(self, cursor_mode: str):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':CURSor:MODE {cursor_mode}')


    def get_cursor_mode(self) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write(':CURSor:MODE?')
        time.sleep(0.2)
        mode_value = self.instrument.read().strip()

        return mode_value


    def set_cursor_position(self, cursor_name: str, position_value: float):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':CURSor:{cursor_name} {position_value}')


    def get_cursor_position(self, cursor_name: str) -> float:
        if not self.is_connected or self.instrument is None:
            return 0.0

        self.instrument.write(f':CURSor:{cursor_name}?')
        time.sleep(0.2)
        position_value = float(self.instrument.read())

        return position_value


    def get_cursor_delta(self) -> Dict[str, float]:
        if not self.is_connected or self.instrument is None:
            return {'delta_x': 0.0, 'delta_y': 0.0, 'inverse_delta_x': 0.0}

        self.instrument.write(':CURSor:XDELta?')
        time.sleep(0.1)
        delta_x = float(self.instrument.read())

        self.instrument.write(':CURSor:YDELta?')
        time.sleep(0.1)
        delta_y = float(self.instrument.read())

        self.instrument.write(':CURSor:INVXDELta?')
        time.sleep(0.1)
        inverse_delta_x = float(self.instrument.read())

        delta_values = {
            'delta_x': delta_x,
            'delta_y': delta_y,
            'inverse_delta_x': inverse_delta_x
        }

        return delta_values


    def set_math_function(self, math_function: str):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':MATH:FUNCtion {math_function}')


    def get_math_function(self) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write(':MATH:FUNCtion?')
        time.sleep(0.2)
        function_value = self.instrument.read().strip()

        return function_value


    def set_math_source(self, source_one: str, source_two: str = None):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':MATH:SOURce1 {source_one}')

        if source_two:
            self.instrument.write(f':MATH:SOURce2 {source_two}')


    def set_math_scale(self, scale_value: float):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':MATH:SCALe {scale_value}')


    def get_math_scale(self) -> float:
        if not self.is_connected or self.instrument is None:
            return 0.0

        self.instrument.write(':MATH:SCALe?')
        time.sleep(0.2)
        scale_value = float(self.instrument.read())

        return scale_value


    def set_math_offset(self, offset_value: float):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':MATH:OFFSet {offset_value}')


    def get_math_offset(self) -> float:
        if not self.is_connected or self.instrument is None:
            return 0.0

        self.instrument.write(':MATH:OFFSet?')
        time.sleep(0.2)
        offset_value = float(self.instrument.read())

        return offset_value


    def set_math_fft_window(self, window_type: str):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':MATH:FFT:WINDow {window_type}')


    def capture_waveform(self, channel_number: int = 1, points_count: int = 2000) -> Tuple[List[float], List[float]]:
        time_values = []
        voltage_values = []

        if self.is_connected:
            try:
                self.instrument.write(':STOP')
                time.sleep(0.05)

                self.instrument.write(f':CHANnel{channel_number}:DISPlay 1')
                self.instrument.write(':SINGle')

                time.sleep(0.5)

                self.instrument.write(f':WAVeform:SOURce CHAN{channel_number}')

                try:
                    self.instrument.write(':WAVeform:FORMat WORD')
                    self.instrument.write(':WAVeform:BYTeorder LSBFirst')
                    use_binary = True
                except:
                    self.instrument.write(':WAVeform:FORMat ASCII')
                    use_binary = False

                self.instrument.write(f':WAVeform:POINts {points_count}')

                self.instrument.write(':WAVeform:PREamble?')
                time.sleep(0.1)
                preamble_string = self.instrument.read()
                preamble_parts = preamble_string.split(',')

                x_increment = float(preamble_parts[4])
                x_origin = float(preamble_parts[5])
                y_increment = float(preamble_parts[7])
                y_origin = float(preamble_parts[8])

                self.instrument.write(':WAVeform:DATA?')
                time.sleep(0.3)

                if use_binary:
                    binary_data = self.instrument.read_binary_values(datatype='h', is_big_endian=False)
                    voltage_values = [(value - y_origin) * y_increment for value in binary_data]
                else:
                    ascii_data = self.instrument.read()

                    if ascii_data.startswith('#'):
                        header_length = int(ascii_data[1])
                        ascii_data = ascii_data[2 + header_length:]

                    voltage_values = [float(value) for value in ascii_data.strip().split(',')]

                time_values = [x_origin + index * x_increment for index in range(len(voltage_values))]
            except Exception as error:
                time_values = []
                voltage_values = []

        return time_values, voltage_values


    def acquire_waveform(self, channel_number: int = 1, points_count: int = 2000, binary_format: bool = False) -> Tuple[List[float], List[float]]:
        time_axis, voltage_data = self.capture_waveform(channel_number, points_count)

        return time_axis, voltage_data


    def acquire_waveform_binary(self, channel_number: int = 1, points_count: int = 2000) -> Tuple[List[float], List[float]]:
        time_axis, voltage_values = self.capture_waveform(channel_number, points_count)

        return time_axis, voltage_values


    def setup_for_experiment(self, channel_number: int = 1, volts_per_division: float = 1.0, seconds_per_division: float = 0.01) -> bool:
        operation_status = False

        if self.is_connected:
            try:
                self.instrument.write(':STOP')
                time.sleep(0.05)

                self.set_channel_display(channel_number, True)
                self.set_channel_scale(channel_number, volts_per_division)
                self.set_channel_offset(channel_number, 0)
                self.set_channel_coupling(channel_number, "DC")
                self.set_timebase_scale(seconds_per_division)
                self.set_trigger_source(f"CHAN{channel_number}")
                self.set_trigger_level(0)
                self.set_trigger_slope("POS")

                operation_status = True
            except Exception as error:
                operation_status = False

        return operation_status


    def get_waveform_preamble(self) -> Dict[str, Any]:
        if not self.is_connected or self.instrument is None:
            return {}

        self.instrument.write(':WAVeform:PREamble?')
        time.sleep(0.2)
        preamble_data = self.instrument.read().split(',')

        preamble_parameters = {
            'format_code': int(preamble_data[0]),
            'acquisition_type': int(preamble_data[1]),
            'points_count': int(preamble_data[2]),
            'average_count': int(preamble_data[3]),
            'x_increment': float(preamble_data[4]),
            'x_origin': float(preamble_data[5]),
            'x_reference': float(preamble_data[6]),
            'y_increment': float(preamble_data[7]),
            'y_origin': float(preamble_data[8]),
            'y_reference': float(preamble_data[9])
        }

        return preamble_parameters


    def set_segment_count(self, segment_quantity: int):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':ACQuire:SEGMent:COUNt {segment_quantity}')


    def get_segment_count(self) -> int:
        if not self.is_connected or self.instrument is None:
            return 0

        self.instrument.write(':ACQuire:SEGMent:COUNt?')
        time.sleep(0.2)
        segment_quantity = int(self.instrument.read())

        return segment_quantity


    def set_segment_index(self, segment_index_number: int):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':ACQuire:SEGMent:INDex {segment_index_number}')


    def get_segment(self, segment_index_number: int, channel_number: int = 1) -> Tuple[List[float], List[float]]:
        self.set_segment_index(segment_index_number)
        time_axis, voltage_values = self.acquire_waveform(channel_number)

        return time_axis, voltage_values


    def load_mask(self, file_name: str):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':MASK:LOAD "{file_name}"')


    def check_mask(self) -> bool:
        if not self.is_connected or self.instrument is None:
            return False

        self.instrument.write(':MASK:FAIL?')
        time.sleep(0.2)
        mask_status = self.instrument.read() == '1'

        return mask_status


    def get_mask_fail_count(self) -> int:
        if not self.is_connected or self.instrument is None:
            return 0

        self.instrument.write(':MASK:COUNt?')
        time.sleep(0.2)
        fail_count = int(self.instrument.read())

        return fail_count


    def clear_mask_fail_count(self):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(':MASK:CLEar')


    def save_screenshot(self, file_name: str = None) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write(':DISPlay:DATA? PNG')
        image_data = self.instrument.read_raw()

        if file_name is None:
            file_name = f"screenshot_{time.strftime('%Y%m%d_%H%M%S')}.png"

        with open(file_name, 'wb') as file_handle:
            if image_data.startswith(b'#'):
                header_length = int(chr(image_data[1]))
                image_data = image_data[2 + header_length:]

            file_handle.write(image_data)

        return file_name


    def save_setup(self, memory_location: str = '1'):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':SAVE:SETup {memory_location}')


    def recall_setup(self, memory_location: str = '1'):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':RECall:SETup {memory_location}')


    def export_waveform_to_csv(self, file_name: str, channel_number: int = 1):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':EXPort:WAVeform:SOURce CHAN{channel_number}')
        self.instrument.write(f':EXPort:WAVeform:STARt "{file_name}"')


    def get_ip_address(self) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write(':SYSTem:COMMunicate:LAN:IPADdress?')
        time.sleep(0.2)
        ip_address = self.instrument.read().strip()

        return ip_address


    def set_ip_address(self, ip_address: str):
        if not self.is_connected or self.instrument is None:
            return

        self.instrument.write(f':SYSTem:COMMunicate:LAN:IPADdress "{ip_address}"')


    def get_mac_address(self) -> str:
        if not self.is_connected or self.instrument is None:
            return ""

        self.instrument.write(':SYSTem:COMMunicate:LAN:MAC?')
        time.sleep(0.2)
        mac_address = self.instrument.read().strip()

        return mac_address


    def get_all_settings(self) -> Dict[str, Any]:
        if not self.is_connected or self.instrument is None:
            return {}

        all_settings = {
            'identification': self.identification(),
            'timebase_scale': self.get_timebase_scale(),
            'timebase_delay': self.get_timebase_delay(),
            'timebase_mode': self.get_timebase_mode(),
            'acquire_type': self.get_acquire_type(),
            'average_count': self.get_average_count(),
            'trigger_source': self.get_trigger_source(),
            'trigger_level': self.get_trigger_level(),
            'trigger_slope': self.get_trigger_slope(),
        }

        for channel_index in range(1, 5):
            try:
                all_settings[f'channel_{channel_index}_display'] = self.get_channel_display(channel_index)
                all_settings[f'channel_{channel_index}_scale'] = self.get_channel_scale(channel_index)
                all_settings[f'channel_{channel_index}_offset'] = self.get_channel_offset(channel_index)
                all_settings[f'channel_{channel_index}_coupling'] = self.get_channel_coupling(channel_index)
            except Exception as error:
                continue

        return all_settings


    def get_signal_statistics(self, channel_number: int = 1) -> Dict[str, float]:
        statistics = {}
        _, voltage_values = self.acquire_waveform(channel_number)

        if voltage_values:
            statistics = {
                'points_count': len(voltage_values),
                'maximum_voltage': max(voltage_values),
                'minimum_voltage': min(voltage_values),
                'peak_to_peak_voltage': max(voltage_values) - min(voltage_values),
                'average_voltage': sum(voltage_values) / len(voltage_values),
                'standard_deviation': float(numpy.std(voltage_values)) if len(voltage_values) > 1 else 0
            }

        return statistics


    def get_device_information(self) -> Dict[str, str]:
        if not self.is_connected or self.instrument is None:
            return {}

        self.instrument.write(':SYSTem:INFo:MANufacturer?')
        time.sleep(0.2)
        manufacturer = self.instrument.read().strip()
        
        self.instrument.write(':SYSTem:INFo:MODeL?')
        time.sleep(0.2)
        model_number = self.instrument.read().strip()
        
        self.instrument.write(':SYSTem:INFo:SERial?')
        time.sleep(0.2)
        serial_number = self.instrument.read().strip()
        
        self.instrument.write(':SYSTem:INFo:Firmware?')
        time.sleep(0.2)
        firmware_version = self.instrument.read().strip()

        device_info = {
            'manufacturer': manufacturer,
            'model_number': model_number,
            'serial_number': serial_number,
            'firmware_version': firmware_version
        }

        return device_info
