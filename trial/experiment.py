import sys
import os
import time
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.getcwd(), "..", "library"))

from chromator import Chromator
from laser_source import LaserSource
from oscilloscope import Oscilloscope
from powermeter import Powermeter


class DeviceControlApp:
    def __init__(self):
        if getattr(sys, "frozen", False):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent

        self.base_path = base_path

        self.chromator_device = None
        self.laser_source_device = None
        self.oscilloscope_device = None
        self.powermeter_device = None

        self.chromator_connected = False
        self.laser_connected = False
        self.oscilloscope_connected = False
        self.powermeter_connected = False

        self.auto_update_enabled = True

        self.root_window = None
        self.status_timer = None

        self.operation_lock = threading.Lock()


    def set_widget_state(self, widget, state):
        try:
            widget.config(state=state)
        except Exception:
            pass


    def update_chromator_status(self, status_labels):
        if not self.chromator_connected:
            return

        try:
            wavelength = self.chromator_device.get_wavelength()
            status_labels["chromator_wavelength"].config(text=f"{wavelength:.2f} нм")

            slit_count = self.chromator_device.get_slit_count()
            if slit_count > 0:
                input_width = self.chromator_device.get_slit_width(0)
                status_labels["chromator_input_slit"].config(text=f"{input_width:.2f} мкм")

            if slit_count > 1:
                output_width = self.chromator_device.get_slit_width(1)
                status_labels["chromator_output_slit"].config(text=f"{output_width:.2f} мкм")

            shutter_state = self.chromator_device.get_shutter_state(0)
            if shutter_state == 1:
                status_labels["chromator_shutter"].config(text="Открыт", foreground="green")
            else:
                status_labels["chromator_shutter"].config(text="Закрыт", foreground="red")

            active_grating = self.chromator_device.get_active_grating()
            status_labels["chromator_grating"].config(text=str(active_grating))

            grating_count = self.chromator_device.get_grating_count()
            status_labels["chromator_grating_count"].config(text=str(grating_count))

        except Exception:
            pass


    def update_laser_status(self, status_labels):
        if not self.laser_connected:
            return

        try:
            wavelength = self.laser_source_device.get_wavelength()
            status_labels["laser_wavelength"].config(text=f"{wavelength:.2f} нм")

            position = self.laser_source_device.get_position(1)
            status_labels["laser_position"].config(text=str(position))

            speed = self.laser_source_device.get_speed(1)
            status_labels["laser_speed"].config(text=str(speed))

            motor_status = self.laser_source_device.get_status(1)
            if motor_status == 0:
                status_labels["laser_motor"].config(text="Готов", foreground="green")
            elif motor_status == 1:
                status_labels["laser_motor"].config(text="Движение", foreground="orange")
            else:
                status_labels["laser_motor"].config(text="Ошибка", foreground="red")

            shutter = self.laser_source_device.get_shutter(1)
            if shutter:
                status_labels["laser_shutter"].config(text="Открыт", foreground="green")
            else:
                status_labels["laser_shutter"].config(text="Закрыт", foreground="red")

        except Exception:
            pass


    def update_oscilloscope_status(self, status_labels):
        if not self.oscilloscope_connected:
            return

        try:
            channel = int(status_labels["oscilloscope_channel"].get())

            scale = self.oscilloscope_device.get_channel_scale(channel)
            status_labels["oscilloscope_scale"].config(text=f"{scale:.3f} В/дел")

            offset = self.oscilloscope_device.get_channel_offset(channel)
            status_labels["oscilloscope_offset"].config(text=f"{offset:.3f} В")

            coupling = self.oscilloscope_device.get_channel_coupling(channel)
            status_labels["oscilloscope_coupling"].config(text=coupling)

            enabled = self.oscilloscope_device.is_channel_enabled(channel)
            if enabled:
                status_labels["oscilloscope_enabled"].config(text="Включён", foreground="green")
            else:
                status_labels["oscilloscope_enabled"].config(text="Отключён", foreground="red")

            timebase = self.oscilloscope_device.get_timebase_scale()
            status_labels["oscilloscope_timebase"].config(text=f"{timebase:.2e} с/дел")

            average_count = self.oscilloscope_device.get_average_count()
            status_labels["oscilloscope_average"].config(text=str(average_count))

            acquisition_type = self.oscilloscope_device.get_acquisition_type()
            status_labels["oscilloscope_acquisition_type"].config(text=acquisition_type)

        except Exception:
            pass


    def update_powermeter_status(self, status_labels):
        if not self.powermeter_connected:
            return

        try:
            power = self.powermeter_device.get_power()
            status_labels["powermeter_power"].config(text=f"{power:.6e} Вт")

            scale_index = self.powermeter_device.get_current_scale_index()
            status_labels["powermeter_scale"].config(text=str(scale_index))

            autoscale = self.powermeter_device.get_autoscale()
            if autoscale:
                status_labels["powermeter_autoscale"].config(text="Включена", foreground="green")
            else:
                status_labels["powermeter_autoscale"].config(text="Отключена", foreground="red")

            wavelength = self.powermeter_device.get_wavelength()
            if wavelength > 0:
                status_labels["powermeter_wavelength"].config(text=f"{wavelength} нм")
            else:
                status_labels["powermeter_wavelength"].config(text="--- нм")

        except Exception:
            pass


    def update_all_status(self, status_labels):
        if not self.auto_update_enabled:
            return

        self.update_chromator_status(status_labels)
        self.update_laser_status(status_labels)
        self.update_oscilloscope_status(status_labels)
        self.update_powermeter_status(status_labels)

        if self.status_timer:
            self.status_timer = threading.Timer(1.5, self.update_all_status, args=(status_labels,))
            self.status_timer.daemon = True
            self.status_timer.start()


    def connect_chromator(self, status_labels, control_buttons):
        def task():
            with self.operation_lock:
                try:
                    self.chromator_device = Chromator()

                    if not self.chromator_device.connect():
                        return

                    self.chromator_connected = True

                    for button in control_buttons["chromator"]:
                        self.set_widget_state(button, tk.NORMAL)

                    self.update_chromator_status(status_labels)

                except Exception:
                    pass

        threading.Thread(target=task, daemon=True).start()


    def disconnect_chromator(self, status_labels, control_buttons):
        def task():
            with self.operation_lock:
                try:
                    if self.chromator_device:
                        self.chromator_device.disconnect()

                    self.chromator_connected = False

                    for button in control_buttons["chromator"]:
                        self.set_widget_state(button, tk.DISABLED)

                    self.update_chromator_status(status_labels)

                except Exception:
                    pass

        threading.Thread(target=task, daemon=True).start()


    def set_chromator_wavelength(self, entry_widget, status_labels):
        if not self.chromator_connected:
            return

        def task():
            try:
                wavelength = float(entry_widget.get())
                if self.chromator_device.set_wavelength(wavelength):
                    time.sleep(0.3)
                    self.update_chromator_status(status_labels)
            except ValueError:
                pass

        threading.Thread(target=task, daemon=True).start()


    def set_chromator_input_slit(self, entry_widget, status_labels):
        if not self.chromator_connected:
            return

        def task():
            try:
                width = float(entry_widget.get())
                self.chromator_device.set_slit_width(0, width)
                self.update_chromator_status(status_labels)
            except ValueError:
                pass

        threading.Thread(target=task, daemon=True).start()


    def set_chromator_output_slit(self, entry_widget, status_labels):
        if not self.chromator_connected:
            return

        def task():
            try:
                width = float(entry_widget.get())
                if self.chromator_device.get_slit_count() > 1:
                    self.chromator_device.set_slit_width(1, width)
                    self.update_chromator_status(status_labels)
            except ValueError:
                pass

        threading.Thread(target=task, daemon=True).start()


    def open_chromator_shutter(self, status_labels):
        if self.chromator_connected:
            self.chromator_device.shutter_open(0)
            self.update_chromator_status(status_labels)


    def close_chromator_shutter(self, status_labels):
        if self.chromator_connected:
            self.chromator_device.shutter_close(0)
            self.update_chromator_status(status_labels)


    def set_chromator_grating(self, spin_widget, status_labels):
        if self.chromator_connected:
            grating_index = spin_widget.get()
            self.chromator_device.set_active_grating(grating_index)
            self.update_chromator_status(status_labels)


    def connect_laser(self, status_labels, control_buttons):
        def task():
            with self.operation_lock:
                try:
                    self.laser_source_device = LaserSource()

                    if not self.laser_source_device.connect():
                        return

                    self.laser_connected = True

                    for button in control_buttons["laser"]:
                        self.set_widget_state(button, tk.NORMAL)

                    self.update_laser_status(status_labels)

                except Exception:
                    pass

        threading.Thread(target=task, daemon=True).start()


    def disconnect_laser(self, status_labels, control_buttons):
        def task():
            with self.operation_lock:
                try:
                    if self.laser_source_device:
                        self.laser_source_device.disconnect()

                    self.laser_connected = False

                    for button in control_buttons["laser"]:
                        self.set_widget_state(button, tk.DISABLED)

                    self.update_laser_status(status_labels)

                except Exception:
                    pass

        threading.Thread(target=task, daemon=True).start()


    def set_laser_wavelength(self, entry_widget, status_labels):
        if not self.laser_connected:
            return

        def task():
            try:
                wavelength = float(entry_widget.get())
                self.laser_source_device.set_wavelength(wavelength)
                time.sleep(0.3)
                self.update_laser_status(status_labels)
            except ValueError:
                pass

        threading.Thread(target=task, daemon=True).start()


    def set_laser_absolute_position(self, entry_widget, status_labels):
        if not self.laser_connected:
            return

        def task():
            try:
                position = int(entry_widget.get())
                self.laser_source_device.set_absolute_position(1, position)
                time.sleep(0.3)
                self.update_laser_status(status_labels)
            except ValueError:
                pass

        threading.Thread(target=task, daemon=True).start()


    def set_laser_relative_position(self, entry_widget, status_labels):
        if not self.laser_connected:
            return

        def task():
            try:
                steps = int(entry_widget.get())
                self.laser_source_device.set_relative_position(1, steps)
                time.sleep(0.3)
                self.update_laser_status(status_labels)
            except ValueError:
                pass

        threading.Thread(target=task, daemon=True).start()


    def set_laser_speed(self, entry_widget, status_labels):
        if not self.laser_connected:
            return

        def task():
            try:
                speed = int(entry_widget.get())
                self.laser_source_device.set_speed(1, speed)
                self.update_laser_status(status_labels)
            except ValueError:
                pass

        threading.Thread(target=task, daemon=True).start()


    def enable_laser_motor(self, status_labels):
        if self.laser_connected:
            self.laser_source_device.enable_motor(1)
            self.update_laser_status(status_labels)


    def disable_laser_motor(self, status_labels):
        if self.laser_connected:
            self.laser_source_device.disable_motor(1)
            self.update_laser_status(status_labels)


    def open_laser_shutter(self, status_labels):
        if self.laser_connected:
            self.laser_source_device.set_shutter(1, True)
            self.update_laser_status(status_labels)


    def close_laser_shutter(self, status_labels):
        if self.laser_connected:
            self.laser_source_device.set_shutter(1, False)
            self.update_laser_status(status_labels)


    def connect_oscilloscope(self, status_labels, control_buttons):
        def task():
            with self.operation_lock:
                try:
                    self.oscilloscope_device = Oscilloscope()

                    if not self.oscilloscope_device.connect():
                        return

                    self.oscilloscope_connected = True

                    for button in control_buttons["oscilloscope"]:
                        self.set_widget_state(button, tk.NORMAL)

                    self.update_oscilloscope_status(status_labels)

                except Exception:
                    pass

        threading.Thread(target=task, daemon=True).start()


    def disconnect_oscilloscope(self, status_labels, control_buttons):
        def task():
            with self.operation_lock:
                try:
                    if self.oscilloscope_device:
                        self.oscilloscope_device.disconnect()

                    self.oscilloscope_connected = False

                    for button in control_buttons["oscilloscope"]:
                        self.set_widget_state(button, tk.DISABLED)

                    self.update_oscilloscope_status(status_labels)

                except Exception:
                    pass

        threading.Thread(target=task, daemon=True).start()


    def set_oscilloscope_scale(self, entry_widget, status_labels):
        if not self.oscilloscope_connected:
            return

        def task():
            try:
                channel = int(status_labels["oscilloscope_channel"].get())
                scale = float(entry_widget.get())
                self.oscilloscope_device.set_channel_scale(channel, scale)
                self.update_oscilloscope_status(status_labels)
            except ValueError:
                pass

        threading.Thread(target=task, daemon=True).start()


    def set_oscilloscope_offset(self, entry_widget, status_labels):
        if not self.oscilloscope_connected:
            return

        def task():
            try:
                channel = int(status_labels["oscilloscope_channel"].get())
                offset = float(entry_widget.get())
                self.oscilloscope_device.set_channel_offset(channel, offset)
                self.update_oscilloscope_status(status_labels)
            except ValueError:
                pass

        threading.Thread(target=task, daemon=True).start()


    def set_oscilloscope_coupling(self, status_labels):
        if not self.oscilloscope_connected:
            return

        channel = int(status_labels["oscilloscope_channel"].get())
        coupling = status_labels["oscilloscope_coupling_combo"].get()
        self.oscilloscope_device.set_channel_coupling(channel, coupling)
        self.update_oscilloscope_status(status_labels)


    def enable_oscilloscope_channel(self, status_labels):
        if self.oscilloscope_connected:
            channel = int(status_labels["oscilloscope_channel"].get())
            self.oscilloscope_device.set_channel_enabled(channel, True)
            self.update_oscilloscope_status(status_labels)


    def disable_oscilloscope_channel(self, status_labels):
        if self.oscilloscope_connected:
            channel = int(status_labels["oscilloscope_channel"].get())
            self.oscilloscope_device.set_channel_enabled(channel, False)
            self.update_oscilloscope_status(status_labels)


    def set_oscilloscope_timebase(self, entry_widget, status_labels):
        if not self.oscilloscope_connected:
            return

        def task():
            try:
                timebase = float(entry_widget.get())
                self.oscilloscope_device.set_timebase_scale(timebase)
                self.update_oscilloscope_status(status_labels)
            except ValueError:
                pass

        threading.Thread(target=task, daemon=True).start()


    def set_oscilloscope_average_count(self, entry_widget, status_labels):
        if not self.oscilloscope_connected:
            return

        def task():
            try:
                average_count = int(entry_widget.get())
                self.oscilloscope_device.set_average_count(average_count)
                self.update_oscilloscope_status(status_labels)
            except ValueError:
                pass

        threading.Thread(target=task, daemon=True).start()


    def run_oscilloscope_acquisition(self):
        if self.oscilloscope_connected:
            self.oscilloscope_device.run_acquisition()


    def stop_oscilloscope_acquisition(self):
        if self.oscilloscope_connected:
            self.oscilloscope_device.stop_acquisition()


    def single_oscilloscope_acquisition(self):
        if self.oscilloscope_connected:
            self.oscilloscope_device.single_acquisition()


    def force_oscilloscope_trigger(self):
        if self.oscilloscope_connected:
            self.oscilloscope_device.force_trigger()


    def save_oscilloscope_screenshot(self):
        if not self.oscilloscope_connected:
            return

        def task():
            try:
                default_name = f"screenshot_{datetime.now().strftime('%d-%m-%Y_%H:%M:%S')}.png"
                file_path = os.path.join(os.getcwd(), default_name)
                self.oscilloscope_device.save_screenshot(file_path)
            except Exception:
                pass

        threading.Thread(target=task, daemon=True).start()


    def save_oscilloscope_csv(self, status_labels):
        if not self.oscilloscope_connected:
            return

        def task():
            try:
                channel = int(status_labels["oscilloscope_channel"].get())
                default_name = f"waveform_{datetime.now().strftime('%d-%m-%Y_%H:%M:%S')}.csv"
                file_path = os.path.join(os.getcwd(), default_name)

                time_values, voltage_values = self.oscilloscope_device.capture_waveform(channel, 2000)

                if time_values and voltage_values:
                    with open(file_path, "w", encoding="utf-8") as file_handle:
                        file_handle.write("time_seconds,voltage_volts\n")
                        for time_value, voltage_value in zip(time_values, voltage_values):
                            file_handle.write(f"{time_value:.8e},{voltage_value:.6f}\n")

            except Exception:
                pass

        threading.Thread(target=task, daemon=True).start()


    def connect_powermeter(self, status_labels, control_buttons):
        def task():
            with self.operation_lock:
                try:
                    self.powermeter_device = Powermeter()

                    if not self.powermeter_device.connect():
                        return

                    self.powermeter_connected = True

                    for button in control_buttons["powermeter"]:
                        self.set_widget_state(button, tk.NORMAL)

                    self.update_powermeter_status(status_labels)

                except Exception:
                    pass

        threading.Thread(target=task, daemon=True).start()


    def disconnect_powermeter(self, status_labels, control_buttons):
        def task():
            with self.operation_lock:
                try:
                    if self.powermeter_device:
                        self.powermeter_device.disconnect()

                    self.powermeter_connected = False

                    for button in control_buttons["powermeter"]:
                        self.set_widget_state(button, tk.DISABLED)

                    self.update_powermeter_status(status_labels)

                except Exception:
                    pass

        threading.Thread(target=task, daemon=True).start()


    def refresh_powermeter_power(self, status_labels):
        if self.powermeter_connected:
            power = self.powermeter_device.get_power()
            status_labels["powermeter_power"].config(text=f"{power:.6e} Вт")


    def measure_average_powermeter_power(self, status_labels):
        if not self.powermeter_connected:
            return

        def task():
            try:
                average_power = self.powermeter_device.get_average_power(10, 0.1)
                status_labels["powermeter_average_power"].config(text=f"{average_power:.6e} Вт")
            except Exception:
                pass

        threading.Thread(target=task, daemon=True).start()


    def increase_powermeter_scale(self, status_labels):
        if self.powermeter_connected and self.powermeter_device.set_scale_up():
            self.update_powermeter_status(status_labels)


    def decrease_powermeter_scale(self, status_labels):
        if self.powermeter_connected and self.powermeter_device.set_scale_down():
            self.update_powermeter_status(status_labels)


    def set_powermeter_scale(self, entry_widget, status_labels):
        if not self.powermeter_connected:
            return

        def task():
            try:
                scale_index = int(entry_widget.get())
                if 0 <= scale_index <= 41 and self.powermeter_device.set_scale(scale_index):
                    self.update_powermeter_status(status_labels)
            except ValueError:
                pass

        threading.Thread(target=task, daemon=True).start()


    def enable_powermeter_autoscale(self, status_labels):
        if self.powermeter_connected and self.powermeter_device.set_autoscale(True):
            self.update_powermeter_status(status_labels)


    def disable_powermeter_autoscale(self, status_labels):
        if self.powermeter_connected and self.powermeter_device.set_autoscale(False):
            self.update_powermeter_status(status_labels)


    def set_powermeter_wavelength(self, entry_widget, status_labels):
        if not self.powermeter_connected:
            return

        def task():
            try:
                wavelength = int(entry_widget.get())
                self.powermeter_device.set_wavelength_nanometers(wavelength)
                self.update_powermeter_status(status_labels)
            except ValueError:
                pass

        threading.Thread(target=task, daemon=True).start()


    def create_chromator_tab(self, parent, status_labels, control_buttons):
        tab = ttk.Frame(parent)

        main_frame = ttk.LabelFrame(tab, text="Монохроматор", padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        connection_frame = ttk.Frame(main_frame)
        connection_frame.pack(fill=tk.X, pady=5)

        center_frame = ttk.Frame(connection_frame)
        center_frame.pack(expand=True)

        ttk.Button(center_frame, text="Подключить", width=14, command=lambda: self.connect_chromator(status_labels, control_buttons)).pack(side=tk.LEFT, padx=5)
        ttk.Button(center_frame, text="Отключить", width=14, command=lambda: self.disconnect_chromator(status_labels, control_buttons)).pack(side=tk.LEFT, padx=5)

        status_frame = ttk.LabelFrame(main_frame, text="Текущее состояние", padding=5)
        status_frame.pack(fill=tk.X, pady=5)

        grid_frame = ttk.Frame(status_frame)
        grid_frame.pack(fill=tk.X)

        ttk.Label(grid_frame, text="Длина волны:", width=18, anchor="w").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        status_labels["chromator_wavelength"] = ttk.Label(grid_frame, text="--- нм", width=16, anchor="w")
        status_labels["chromator_wavelength"].grid(row=0, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Входная щель:", width=18, anchor="w").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        status_labels["chromator_input_slit"] = ttk.Label(grid_frame, text="--- мкм", width=16, anchor="w")
        status_labels["chromator_input_slit"].grid(row=1, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Выходная щель:", width=18, anchor="w").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        status_labels["chromator_output_slit"] = ttk.Label(grid_frame, text="--- мкм", width=16, anchor="w")
        status_labels["chromator_output_slit"].grid(row=2, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Затвор:", width=18, anchor="w").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        status_labels["chromator_shutter"] = ttk.Label(grid_frame, text="---", width=16, anchor="w")
        status_labels["chromator_shutter"].grid(row=3, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Активная решётка:", width=18, anchor="w").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        status_labels["chromator_grating"] = ttk.Label(grid_frame, text="-", width=16, anchor="w")
        status_labels["chromator_grating"].grid(row=4, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Всего решёток:", width=18, anchor="w").grid(row=5, column=0, sticky="w", padx=5, pady=2)
        status_labels["chromator_grating_count"] = ttk.Label(grid_frame, text="0", width=16, anchor="w")
        status_labels["chromator_grating_count"].grid(row=5, column=1, sticky="w", padx=5, pady=2)

        control_frame = ttk.LabelFrame(main_frame, text="Управление", padding=5)
        control_frame.pack(fill=tk.X, pady=5)

        ttk.Label(control_frame, text="Длина волны (нм):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        wavelength_entry = ttk.Entry(control_frame, width=14)
        wavelength_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(control_frame, text="Установить", width=12, command=lambda: self.set_chromator_wavelength(wavelength_entry, status_labels)).grid(row=0, column=2, padx=5, pady=2)

        ttk.Label(control_frame, text="Входная щель (мкм):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        input_slit_entry = ttk.Entry(control_frame, width=14)
        input_slit_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(control_frame, text="Установить", width=12, command=lambda: self.set_chromator_input_slit(input_slit_entry, status_labels)).grid(row=1, column=2, padx=5, pady=2)

        ttk.Label(control_frame, text="Выходная щель (мкм):").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        output_slit_entry = ttk.Entry(control_frame, width=14)
        output_slit_entry.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(control_frame, text="Установить", width=12, command=lambda: self.set_chromator_output_slit(output_slit_entry, status_labels)).grid(row=2, column=2, padx=5, pady=2)

        shutter_frame = ttk.Frame(control_frame)
        shutter_frame.grid(row=3, column=0, columnspan=3, pady=5)
        ttk.Button(shutter_frame, text="Открыть затвор", width=14, command=lambda: self.open_chromator_shutter(status_labels)).pack(side=tk.LEFT, padx=5)
        ttk.Button(shutter_frame, text="Закрыть затвор", width=14, command=lambda: self.close_chromator_shutter(status_labels)).pack(side=tk.LEFT, padx=5)

        grating_frame = ttk.Frame(control_frame)
        grating_frame.grid(row=4, column=0, columnspan=3, pady=5)
        ttk.Label(grating_frame, text="Номер решётки:", width=14).pack(side=tk.LEFT, padx=5)
        grating_spin = ttk.Spinbox(grating_frame, from_=0, to=10, width=10)
        grating_spin.pack(side=tk.LEFT, padx=5)
        ttk.Button(grating_frame, text="Выбрать решётку", width=14, command=lambda: self.set_chromator_grating(grating_spin, status_labels)).pack(side=tk.LEFT, padx=5)

        control_buttons["chromator"] = [
            self.find_child_by_text(connection_frame, "Отключить")
        ]

        return tab


    def create_laser_tab(self, parent, status_labels, control_buttons):
        tab = ttk.Frame(parent)

        main_frame = ttk.LabelFrame(tab, text="Лазер", padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        connection_frame = ttk.Frame(main_frame)
        connection_frame.pack(fill=tk.X, pady=5)

        center_frame = ttk.Frame(connection_frame)
        center_frame.pack(expand=True)

        ttk.Button(center_frame, text="Подключить", width=14, command=lambda: self.connect_laser(status_labels, control_buttons)).pack(side=tk.LEFT, padx=5)
        ttk.Button(center_frame, text="Отключить", width=14, command=lambda: self.disconnect_laser(status_labels, control_buttons)).pack(side=tk.LEFT, padx=5)

        status_frame = ttk.LabelFrame(main_frame, text="Текущее состояние", padding=5)
        status_frame.pack(fill=tk.X, pady=5)

        grid_frame = ttk.Frame(status_frame)
        grid_frame.pack(fill=tk.X)

        ttk.Label(grid_frame, text="Длина волны:", width=18, anchor="w").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        status_labels["laser_wavelength"] = ttk.Label(grid_frame, text="--- нм", width=16, anchor="w")
        status_labels["laser_wavelength"].grid(row=0, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Положение (шаги):", width=18, anchor="w").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        status_labels["laser_position"] = ttk.Label(grid_frame, text="---", width=16, anchor="w")
        status_labels["laser_position"].grid(row=1, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Скорость (шаги/с):", width=18, anchor="w").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        status_labels["laser_speed"] = ttk.Label(grid_frame, text="---", width=16, anchor="w")
        status_labels["laser_speed"].grid(row=2, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Статус двигателя:", width=18, anchor="w").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        status_labels["laser_motor"] = ttk.Label(grid_frame, text="---", width=16, anchor="w")
        status_labels["laser_motor"].grid(row=3, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Затвор:", width=18, anchor="w").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        status_labels["laser_shutter"] = ttk.Label(grid_frame, text="---", width=16, anchor="w")
        status_labels["laser_shutter"].grid(row=4, column=1, sticky="w", padx=5, pady=2)

        control_frame = ttk.LabelFrame(main_frame, text="Управление", padding=5)
        control_frame.pack(fill=tk.X, pady=5)

        ttk.Label(control_frame, text="Длина волны (нм):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        wavelength_entry = ttk.Entry(control_frame, width=14)
        wavelength_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(control_frame, text="Установить", width=12, command=lambda: self.set_laser_wavelength(wavelength_entry, status_labels)).grid(row=0, column=2, padx=5, pady=2)

        ttk.Label(control_frame, text="Абсолютное положение:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        absolute_entry = ttk.Entry(control_frame, width=14)
        absolute_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(control_frame, text="Установить", width=12, command=lambda: self.set_laser_absolute_position(absolute_entry, status_labels)).grid(row=1, column=2, padx=5, pady=2)

        ttk.Label(control_frame, text="Относительное смещение:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        relative_entry = ttk.Entry(control_frame, width=14)
        relative_entry.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(control_frame, text="Переместить", width=12, command=lambda: self.set_laser_relative_position(relative_entry, status_labels)).grid(row=2, column=2, padx=5, pady=2)

        ttk.Label(control_frame, text="Скорость (шаги/с):").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        speed_entry = ttk.Entry(control_frame, width=14)
        speed_entry.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(control_frame, text="Установить", width=12, command=lambda: self.set_laser_speed(speed_entry, status_labels)).grid(row=3, column=2, padx=5, pady=2)

        motor_frame = ttk.Frame(control_frame)
        motor_frame.grid(row=4, column=0, columnspan=3, pady=5)
        ttk.Button(motor_frame, text="Включить двигатель", width=16, command=lambda: self.enable_laser_motor(status_labels)).pack(side=tk.LEFT, padx=5)
        ttk.Button(motor_frame, text="Отключить двигатель", width=16, command=lambda: self.disable_laser_motor(status_labels)).pack(side=tk.LEFT, padx=5)

        shutter_frame = ttk.Frame(control_frame)
        shutter_frame.grid(row=5, column=0, columnspan=3, pady=5)
        ttk.Button(shutter_frame, text="Открыть затвор", width=14, command=lambda: self.open_laser_shutter(status_labels)).pack(side=tk.LEFT, padx=5)
        ttk.Button(shutter_frame, text="Закрыть затвор", width=14, command=lambda: self.close_laser_shutter(status_labels)).pack(side=tk.LEFT, padx=5)

        control_buttons["laser"] = [
            self.find_child_by_text(connection_frame, "Отключить"),
            wavelength_entry, absolute_entry, relative_entry, speed_entry
        ]

        return tab


    def create_oscilloscope_tab(self, parent, status_labels, control_buttons):
        tab = ttk.Frame(parent)

        main_frame = ttk.LabelFrame(tab, text="Осциллограф", padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        connection_frame = ttk.Frame(main_frame)
        connection_frame.pack(fill=tk.X, pady=5)

        center_frame = ttk.Frame(connection_frame)
        center_frame.pack(expand=True)

        ttk.Button(center_frame, text="Подключить", width=14, command=lambda: self.connect_oscilloscope(status_labels, control_buttons)).pack(side=tk.LEFT, padx=5)
        ttk.Button(center_frame, text="Отключить", width=14, command=lambda: self.disconnect_oscilloscope(status_labels, control_buttons)).pack(side=tk.LEFT, padx=5)

        status_frame = ttk.LabelFrame(main_frame, text="Текущее состояние", padding=5)
        status_frame.pack(fill=tk.X, pady=5)

        grid_frame = ttk.Frame(status_frame)
        grid_frame.pack(fill=tk.X)

        ttk.Label(grid_frame, text="Номер канала:", width=20, anchor="w").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        status_labels["oscilloscope_channel"] = tk.StringVar(value="1")
        channel_combo = ttk.Combobox(grid_frame, textvariable=status_labels["oscilloscope_channel"], values=["1", "2", "3", "4"], width=12, state="readonly")
        channel_combo.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        channel_combo.bind("<<ComboboxSelected>>", lambda e: self.update_oscilloscope_status(status_labels))

        ttk.Label(grid_frame, text="Вертикальный масштаб:", width=20, anchor="w").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        status_labels["oscilloscope_scale"] = ttk.Label(grid_frame, text="--- В/дел", width=16, anchor="w")
        status_labels["oscilloscope_scale"].grid(row=1, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Вертикальное смещение:", width=20, anchor="w").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        status_labels["oscilloscope_offset"] = ttk.Label(grid_frame, text="--- В", width=16, anchor="w")
        status_labels["oscilloscope_offset"].grid(row=2, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Тип связи:", width=20, anchor="w").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        status_labels["oscilloscope_coupling"] = ttk.Label(grid_frame, text="---", width=16, anchor="w")
        status_labels["oscilloscope_coupling"].grid(row=3, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Состояние канала:", width=20, anchor="w").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        status_labels["oscilloscope_enabled"] = ttk.Label(grid_frame, text="---", width=16, anchor="w")
        status_labels["oscilloscope_enabled"].grid(row=4, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Горизонтальный масштаб:", width=20, anchor="w").grid(row=5, column=0, sticky="w", padx=5, pady=2)
        status_labels["oscilloscope_timebase"] = ttk.Label(grid_frame, text="--- с/дел", width=16, anchor="w")
        status_labels["oscilloscope_timebase"].grid(row=5, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Режим усреднения:", width=20, anchor="w").grid(row=6, column=0, sticky="w", padx=5, pady=2)
        status_labels["oscilloscope_acquisition_type"] = ttk.Label(grid_frame, text="---", width=16, anchor="w")
        status_labels["oscilloscope_acquisition_type"].grid(row=6, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Количество кадров:", width=20, anchor="w").grid(row=7, column=0, sticky="w", padx=5, pady=2)
        status_labels["oscilloscope_average"] = ttk.Label(grid_frame, text="---", width=16, anchor="w")
        status_labels["oscilloscope_average"].grid(row=7, column=1, sticky="w", padx=5, pady=2)

        control_frame = ttk.LabelFrame(main_frame, text="Управление", padding=5)
        control_frame.pack(fill=tk.X, pady=5)

        ttk.Label(control_frame, text="Вертикальный масштаб:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        scale_entry = ttk.Entry(control_frame, width=14)
        scale_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(control_frame, text="Установить", width=12, command=lambda: self.set_oscilloscope_scale(scale_entry, status_labels)).grid(row=0, column=2, padx=5, pady=2)

        ttk.Label(control_frame, text="Вертикальное смещение:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        offset_entry = ttk.Entry(control_frame, width=14)
        offset_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(control_frame, text="Установить", width=12, command=lambda: self.set_oscilloscope_offset(offset_entry, status_labels)).grid(row=1, column=2, padx=5, pady=2)

        ttk.Label(control_frame, text="Тип связи:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        status_labels["oscilloscope_coupling_combo"] = ttk.Combobox(control_frame, values=["DC", "AC", "GND"], width=12, state="readonly")
        status_labels["oscilloscope_coupling_combo"].set("DC")
        status_labels["oscilloscope_coupling_combo"].grid(row=2, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(control_frame, text="Установить", width=12, command=lambda: self.set_oscilloscope_coupling(status_labels)).grid(row=2, column=2, padx=5, pady=2)

        channel_control_frame = ttk.Frame(control_frame)
        channel_control_frame.grid(row=3, column=0, columnspan=3, pady=5)
        ttk.Button(channel_control_frame, text="Включить канал", width=14, command=lambda: self.enable_oscilloscope_channel(status_labels)).pack(side=tk.LEFT, padx=5)
        ttk.Button(channel_control_frame, text="Отключить канал", width=14, command=lambda: self.disable_oscilloscope_channel(status_labels)).pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="Горизонтальный масштаб:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        timebase_entry = ttk.Entry(control_frame, width=14)
        timebase_entry.grid(row=4, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(control_frame, text="Установить", width=12, command=lambda: self.set_oscilloscope_timebase(timebase_entry, status_labels)).grid(row=4, column=2, padx=5, pady=2)

        ttk.Label(control_frame, text="Количество кадров усреднения:").grid(row=5, column=0, sticky="w", padx=5, pady=2)
        average_entry = ttk.Entry(control_frame, width=14)
        average_entry.grid(row=5, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(control_frame, text="Установить", width=12, command=lambda: self.set_oscilloscope_average_count(average_entry, status_labels)).grid(row=5, column=2, padx=5, pady=2)

        acquisition_control_frame = ttk.Frame(control_frame)
        acquisition_control_frame.grid(row=6, column=0, columnspan=3, pady=5)
        ttk.Button(acquisition_control_frame, text="Запустить", width=12, command=lambda: self.run_oscilloscope_acquisition()).pack(side=tk.LEFT, padx=5)
        ttk.Button(acquisition_control_frame, text="Остановить", width=12, command=lambda: self.stop_oscilloscope_acquisition()).pack(side=tk.LEFT, padx=5)
        ttk.Button(acquisition_control_frame, text="Однократно", width=12, command=lambda: self.single_oscilloscope_acquisition()).pack(side=tk.LEFT, padx=5)
        ttk.Button(acquisition_control_frame, text="Принудить", width=12, command=lambda: self.force_oscilloscope_trigger()).pack(side=tk.LEFT, padx=5)

        save_control_frame = ttk.Frame(control_frame)
        save_control_frame.grid(row=7, column=0, columnspan=3, pady=5)
        ttk.Button(save_control_frame, text="Скриншот", width=14, command=lambda: self.save_oscilloscope_screenshot()).pack(side=tk.LEFT, padx=5)
        ttk.Button(save_control_frame, text="Сохранить", width=14, command=lambda: self.save_oscilloscope_csv(status_labels)).pack(side=tk.LEFT, padx=5)

        control_buttons["oscilloscope"] = [
            self.find_child_by_text(connection_frame, "Отключить"),
            scale_entry, offset_entry, timebase_entry, average_entry
        ]

        return tab


    def create_powermeter_tab(self, parent, status_labels, control_buttons):
        tab = ttk.Frame(parent)

        main_frame = ttk.LabelFrame(tab, text="Энергометр", padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        connection_frame = ttk.Frame(main_frame)
        connection_frame.pack(fill=tk.X, pady=5)

        center_frame = ttk.Frame(connection_frame)
        center_frame.pack(expand=True)

        ttk.Button(center_frame, text="Подключить", width=14, command=lambda: self.connect_powermeter(status_labels, control_buttons)).pack(side=tk.LEFT, padx=5)
        ttk.Button(center_frame, text="Отключить", width=14, command=lambda: self.disconnect_powermeter(status_labels, control_buttons)).pack(side=tk.LEFT, padx=5)

        status_frame = ttk.LabelFrame(main_frame, text="Текущее состояние", padding=5)
        status_frame.pack(fill=tk.X, pady=5)

        grid_frame = ttk.Frame(status_frame)
        grid_frame.pack(fill=tk.X)

        ttk.Label(grid_frame, text="Мощность:", width=18, anchor="w").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        status_labels["powermeter_power"] = ttk.Label(grid_frame, text="--- Вт", width=22, anchor="w")
        status_labels["powermeter_power"].grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(grid_frame, text="Обновить", width=12, command=lambda: self.refresh_powermeter_power(status_labels)).grid(row=0, column=2, padx=5, pady=2)

        ttk.Label(grid_frame, text="Средняя мощность (10 изм.):", width=18, anchor="w").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        status_labels["powermeter_average_power"] = ttk.Label(grid_frame, text="--- Вт", width=22, anchor="w")
        status_labels["powermeter_average_power"].grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(grid_frame, text="Измерить", width=12, command=lambda: self.measure_average_powermeter_power(status_labels)).grid(row=1, column=2, padx=5, pady=2)

        ttk.Label(grid_frame, text="Индекс шкалы:", width=18, anchor="w").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        status_labels["powermeter_scale"] = ttk.Label(grid_frame, text="---", width=22, anchor="w")
        status_labels["powermeter_scale"].grid(row=2, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Автошкала:", width=18, anchor="w").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        status_labels["powermeter_autoscale"] = ttk.Label(grid_frame, text="---", width=22, anchor="w")
        status_labels["powermeter_autoscale"].grid(row=3, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid_frame, text="Длина волны:", width=18, anchor="w").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        status_labels["powermeter_wavelength"] = ttk.Label(grid_frame, text="--- нм", width=22, anchor="w")
        status_labels["powermeter_wavelength"].grid(row=4, column=1, sticky="w", padx=5, pady=2)

        control_frame = ttk.LabelFrame(main_frame, text="Управление", padding=5)
        control_frame.pack(fill=tk.X, pady=5)

        scale_buttons_frame = ttk.Frame(control_frame)
        scale_buttons_frame.grid(row=0, column=0, columnspan=3, pady=5)
        ttk.Button(scale_buttons_frame, text="Увеличить шкалу", width=16, command=lambda: self.increase_powermeter_scale(status_labels)).pack(side=tk.LEFT, padx=5)
        ttk.Button(scale_buttons_frame, text="Уменьшить шкалу", width=16, command=lambda: self.decrease_powermeter_scale(status_labels)).pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="Новый индекс шкалы (0-41):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        scale_entry = ttk.Entry(control_frame, width=14)
        scale_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(control_frame, text="Установить", width=12, command=lambda: self.set_powermeter_scale(scale_entry, status_labels)).grid(row=1, column=2, padx=5, pady=2)

        autoscale_buttons_frame = ttk.Frame(control_frame)
        autoscale_buttons_frame.grid(row=2, column=0, columnspan=3, pady=5)
        ttk.Button(autoscale_buttons_frame, text="Включить автошкалу", width=16, command=lambda: self.enable_powermeter_autoscale(status_labels)).pack(side=tk.LEFT, padx=5)
        ttk.Button(autoscale_buttons_frame, text="Отключить автошкалу", width=16, command=lambda: self.disable_powermeter_autoscale(status_labels)).pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="Длина волны (нм):").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        wavelength_entry = ttk.Entry(control_frame, width=14)
        wavelength_entry.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(control_frame, text="Установить", width=12, command=lambda: self.set_powermeter_wavelength(wavelength_entry, status_labels)).grid(row=3, column=2, padx=5, pady=2)

        control_buttons["powermeter"] = [
            self.find_child_by_text(connection_frame, "Отключить"),
            scale_entry, wavelength_entry
        ]

        return tab


    def find_child_by_text(self, parent, text):
        for child in parent.winfo_children():
            if isinstance(child, ttk.Button) and child.cget("text") == text:
                return child
        return None


    def initialize_user_interface(self):
        self.root_window = tk.Tk()
        self.root_window.title("Управление лабораторным оборудованием")
        self.root_window.geometry("450x650")
        self.root_window.resizable(False, False)

        icon_path = self.base_path / "icon.png"
        if icon_path.exists():
            try:
                icon = tk.PhotoImage(file=str(icon_path))
                self.root_window.iconphoto(True, icon)
            except Exception:
                pass

        style = ttk.Style()
        style.configure("TNotebook.Tab", padding=[8, 4])
        style.configure("TLabelframe.Label", font=("Segoe Ui", 10, "bold"))
        style.configure("TButton", font=("Segoe Ui", 9))
        style.configure("TLabel", font=("Segoe Ui", 9))

        main_frame = ttk.Frame(self.root_window, padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        status_labels = {}
        control_buttons = {"chromator": [], "laser": [], "oscilloscope": [], "powermeter": []}

        chromator_tab = self.create_chromator_tab(notebook, status_labels, control_buttons)
        notebook.add(chromator_tab, text="Монохроматор")

        laser_tab = self.create_laser_tab(notebook, status_labels, control_buttons)
        notebook.add(laser_tab, text="Лазер")

        oscilloscope_tab = self.create_oscilloscope_tab(notebook, status_labels, control_buttons)
        notebook.add(oscilloscope_tab, text="Осциллограф")

        powermeter_tab = self.create_powermeter_tab(notebook, status_labels, control_buttons)
        notebook.add(powermeter_tab, text="Энергометр")

        self.update_all_status(status_labels)

        self.root_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root_window.mainloop()


    def on_closing(self):
        self.auto_update_enabled = False
        if self.status_timer:
            self.status_timer.cancel()
        self.root_window.destroy()


if __name__ == "__main__":
    application = DeviceControlApp()
    application.initialize_user_interface()