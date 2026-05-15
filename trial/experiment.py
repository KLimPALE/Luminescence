import sys
import os
import time
import threading
import json
import numpy
import tkinter
from tkinter import ttk, filedialog, simpledialog
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
from mathematics import integrate_signal, approximate_signal, energy_calibration


class MeasurementConfiguration:
    def __init__(self):
        self.start_wavelength_nanometers = 1300.0
        self.end_wavelength_nanometers = 1400.0
        self.wavelength_step_nanometers = 0.5
        
        self.input_slit_micrometers = 100.0
        self.output_slit_micrometers = 100.0
        self.oscilloscope_average_count = 65536
        
        self.oscilloscope_signal_channel = 2
        self.oscilloscope_trigger_channel = 1
        self.oscilloscope_volts_per_division = 0.5
        self.oscilloscope_seconds_per_division = 1e-6
        
        self.power_meter_average_count = 10
        
        self.baseline_start_time_seconds = -10e-6
        self.baseline_end_time_seconds = -2e-6
        self.signal_integration_start_time_seconds = -2e-6
        self.signal_integration_end_time_seconds = 20e-6


class CalibrationData:
    def __init__(self):
        self.is_enabled = False
        self.calibration_method = "wavelength_offset"
        self.slope_factor = 1.0
        self.intercept_nanometers = 0.0
        self.offset_nanometers = 0.0
        self.calibration_date = ""
    
    def load_from_file(self, config_path: Path):
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                chromator_data = data.get("chromator", {})
                self.is_enabled = chromator_data.get("is_calibration_enabled", False)
                self.calibration_method = chromator_data.get("calibration_method", "wavelength_offset")
                self.slope_factor = chromator_data.get("slope_factor", 1.0)
                self.intercept_nanometers = chromator_data.get("intercept_nanometers", 0.0)
                self.offset_nanometers = chromator_data.get("offset_nanometers", 0.0)
                self.calibration_date = chromator_data.get("calibration_date", "")
    
    def apply_to_wavelength(self, raw_wavelength: float) -> float:
        if not self.is_enabled:
            return raw_wavelength
        
        if self.calibration_method == "wavelength_offset":
            return raw_wavelength - self.offset_nanometers
        else:
            return (raw_wavelength - self.intercept_nanometers) / self.slope_factor


