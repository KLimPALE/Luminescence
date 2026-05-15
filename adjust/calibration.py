import sys
import time
import threading
import json
import numpy
import tkinter
from tkinter import ttk, filedialog
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

if getattr(sys, "frozen", False):
    library_path = Path(sys._MEIPASS) / 'library'
else:
    library_path = Path(__file__).resolve().parent.parent / 'library'

sys.path.insert(0, str(library_path))

from chromator import Chromator
from oscilloscope import Oscilloscope
from mathematics import integrate_signal


class CalibrationConfiguration:
    def __init__(self):
        self.start_wavelength_nanometers = 1307.1
        self.end_wavelength_nanometers = 1309.1
        self.wavelength_step_nanometers = 0.2

        self.input_slit_micrometers = 100.0
        self.output_slit_micrometers = 100.0
        self.oscilloscope_average_count = 65536

        self.oscilloscope_signal_channel = 1
        self.oscilloscope_trigger_channel = 2
        self.oscilloscope_volts_per_division = 0.05
        self.oscilloscope_seconds_per_division = 1e-6

        self.signal_amplitude_threshold = 0.1
        self.peak_matching_tolerance_nanometers = 2.0

        self.baseline_start_time_seconds = -10e-6
        self.baseline_end_time_seconds = -2e-6
        self.signal_integration_start_time_seconds = -2e-6
        self.signal_integration_end_time_seconds = 20e-6


