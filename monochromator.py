import pyvisa
import time
import threading

class MonochromatorController:
    def __init__(self):
        self.resource_manager = None
        self.instrument = None
        self.connected = False
        self.current_wavelength = 0.0
        self._lock = threading.Lock()
        self.is_moving = False
        
    def connect(self, resource_name=None):
        """Подключение к монохроматору"""
        try:
            self.resource_manager = pyvisa.ResourceManager()
            
            resources = self.resource_manager.list_resources()
            for resource in resources:
                try:
                    self.instrument = self.resource_manager.open_resource(resource)
                    self.instrument.timeout = 10000
                    idn = self.instrument.query('*IDN?')
                    
                    if any(keyword in idn.upper() for keyword in ['MONOCHROMATOR', 'ORIEL']):
                        self.connected = True
                        print(f"Подключено к монохроматору: {idn.strip()}")
                        return True
                    else:
                        self.instrument.close()
                except:
                    continue
            
            print("Монохроматор не найден")
            return False
                
        except Exception as error:
            print(f"Ошибка подключения к монохроматору: {error}")
            return False
    
    def set_wavelength(self, wavelength):
        """Установка длины волны монохроматора"""
        if not self.connected:
            print("Монохроматор не подключен")
            return False
        
        try:
            with self._lock:
                self.is_moving = True
                self.instrument.write(f'GOWAVE {wavelength}')
                
                timeout = 30
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    time.sleep(0.5)
                    current_pos = float(self.instrument.query('WAVE?'))
                    
                    if abs(current_pos - wavelength) <= 0.1:
                        self.current_wavelength = current_pos
                        self.is_moving = False
                        print(f"Длина волны установлена: {current_pos} нм")
                        return True
                
                self.is_moving = False
                print("Таймаут установки длины волны")
                return False
                
        except Exception as error:
            self.is_moving = False
            print(f"Ошибка установки длины волны: {error}")
            return False
    
    def get_current_wavelength(self):
        """Получение текущей длины волны"""
        if not self.connected:
            return 0.0
        
        try:
            response = self.instrument.query('WAVE?')
            return float(response.strip())
        except:
            return 0.0
    
    def disconnect(self):
        """Отключение монохроматора"""
        try:
            if self.connected and self.instrument:
                self.instrument.close()
                self.connected = False
                print("Монохроматор отключен")
        except Exception as error:
            print(f"Ошибка отключения монохроматора: {error}")
    
    def is_connected(self):
        return self.connected
