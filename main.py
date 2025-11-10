import sys
import numpy as np
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

class Oscilloscope:
    def connect(self): return True
    def is_connected(self): return True
    def get_current_data(self):
        x = np.linspace(0, 10, 1000)
        y = np.sin(x) + 0.1 * np.random.randn(1000)
        return x, y
    def disconnect(self): pass

class LaserController:
    def connect(self): return True
    def is_connected(self): return True
    def set_wavelength(self, wavelength): pass
    def disconnect(self): pass

class MonochromatorController:
    def connect(self): return True
    def is_connected(self): return True
    def set_wavelength(self, wavelength): pass
    def disconnect(self): pass

class PowerMeter:
    def connect(self): return True
    def is_connected(self): return True
    def set_wavelength(self, wavelength): pass
    def get_average_energy(self, n): return 0.00015 + 0.00005 * np.random.random()
    def disconnect(self): pass

from interface import MainWindow

class Application:
    def __init__(self):
        self.oscilloscope = Oscilloscope()
        self.laser = LaserController()
        self.monochromator = MonochromatorController()
        self.powermeter = PowerMeter()
        
        self.window = MainWindow()
        self.window.parent_app = self
        
        self.setup_connections()
        self.setup_equipment()
        
    def setup_connections(self):
        self.window.time_plot.parent_window = self.window
        self.window.start_experiment_button.clicked.connect(self.start_experiment)
        self.window.calibrate_button.clicked.connect(self.start_calibration)
        
    def setup_equipment(self):
        if self.oscilloscope.connect():
            self.oscilloscope_timer = QTimer()
            self.oscilloscope_timer.timeout.connect(self.read_oscilloscope_data)
            self.oscilloscope_timer.start(1000)
        
        self.laser.connect()
        self.monochromator.connect()
        self.powermeter.connect()
        
        print("Все устройства подключены (эмуляция)")
    
    def read_oscilloscope_data(self):
        if self.oscilloscope.is_connected():
            x_data, y_data = self.oscilloscope.get_current_data()
            if x_data is not None and y_data is not None:
                self.window.set_time_data(x_data, y_data)
    
    def start_experiment(self):
        try:
            params = self.get_experiment_parameters()
            print(f"Запуск эксперимента с параметрами: {params}")
            
            # Генерируем тестовые данные для спектра
            wavelengths = np.linspace(params['start_wavelength'], params['end_wavelength'], 
                                    int((params['end_wavelength'] - params['start_wavelength']) / params['step']) + 1)
            energies = 0.0001 + 0.0002 * np.exp(-0.01 * (wavelengths - 550)**2) + 0.00005 * np.random.randn(len(wavelengths))
            
            # ✅ ВОТ ЭТА СТРОКА ОТСУТСТВОВАЛА - передаем данные в интерфейс
            self.window.set_spectrum_data(wavelengths, energies)
            print("Эксперимент завершен успешно")
            
        except Exception as e:
            print(f"Ошибка: {e}")
    
    def start_calibration(self):
        try:
            start_wl = float(self.window.monochromator_start_input.text())
            end_wl = float(self.window.monochromator_end_input.text())
            step = float(self.window.step_input.text())
            
            print(f"Запуск калибровки: {start_wl} - {end_wl} нм, шаг {step}")
            
            wavelengths = np.linspace(start_wl, end_wl, int((end_wl - start_wl) / step) + 1)
            energies = 0.00015 + 0.0001 * np.sin(0.1 * wavelengths) + 0.00002 * np.random.randn(len(wavelengths))
            
            # ✅ Передаем данные калибровки в интерфейс
            self.window.update_calibration_plot(wavelengths, energies)
            print("Калибровка завершена")
            
        except Exception as e:
            print(f"Ошибка калибровки: {e}")
    
    def get_experiment_parameters(self):
        return {
            'laser_wavelength': float(self.window.laser_wavelength_input.text()),
            'start_wavelength': float(self.window.monochromator_start_input.text()),
            'end_wavelength': float(self.window.monochromator_end_input.text()),
            'step': float(self.window.step_input.text())
        }
    
    def close_application(self):
        if hasattr(self, 'oscilloscope_timer'):
            self.oscilloscope_timer.stop()
        self.oscilloscope.disconnect()
        self.laser.disconnect()
        self.monochromator.disconnect()
        self.powermeter.disconnect()

def main():
    app = QApplication(sys.argv)
    application = Application()
    application.window.show()
    app.aboutToQuit.connect(application.close_application)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
