import pyvisa
import time
import numpy as np
import threading

class PowerMeter:
    def __init__(self):
        self.resource_manager = None
        self.instrument = None
        self.connected = False
        self.wavelength = 0.0
        self.auto_range = True
        self.range = 0
        self._lock = threading.Lock()
        self.measurement_buffer = []
        self.buffer_size = 10
        
    def connect(self, resource_name=None):
        """Подключение к измерителю энергии/мощности"""
        try:
            self.resource_manager = pyvisa.ResourceManager()
            
            if resource_name:
                self.instrument = self.resource_manager.open_resource(resource_name)
                self.instrument.timeout = 5000
                
                idn = self.instrument.query('*IDN?')
                if any(keyword in idn.upper() for keyword in ['POWER', 'ENERGY', 'NEWPORT', 'THORLABS', 'COHERENT', 'GENTEC']):
                    self.connected = True
                    print(f"Подключено к измерителю мощности: {idn.strip()}")
                    self.initialize_powermeter()
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
                        
                        if any(keyword in idn.upper() for keyword in ['POWER', 'ENERGY', 'NEWPORT', 'THORLABS', 'COHERENT', 'GENTEC']):
                            self.connected = True
                            print(f"Подключено к измерителю мощности: {idn.strip()}")
                            self.initialize_powermeter()
                            return True
                        else:
                            self.instrument.close()
                    except:
                        continue
                
                print("Измеритель мощности не найден")
                return False
                
        except Exception as error:
            print(f"Ошибка подключения к измерителю мощности: {error}")
            return False
    
    def initialize_powermeter(self):
        """Инициализация измерителя мощности"""
        try:
            self.set_wavelength(532)
            self.set_auto_range(True)
            print("Измеритель мощности инициализирован")
        except Exception as error:
            print(f"Ошибка инициализации измерителя мощности: {error}")
    
    def set_wavelength(self, wavelength):
        """Установка длины волны для калибровки измерений"""
        if not self.connected:
            print("Измеритель мощности не подключен")
            return False
        
        try:
            with self._lock:
                self.instrument.write(f':SENS:CORR:WAV {wavelength}')
                time.sleep(0.1)
                
                actual_wavelength = float(self.instrument.query(':SENS:CORR:WAV?'))
                self.wavelength = actual_wavelength
                print(f"Длина волны для измерений установлена: {actual_wavelength} нм")
                return True
                
        except Exception as error:
            print(f"Ошибка установки длины волны: {error}")
            return False
    
    def set_auto_range(self, auto_range):
        """Включение/выключение автодиапазона"""
        if not self.connected:
            print("Измеритель мощности не подключен")
            return False
        
        try:
            with self._lock:
                if auto_range:
                    self.instrument.write(':SENS:POW:RANG:AUTO 1')
                    self.auto_range = True
                    print("Автодиапазон включен")
                else:
                    self.instrument.write(':SENS:POW:RANG:AUTO 0')
                    self.auto_range = False
                    print("Автодиапазон выключен")
                
                return True
                
        except Exception as error:
            print(f"Ошибка установки автодиапазона: {error}")
            return False
    
    def set_range(self, range_value):
        """Установка диапазона измерений вручную"""
        if not self.connected:
            print("Измеритель мощности не подключен")
            return False
        
        try:
            with self._lock:
                self.instrument.write(f':SENS:POW:RANG {range_value}')
                self.range = range_value
                print(f"Диапазон измерений установлен: {range_value}")
                return True
                
        except Exception as error:
            print(f"Ошибка установки диапазона: {error}")
            return False
    
    def get_power(self):
        """Получение текущего значения мощности"""
        if not self.connected:
            print("Измеритель мощности не подключен")
            return 0.0
        
        try:
            with self._lock:
                power_str = self.instrument.query(':READ:POW?')
                power = float(power_str)
                
                self.measurement_buffer.append(power)
                if len(self.measurement_buffer) > self.buffer_size:
                    self.measurement_buffer.pop(0)
                
                return power
                
        except Exception as error:
            print(f"Ошибка получения мощности: {error}")
            return 0.0
    
    def get_average_power(self, n=10):
        """Получение усредненного значения мощности"""
        if not self.connected:
            print("Измеритель мощности не подключен")
            return 0.0
        
        try:
            with self._lock:
                measurements = []
                for i in range(n):
                    power_str = self.instrument.query(':READ:POW?')
                    power = float(power_str)
                    measurements.append(power)
                    if i < n-1:
                        time.sleep(0.1)
                
                average_power = np.mean(measurements)
                return average_power
                
        except Exception as error:
            print(f"Ошибка получения усредненной мощности: {error}")
            return 0.0
    
    def get_energy(self):
        """Получение текущего значения энергии (для импульсных измерений)"""
        if not self.connected:
            print("Измеритель мощности не подключен")
            return 0.0
        
        try:
            with self._lock:
                energy_str = self.instrument.query(':READ:ENER?')
                energy = float(energy_str)
                return energy
                
        except Exception as error:
            print(f"Ошибка получения энергии: {error}")
            return 0.0
    
    def zero_calibration(self):
        """Калибровка нуля"""
        if not self.connected:
            print("Измеритель мощности не подключен")
            return False
        
        try:
            with self._lock:
                self.instrument.write(':SENS:CORR:COLL:ZERO:INIT')
                print("Калибровка нуля выполнена")
                return True
                
        except Exception as error:
            print(f"Ошибка калибровки нуля: {error}")
            return False
    
    def get_status(self):
        """Получение статуса измерителя мощности"""
        if not self.connected:
            return {
                'connected': False,
                'wavelength': 0.0,
                'auto_range': False,
                'range': 0,
                'error': 'Не подключен'
            }
        
        try:
            with self._lock:
                status = {
                    'connected': True,
                    'wavelength': self.wavelength,
                    'auto_range': self.auto_range,
                    'range': self.range,
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
                'auto_range': False,
                'range': 0,
                'error': str(error)
            }
    
    def disconnect(self):
        """Отключение измерителя мощности"""
        try:
            if self.connected:
                if self.instrument:
                    self.instrument.close()
                if self.resource_manager:
                    self.resource_manager.close()
                
                self.connected = False
                print("Измеритель мощности отключен")
                
        except Exception as error:
            print(f"Ошибка отключения измерителя мощности: {error}")
    
    def is_connected(self):
        return self.connected