class CalibrationManager:
    def __init__(self):
        if getattr(sys, "frozen", False):
            self.base_path = Path(sys._MEIPASS)
        else:
            self.base_path = Path(__file__).parent.parent

        self.configuration = CalibrationConfiguration()

        self.chromator_device = None
        self.oscilloscope_device = None

        self.is_chromator_connected = False
        self.is_oscilloscope_connected = False

        self.calibration_result = None

        self.builtin_reference_data = {
            "led_1308_nanometers": {
                "display_name": "Автомат (светодиод 1308 нм)",
                "peaks_with_names": [(1308.0, "Основной пик")],
                "description": "Светодиод с известной длиной волны 1308 нм"
            }
        }

        self.custom_reference_peaks = []
        self.custom_reference_filename = None

        self.application_window = None
        self.operation_lock = threading.Lock()

    def connect_instruments(self, log_widget: tkinter.Text) -> bool:
        connection_success = True

        log_widget.insert(tkinter.END, "Подключение к оборудованию...\n")

        try:
            self.chromator_device = Chromator()
            if self.chromator_device.connect():
                self.is_chromator_connected = True
                log_widget.insert(tkinter.END, "Монохроматор подключен\n")
            else:
                log_widget.insert(tkinter.END, "Монохроматор НЕ подключен\n")
                connection_success = False
        except Exception as error:
            log_widget.insert(tkinter.END, f"Ошибка подключения монохроматора: {error}\n")
            connection_success = False

        try:
            self.oscilloscope_device = Oscilloscope()
            if self.oscilloscope_device.connect():
                self.is_oscilloscope_connected = True
                log_widget.insert(tkinter.END, "Осциллограф подключен\n")
            else:
                log_widget.insert(tkinter.END, "Осциллограф НЕ подключен\n")
                connection_success = False
        except Exception as error:
            log_widget.insert(tkinter.END, f"Ошибка подключения осциллографа: {error}\n")
            connection_success = False

        return connection_success

    def disconnect_instruments(self, log_widget: tkinter.Text):
        log_widget.insert(tkinter.END, "Отключение оборудования...\n")

        if self.chromator_device:
            try:
                self.chromator_device.disconnect()
                self.is_chromator_connected = False
                log_widget.insert(tkinter.END, "Монохроматор отключен\n")
            except Exception as error:
                log_widget.insert(tkinter.END, f"Ошибка отключения монохроматора: {error}\n")

        if self.oscilloscope_device:
            try:
                self.oscilloscope_device.disconnect()
                self.is_oscilloscope_connected = False
                log_widget.insert(tkinter.END, "Осциллограф отключен\n")
            except Exception as error:
                log_widget.insert(tkinter.END, f"Ошибка отключения осциллографа: {error}\n")

    def apply_device_settings(self, log_widget: tkinter.Text):
        if self.chromator_device:
            try:
                self.chromator_device.set_slit_width(0, self.configuration.input_slit_micrometers)
                self.chromator_device.set_slit_width(1, self.configuration.output_slit_micrometers)
                log_widget.insert(tkinter.END, f"Щели установлены: вход={self.configuration.input_slit_micrometers} мкм, выход={self.configuration.output_slit_micrometers} мкм\n")
            except Exception as error:
                log_widget.insert(tkinter.END, f"Ошибка настройки монохроматора: {error}\n")

        if self.oscilloscope_device:
            try:
                self.oscilloscope_device.set_channel_scale(self.configuration.oscilloscope_signal_channel,
                                                           self.configuration.oscilloscope_volts_per_division)
                self.oscilloscope_device.set_timebase_scale(self.configuration.oscilloscope_seconds_per_division)
                self.oscilloscope_device.set_trigger_source(f"CHAN{self.configuration.oscilloscope_trigger_channel}")
                self.oscilloscope_device.set_trigger_level(0.5)
                log_widget.insert(tkinter.END, f"Осциллограф настроен\n")
            except Exception as error:
                log_widget.insert(tkinter.END, f"Ошибка настройки осциллографа: {error}\n")

    def check_oscilloscope_communication(self) -> bool:
        if not self.oscilloscope_device:
            return False

        try:
            self.oscilloscope_device._instrument.write("*IDN?")
            time.sleep(0.2)
            response = self.oscilloscope_device._instrument.read()
            return len(response) > 0
        except Exception:
            return False

    def measure_signal_integral(self) -> float:
        if not self.oscilloscope_device:
            return 0.0

        if not self.check_oscilloscope_communication():
            return 0.0

        try:
            self.oscilloscope_device.stop_acquisition()
            time.sleep(0.05)
            self.oscilloscope_device.run_acquisition()
            time.sleep(0.5)

            time_values, voltage_values = self.oscilloscope_device.capture_waveform(self.configuration.oscilloscope_signal_channel, 2000)
        except Exception:
            return 0.0

        if not voltage_values:
            return 0.0

        corrected_signal = []
        baseline_signal = []

        for point_index in range(len(time_values)):
            if self.configuration.baseline_start_time_seconds <= time_values[point_index] <= self.configuration.baseline_end_time_seconds:
                baseline_signal.append(voltage_values[point_index])

        if baseline_signal:
            baseline_level = numpy.mean(baseline_signal)
            for voltage in voltage_values:
                corrected_signal.append(voltage - baseline_level)
        else:
            corrected_signal = voltage_values.copy()

        integration_start = self.configuration.signal_integration_start_time_seconds
        integration_end = self.configuration.signal_integration_end_time_seconds

        integration_time = []
        integration_signal = []
        for point_index in range(len(time_values)):
            if integration_start <= time_values[point_index] <= integration_end:
                integration_time.append(time_values[point_index])
                integration_signal.append(corrected_signal[point_index])

        if len(integration_time) < 2:
            return 0.0

        integral_value = integrate_signal(integration_time, integration_signal)

        return integral_value

    def scan_spectrum(self, log_widget: tkinter.Text, progress_callback) -> List[Tuple[float, float]]:
        measurement_results = []
        wavelength_list = numpy.arange(self.configuration.start_wavelength_nanometers,
                                       self.configuration.end_wavelength_nanometers + self.configuration.wavelength_step_nanometers,
                                       self.configuration.wavelength_step_nanometers)

        total_points = len(wavelength_list)

        for point_index, wavelength in enumerate(wavelength_list):
            self.chromator_device.set_wavelength(wavelength)
            time.sleep(0.5)

            signal_integral = self.measure_signal_integral()
            measurement_results.append((wavelength, signal_integral))

            completion_percent = int((point_index + 1) / total_points * 100)
            progress_callback(completion_percent)

            if point_index % 5 == 0:
                log_widget.insert(tkinter.END, f"   {wavelength:.1f} нм -> {signal_integral:.6e} В·с\n")
                log_widget.see(tkinter.END)

        return measurement_results

    def find_spectral_peaks(self, spectrum_data: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        wavelength_array = numpy.array([point[0] for point in spectrum_data])
        intensity_array = numpy.array([point[1] for point in spectrum_data])

        maximum_intensity = numpy.max(intensity_array)
        intensity_threshold = maximum_intensity * self.configuration.signal_amplitude_threshold

        detected_peaks = []
        for index in range(1, len(intensity_array) - 1):
            if intensity_array[index] > intensity_array[index - 1] and intensity_array[index] > intensity_array[index + 1]:
                if intensity_array[index] > intensity_threshold:
                    detected_peaks.append((wavelength_array[index], intensity_array[index]))

        return detected_peaks

    def compute_calibration_coefficients(self, measured_peaks: List[Tuple[float, float]],
                                          reference_peaks: List[Tuple[float, str]]) -> dict:
        if not measured_peaks:
            return {"error_message": "Пики не найдены"}

        matched_points = []
        for reference_wavelength, reference_name in reference_peaks:
            nearest_peak = min(measured_peaks, key=lambda peak: abs(peak[0] - reference_wavelength))
            if abs(nearest_peak[0] - reference_wavelength) < self.configuration.peak_matching_tolerance_nanometers:
                matched_points.append({
                    "reference_wavelength": reference_wavelength,
                    "measured_wavelength": nearest_peak[0],
                    "peak_name": reference_name,
                    "measurement_error": nearest_peak[0] - reference_wavelength
                })

        if not matched_points:
            return {"error_message": "Не найдено совпадающих пиков"}

        if len(matched_points) == 1:
            wavelength_offset = matched_points[0]["measured_wavelength"] - matched_points[0]["reference_wavelength"]
            calibration_result = {
                "calibration_method": "wavelength_offset",
                "offset_nanometers": wavelength_offset,
                "intercept_nanometers": -wavelength_offset,
                "slope_factor": 1.0,
                "matched_points": matched_points
            }
        else:
            reference_wavelengths = numpy.array([point["reference_wavelength"] for point in matched_points])
            measured_wavelengths = numpy.array([point["measured_wavelength"] for point in matched_points])
            slope_factor, intercept_nanometers = numpy.polyfit(reference_wavelengths, measured_wavelengths, 1)
            calibration_result = {
                "calibration_method": "linear_regression",
                "slope_factor": slope_factor,
                "intercept_nanometers": intercept_nanometers,
                "offset_nanometers": None,
                "matched_points": matched_points
            }

        measurement_errors = [point["measurement_error"] for point in matched_points]
        calibration_result["statistics"] = {
            "mean_error_nanometers": numpy.mean(measurement_errors),
            "std_deviation_error": numpy.std(measurement_errors),
            "maximum_absolute_error": numpy.max(numpy.abs(measurement_errors))
        }

        return calibration_result

    def apply_calibration_to_spectrum(self, spectrum_data: List[Tuple[float, float]], calibration_result: dict) -> List[Tuple[float, float]]:
        if "error_message" in calibration_result:
            return spectrum_data

        calibrated_spectrum = []
        if calibration_result["calibration_method"] == "wavelength_offset":
            offset = calibration_result["offset_nanometers"]
            for wavelength, intensity in spectrum_data:
                calibrated_spectrum.append((wavelength - offset, intensity))
        else:
            slope = calibration_result["slope_factor"]
            intercept = calibration_result["intercept_nanometers"]
            for wavelength, intensity in spectrum_data:
                calibrated_wavelength = (wavelength - intercept) / slope
                calibrated_spectrum.append((calibrated_wavelength, intensity))

        return calibrated_spectrum

    def save_calibration_data(self, calibration_data: dict) -> Path:
        timestamp_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"calibration_{timestamp_string}.json"

        calibration_data["calibration_date"] = datetime.now().isoformat()
        calibration_data["scan_parameters"] = {
            "start_wavelength_nanometers": self.configuration.start_wavelength_nanometers,
            "end_wavelength_nanometers": self.configuration.end_wavelength_nanometers,
            "step_nanometers": self.configuration.wavelength_step_nanometers,
            "input_slit_micrometers": self.configuration.input_slit_micrometers,
            "output_slit_micrometers": self.configuration.output_slit_micrometers,
            "oscilloscope_average_count": self.configuration.oscilloscope_average_count
        }

        calibration_filepath = self.base_path / "calibration_results" / filename
        calibration_filepath.parent.mkdir(exist_ok=True)

        with open(calibration_filepath, 'w', encoding='utf-8') as file_handle:
            json.dump(calibration_data, file_handle, indent=2, ensure_ascii=False)

        main_application_config = {
            "chromator": {
                "calibration_date": calibration_data["calibration_date"],
                "calibration_method": calibration_data["calibration_method"],
                "slope_factor": calibration_data.get("slope_factor", 1.0),
                "intercept_nanometers": calibration_data.get("intercept_nanometers", 0.0),
                "offset_nanometers": calibration_data.get("offset_nanometers", 0.0),
                "is_calibration_enabled": True
            }
        }

        config_filepath = self.base_path / "calibration_config.json"
        with open(config_filepath, 'w', encoding='utf-8') as file_handle:
            json.dump(main_application_config, file_handle, indent=2, ensure_ascii=False)

        return calibration_filepath

    def load_custom_reference_file(self, file_path: Path) -> List[Tuple[float, str]]:
        loaded_peaks = []
        try:
            if file_path.suffix == '.csv':
                import csv
                with open(file_path, 'r', encoding='utf-8') as csv_file:
                    csv_reader = csv.reader(csv_file)
                    for row in csv_reader:
                        if row and len(row) >= 2:
                            loaded_peaks.append((float(row[0]), row[1]))
            else:
                with open(file_path, 'r', encoding='utf-8') as text_file:
                    for line in text_file:
                        if ',' in line:
                            parts = line.strip().split(',')
                            loaded_peaks.append((float(parts[0]), parts[1]))
        except Exception as error:
            raise Exception(f"Ошибка загрузки файла: {error}")

        return loaded_peaks

    def save_parameters_to_file(self, file_path: Path):
        parameters = {
            "start_wavelength_nanometers": self.configuration.start_wavelength_nanometers,
            "end_wavelength_nanometers": self.configuration.end_wavelength_nanometers,
            "wavelength_step_nanometers": self.configuration.wavelength_step_nanometers,
            "input_slit_micrometers": self.configuration.input_slit_micrometers,
            "output_slit_micrometers": self.configuration.output_slit_micrometers,
            "oscilloscope_average_count": self.configuration.oscilloscope_average_count,
            "baseline_start_time_seconds": self.configuration.baseline_start_time_seconds,
            "baseline_end_time_seconds": self.configuration.baseline_end_time_seconds,
            "signal_integration_start_time_seconds": self.configuration.signal_integration_start_time_seconds,
            "signal_integration_end_time_seconds": self.configuration.signal_integration_end_time_seconds
        }

        with open(file_path, 'w', encoding='utf-8') as file_handle:
            json.dump(parameters, file_handle, indent=2, ensure_ascii=False)

    def load_parameters_from_file(self, file_path: Path):
        with open(file_path, 'r', encoding='utf-8') as file_handle:
            parameters = json.load(file_handle)

        self.configuration.start_wavelength_nanometers = parameters.get("start_wavelength_nanometers", self.configuration.start_wavelength_nanometers)
        self.configuration.end_wavelength_nanometers = parameters.get("end_wavelength_nanometers", self.configuration.end_wavelength_nanometers)
        self.configuration.wavelength_step_nanometers = parameters.get("wavelength_step_nanometers", self.configuration.wavelength_step_nanometers)
        self.configuration.input_slit_micrometers = parameters.get("input_slit_micrometers", self.configuration.input_slit_micrometers)
        self.configuration.output_slit_micrometers = parameters.get("output_slit_micrometers", self.configuration.output_slit_micrometers)
        self.configuration.oscilloscope_average_count = parameters.get("oscilloscope_average_count", self.configuration.oscilloscope_average_count)
        self.configuration.baseline_start_time_seconds = parameters.get("baseline_start_time_seconds", self.configuration.baseline_start_time_seconds)
        self.configuration.baseline_end_time_seconds = parameters.get("baseline_end_time_seconds", self.configuration.baseline_end_time_seconds)
        self.configuration.signal_integration_start_time_seconds = parameters.get("signal_integration_start_time_seconds", self.configuration.signal_integration_start_time_seconds)
        self.configuration.signal_integration_end_time_seconds = parameters.get("signal_integration_end_time_seconds", self.configuration.signal_integration_end_time_seconds)


class CalibrationApplication:
    def __init__(self):
        self.calibration_manager = CalibrationManager()
        self.application_window = None
        self.is_automatic_mode = True
        self.measured_spectrum = []
        self.calibrated_spectrum = []
        self.calibration_result = None

    def initialize_user_interface(self):
        self.application_window = tkinter.Tk()
        self.application_window.title("Калибровка оборудования")
        self.application_window.geometry("1000x800")
        self.application_window.resizable(False, False)

        icon_file_path = self.calibration_manager.base_path / "icon.png"
        if icon_file_path.exists():
            try:
                application_icon = tkinter.PhotoImage(file=str(icon_file_path))
                self.application_window.iconphoto(True, application_icon)
            except Exception:
                pass

        main_container = ttk.Frame(self.application_window, padding=10)
        main_container.pack(fill=tkinter.BOTH, expand=True)

        graph_frame = ttk.LabelFrame(main_container, text="Спектр:", padding=5)
        graph_frame.pack(fill=tkinter.BOTH, expand=True, pady=(0, 10))

        self.graph_canvas = tkinter.Canvas(graph_frame, bg="white", height=250)
        self.graph_canvas.pack(fill=tkinter.BOTH, expand=True)

        control_frame = ttk.Frame(main_container)
        control_frame.pack(fill=tkinter.X, pady=5)

        self.connect_button = ttk.Button(control_frame, text="Подключить", width=15, command=self.connect_instruments)
        self.connect_button.pack(side=tkinter.LEFT, padx=5)

        self.disconnect_button = ttk.Button(control_frame, text="Отключить", width=15, command=self.disconnect_instruments, state=tkinter.DISABLED)
        self.disconnect_button.pack(side=tkinter.LEFT, padx=5)

        self.mode_button = ttk.Button(control_frame, text="Ручной", width=15, command=self.toggle_calibration_mode)
        self.mode_button.pack(side=tkinter.LEFT, padx=50)

        self.load_parameters_button = ttk.Button(control_frame, text="Загрузить", width=15,
                                                  command=self.load_parameters_from_file, state=tkinter.DISABLED)
        self.load_parameters_button.pack(side=tkinter.LEFT, padx=5)

        self.start_calibration_button = ttk.Button(control_frame, text="Калибровать", width=15,
                                                    command=self.start_calibration_process, state=tkinter.DISABLED)
        self.start_calibration_button.pack(side=tkinter.LEFT, padx=5)

        parameters_frame = ttk.LabelFrame(main_container, text="Параметры:", padding=10)
        parameters_frame.pack(fill=tkinter.X, pady=5)

        left_parameters_frame = ttk.Frame(parameters_frame)
        left_parameters_frame.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True, padx=10)

        right_parameters_frame = ttk.Frame(parameters_frame)
        right_parameters_frame.pack(side=tkinter.RIGHT, fill=tkinter.BOTH, expand=True, padx=10)

        left_parameters_frame.columnconfigure(0, weight=1)
        left_parameters_frame.columnconfigure(1, weight=0)
        right_parameters_frame.columnconfigure(0, weight=1)
        right_parameters_frame.columnconfigure(1, weight=0)

        start_wavelength_label = ttk.Label(left_parameters_frame, text="Начальная длина волны (нм):", anchor="w")
        start_wavelength_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.start_wavelength_entry = ttk.Entry(left_parameters_frame, width=15)
        self.start_wavelength_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.start_wavelength_entry.insert(0, str(self.calibration_manager.configuration.start_wavelength_nanometers))

        end_wavelength_label = ttk.Label(left_parameters_frame, text="Конечная длина волны (нм):", anchor="w")
        end_wavelength_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.end_wavelength_entry = ttk.Entry(left_parameters_frame, width=15)
        self.end_wavelength_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.end_wavelength_entry.insert(0, str(self.calibration_manager.configuration.end_wavelength_nanometers))

        step_label = ttk.Label(left_parameters_frame, text="Шаг сканирования (нм):", anchor="w")
        step_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.step_entry = ttk.Entry(left_parameters_frame, width=15)
        self.step_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.step_entry.insert(0, str(self.calibration_manager.configuration.wavelength_step_nanometers))

        input_slit_label = ttk.Label(right_parameters_frame, text="Входная щель (мкм):", anchor="w")
        input_slit_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.input_slit_entry = ttk.Entry(right_parameters_frame, width=15)
        self.input_slit_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.input_slit_entry.insert(0, str(self.calibration_manager.configuration.input_slit_micrometers))

        output_slit_label = ttk.Label(right_parameters_frame, text="Выходная щель (мкм):", anchor="w")
        output_slit_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.output_slit_entry = ttk.Entry(right_parameters_frame, width=15)
        self.output_slit_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.output_slit_entry.insert(0, str(self.calibration_manager.configuration.output_slit_micrometers))

        average_label = ttk.Label(right_parameters_frame, text="Усреднение кадров:", anchor="w")
        average_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.average_entry = ttk.Entry(right_parameters_frame, width=15)
        self.average_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.average_entry.insert(0, str(self.calibration_manager.configuration.oscilloscope_average_count))

        log_frame = ttk.LabelFrame(main_container, text="Выводы:", padding=5)
        log_frame.pack(fill=tkinter.BOTH, expand=True, pady=(5, 0))

        self.log_text_widget = tkinter.Text(log_frame, height=8, wrap=tkinter.WORD, font=("Consolas", 9))
        self.log_text_widget.config(state=tkinter.DISABLED)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tkinter.VERTICAL, command=self.log_text_widget.yview)
        self.log_text_widget.configure(yscrollcommand=log_scrollbar.set)
        self.log_text_widget.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        log_scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)

        self.update_parameters_state()

        self.application_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.application_window.mainloop()

    def toggle_calibration_mode(self):
        self.is_automatic_mode = not self.is_automatic_mode
        if self.is_automatic_mode:
            self.mode_button.config(text="Ручной")
            self.load_parameters_button.config(state=tkinter.DISABLED)
            self.append_to_log("Переключено в автоматический режим калибровки\n")
        else:
            self.mode_button.config(text="Автомат")
            self.load_parameters_button.config(state=tkinter.NORMAL)
            self.append_to_log("Переключено в ручной режим калибровки\n")

        self.update_parameters_state()

    def update_parameters_state(self):
        if self.is_automatic_mode:
            state = tkinter.DISABLED
        else:
            state = tkinter.NORMAL

        self.start_wavelength_entry.config(state=state)
        self.end_wavelength_entry.config(state=state)
        self.step_entry.config(state=state)
        self.input_slit_entry.config(state=state)
        self.output_slit_entry.config(state=state)
        self.average_entry.config(state=state)

    def load_parameters_from_file(self):
        file_path = filedialog.askopenfilename(
            title="Выберите файл с параметрами",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )
        if file_path:
            try:
                self.calibration_manager.load_parameters_from_file(Path(file_path))
                self.start_wavelength_entry.delete(0, tkinter.END)
                self.start_wavelength_entry.insert(0, str(self.calibration_manager.configuration.start_wavelength_nanometers))
                self.end_wavelength_entry.delete(0, tkinter.END)
                self.end_wavelength_entry.insert(0, str(self.calibration_manager.configuration.end_wavelength_nanometers))
                self.step_entry.delete(0, tkinter.END)
                self.step_entry.insert(0, str(self.calibration_manager.configuration.wavelength_step_nanometers))
                self.input_slit_entry.delete(0, tkinter.END)
                self.input_slit_entry.insert(0, str(self.calibration_manager.configuration.input_slit_micrometers))
                self.output_slit_entry.delete(0, tkinter.END)
                self.output_slit_entry.insert(0, str(self.calibration_manager.configuration.output_slit_micrometers))
                self.average_entry.delete(0, tkinter.END)
                self.average_entry.insert(0, str(self.calibration_manager.configuration.oscilloscope_average_count))
                self.append_to_log(f"Параметры загружены из файла: {file_path}\n")
            except Exception as error:
                self.append_to_log(f"Ошибка загрузки параметров: {error}\n")

    def update_parameters_from_entries(self):
        try:
            self.calibration_manager.configuration.start_wavelength_nanometers = float(self.start_wavelength_entry.get())
            self.calibration_manager.configuration.end_wavelength_nanometers = float(self.end_wavelength_entry.get())
            self.calibration_manager.configuration.wavelength_step_nanometers = float(self.step_entry.get())
            self.calibration_manager.configuration.input_slit_micrometers = float(self.input_slit_entry.get())
            self.calibration_manager.configuration.output_slit_micrometers = float(self.output_slit_entry.get())
            self.calibration_manager.configuration.oscilloscope_average_count = int(self.average_entry.get())
        except ValueError as error:
            raise Exception(f"Ошибка в параметрах: {error}")

    def append_to_log(self, message: str):
        self.log_text_widget.config(state=tkinter.NORMAL)
        self.log_text_widget.insert(tkinter.END, message)
        self.log_text_widget.see(tkinter.END)
        self.log_text_widget.config(state=tkinter.DISABLED)

    def connect_instruments(self):
        def connection_task():
            self.connect_button.config(state=tkinter.DISABLED)
            self.append_to_log("\n" + "="*50 + "\n")
            self.append_to_log("ПОДКЛЮЧЕНИЕ ОБОРУДОВАНИЯ\n")
            self.append_to_log("="*50 + "\n")

            connection_successful = self.calibration_manager.connect_instruments(self.log_text_widget)

            if connection_successful:
                self.calibration_manager.apply_device_settings(self.log_text_widget)
                self.disconnect_button.config(state=tkinter.NORMAL)
                self.start_calibration_button.config(state=tkinter.NORMAL)
                self.append_to_log("\nОборудование готово к калибровке\n")
            else:
                self.append_to_log("\nПроверьте подключение приборов\n")
                self.connect_button.config(state=tkinter.NORMAL)

        threading.Thread(target=connection_task, daemon=True).start()

    def disconnect_instruments(self):
        def disconnection_task():
            self.disconnect_button.config(state=tkinter.DISABLED)
            self.start_calibration_button.config(state=tkinter.DISABLED)
            self.connect_button.config(state=tkinter.DISABLED)

            self.append_to_log("\n" + "="*50 + "\n")
            self.append_to_log("ОТКЛЮЧЕНИЕ ОБОРУДОВАНИЯ\n")
            self.append_to_log("="*50 + "\n")

            self.calibration_manager.disconnect_instruments(self.log_text_widget)

            self.connect_button.config(state=tkinter.NORMAL)
            self.disconnect_button.config(state=tkinter.DISABLED)
            self.start_calibration_button.config(state=tkinter.DISABLED)

        threading.Thread(target=disconnection_task, daemon=True).start()

    def draw_spectrum(self):
        self.graph_canvas.delete("all")

        if not self.measured_spectrum:
            return

        canvas_width = self.graph_canvas.winfo_width()
        canvas_height = self.graph_canvas.winfo_height()

        if canvas_width <= 1:
            canvas_width = 900
        if canvas_height <= 1:
            canvas_height = 250

        margin_left = 60
        margin_right = 40
        margin_top = 20
        margin_bottom = 40

        plot_width = canvas_width - margin_left - margin_right
        plot_height = canvas_height - margin_top - margin_bottom

        all_wavelengths = [point[0] for point in self.measured_spectrum]
        if self.calibrated_spectrum:
            all_wavelengths.extend([point[0] for point in self.calibrated_spectrum])

        if not all_wavelengths:
            return

        min_wavelength = min(all_wavelengths)
        max_wavelength = max(all_wavelengths)

        if min_wavelength == max_wavelength:
            min_wavelength = min_wavelength - 0.5
            max_wavelength = max_wavelength + 0.5

        all_intensities = [point[1] for point in self.measured_spectrum]
        if self.calibrated_spectrum:
            all_intensities.extend([point[1] for point in self.calibrated_spectrum])

        if not all_intensities:
            return

        max_intensity = max(all_intensities)
        min_intensity = min(all_intensities)

        if max_intensity == min_intensity:
            max_intensity = max_intensity + 1.0
            min_intensity = min_intensity - 1.0

        intensity_padding = (max_intensity - min_intensity) * 0.1
        wavelength_padding = (max_wavelength - min_wavelength) * 0.05

        max_intensity_display = max_intensity + intensity_padding
        min_intensity_display = min_intensity - intensity_padding
        max_wavelength_display = max_wavelength + wavelength_padding
        min_wavelength_display = min_wavelength - wavelength_padding

        if min_intensity_display < 0:
            min_intensity_display = 0
        if min_wavelength_display < 0:
            min_wavelength_display = 0

        def wavelength_to_x(wavelength):
            if max_wavelength_display == min_wavelength_display:
                return margin_left + plot_width / 2
            return margin_left + (wavelength - min_wavelength_display) / (max_wavelength_display - min_wavelength_display) * plot_width

        def intensity_to_y(intensity):
            if max_intensity_display == min_intensity_display:
                return margin_top + plot_height / 2
            return margin_top + plot_height - (intensity - min_intensity_display) / (max_intensity_display - min_intensity_display) * plot_height

        for i in range(len(self.measured_spectrum) - 1):
            x1 = wavelength_to_x(self.measured_spectrum[i][0])
            y1 = intensity_to_y(self.measured_spectrum[i][1])
            x2 = wavelength_to_x(self.measured_spectrum[i + 1][0])
            y2 = intensity_to_y(self.measured_spectrum[i + 1][1])
            self.graph_canvas.create_line(x1, y1, x2, y2, fill="blue", width=2)

        if self.calibrated_spectrum:
            for i in range(len(self.calibrated_spectrum) - 1):
                x1 = wavelength_to_x(self.calibrated_spectrum[i][0])
                y1 = intensity_to_y(self.calibrated_spectrum[i][1])
                x2 = wavelength_to_x(self.calibrated_spectrum[i + 1][0])
                y2 = intensity_to_y(self.calibrated_spectrum[i + 1][1])
                self.graph_canvas.create_line(x1, y1, x2, y2, fill="red", width=2)

        for x in range(6):
            wavelength = min_wavelength_display + (max_wavelength_display - min_wavelength_display) * x / 5
            x_position = wavelength_to_x(wavelength)
            if margin_left <= x_position <= margin_left + plot_width:
                self.graph_canvas.create_line(x_position, margin_top, x_position, margin_top + plot_height, fill="gray", width=1)
                self.graph_canvas.create_text(x_position, margin_top + plot_height + 10, text=f"{wavelength:.0f}", anchor="n", font=("Arial", 8))

        for y in range(5):
            intensity = min_intensity_display + (max_intensity_display - min_intensity_display) * y / 4
            y_position = intensity_to_y(intensity)
            if margin_top <= y_position <= margin_top + plot_height:
                self.graph_canvas.create_line(margin_left, y_position, margin_left + plot_width, y_position, fill="gray", width=1)
                intensity_text = f"{intensity:.2e}" if intensity < 1 else f"{intensity:.2f}"
                self.graph_canvas.create_text(margin_left - 5, y_position, text=intensity_text, anchor="e", font=("Arial", 8))

        self.graph_canvas.create_text(margin_left + plot_width // 2, margin_top + plot_height + 25, text="Длина волны (нм)", anchor="n", font=("Arial", 9))
        self.graph_canvas.create_text(margin_left - 35, margin_top + plot_height // 2, text="Интенсивность (В·с)", anchor="center", angle=90, font=("Arial", 9))

        self.graph_canvas.create_text(margin_left + 80, margin_top + 15, text="До калибровки", anchor="nw", fill="blue", font=("Arial", 9))
        if self.calibrated_spectrum:
            self.graph_canvas.create_text(margin_left + 80, margin_top + 30, text="После калибровки", anchor="nw", fill="red", font=("Arial", 9))

    def start_calibration_process(self):
        def calibration_task():
            self.start_calibration_button.config(state=tkinter.DISABLED)
            self.connect_button.config(state=tkinter.DISABLED)
            self.disconnect_button.config(state=tkinter.DISABLED)
            self.mode_button.config(state=tkinter.DISABLED)

            self.append_to_log("\n" + "="*50 + "\n")
            self.append_to_log("КАЛИБРОВКА\n")
            self.append_to_log("="*50 + "\n")

            try:
                if not self.is_automatic_mode:
                    self.update_parameters_from_entries()

                self.calibration_manager.apply_device_settings(self.log_text_widget)

                if self.is_automatic_mode:
                    for reference_data in self.calibration_manager.builtin_reference_data.values():
                        reference_peaks = reference_data["peaks_with_names"]
                        self.append_to_log(f"Используются данные: {reference_data['description']}\n")
                        break
                else:
                    reference_file_path = filedialog.askopenfilename(
                        title="Выберите файл с эталонными данными",
                        filetypes=[("CSV файлы", "*.csv"), ("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
                    )
                    if not reference_file_path:
                        self.append_to_log("Калибровка отменена: не выбран файл с эталонными данными\n")
                        self.start_calibration_button.config(state=tkinter.NORMAL)
                        self.connect_button.config(state=tkinter.NORMAL)
                        self.disconnect_button.config(state=tkinter.NORMAL)
                        self.mode_button.config(state=tkinter.NORMAL)
                        return

                    try:
                        reference_peaks = self.calibration_manager.load_custom_reference_file(Path(reference_file_path))
                        self.append_to_log(f"Загружено {len(reference_peaks)} эталонных пиков\n")
                    except Exception as error:
                        self.append_to_log(f"Ошибка загрузки эталонных данных: {error}\n")
                        self.start_calibration_button.config(state=tkinter.NORMAL)
                        self.connect_button.config(state=tkinter.NORMAL)
                        self.disconnect_button.config(state=tkinter.NORMAL)
                        self.mode_button.config(state=tkinter.NORMAL)
                        return

                self.append_to_log(f"\nСканирование спектра в диапазоне: {self.calibration_manager.configuration.start_wavelength_nanometers} - {self.calibration_manager.configuration.end_wavelength_nanometers} нм\n")
                self.append_to_log(f"Шаг сканирования: {self.calibration_manager.configuration.wavelength_step_nanometers} нм\n\n")

                def update_progress(percent_value):
                    pass

                self.measured_spectrum = self.calibration_manager.scan_spectrum(self.log_text_widget, update_progress)

                detected_peaks = self.calibration_manager.find_spectral_peaks(self.measured_spectrum)
                self.append_to_log(f"\nОбнаружено пиков в спектре: {len(detected_peaks)}\n")

                for peak_index, (wavelength_value, amplitude_value) in enumerate(detected_peaks):
                    self.append_to_log(f"  Пик {peak_index + 1}: {wavelength_value:.2f} нм (интеграл {amplitude_value:.6e} В·с)\n")

                self.calibration_result = self.calibration_manager.compute_calibration_coefficients(detected_peaks, reference_peaks)

                if "error_message" in self.calibration_result:
                    self.append_to_log(f"\nОшибка расчёта калибровки: {self.calibration_result['error_message']}\n")
                else:
                    self.append_to_log(f"\nРЕЗУЛЬТАТЫ КАЛИБРОВКИ:\n")
                    if self.calibration_result['calibration_method'] == 'wavelength_offset':
                        self.append_to_log(f"  Сдвиг длины волны: {self.calibration_result['offset_nanometers']:.3f} нм\n")
                    else:
                        self.append_to_log(f"  Сдвиг (intercept): {self.calibration_result['intercept_nanometers']:.3f} нм\n")
                        self.append_to_log(f"  Масштаб (slope): {self.calibration_result['slope_factor']:.6f}\n")

                    self.append_to_log(f"\nСтатистическая погрешность:\n")
                    self.append_to_log(f"  Средняя ошибка: {self.calibration_result['statistics']['mean_error_nanometers']:.3f} нм\n")
                    self.append_to_log(f"  Максимальная ошибка: {self.calibration_result['statistics']['maximum_absolute_error']:.3f} нм\n")

                    self.append_to_log(f"\nСопоставление измеренных и эталонных пиков:\n")
                    for matched_point in self.calibration_result['matched_points']:
                        self.append_to_log(f"  {matched_point['peak_name']}: эталон {matched_point['reference_wavelength']:.1f} нм -> измерено {matched_point['measured_wavelength']:.2f} нм (ошибка {matched_point['measurement_error']:.3f} нм)\n")

                    self.calibrated_spectrum = self.calibration_manager.apply_calibration_to_spectrum(self.measured_spectrum, self.calibration_result)

                    self.draw_spectrum()

                    saved_file_path = self.calibration_manager.save_calibration_data(self.calibration_result)
                    self.append_to_log(f"\nРезультаты сохранены в файл: {saved_file_path}\n")
                    self.append_to_log(f"Файл конфигурации: {self.calibration_manager.base_path / 'calibration_config.json'}\n")
                    self.append_to_log("\nКалибровка завершена. Теперь её можно применить в основном приложении.\n")

            except Exception as error:
                self.append_to_log(f"\nОшибка: {error}\n")

            self.start_calibration_button.config(state=tkinter.NORMAL)
            self.connect_button.config(state=tkinter.NORMAL)
            self.disconnect_button.config(state=tkinter.NORMAL)
            self.mode_button.config(state=tkinter.NORMAL)

        threading.Thread(target=calibration_task, daemon=True).start()

    def on_closing(self):
        if self.calibration_manager.chromator_device:
            self.calibration_manager.chromator_device.disconnect()
        if self.calibration_manager.oscilloscope_device:
            self.calibration_manager.oscilloscope_device.disconnect()
        self.application_window.destroy()


if __name__ == "__main__":
    calibration_application = CalibrationApplication()
    calibration_application.initialize_user_interface()