class SpectrumMeasurement:
    def __init__(self):
        self.configuration = MeasurementConfiguration()
        self.calibration = CalibrationData()
        
        self.chromator_device = None
        self.oscilloscope_device = None
        
        self.is_chromator_connected = False
        self.is_oscilloscope_connected = False
        
        self.measured_spectrum = []
        self.calibrated_spectrum = []
        
        self.test_signal_time = []
        self.test_signal_voltage = []
        self.processed_signal = []
        
        self.energy_calibration_result = None
        self.energy_measurements = []
        
        self.base_path = Path(__file__).parent.parent
        self.load_calibration()
        
        self.application_window = None
        self.operation_lock = threading.Lock()
    
    def load_calibration(self):
        config_path = self.base_path / "calibration_config.json"
        self.calibration.load_from_file(config_path)
    
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
                self.chromator_device.set_acquisition_type("AVER")
                self.chromator_device.set_average_count(self.configuration.oscilloscope_average_count)
                log_widget.insert(tkinter.END, f"Усреднение осциллографа: {self.configuration.oscilloscope_average_count}\n")
            except Exception as error:
                log_widget.insert(tkinter.END, f"Ошибка настройки монохроматора: {error}\n")
        
        if self.oscilloscope_device:
            try:
                self.oscilloscope_device.set_channel_scale(self.configuration.oscilloscope_signal_channel, 
                                                           self.configuration.oscilloscope_volts_per_division)
                self.oscilloscope_device.set_timebase_scale(self.configuration.oscilloscope_seconds_per_division)
                self.oscilloscope_device.set_trigger_source(f"CHAN{self.configuration.oscilloscope_trigger_channel}")
                self.oscilloscope_device.set_trigger_level(0.5)
                log_widget.insert(tkinter.END, f"Осциллограф настроен (триггер на канал {self.configuration.oscilloscope_trigger_channel})\n")
            except Exception as error:
                log_widget.insert(tkinter.END, f"Ошибка настройки осциллографа: {error}\n")
    
    def capture_signal_with_integration(self) -> float:
        if not self.oscilloscope_device:
            return 0.0
        
        time_values, voltage_values = self.oscilloscope_device.capture_waveform(
            self.configuration.oscilloscope_signal_channel, 2000
        )
        
        if not voltage_values:
            return 0.0
        
        corrected_signal = []
        for point_index in range(len(voltage_values)):
            corrected_signal.append(voltage_values[point_index])
        
        baseline_time = []
        baseline_signal = []
        for point_index in range(len(time_values)):
            if self.configuration.baseline_start_time_seconds <= time_values[point_index] <= self.configuration.baseline_end_time_seconds:
                baseline_time.append(time_values[point_index])
                baseline_signal.append(voltage_values[point_index])
        
        if baseline_signal:
            baseline_level = numpy.mean(baseline_signal)
            for point_index in range(len(voltage_values)):
                corrected_signal[point_index] = voltage_values[point_index] - baseline_level
        
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
        
        integrated_value = integrate_signal(integration_time, integration_signal)
        
        return integrated_value
    
    def measure_signal_amplitude(self) -> float:
        if not self.oscilloscope_device:
            return 0.0
        
        time_values, voltage_values = self.oscilloscope_device.capture_waveform(
            self.configuration.oscilloscope_signal_channel, 2000
        )
        
        if not voltage_values:
            return 0.0
        
        approximated_signal, fit_parameters = approximate_signal(time_values, voltage_values, use_background=True)
        
        if fit_parameters.get("fit_successful", False):
            peak_amplitude = fit_parameters.get("signal_amplitude_volts", 0.0)
        else:
            peak_amplitude = max(approximated_signal) if approximated_signal else 0.0
        
        return peak_amplitude
    
    def measure_integrated_signal(self) -> float:
        return self.capture_signal_with_integration()
    
    def acquire_test_signal(self, log_widget: tkinter.Text):
        if not self.oscilloscope_device:
            log_widget.insert(tkinter.END, "Осциллограф не подключен\n")
            return False
        
        log_widget.insert(tkinter.END, "Захват тестового сигнала...\n")
        
        self.test_signal_time, self.test_signal_voltage = self.oscilloscope_device.capture_waveform(
            self.configuration.oscilloscope_signal_channel, 2000
        )
        
        if not self.test_signal_voltage:
            log_widget.insert(tkinter.END, "Ошибка захвата сигнала\n")
            return False
        
        baseline_time = []
        baseline_signal = []
        for point_index in range(len(self.test_signal_time)):
            if self.configuration.baseline_start_time_seconds <= self.test_signal_time[point_index] <= self.configuration.baseline_end_time_seconds:
                baseline_time.append(self.test_signal_time[point_index])
                baseline_signal.append(self.test_signal_voltage[point_index])
        
        if baseline_signal:
            baseline_level = numpy.mean(baseline_signal)
            self.processed_signal = []
            for voltage in self.test_signal_voltage:
                self.processed_signal.append(voltage - baseline_level)
        else:
            self.processed_signal = self.test_signal_voltage.copy()
        
        log_widget.insert(tkinter.END, f"Сигнал захвачен. Точек: {len(self.test_signal_time)}\n")
        
        return True
    
    def scan_spectrum(self, log_widget: tkinter.Text, progress_callback) -> List[Tuple[float, float]]:
        measurement_results = []
        wavelength_list = numpy.arange(
            self.configuration.start_wavelength_nanometers,
            self.configuration.end_wavelength_nanometers + self.configuration.wavelength_step_nanometers,
            self.configuration.wavelength_step_nanometers
        )
        
        total_points = len(wavelength_list)
        
        for point_index, wavelength in enumerate(wavelength_list):
            self.chromator_device.set_wavelength(wavelength)
            time.sleep(0.3)
            
            signal_value = self.measure_integrated_signal()
            measurement_results.append((wavelength, signal_value))
            
            completion_percent = int((point_index + 1) / total_points * 100)
            progress_callback(completion_percent)
            
            if point_index % 10 == 0:
                log_widget.insert(tkinter.END, f"   {wavelength:.1f} нм -> {signal_value:.6e} В·с\n")
                log_widget.see(tkinter.END)
        
        return measurement_results
    
    def apply_calibration_to_spectrum(self):
        self.calibrated_spectrum = []
        for wavelength, intensity in self.measured_spectrum:
            calibrated_wavelength = self.calibration.apply_to_wavelength(wavelength)
            self.calibrated_spectrum.append((calibrated_wavelength, intensity))
    
    def save_spectrum_to_csv(self, file_path: Path):
        with open(file_path, 'w', encoding='utf-8') as file_handle:
            file_handle.write("wavelength_nanometers,integrated_signal_vs\n")
            for wavelength, intensity in self.calibrated_spectrum:
                file_handle.write(f"{wavelength:.3f},{intensity:.6e}\n")
    
    def measure_energy_series(self, points_count: int = 10, log_widget: tkinter.Text = None) -> List[float]:
        energy_values = []
        
        for point_index in range(points_count):
            energy_value = self.measure_integrated_signal()
            energy_values.append(energy_value)
            
            if log_widget:
                log_widget.insert(tkinter.END, f"  Измерение {point_index + 1}/{points_count}: {energy_value:.6e} В·с\n")
                log_widget.see(tkinter.END)
            
            time.sleep(0.1)
        
        return energy_values
    
    def calibrate_energy_detector(self, energy_values: List[float], reference_energies: List[float], 
                                   log_widget: tkinter.Text = None) -> dict:
        if len(energy_values) != len(reference_energies):
            if log_widget:
                log_widget.insert(tkinter.END, "Ошибка: массивы сигналов и эталонных энергий разной длины\n")
            return {"calibration_success": False}
        
        calibration_result = energy_calibration(reference_energies, energy_values, force_zero=True)
        
        if log_widget:
            if calibration_result.get("calibration_success", False):
                log_widget.insert(tkinter.END, f"Калибровка энергометра выполнена:\n")
                log_widget.insert(tkinter.END, f"  Чувствительность: {calibration_result['detector_sensitivity']:.6e} В·с/Дж\n")
                log_widget.insert(tkinter.END, f"  Качество аппроксимации: {calibration_result['fit_quality']:.4f}\n")
            else:
                log_widget.insert(tkinter.END, f"Ошибка калибровки: {calibration_result.get('error_description', 'Unknown')}\n")
        
        return calibration_result


