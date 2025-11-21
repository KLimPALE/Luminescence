import pyvisa
import numpy as np
import time
import struct

class Oscilloscope:
    def __init__(self):
        self.resource_manager = None
        self.instrument = None
        self.connected = False
        
    def connect(self):
        try:
            self.resource_manager = pyvisa.ResourceManager()
            resources = self.resource_manager.list_resources()
            
            oscilloscope_resource = None
            for resource in resources:
                if 'USB' in resource or 'ASRL' in resource:
                    try:
                        temp_instr = self.resource_manager.open_resource(resource)
                        idn = temp_instr.query('*IDN?')

                        if 'MSO-X 2024A' in idn or 'Keysight' in idn:
                            oscilloscope_resource = resource
                            temp_instr.close()
                            break
                        
                        temp_instr.close()
                    except:
                        continue
            
            if oscilloscope_resource:
                self.instrument = self.resource_manager.open_resource(oscilloscope_resource)
                self.instrument.timeout = 10000
                self.connected = True
                print(f"Подключено к осциллографу: {self.instrument.query('*IDN?')}")
                
                self.setup_waveform_acquisition()
                return True
            else:
                print("Осциллограф Keysight MSOX2024A не найден")
                return False
                
        except Exception as exception:
            print(f"Ошибка подключения: {exception}")
            return False
    
    def setup_waveform_acquisition(self):
        """Настройка параметров сбора данных waveform"""
        try:
            self.instrument.write(':WAVeform:SOURce CHAN1')
            self.instrument.write(':WAVeform:FORMat WORD')
            self.instrument.write(':WAVeform:BYTeorder LSBFirst')
            self.instrument.write(':WAVeform:UNSigned OFF')
            print("Настройки waveform установлены")
        except Exception as exception:
            print(f"Ошибка настройки waveform: {exception}")
    
    def disconnect(self):
        if self.instrument:
            self.instrument.close()
        if self.resource_manager:
            self.resource_manager.close()
        self.connected = False
        print("Отключено от осциллографа")
    
    def get_waveform_data(self):
        if not self.connected:
            print("Осциллограф не подключен")
            return None, None
        
        try:
            preamble = self.instrument.query(':WAVeform:PREamble?')
            preamble_parts = preamble.split(',')
            
            format_type = int(preamble_parts[0])
            acquisition_type = int(preamble_parts[1])
            points_count = int(preamble_parts[2])
            average_count = int(preamble_parts[3])
            x_increment = float(preamble_parts[4])
            x_origin = float(preamble_parts[5])
            x_reference = float(preamble_parts[6])
            y_increment = float(preamble_parts[7])
            y_origin = float(preamble_parts[8])
            y_reference = float(preamble_parts[9])
            
            waveform_data = self.instrument.query_binary_values(':WAVeform:DATA?', datatype='h', container=np.array)
            
            if len(waveform_data) != points_count:
                print(f"Предупреждение: получено {len(waveform_data)} точек, ожидалось {points_count}")
            
            y_data = np.array(waveform_data, dtype=float)
            x_data = np.array([x_origin + x_increment * i for i in range(len(y_data))])
            
            y_data = (y_data - y_reference) * y_increment + y_origin
            
            print(f"Получено {len(x_data)} точек, X: [{x_data[0]:.6f}, {x_data[-1]:.6f}], Y: [{min(y_data):.3f}, {max(y_data):.3f}]")
            return x_data, y_data
            
        except Exception as exception:
            print(f"Ошибка получения данных: {exception}")
            return None, None
    
    def get_channel_settings(self):
        """Получение дополнительных настроек канала для точного отображения"""
        if not self.connected:
            return None
        
        try:
            vertical_scale = float(self.instrument.query(':CHANnel1:SCALe?'))
            vertical_offset = float(self.instrument.query(':CHANnel1:OFFSet?'))
            vertical_position = float(self.instrument.query(':CHANnel1:POSition?'))
            
            timebase_scale = float(self.instrument.query(':TIMebase:SCALe?'))
            timebase_position = float(self.instrument.query(':TIMebase:POSition?'))
            timebase_reference = self.instrument.query(':TIMebase:REFerence?').strip()
            
            coupling = self.instrument.query(':CHANnel1:COUPling?').strip()
            bandwidth = self.instrument.query(':CHANnel1:BANDwidth?').strip()
            
            settings = {
                'vertical_scale': vertical_scale,
                'vertical_offset': vertical_offset,
                'vertical_position': vertical_position,
                'timebase_scale': timebase_scale,
                'timebase_position': timebase_position,
                'timebase_reference': timebase_reference,
                'coupling': coupling,
                'bandwidth': bandwidth
            }
            
            print("Настройки канала получены")
            return settings
            
        except Exception as exception:
            print(f"Ошибка получения настроек канала: {exception}")
            return None
    
    def get_current_data(self):
        if not self.connected:
            print("Осциллограф не подключен")
            return None, None
        
        try:
            channel_settings = self.get_channel_settings()
            x_data, y_data = self.get_waveform_data()
            
            if x_data is not None and y_data is not None and channel_settings is not None:
                print(f"Вертикальная шкала: {channel_settings['vertical_scale']} В/дел")
                print(f"Временная база: {channel_settings['timebase_scale']} с/дел")
            
            return x_data, y_data
            
        except Exception as exception:
            print(f"Ошибка получения данных: {exception}")
            return None, None
    
    def is_connected(self):
        return self.connected
