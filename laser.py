import pyvisa
import time
import threading

class LaserController:
    def __init__(self):
        self.resource_manager = None
        self.instrument = None
        self.connected = False
        self.wavelength = 0.0
        self.power = 0.0
        self.emission = False
        self._lock = threading.Lock()
        
    def connect(self, resource_name=None):
        """Подключение к лазеру"""
        try:
            self.resource_manager = pyvisa.ResourceManager()
            
            if resource_name:
                self.instrument = self.resource_manager.open_resource(resource_name)
                self.instrument.timeout = 5000
                
                idn = self.instrument.query('*IDN?')
                if any(keyword in idn.upper() for keyword in ['LASER', 'NEWPORT', 'COHERENT', 'SPECTRA']):
                    self.connected = True
                    print(f"Подключено к лазеру: {idn.strip()}")
                    self.initialize_laser()
                    return True
                else:
                    self.instrument.close()
                    return False
            else:
                resources = self.resource_manager.list_resources()
                for resource in resources:
                    try:
                        self.instrument = self.resource_manager.open_resource(resource)
                        self.instrument.timeout = 5000
                        idn = self.instrument.query('*IDN?')
                        
                        if any(keyword in idn.upper() for keyword in ['LASER', 'NEWPORT', 'COHERENT', 'SPECTRA']):
                            self.connected = True
                            print(f"Подключено к лазеру: {idn.strip()}")
                            self.initialize_laser()
                            return True
                        else:
                            self.instrument.close()
                    except:
                        continue
                
                print("Лазер не найден")
                return False
                
        except Exception as error:
            print(f"Ошибка подключения к лазеру: {error}")
            return False
    
    def initialize_laser(self):
        """Инициализация лазера в безопасное состояние"""
        try:
            self.set_emission(False)
            self.set_power(0)
            print("Лазер инициализирован")
        except Exception as error:
            print(f"Ошибка инициализации лазера: {error}")
    
    def set_wavelength(self, wavelength):
        """Установка длины волны лазера (нм)"""
        if not self.connected:
            print("Лазер не подключен")
            return False
        
        try:
            with self._lock:
                self.instrument.write(f':WAVELENGTH {wavelength}')
                time.sleep(0.5)
                
                actual_wavelength = float(self.instrument.query(':WAVELENGTH?'))
                self.wavelength = actual_wavelength
                print(f"Длина волны лазера установлена: {actual_wavelength} нм")
                return True
                
        except Exception as error:
            print(f"Ошибка установки длины волны: {error}")
            return False
    
    def set_power(self, power):
        """Установка мощности лазера (%)"""
        if not self.connected:
            print("Лазер не подключен")
            return False
        
        try:
            with self._lock:
                power = max(0, min(100, power))
                self.instrument.write(f':POWER {power}')
                time.sleep(0.1)
                
                self.power = power
                print(f"Мощность лазера установлена: {power}%")
                return True
                
        except Exception as error:
            print(f"Ошибка установки мощности: {error}")
            return False
    
    def set_emission(self, state):
        """Включение/выключение излучения лазера"""
        if not self.connected:
            print("Лазер не подключен")
            return False
        
        try:
            with self._lock:
                if state:
                    self.instrument.write(':EMISSION ON')
                    self.emission = True
                    print("Излучение лазера включено")
                else:
                    self.instrument.write(':EMISSION OFF')
                    self.emission = False
                    print("Излучение лазера выключено")
                
                return True
                
        except Exception as error:
            print(f"Ошибка управления излучением: {error}")
            return False
    
    def get_status(self):
        """Получение статуса лазера"""
        if not self.connected:
            return {
                'connected': False,
                'wavelength': 0.0,
                'power': 0.0,
                'emission': False,
                'error': 'Не подключен'
            }
        
        try:
            with self._lock:
                status = {
                    'connected': True,
                    'wavelength': self.wavelength,
                    'power': self.power,
                    'emission': self.emission,
                    'error': None
                }
                
                try:
                    error_code = self.instrument.query(':SYST:ERR?')
                    status['error'] = error_code.strip() if error_code else None
                except:
                    pass
                
                return status
                
        except Exception as error:
            return {
                'connected': False,
                'wavelength': 0.0,
                'power': 0.0,
                'emission': False,
                'error': str(error)
            }
    
    def disconnect(self):
        """Отключение лазера"""
        try:
            if self.connected:
                self.set_emission(False)
                self.set_power(0)
                
                if self.instrument:
                    self.instrument.close()
                if self.resource_manager:
                    self.resource_manager.close()
                
                self.connected = False
                print("Лазер отключен")
                
        except Exception as error:
            print(f"Ошибка отключения лазера: {error}")
    
    def is_connected(self):
        return self.connected