class MeasurementApplication:
    def __init__(self):
        self.measurement = SpectrumMeasurement()
        self.application_window = None
        self.integration_lines = []
        self.current_tab = None
    
    def initialize_user_interface(self):
        self.application_window = tkinter.Tk()
        self.application_window.title("Измерение спектров")
        self.application_window.geometry("1200x800")
        self.application_window.resizable(True, True)
        
        icon_file_path = self.measurement.base_path / "icon.png"
        if icon_file_path.exists():
            try:
                application_icon = tkinter.PhotoImage(file=str(icon_file_path))
                self.application_window.iconphoto(True, application_icon)
            except Exception:
                pass
        
        main_container = ttk.Frame(self.application_window, padding=10)
        main_container.pack(fill=tkinter.BOTH, expand=True)
        
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill=tkinter.BOTH, expand=True)
        
        calibration_frame = self.create_calibration_tab(notebook)
        notebook.add(calibration_frame, text="Калибровка")
        
        signal_frame = self.create_signal_tab(notebook)
        notebook.add(signal_frame, text="Сигнал")
        
        spectrum_frame = self.create_spectrum_tab(notebook)
        notebook.add(spectrum_frame, text="Спектр")
        
        energy_frame = self.create_energy_tab(notebook)
        notebook.add(energy_frame, text="Энергия")
        
        self.application_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.application_window.mainloop()
    
    def create_calibration_tab(self, parent):
        tab = ttk.Frame(parent)
        
        settings_frame = ttk.LabelFrame(tab, text="Параметры измерения:", padding=10)
        settings_frame.pack(fill=tkinter.X, pady=5)
        
        left_frame = ttk.Frame(settings_frame)
        left_frame.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True, padx=10)
        
        right_frame = ttk.Frame(settings_frame)
        right_frame.pack(side=tkinter.RIGHT, fill=tkinter.BOTH, expand=True, padx=10)
        
        left_frame.columnconfigure(0, weight=1)
        left_frame.columnconfigure(1, weight=0)
        right_frame.columnconfigure(0, weight=1)
        right_frame.columnconfigure(1, weight=0)
        
        ttk.Label(left_frame, text="Начальная длина волны (нм):", anchor="w").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.start_wavelength_entry = ttk.Entry(left_frame, width=15)
        self.start_wavelength_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.start_wavelength_entry.insert(0, str(self.measurement.configuration.start_wavelength_nanometers))
        
        ttk.Label(left_frame, text="Конечная длина волны (нм):", anchor="w").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.end_wavelength_entry = ttk.Entry(left_frame, width=15)
        self.end_wavelength_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.end_wavelength_entry.insert(0, str(self.measurement.configuration.end_wavelength_nanometers))
        
        ttk.Label(left_frame, text="Шаг сканирования (нм):", anchor="w").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.step_entry = ttk.Entry(left_frame, width=15)
        self.step_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.step_entry.insert(0, str(self.measurement.configuration.wavelength_step_nanometers))
        
        ttk.Label(left_frame, text="Входная щель (мкм):", anchor="w").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.input_slit_entry = ttk.Entry(left_frame, width=15)
        self.input_slit_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.input_slit_entry.insert(0, str(self.measurement.configuration.input_slit_micrometers))
        
        ttk.Label(left_frame, text="Выходная щель (мкм):", anchor="w").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.output_slit_entry = ttk.Entry(left_frame, width=15)
        self.output_slit_entry.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        self.output_slit_entry.insert(0, str(self.measurement.configuration.output_slit_micrometers))
        
        ttk.Label(right_frame, text="Канал осциллографа:", anchor="w").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.channel_entry = ttk.Entry(right_frame, width=15)
        self.channel_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.channel_entry.insert(0, str(self.measurement.configuration.oscilloscope_signal_channel))
        
        ttk.Label(right_frame, text="Усреднение осциллографа:", anchor="w").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.average_entry = ttk.Entry(right_frame, width=15)
        self.average_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.average_entry.insert(0, str(self.measurement.configuration.oscilloscope_average_count))
        
        ttk.Label(right_frame, text="Усреднение энергометра:", anchor="w").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.power_average_entry = ttk.Entry(right_frame, width=15)
        self.power_average_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.power_average_entry.insert(0, str(self.measurement.configuration.power_meter_average_count))
        
        calibration_frame = ttk.LabelFrame(tab, text="Калибровка монохроматора:", padding=10)
        calibration_frame.pack(fill=tkinter.X, pady=5)
        
        cal_status_frame = ttk.Frame(calibration_frame)
        cal_status_frame.pack(fill=tkinter.X, pady=5)
        
        ttk.Label(cal_status_frame, text="Статус калибровки:", anchor="w").pack(side=tkinter.LEFT, padx=5)
        self.calibration_status_label = ttk.Label(cal_status_frame, text="Применена" if self.measurement.calibration.is_enabled else "Не применена", 
                                                   foreground="green" if self.measurement.calibration.is_enabled else "red")
        self.calibration_status_label.pack(side=tkinter.LEFT, padx=5)
        
        ttk.Button(calibration_frame, text="Загрузить калибровку из файла", command=self.load_calibration_file).pack(pady=5)
        
        devices_frame = ttk.LabelFrame(tab, text="Управление оборудованием:", padding=10)
        devices_frame.pack(fill=tkinter.X, pady=5)
        
        button_frame = ttk.Frame(devices_frame)
        button_frame.pack(fill=tkinter.X, pady=5)
        
        self.connect_button = ttk.Button(button_frame, text="Подключить", command=self.connect_devices)
        self.connect_button.pack(side=tkinter.LEFT, padx=5)
        
        self.disconnect_button = ttk.Button(button_frame, text="Отключить", command=self.disconnect_devices, state=tkinter.DISABLED)
        self.disconnect_button.pack(side=tkinter.LEFT, padx=5)
        
        self.apply_settings_button = ttk.Button(button_frame, text="Применить настройки", command=self.apply_device_settings, state=tkinter.DISABLED)
        self.apply_settings_button.pack(side=tkinter.LEFT, padx=5)
        
        log_frame = ttk.LabelFrame(tab, text="Выводы:", padding=5)
        log_frame.pack(fill=tkinter.BOTH, expand=True, pady=5)
        
        self.log_text = tkinter.Text(log_frame, height=10, wrap=tkinter.WORD, font=("Consolas", 9))
        self.log_text.config(state=tkinter.DISABLED)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tkinter.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        self.log_text.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        log_scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        
        return tab
    
    def create_signal_tab(self, parent):
        tab = ttk.Frame(parent)
        
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill=tkinter.X, pady=5)
        
        self.capture_button = ttk.Button(control_frame, text="Захватить сигнал", command=self.capture_test_signal, state=tkinter.DISABLED)
        self.capture_button.pack(side=tkinter.LEFT, padx=5)
        
        integration_frame = ttk.LabelFrame(tab, text="Границы интегрирования (микросекунды):", padding=10)
        integration_frame.pack(fill=tkinter.X, pady=5)
        
        baseline_frame = ttk.Frame(integration_frame)
        baseline_frame.pack(fill=tkinter.X, pady=5)
        
        ttk.Label(baseline_frame, text="Вычитание фона:").pack(side=tkinter.LEFT, padx=5)
        ttk.Label(baseline_frame, text="от").pack(side=tkinter.LEFT, padx=5)
        self.baseline_start_entry = ttk.Entry(baseline_frame, width=10)
        self.baseline_start_entry.pack(side=tkinter.LEFT, padx=5)
        self.baseline_start_entry.insert(0, str(self.measurement.configuration.baseline_start_time_seconds * 1e6))
        ttk.Label(baseline_frame, text="до").pack(side=tkinter.LEFT, padx=5)
        self.baseline_end_entry = ttk.Entry(baseline_frame, width=10)
        self.baseline_end_entry.pack(side=tkinter.LEFT, padx=5)
        self.baseline_end_entry.insert(0, str(self.measurement.configuration.baseline_end_time_seconds * 1e6))
        
        signal_frame_integ = ttk.Frame(integration_frame)
        signal_frame_integ.pack(fill=tkinter.X, pady=5)
        
        ttk.Label(signal_frame_integ, text="Интегрирование сигнала:").pack(side=tkinter.LEFT, padx=5)
        ttk.Label(signal_frame_integ, text="от").pack(side=tkinter.LEFT, padx=5)
        self.integration_start_entry = ttk.Entry(signal_frame_integ, width=10)
        self.integration_start_entry.pack(side=tkinter.LEFT, padx=5)
        self.integration_start_entry.insert(0, str(self.measurement.configuration.signal_integration_start_time_seconds * 1e6))
        ttk.Label(signal_frame_integ, text="до").pack(side=tkinter.LEFT, padx=5)
        self.integration_end_entry = ttk.Entry(signal_frame_integ, width=10)
        self.integration_end_entry.pack(side=tkinter.LEFT, padx=5)
        self.integration_end_entry.insert(0, str(self.measurement.configuration.signal_integration_end_time_seconds * 1e6))
        
        ttk.Button(integration_frame, text="Обновить границы", command=self.update_integration_bounds).pack(pady=5)
        
        graph_frame = ttk.LabelFrame(tab, text="Форма сигнала:", padding=5)
        graph_frame.pack(fill=tkinter.BOTH, expand=True, pady=5)
        
        self.signal_canvas = tkinter.Canvas(graph_frame, bg="white", height=300)
        self.signal_canvas.pack(fill=tkinter.BOTH, expand=True)
        
        return tab
    
    def create_spectrum_tab(self, parent):
        tab = ttk.Frame(parent)
        
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill=tkinter.X, pady=5)
        
        self.scan_button = ttk.Button(control_frame, text="Начать сканирование", command=self.start_spectrum_scan, state=tkinter.DISABLED)
        self.scan_button.pack(side=tkinter.LEFT, padx=5)
        
        self.save_spectrum_button = ttk.Button(control_frame, text="Сохранить спектр", command=self.save_spectrum_to_file, state=tkinter.DISABLED)
        self.save_spectrum_button.pack(side=tkinter.LEFT, padx=5)
        
        progress_frame = ttk.LabelFrame(tab, text="Прогресс:", padding=5)
        progress_frame.pack(fill=tkinter.X, pady=5)
        
        self.scan_progress = ttk.Progressbar(progress_frame, mode="determinate")
        self.scan_progress.pack(fill=tkinter.X)
        
        graph_frame = ttk.LabelFrame(tab, text="Спектр:", padding=5)
        graph_frame.pack(fill=tkinter.BOTH, expand=True, pady=5)
        
        self.spectrum_canvas = tkinter.Canvas(graph_frame, bg="white", height=400)
        self.spectrum_canvas.pack(fill=tkinter.BOTH, expand=True)
        
        spectrum_log_frame = ttk.LabelFrame(tab, text="Выводы сканирования:", padding=5)
        spectrum_log_frame.pack(fill=tkinter.BOTH, expand=True, pady=5)
        
        self.spectrum_log = tkinter.Text(spectrum_log_frame, height=8, wrap=tkinter.WORD, font=("Consolas", 9))
        self.spectrum_log.config(state=tkinter.DISABLED)
        spec_log_scrollbar = ttk.Scrollbar(spectrum_log_frame, orient=tkinter.VERTICAL, command=self.spectrum_log.yview)
        self.spectrum_log.configure(yscrollcommand=spec_log_scrollbar.set)
        self.spectrum_log.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        spec_log_scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        
        return tab
    
    def create_energy_tab(self, parent):
        tab = ttk.Frame(parent)
        
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill=tkinter.X, pady=5)
        
        points_frame = ttk.Frame(control_frame)
        points_frame.pack(side=tkinter.LEFT, padx=5)
        
        ttk.Label(points_frame, text="Количество точек:").pack(side=tkinter.LEFT, padx=5)
        self.energy_points_entry = ttk.Entry(points_frame, width=10)
        self.energy_points_entry.pack(side=tkinter.LEFT, padx=5)
        self.energy_points_entry.insert(0, "10")
        
        self.measure_energy_button = ttk.Button(control_frame, text="Измерить энергию", command=self.measure_energy_series, state=tkinter.DISABLED)
        self.measure_energy_button.pack(side=tkinter.LEFT, padx=5)
        
        self.calibrate_energy_button = ttk.Button(control_frame, text="Калибровать энергометр", command=self.calibrate_energy_detector, state=tkinter.DISABLED)
        self.calibrate_energy_button.pack(side=tkinter.LEFT, padx=5)
        
        graph_frame = ttk.LabelFrame(tab, text="Зависимость сигнала от энергии:", padding=5)
        graph_frame.pack(fill=tkinter.BOTH, expand=True, pady=5)
        
        self.energy_canvas = tkinter.Canvas(graph_frame, bg="white", height=300)
        self.energy_canvas.pack(fill=tkinter.BOTH, expand=True)
        
        energy_log_frame = ttk.LabelFrame(tab, text="Выводы:", padding=5)
        energy_log_frame.pack(fill=tkinter.BOTH, expand=True, pady=5)
        
        self.energy_log = tkinter.Text(energy_log_frame, height=8, wrap=tkinter.WORD, font=("Consolas", 9))
        self.energy_log.config(state=tkinter.DISABLED)
        energy_scrollbar = ttk.Scrollbar(energy_log_frame, orient=tkinter.VERTICAL, command=self.energy_log.yview)
        self.energy_log.configure(yscrollcommand=energy_scrollbar.set)
        self.energy_log.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        energy_scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        
        return tab
    
    def append_log(self, message: str, log_widget: tkinter.Text = None):
        if log_widget is None:
            log_widget = self.log_text
        
        log_widget.config(state=tkinter.NORMAL)
        log_widget.insert(tkinter.END, message)
        log_widget.see(tkinter.END)
        log_widget.config(state=tkinter.DISABLED)
    
    def load_calibration_file(self):
        file_path = filedialog.askopenfilename(
            title="Выберите файл калибровки",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.measurement.calibration.load_from_file(Path(file_path))
            status_text = "Применена" if self.measurement.calibration.is_enabled else "Не применена"
            status_color = "green" if self.measurement.calibration.is_enabled else "red"
            self.calibration_status_label.config(text=status_text, foreground=status_color)
            self.append_log(f"Калибровка загружена из {file_path}\n")
    
    def connect_devices(self):
        def connection_task():
            self.connect_button.config(state=tkinter.DISABLED)
            self.append_log("\n" + "="*50 + "\n")
            self.append_log("ПОДКЛЮЧЕНИЕ ОБОРУДОВАНИЯ\n")
            self.append_log("="*50 + "\n")
            
            connection_successful = self.measurement.connect_instruments(self.log_text)
            
            if connection_successful:
                self.disconnect_button.config(state=tkinter.NORMAL)
                self.apply_settings_button.config(state=tkinter.NORMAL)
                self.capture_button.config(state=tkinter.NORMAL)
                self.scan_button.config(state=tkinter.NORMAL)
                self.measure_energy_button.config(state=tkinter.NORMAL)
                self.calibrate_energy_button.config(state=tkinter.NORMAL)
                self.append_log("\nОборудование готово к работе\n")
            else:
                self.append_log("\nПроверьте подключение приборов\n")
                self.connect_button.config(state=tkinter.NORMAL)
        
        threading.Thread(target=connection_task, daemon=True).start()
    
    def disconnect_devices(self):
        def disconnection_task():
            self.disconnect_button.config(state=tkinter.DISABLED)
            self.apply_settings_button.config(state=tkinter.DISABLED)
            self.capture_button.config(state=tkinter.DISABLED)
            self.scan_button.config(state=tkinter.DISABLED)
            self.measure_energy_button.config(state=tkinter.DISABLED)
            self.calibrate_energy_button.config(state=tkinter.DISABLED)
            self.connect_button.config(state=tkinter.DISABLED)
            
            self.append_log("\n" + "="*50 + "\n")
            self.append_log("ОТКЛЮЧЕНИЕ ОБОРУДОВАНИЯ\n")
            self.append_log("="*50 + "\n")
            
            self.measurement.disconnect_instruments(self.log_text)
            
            self.connect_button.config(state=tkinter.NORMAL)
        
        threading.Thread(target=disconnection_task, daemon=True).start()
    
    def apply_device_settings(self):
        try:
            self.measurement.configuration.start_wavelength_nanometers = float(self.start_wavelength_entry.get())
            self.measurement.configuration.end_wavelength_nanometers = float(self.end_wavelength_entry.get())
            self.measurement.configuration.wavelength_step_nanometers = float(self.step_entry.get())
            self.measurement.configuration.input_slit_micrometers = float(self.input_slit_entry.get())
            self.measurement.configuration.output_slit_micrometers = float(self.output_slit_entry.get())
            self.measurement.configuration.oscilloscope_signal_channel = int(self.channel_entry.get())
            self.measurement.configuration.oscilloscope_average_count = int(self.average_entry.get())
            self.measurement.configuration.power_meter_average_count = int(self.power_average_entry.get())
            
            self.append_log("Настройки применены\n")
            self.measurement.apply_device_settings(self.log_text)
        except ValueError as error:
            self.append_log(f"Ошибка в параметрах: {error}\n")
    
    def update_integration_bounds(self):
        try:
            baseline_start = float(self.baseline_start_entry.get()) * 1e-6
            baseline_end = float(self.baseline_end_entry.get()) * 1e-6
            integration_start = float(self.integration_start_entry.get()) * 1e-6
            integration_end = float(self.integration_end_entry.get()) * 1e-6
            
            self.measurement.configuration.baseline_start_time_seconds = baseline_start
            self.measurement.configuration.baseline_end_time_seconds = baseline_end
            self.measurement.configuration.signal_integration_start_time_seconds = integration_start
            self.measurement.configuration.signal_integration_end_time_seconds = integration_end
            
            self.draw_signal_with_bounds()
            self.append_log("Границы интегрирования обновлены\n")
        except ValueError as error:
            self.append_log(f"Ошибка в границах: {error}\n")
    
    def capture_test_signal(self):
        def capture_task():
            self.capture_button.config(state=tkinter.DISABLED)
            success = self.measurement.acquire_test_signal(self.log_text)
            if success:
                self.draw_signal_with_bounds()
            self.capture_button.config(state=tkinter.NORMAL)
        
        threading.Thread(target=capture_task, daemon=True).start()
    
    def draw_signal_with_bounds(self):
        self.signal_canvas.delete("all")
        
        if not self.measurement.test_signal_time:
            return
        
        canvas_width = self.signal_canvas.winfo_width()
        canvas_height = self.signal_canvas.winfo_height()
        
        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 300
        
        margin_left = 60
        margin_right = 40
        margin_top = 20
        margin_bottom = 40
        
        plot_width = canvas_width - margin_left - margin_right
        plot_height = canvas_height - margin_top - margin_bottom
        
        time_array = numpy.array(self.measurement.test_signal_time)
        signal_array = numpy.array(self.measurement.processed_signal)
        
        if len(time_array) == 0:
            return
        
        min_time = numpy.min(time_array)
        max_time = numpy.max(time_array)
        
        if len(signal_array) > 0:
            max_signal = numpy.max(signal_array)
            min_signal = numpy.min(signal_array)
        else:
            max_signal = 1.0
            min_signal = -1.0
        
        if max_signal == min_signal:
            max_signal = min_signal + 1.0
        
        if max_time == min_time:
            max_time = min_time + 1.0
        
        signal_padding = (max_signal - min_signal) * 0.1
        if signal_padding == 0:
            signal_padding = 0.1
        
        max_signal_display = max_signal + signal_padding
        min_signal_display = min_signal - signal_padding
        
        time_padding = (max_time - min_time) * 0.05
        min_time_display = min_time - time_padding
        max_time_display = max_time + time_padding
        
        if min_time_display == max_time_display:
            max_time_display = min_time_display + 1.0
        
        def time_to_x(time_value):
            return margin_left + (time_value - min_time_display) / (max_time_display - min_time_display) * plot_width
        
        def signal_to_y(signal_value):
            return margin_top + plot_height - (signal_value - min_signal_display) / (max_signal_display - min_signal_display) * plot_height
        
        for i in range(len(time_array) - 1):
            x1 = time_to_x(time_array[i])
            y1 = signal_to_y(signal_array[i])
            x2 = time_to_x(time_array[i + 1])
            y2 = signal_to_y(signal_array[i + 1])
            self.signal_canvas.create_line(x1, y1, x2, y2, fill="blue", width=2)
        
        baseline_start_x = time_to_x(self.measurement.configuration.baseline_start_time_seconds)
        baseline_end_x = time_to_x(self.measurement.configuration.baseline_end_time_seconds)
        integration_start_x = time_to_x(self.measurement.configuration.signal_integration_start_time_seconds)
        integration_end_x = time_to_x(self.measurement.configuration.signal_integration_end_time_seconds)
        
        if baseline_start_x < margin_left:
            baseline_start_x = margin_left
        if baseline_end_x > margin_left + plot_width:
            baseline_end_x = margin_left + plot_width
        if integration_start_x < margin_left:
            integration_start_x = margin_left
        if integration_end_x > margin_left + plot_width:
            integration_end_x = margin_left + plot_width
        
        self.signal_canvas.create_rectangle(baseline_start_x, margin_top, baseline_end_x, margin_top + plot_height, 
                                             fill="lightgreen", outline="", stipple="gray50")
        self.signal_canvas.create_rectangle(integration_start_x, margin_top, integration_end_x, margin_top + plot_height, 
                                             fill="lightblue", outline="", stipple="gray50")
        
        for x in range(0, 6):
            time_value = min_time_display + (max_time_display - min_time_display) * x / 5
            x_pos = time_to_x(time_value)
            if margin_left <= x_pos <= margin_left + plot_width:
                self.signal_canvas.create_line(x_pos, margin_top, x_pos, margin_top + plot_height, fill="gray", width=1)
                self.signal_canvas.create_text(x_pos, margin_top + plot_height + 10, text=f"{time_value*1e6:.1f}", anchor="n", font=("Arial", 8))
        
        for y in range(0, 5):
            signal_value = min_signal_display + (max_signal_display - min_signal_display) * y / 4
            y_pos = signal_to_y(signal_value)
            if margin_top <= y_pos <= margin_top + plot_height:
                self.signal_canvas.create_line(margin_left, y_pos, margin_left + plot_width, y_pos, fill="gray", width=1)
                self.signal_canvas.create_text(margin_left - 5, y_pos, text=f"{signal_value:.3f}", anchor="e", font=("Arial", 8))
        
        self.signal_canvas.create_text(margin_left + plot_width // 2, margin_top + plot_height + 25, text="Время (мкс)", anchor="n", font=("Arial", 9))
        self.signal_canvas.create_text(margin_left - 35, margin_top + plot_height // 2, text="Напряжение (В)", anchor="center", angle=90, font=("Arial", 9))
        
        self.signal_canvas.create_text(margin_left + 80, margin_top + 15, text="Фон", anchor="nw", fill="darkgreen", font=("Arial", 9))
        self.signal_canvas.create_text(margin_left + 80, margin_top + 30, text="Интегрирование", anchor="nw", fill="darkblue", font=("Arial", 9))
    
    def start_spectrum_scan(self):
        def scan_task():
            self.scan_button.config(state=tkinter.DISABLED)
            self.save_spectrum_button.config(state=tkinter.DISABLED)
            self.spectrum_log.config(state=tkinter.NORMAL)
            self.spectrum_log.delete(1.0, tkinter.END)
            self.spectrum_log.config(state=tkinter.DISABLED)
            
            self.append_log("\n" + "="*50 + "\n", self.spectrum_log)
            self.append_log("СКАНИРОВАНИЕ СПЕКТРА\n", self.spectrum_log)
            self.append_log("="*50 + "\n", self.spectrum_log)
            
            def update_progress(percent_value):
                self.scan_progress["value"] = percent_value
                self.application_window.update()
            
            self.measurement.measured_spectrum = self.measurement.scan_spectrum(self.spectrum_log, update_progress)
            self.measurement.apply_calibration_to_spectrum()
            
            self.append_log(f"\nСканирование завершено. Измерено {len(self.measurement.measured_spectrum)} точек\n", self.spectrum_log)
            
            self.draw_spectrum()
            
            self.save_spectrum_button.config(state=tkinter.NORMAL)
            self.scan_button.config(state=tkinter.NORMAL)
        
        threading.Thread(target=scan_task, daemon=True).start()
    
    def draw_spectrum(self):
        self.spectrum_canvas.delete("all")
        
        if not self.measurement.calibrated_spectrum:
            return
        
        canvas_width = self.spectrum_canvas.winfo_width()
        canvas_height = self.spectrum_canvas.winfo_height()
        
        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 400
        
        margin_left = 60
        margin_right = 40
        margin_top = 20
        margin_bottom = 40
        
        plot_width = canvas_width - margin_left - margin_right
        plot_height = canvas_height - margin_top - margin_bottom
        
        wavelengths = [point[0] for point in self.measurement.calibrated_spectrum]
        intensities = [point[1] for point in self.measurement.calibrated_spectrum]
        
        if not wavelengths:
            return
        
        min_wavelength = min(wavelengths)
        max_wavelength = max(wavelengths)
        
        if len(intensities) > 0:
            max_intensity = max(intensities)
            min_intensity = min(intensities)
        else:
            max_intensity = 1.0
            min_intensity = 0.0
        
        if max_intensity <= 0:
            max_intensity = 1.0
        
        if max_intensity == min_intensity:
            max_intensity = min_intensity + 1.0
        
        if max_wavelength == min_wavelength:
            max_wavelength = min_wavelength + 1.0
        
        intensity_padding = (max_intensity - min_intensity) * 0.1
        if intensity_padding == 0:
            intensity_padding = 0.1
        
        max_intensity_display = max_intensity + intensity_padding
        min_intensity_display = min_intensity - intensity_padding
        
        if min_intensity_display < 0:
            min_intensity_display = 0
        
        wavelength_padding = (max_wavelength - min_wavelength) * 0.05
        min_wavelength_display = min_wavelength - wavelength_padding
        max_wavelength_display = max_wavelength + wavelength_padding
        
        if min_wavelength_display < 0:
            min_wavelength_display = 0
        
        def wavelength_to_x(wavelength):
            return margin_left + (wavelength - min_wavelength_display) / (max_wavelength_display - min_wavelength_display) * plot_width
        
        def intensity_to_y(intensity):
            return margin_top + plot_height - (intensity - min_intensity_display) / (max_intensity_display - min_intensity_display) * plot_height
        
        for i in range(len(wavelengths) - 1):
            x1 = wavelength_to_x(wavelengths[i])
            y1 = intensity_to_y(intensities[i])
            x2 = wavelength_to_x(wavelengths[i + 1])
            y2 = intensity_to_y(intensities[i + 1])
            self.spectrum_canvas.create_line(x1, y1, x2, y2, fill="red", width=2)
        
        for x in range(0, 6):
            wavelength = min_wavelength_display + (max_wavelength_display - min_wavelength_display) * x / 5
            x_pos = wavelength_to_x(wavelength)
            if margin_left <= x_pos <= margin_left + plot_width:
                self.spectrum_canvas.create_line(x_pos, margin_top, x_pos, margin_top + plot_height, fill="gray", width=1)
                self.spectrum_canvas.create_text(x_pos, margin_top + plot_height + 10, text=f"{wavelength:.0f}", anchor="n", font=("Arial", 8))
        
        for y in range(0, 5):
            intensity = min_intensity_display + (max_intensity_display - min_intensity_display) * y / 4
            y_pos = intensity_to_y(intensity)
            if margin_top <= y_pos <= margin_top + plot_height:
                self.spectrum_canvas.create_line(margin_left, y_pos, margin_left + plot_width, y_pos, fill="gray", width=1)
                self.spectrum_canvas.create_text(margin_left - 5, y_pos, text=f"{intensity:.2e}", anchor="e", font=("Arial", 8))
        
        self.spectrum_canvas.create_text(margin_left + plot_width // 2, margin_top + plot_height + 25, text="Длина волны (нм)", anchor="n", font=("Arial", 9))
        self.spectrum_canvas.create_text(margin_left - 35, margin_top + plot_height // 2, text="Интеграл сигнала (В·с)", anchor="center", angle=90, font=("Arial", 9))
    
    def save_spectrum_to_file(self):
        file_path = filedialog.asksaveasfilename(
            title="Сохранить спектр",
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.measurement.save_spectrum_to_csv(Path(file_path))
            self.append_log(f"Спектр сохранён в {file_path}\n")
    
    def measure_energy_series(self):
        def measure_task():
            self.measure_energy_button.config(state=tkinter.DISABLED)
            
            points_count = int(self.energy_points_entry.get())
            
            self.energy_log.config(state=tkinter.NORMAL)
            self.energy_log.delete(1.0, tkinter.END)
            self.energy_log.config(state=tkinter.DISABLED)
            
            self.append_log("\n" + "="*50 + "\n", self.energy_log)
            self.append_log("ИЗМЕРЕНИЕ ЭНЕРГИИ\n", self.energy_log)
            self.append_log("="*50 + "\n", self.energy_log)
            
            self.measurement.energy_measurements = self.measurement.measure_energy_series(points_count, self.energy_log)
            
            average_energy = numpy.mean(self.measurement.energy_measurements)
            std_energy = numpy.std(self.measurement.energy_measurements)

            self.append_log(f"\nРезультаты:\n", self.energy_log)
            self.append_log(f"  Среднее значение: {average_energy:.6e} В·с\n", self.energy_log)
            self.append_log(f"  Стандартное отклонение: {std_energy:.6e} В·с\n", self.energy_log)
            
            self.energy_canvas.delete("all")
            self.energy_canvas.create_text(400, 150, text="Нажмите 'Калибровать энергометр' для построения графика", 
                                            anchor="center", font=("Arial", 12), fill="gray")
            
            self.measure_energy_button.config(state=tkinter.NORMAL)
        
        threading.Thread(target=measure_task, daemon=True).start()
    
    def calibrate_energy_detector(self):
        def ask_reference_energies():
            reference_input = simpledialog.askstring("Эталонные энергии", 
                                                    "Введите эталонные значения энергии (Дж) через запятую:\nПример: 1e-6, 2e-6, 5e-6, 10e-6, 20e-6",
                                                    parent=self.application_window)
            
            if not reference_input:
                self.calibrate_energy_button.config(state=tkinter.NORMAL)
                return
            
            try:
                reference_energies = [float(x.strip()) for x in reference_input.split(",")]
            except ValueError:
                self.append_log("Ошибка: неверный формат ввода\n", self.energy_log)
                self.calibrate_energy_button.config(state=tkinter.NORMAL)
                return
            
            if len(reference_energies) != len(self.measurement.energy_measurements):
                self.append_log(f"Ошибка: количество эталонных значений ({len(reference_energies)}) не совпадает с количеством измерений ({len(self.measurement.energy_measurements)})\n", self.energy_log)
                self.calibrate_energy_button.config(state=tkinter.NORMAL)
                return
            
            calibration_result = self.measurement.calibrate_energy_detector(
                self.measurement.energy_measurements, reference_energies, self.energy_log
            )
            
            if calibration_result.get("calibration_success", False):
                self.draw_energy_calibration_graph(reference_energies, self.measurement.energy_measurements, calibration_result)
            
            self.calibrate_energy_button.config(state=tkinter.NORMAL)
        
        def calibrate_task():
            self.calibrate_energy_button.config(state=tkinter.DISABLED)
            
            self.energy_log.config(state=tkinter.NORMAL)
            self.energy_log.delete(1.0, tkinter.END)
            self.energy_log.config(state=tkinter.DISABLED)
            
            self.append_log("\n" + "="*50 + "\n", self.energy_log)
            self.append_log("КАЛИБРОВКА ЭНЕРГОМЕТРА\n", self.energy_log)
            self.append_log("="*50 + "\n", self.energy_log)
            
            self.application_window.after(0, ask_reference_energies)
        
        threading.Thread(target=calibrate_task, daemon=True).start()
    
    def draw_energy_calibration_graph(self, reference_energies, measured_signals, calibration_result):
        self.energy_canvas.delete("all")
        
        canvas_width = self.energy_canvas.winfo_width()
        canvas_height = self.energy_canvas.winfo_height()
        
        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 300
        
        margin_left = 60
        margin_right = 40
        margin_top = 20
        margin_bottom = 40
        
        plot_width = canvas_width - margin_left - margin_right
        plot_height = canvas_height - margin_top - margin_bottom
        
        if not reference_energies:
            return
        
        min_energy = min(reference_energies)
        max_energy = max(reference_energies)
        min_signal = min(measured_signals)
        max_signal = max(measured_signals)
        
        if max_energy == min_energy:
            max_energy = min_energy + 1.0
        if max_signal == min_signal:
            max_signal = min_signal + 1.0
        
        energy_padding = (max_energy - min_energy) * 0.1
        if energy_padding == 0:
            energy_padding = 0.1
        signal_padding = (max_signal - min_signal) * 0.1
        if signal_padding == 0:
            signal_padding = 0.1
        
        min_energy_display = min_energy - energy_padding
        max_energy_display = max_energy + energy_padding
        min_signal_display = min_signal - signal_padding
        max_signal_display = max_signal + signal_padding
        
        if min_energy_display < 0:
            min_energy_display = 0
        if min_signal_display < 0:
            min_signal_display = 0
        
        def energy_to_x(energy_value):
            return margin_left + (energy_value - min_energy_display) / (max_energy_display - min_energy_display) * plot_width
        
        def signal_to_y(signal_value):
            return margin_top + plot_height - (signal_value - min_signal_display) / (max_signal_display - min_signal_display) * plot_height
        
        for i in range(len(reference_energies)):
            x = energy_to_x(reference_energies[i])
            y = signal_to_y(measured_signals[i])
            self.energy_canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="blue", outline="blue")
        
        if calibration_result.get("calibration_success", False):
            sensitivity = calibration_result["detector_sensitivity"]
            dark_signal = calibration_result["dark_signal_offset"]
            
            line_energies = [min_energy_display, max_energy_display]
            line_signals = [sensitivity * e + dark_signal for e in line_energies]
            
            x1 = energy_to_x(line_energies[0])
            y1 = signal_to_y(line_signals[0])
            x2 = energy_to_x(line_energies[1])
            y2 = signal_to_y(line_signals[1])
            self.energy_canvas.create_line(x1, y1, x2, y2, fill="red", width=2, dash=(5, 5))
            
            fit_quality = calibration_result.get("fit_quality", 0)
            self.energy_canvas.create_text(margin_left + plot_width - 10, margin_top + 15, 
                                            text=f"R² = {fit_quality:.4f}", anchor="ne", font=("Arial", 9))
            self.energy_canvas.create_text(margin_left + plot_width - 10, margin_top + 30,
                                            text=f"y = {sensitivity:.3e}x + {dark_signal:.3e}", anchor="ne", font=("Arial", 9))
        
        for x in range(0, 6):
            energy_value = min_energy_display + (max_energy_display - min_energy_display) * x / 5
            x_pos = energy_to_x(energy_value)
            if margin_left <= x_pos <= margin_left + plot_width:
                self.energy_canvas.create_line(x_pos, margin_top, x_pos, margin_top + plot_height, fill="gray", width=1)
                self.energy_canvas.create_text(x_pos, margin_top + plot_height + 10, text=f"{energy_value:.2e}", anchor="n", font=("Arial", 8))
        
        for y in range(0, 5):
            signal_value = min_signal_display + (max_signal_display - min_signal_display) * y / 4
            y_pos = signal_to_y(signal_value)
            if margin_top <= y_pos <= margin_top + plot_height:
                self.energy_canvas.create_line(margin_left, y_pos, margin_left + plot_width, y_pos, fill="gray", width=1)
                self.energy_canvas.create_text(margin_left - 5, y_pos, text=f"{signal_value:.2e}", anchor="e", font=("Arial", 8))
        
        self.energy_canvas.create_text(margin_left + plot_width // 2, margin_top + plot_height + 25, text="Энергия (Дж)", anchor="n", font=("Arial", 9))
        self.energy_canvas.create_text(margin_left - 35, margin_top + plot_height // 2, text="Сигнал (В·с)", anchor="center", angle=90, font=("Arial", 9))
        self.energy_canvas.create_text(margin_left + 80, margin_top + 15, text="Измерения", anchor="nw", fill="blue", font=("Arial", 9))
        self.energy_canvas.create_text(margin_left + 80, margin_top + 30, text="Аппроксимация", anchor="nw", fill="red", font=("Arial", 9))
    
    def on_closing(self):
        if self.measurement.chromator_device:
            self.measurement.chromator_device.disconnect()
        if self.measurement.oscilloscope_device:
            self.measurement.oscilloscope_device.disconnect()
        self.application_window.destroy()


if __name__ == "__main__":
    application = MeasurementApplication()
    application.initialize_user_interface()