import sys
import numpy as np
from PyQt5.QtWidgets import QApplication
from interface import MainWindow

class Application:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MainWindow()
        self.window.parent_app = self
        
    def get_settings_parameters(self):
        params = self.window.get_settings_parameters()
        print("Полученные параметры:")
        print(f"Длина волны лазера: {params['laser_wavelength']}")
        print(f"Верхняя граница монохроматора: {params['monochromator_upper']}")
        print(f"Нижняя граница монохроматора: {params['monochromator_lower']}")
        print(f"Шаг сканирования: {params['step']}")
        print(f"Направление: {params['direction']}")
        return params
    
    def get_line_positions(self):
        positions = self.window.get_line_positions()
        print("Позиции линий:")
        print(f"Фон (левый): {positions['background_left']:.3f}")
        print(f"Фон (правый): {positions['background_right']:.3f}")
        print(f"Сигнал (левый): {positions['signal_left']:.3f}")
        print(f"Сигнал (правый): {positions['signal_right']:.3f}")
        return positions
    
    def on_lines_changed(self, positions):
        print("Позиции линий обновлены (автоматически):")
        print(f"Фон (левый): {positions['background_left']:.3f}")
        print(f"Фон (правый): {positions['background_right']:.3f}")
        print(f"Сигнал (левый): {positions['signal_left']:.3f}")
        print(f"Сигнал (правый): {positions['signal_right']:.3f}")
        
    def set_time_data(self, x_data, y_data):
        self.window.set_time_data(x_data, y_data)
    
    def set_spectrum_data(self, x_data, y_data):
        self.window.set_spectrum_data(x_data, y_data)
    
    def run(self):
        self.window.show()
        
        import threading
        def demo_data():
            import time
            time.sleep(2)
            
            x_time = np.linspace(0, 10, 1000)
            y_time = np.sin(x_time) + 0.5 * np.sin(3*x_time) + 0.3 * np.random.normal(0, 0.1, 1000)
            self.set_time_data(x_time, y_time)
            
            x_spectrum = np.linspace(400, 800, 200)
            y_spectrum = np.exp(-(x_spectrum - 550)**2 / 1000) + 0.1 * np.random.normal(0, 0.05, 200)
            self.set_spectrum_data(x_spectrum, y_spectrum)
        
        thread = threading.Thread(target=demo_data, daemon=True)
        thread.start()
        
        return self.app.exec_()

def main():
    application = Application()
    sys.exit(application.run())

if __name__ == '__main__':
    main()
