import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QMutex
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import (
    QMainWindow, QHBoxLayout, QVBoxLayout, QPushButton, 
    QWidget, QLabel, QStackedWidget, QProgressBar,
    QLineEdit, QTextEdit, QGroupBox, QComboBox, QRadioButton, QButtonGroup, QCheckBox
)

plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'axes.edgecolor': 'black',
    'axes.labelcolor': 'black',
    'text.color': 'black',
    'xtick.color': 'black',
    'ytick.color': 'black',
    'grid.color': 'gray',
    'grid.alpha': 0.3
})

class DraggableLinesPlot(FigureCanvas):
    def __init__(self, parent=None, language="russian", theme="light"):
        self.figure = Figure(figsize=(10, 6))
        super().__init__(self.figure)
        self.setParent(parent)
        self.language = language
        self.theme = theme
        self.axes = self.figure.add_subplot(111)
        self.x_data = np.array([])
        self.y_data = np.array([])
        self.lines = {
            'background': {'left': None, 'right': None},
            'signal': {'left': None, 'right': None}
        }
        self.text_annotations = {}
        self.dragging_line = None
        self.lines_initialized = False
        self.line_positions = {
            'background_left': 0.2,
            'background_right': 0.3,
            'signal_left': 0.6,
            'signal_right': 0.7
        }
        self.apply_theme()
        self.setup_plot()
        self.connect_events()
    
    def apply_theme(self):
        if self.theme == "dark":
            self.figure.patch.set_facecolor('#2b2b2b')
            self.axes.set_facecolor('#404040')

            for spine in self.axes.spines.values():
                spine.set_color('white')
            
            self.axes.xaxis.label.set_color('white')
            self.axes.yaxis.label.set_color('white')
            self.axes.title.set_color('white')
            self.axes.tick_params(axis='x', colors='white')
            self.axes.tick_params(axis='y', colors='white')
        else:
            self.figure.patch.set_facecolor('white')
            self.axes.set_facecolor('white')

            for spine in self.axes.spines.values():
                spine.set_color('black')
            
            self.axes.xaxis.label.set_color('black')
            self.axes.yaxis.label.set_color('black')
            self.axes.title.set_color('black')
            self.axes.tick_params(axis='x', colors='black')
            self.axes.tick_params(axis='y', colors='black')
    
    def setup_plot(self):
        x_label = 'Время' if self.language == "russian" else 'Time'
        y_label = 'Интенсивность' if self.language == "russian" else 'Intensity'
        title = 'Интенсивность сигнала от времени' if self.language == "russian" else 'Signal intensity vs time'
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
        self.axes.set_title(title)
        self.axes.grid(True, alpha=0.3)
        self.create_lines()
    
    def create_lines(self):
        colors = {'background': 'red', 'signal': 'blue'}

        for line_type in ['background', 'signal']:
            for side in ['left', 'right']:
                self.lines[line_type][side] = self.axes.axvline(
                    self.line_positions[f'{line_type}_{side}'], 
                    color=colors[line_type], linestyle='--', alpha=0.7, linewidth=2,
                    picker=True, pickradius=5
                )
        
        self.create_text_annotations()
    
    def create_text_annotations(self):
        texts = {
            'background_left': 'Фон\nлевый' if self.language == "russian" else 'Background\nleft',
            'background_right': 'Фон\nправый' if self.language == "russian" else 'Background\nright',
            'signal_left': 'Сигнал\nлевый' if self.language == "russian" else 'Signal\nleft',
            'signal_right': 'Сигнал\nправый' if self.language == "russian" else 'Signal\nright'
        }
        
        y_min, y_max = (0, 1) if len(self.y_data) == 0 else (np.min(self.y_data), np.max(self.y_data))

        if y_min == y_max:
            y_min, y_max = 0, 1
        
        text_y = y_min + 0.9 * (y_max - y_min)
        bbox_color = '#404040' if self.theme == "dark" else 'white'
        
        for key in list(self.text_annotations.keys()):
            if self.text_annotations[key]:
                try:
                    self.text_annotations[key].remove()
                except:
                    pass
        
        for key, text in texts.items():
            color = 'red' if 'background' in key else 'blue'
            self.text_annotations[key] = self.axes.text(
                self.line_positions[key], text_y, text,
                color=color, ha='center', va='bottom', fontsize=9, weight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor=bbox_color, alpha=0.8, edgecolor=color)
            )
    
    def connect_events(self):
        self.mpl_connect('button_press_event', self.on_press)
        self.mpl_connect('motion_notify_event', self.on_motion)
        self.mpl_connect('button_release_event', self.on_release)
    
    def on_press(self, event):
        if event.inaxes != self.axes:
            return
        
        for line_type in ['background', 'signal']:
            for side, line in self.lines[line_type].items():
                if line.contains(event)[0]:
                    self.dragging_line = (line_type, side)
                    return
    
    def on_motion(self, event):
        if self.dragging_line is None or event.inaxes != self.axes:
            return
        
        line_type, side = self.dragging_line
        line = self.lines[line_type][side]
        line.set_xdata([event.xdata, event.xdata])
        self.line_positions[f'{line_type}_{side}'] = event.xdata
        text_key = f'{line_type}_{side}'

        if text_key in self.text_annotations and self.text_annotations[text_key]:
            self.text_annotations[text_key].set_x(event.xdata)
        
        self.draw_idle()

        if hasattr(self, 'parent_window'):
            self.parent_window.on_lines_changed()
    
    def on_release(self, event):
        self.dragging_line = None
    
    def set_data(self, x_data, y_data):
        self.x_data = x_data
        self.y_data = y_data
        
        self.axes.clear()
        self.apply_theme()

        if len(x_data) > 0 and len(y_data) > 0:
            self.axes.plot(x_data, y_data, 'b-', linewidth=1)
        
        x_label = 'Время' if self.language == "russian" else 'Time'
        y_label = 'Интенсивность' if self.language == "russian" else 'Intensity'
        title = 'Интенсивность сигнала от времени' if self.language == "russian" else 'Signal intensity vs time'
        
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
        self.axes.set_title(title)
        self.axes.grid(True, alpha=0.3)
        
        if len(x_data) > 0 and not self.lines_initialized:
            x_range = x_data[-1] - x_data[0]
            self.line_positions = {
                'background_left': x_data[0] + 0.1 * x_range,
                'background_right': x_data[0] + 0.2 * x_range,
                'signal_left': x_data[0] + 0.6 * x_range,
                'signal_right': x_data[0] + 0.7 * x_range
            }
            self.lines_initialized = True
        
        self.create_lines()
        self.draw_idle()
    
    def get_line_positions(self):
        return self.line_positions.copy()
    
    def update_language(self, language):
        if self.language != language:
            self.language = language
            x_label = 'Время' if self.language == "russian" else 'Time'
            y_label = 'Интенсивность' if self.language == "russian" else 'Intensity'
            title = 'Интенсивность сигнала от времени' if self.language == "russian" else 'Signal intensity vs time'
            self.axes.set_xlabel(x_label)
            self.axes.set_ylabel(y_label)
            self.axes.set_title(title)
            self.create_text_annotations()
            self.draw_idle()
    
    def update_theme(self, theme):
        if self.theme != theme:
            self.theme = theme
            self.apply_theme()
            self.create_text_annotations()
            self.draw_idle()

class SpectrumPlot(FigureCanvas):
    def __init__(self, parent=None, language="russian", theme="light"):
        self.figure = Figure(figsize=(10, 6))
        super().__init__(self.figure)
        self.setParent(parent)
        self.language = language
        self.theme = theme
        self.axes = self.figure.add_subplot(111)
        self.x_data = np.array([])
        self.y_data = np.array([])
        self.approximation_line = None
        self.show_approximation = False
        self.apply_theme()
        self.setup_plot()
    
    def apply_theme(self):
        if self.theme == "dark":
            self.figure.patch.set_facecolor('#2b2b2b')
            self.axes.set_facecolor('#404040')

            for spine in self.axes.spines.values():
                spine.set_color('white')
            
            self.axes.xaxis.label.set_color('white')
            self.axes.yaxis.label.set_color('white')
            self.axes.title.set_color('white')
            self.axes.tick_params(axis='x', colors='white')
            self.axes.tick_params(axis='y', colors='white')
        else:
            self.figure.patch.set_facecolor('white')
            self.axes.set_facecolor('white')
            
            for spine in self.axes.spines.values():
                spine.set_color('black')
            
            self.axes.xaxis.label.set_color('black')
            self.axes.yaxis.label.set_color('black')
            self.axes.title.set_color('black')
            self.axes.tick_params(axis='x', colors='black')
            self.axes.tick_params(axis='y', colors='black')
    
    def setup_plot(self):
        x_label = 'Длина волны (нм)' if self.language == "russian" else 'Wavelength (nm)'
        y_label = 'Энергия (Дж)' if self.language == "russian" else 'Energy (J)'
        title = 'Спектр ИК-люминесценции' if self.language == "russian" else 'IR-luminescence spectrum'
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
        self.axes.set_title(title)
        self.axes.grid(True, alpha=0.3)
    
    def set_data(self, x_data, y_data, approximation_data=None):
        self.x_data, self.y_data = x_data, y_data
        self.axes.clear()
        self.apply_theme()

        if len(x_data) > 0 and len(y_data) > 0:
            self.axes.plot(x_data, y_data, 'g-', linewidth=2, label='Спектр' if self.language == "russian" else 'Spectrum')
            
            if self.show_approximation and approximation_data is not None and len(approximation_data) > 0:
                if self.approximation_line:
                    self.approximation_line.remove()
                self.approximation_line, = self.axes.plot(x_data, approximation_data, 'r--', linewidth=1, alpha=0.7, label='Аппроксимация' if self.language == "russian" else 'Approximation')
                
                if self.language == "russian":
                    self.axes.legend(loc='best')
                else:
                    self.axes.legend(loc='best')
        
        x_label = 'Длина волны (нм)' if self.language == "russian" else 'Wavelength (nm)'
        y_label = 'Энергия (Дж)' if self.language == "russian" else 'Energy (J)'
        title = 'Спектр ИК-люминесценции' if self.language == "russian" else 'IR-luminescence spectrum'
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
        self.axes.set_title(title)
        self.axes.grid(True, alpha=0.3)
        self.draw_idle()
    
    def set_approximation_visible(self, visible):
        self.show_approximation = visible
        if self.approximation_line:
            self.approximation_line.set_visible(visible)
        self.draw_idle()
    
    def update_language(self, language):
        if self.language != language:
            self.language = language
            x_label = 'Длина волны (нм)' if self.language == "russian" else 'Wavelength (nm)'
            y_label = 'Энергия (Дж)' if self.language == "russian" else 'Energy (J)'
            title = 'Спектр ИК-люминесценции' if self.language == "russian" else 'IR-luminescence spectrum'
            self.axes.set_xlabel(x_label)
            self.axes.set_ylabel(y_label)
            self.axes.set_title(title)
            self.draw_idle()
    
    def update_theme(self, theme):
        if self.theme != theme:
            self.theme = theme
            self.apply_theme()
            self.draw_idle()

class AveragingPlot(FigureCanvas):
    def __init__(self, parent=None, language="russian", theme="light"):
        self.figure = Figure(figsize=(10, 6))
        super().__init__(self.figure)
        self.setParent(parent)
        self.language = language
        self.theme = theme
        self.axes = self.figure.add_subplot(111)
        self.x_data = np.array([])
        self.y_data = np.array([])
        self.apply_theme()
        self.setup_plot()
    
    def apply_theme(self):
        if self.theme == "dark":
            self.figure.patch.set_facecolor('#2b2b2b')
            self.axes.set_facecolor('#404040')
            
            for spine in self.axes.spines.values():
                spine.set_color('white')
            
            self.axes.xaxis.label.set_color('white')
            self.axes.yaxis.label.set_color('white')
            self.axes.title.set_color('white')
            self.axes.tick_params(axis='x', colors='white')
            self.axes.tick_params(axis='y', colors='white')
        else:
            self.figure.patch.set_facecolor('white')
            self.axes.set_facecolor('white')
            
            for spine in self.axes.spines.values():
                spine.set_color('black')
            
            self.axes.xaxis.label.set_color('black')
            self.axes.yaxis.label.set_color('black')
            self.axes.title.set_color('black')
            self.axes.tick_params(axis='x', colors='black')
            self.axes.tick_params(axis='y', colors='black')
    
    def setup_plot(self):
        x_label = 'Интенсивность' if self.language == "russian" else 'Intensity'
        y_label = 'Энергия лазера (Дж)' if self.language == "russian" else 'Laser energy (J)'
        title = 'Энергия лазера от интенсивности' if self.language == "russian" else 'Laser energy vs intensity'
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
        self.axes.set_title(title)
        self.axes.grid(True, alpha=0.3)
    
    def set_data(self, x_data, y_data):
        self.x_data, self.y_data = x_data, y_data
        self.axes.clear()
        self.apply_theme()
        
        if len(x_data) > 0 and len(y_data) > 0:
            self.axes.plot(x_data, y_data, 'r-', linewidth=2, marker='o', markersize=4)
        
        x_label = 'Интенсивность' if self.language == "russian" else 'Intensity'
        y_label = 'Энергия лазера (Дж)' if self.language == "russian" else 'Laser energy (J)'
        title = 'Энергия лазера от интенсивности' if self.language == "russian" else 'Laser energy vs intensity'
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
        self.axes.set_title(title)
        self.axes.grid(True, alpha=0.3)
        self.draw_idle()
    
    def update_language(self, language):
        if self.language != language:
            self.language = language
            x_label = 'Интенсивность' if self.language == "russian" else 'Intensity'
            y_label = 'Энергия лазера (Дж)' if self.language == "russian" else 'Laser energy (J)'
            title = 'Энергия лазера от интенсивности' if self.language == "russian" else 'Laser energy vs intensity'
            self.axes.set_xlabel(x_label)
            self.axes.set_ylabel(y_label)
            self.axes.set_title(title)
            self.draw_idle()
    
    def update_theme(self, theme):
        if self.theme != theme:
            self.theme = theme
            self.apply_theme()
            self.draw_idle()

class ProcessingThread(QThread):
    progress_updated = pyqtSignal(int)
    finished_processing = pyqtSignal(str)
    
    def __init__(self, data):
        super().__init__()
        self.data = data
        
    def run(self):
        for i in range(101):
            self.progress_updated.emit(i)
            self.msleep(50)
        
        self.finished_processing.emit("processing_complete")

class CalibrationThread(QThread):
    progress_updated = pyqtSignal(int)
    data_updated = pyqtSignal(list, list)
    finished = pyqtSignal()
    
    def __init__(self, powermeter, monochromator, start_wl, end_wl, step):
        super().__init__()
        self.powermeter = powermeter
        self.monochromator = monochromator
        self.start_wl = start_wl
        self.end_wl = end_wl
        self.step = step
        self._is_running = True
        self.mutex = QMutex()
    
    def stop_calibration(self):
        self.mutex.lock()
        self._is_running = False
        self.mutex.unlock()
    
    def run(self):
        wavelengths = []
        energies = []
        total_points = int((self.end_wl - self.start_wl) / self.step) + 1
        current_point = 0
        
        current_wl = self.start_wl

        while current_wl <= self.end_wl and self._is_running:
            if self.monochromator.is_connected():
                self.monochromator.set_wavelength(current_wl)
                QThread.msleep(500)
            
            energy = self.powermeter.get_average_energy(3)
            wavelengths.append(current_wl)
            energies.append(energy)
            
            self.data_updated.emit(wavelengths, energies)
            progress = int((current_point / total_points) * 100)
            self.progress_updated.emit(progress)
            
            current_wl += self.step
            current_point += 1
        
        self.finished.emit()

class ExperimentThread(QThread):
    progress_updated = pyqtSignal(int, float, float)
    data_updated = pyqtSignal(list, list)
    finished = pyqtSignal()
    
    def __init__(self, powermeter, monochromator, start_wl, end_wl, step, measurement_count):
        super().__init__()
        self.powermeter = powermeter
        self.monochromator = monochromator
        self.start_wl = start_wl
        self.end_wl = end_wl
        self.step = step
        self.measurement_count = measurement_count
        self._is_running = True
        self.mutex = QMutex()
    
    def stop_experiment(self):
        self.mutex.lock()
        self._is_running = False
        self.mutex.unlock()
    
    def run(self):
        wavelengths = []
        energies = []
        total_points = int((self.end_wl - self.start_wl) / self.step) + 1
        current_point = 0
        
        current_wl = self.start_wl

        while current_wl <= self.end_wl and self._is_running:
            if self.monochromator.is_connected():
                self.monochromator.set_wavelength(current_wl)
                QThread.msleep(300)
            
            energy = self.powermeter.get_average_energy(self.measurement_count)
            
            wavelengths.append(current_wl)
            energies.append(energy)
            
            progress = int((current_point / total_points) * 100)
            self.progress_updated.emit(progress, current_wl, energy)
            self.data_updated.emit(wavelengths, energies)
            
            current_wl += self.step
            current_point += 1
        
        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self, language="russian", theme="light"):
        super().__init__()
        self.language = language
        self.theme = theme
        self.margin = 8
        self.current_tab = 0
        self.processing_thread = None
        self.calibration_thread = None
        self.experiment_thread = None
        self.calibration_data = {'wavelengths': [], 'energies': []}
        self.measurement_count = 15
        self.initialize_interface()
        
    def initialize_interface(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        self.update_styles()
        
        main_widget = QWidget()
        main_widget.setMouseTracking(True)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.panel = self.create_panel()
        self.menu = self.create_menu()
        self.content_stack = self.create_content_stack()
        
        main_layout.addWidget(self.panel)
        main_layout.addWidget(self.menu)
        main_layout.addWidget(self.content_stack)
        
        self.setCentralWidget(main_widget)
        self.setWindowIcon(QIcon("icon.ico"))
        self.setup_minimum_size()
        self.showMaximized()
        
        self.switch_tab(0)
    
    def create_content_stack(self):
        stack = QStackedWidget()
        
        self.settings_tab = self.create_settings_tab()
        self.processing_tab = self.create_processing_tab()
        self.visualization_tab = self.create_visualization_tab()
        self.averaging_tab = self.create_averaging_tab()
        
        stack.addWidget(self.settings_tab)
        stack.addWidget(self.processing_tab)
        stack.addWidget(self.visualization_tab)
        stack.addWidget(self.averaging_tab)
        
        return stack
    
    def create_settings_tab(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        
        top_spacer = QWidget()
        top_spacer.setFixedHeight(int(self.height() * 0.1))
        main_layout.addWidget(top_spacer)
        
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        
        left_spacer = QWidget()
        left_spacer.setFixedWidth(int(self.width() * 0.2))
        center_layout.addWidget(left_spacer)
        
        group_widget = QWidget()
        group_widget.setFixedWidth(int(self.width() * 0.6))
        layout = QVBoxLayout(group_widget)
        
        group = QGroupBox("Параметры эксперимента" if self.language == "russian" else "Experiment parameters")
        group.setFixedHeight(450)
        group.setStyleSheet(self.get_group_box_style())
        group_layout = QVBoxLayout()
        group_layout.setSpacing(8)
        
        self.laser_wavelength_label = QLabel("Длина волны лазера (нм):" if self.language == "russian" else "Laser wavelength (nm):")
        group_layout.addWidget(self.laser_wavelength_label)
        self.laser_wavelength_input = QLineEdit()
        self.laser_wavelength_input.setText("532")
        group_layout.addWidget(self.laser_wavelength_input)
        
        self.monochromator_start_label = QLabel("Начальная длина волны (нм):" if self.language == "russian" else "Start wavelength (nm):")
        group_layout.addWidget(self.monochromator_start_label)
        self.monochromator_start_input = QLineEdit()
        self.monochromator_start_input.setText("400")
        group_layout.addWidget(self.monochromator_start_input)
        
        self.monochromator_end_label = QLabel("Конечная длина волны (нм):" if self.language == "russian" else "End wavelength (nm):")
        group_layout.addWidget(self.monochromator_end_label)
        self.monochromator_end_input = QLineEdit()
        self.monochromator_end_input.setText("700")
        group_layout.addWidget(self.monochromator_end_input)
        
        self.step_label = QLabel("Шаг монохроматора (нм):" if self.language == "russian" else "Monochromator step (nm):")
        group_layout.addWidget(self.step_label)
        self.step_input = QLineEdit()
        self.step_input.setText("5")
        group_layout.addWidget(self.step_input)
        
        group_layout.addSpacing(10)
        
        buttons_layout = QHBoxLayout()
        
        self.calibrate_button = QPushButton("Автокалибровка" if self.language == "russian" else "Auto-calibration")
        self.calibrate_button.clicked.connect(self.start_calibration)
        buttons_layout.addWidget(self.calibrate_button)
        
        self.reset_button = QPushButton("Сброс параметров" if self.language == "russian" else "Reset parameters")
        self.reset_button.clicked.connect(self.reset_parameters)
        buttons_layout.addWidget(self.reset_button)
        
        self.start_experiment_button = QPushButton("Запуск эксперимента" if self.language == "russian" else "Start experiment")
        self.start_experiment_button.clicked.connect(self.start_experiment)
        buttons_layout.addWidget(self.start_experiment_button)
        
        group_layout.addLayout(buttons_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        center_layout.addWidget(group_widget)
        
        right_spacer = QWidget()
        right_spacer.setFixedWidth(int(self.width() * 0.2))
        center_layout.addWidget(right_spacer)
        
        main_layout.addWidget(center_widget)
        
        bottom_spacer = QWidget()
        bottom_spacer.setFixedHeight(int(self.height() * 0.1))
        main_layout.addWidget(bottom_spacer)
        
        return widget
    
    def create_processing_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.time_plot = DraggableLinesPlot(language=self.language, theme=self.theme)
        self.time_plot.parent_window = self
        self.time_plot_toolbar = NavigationToolbar(self.time_plot, widget)
        layout.addWidget(self.time_plot_toolbar)
        layout.addWidget(self.time_plot)
        
        return widget
    
    def create_visualization_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.spectrum_plot = SpectrumPlot(language=self.language, theme=self.theme)
        self.spectrum_plot_toolbar = NavigationToolbar(self.spectrum_plot, widget)
        
        control_layout = QHBoxLayout()
        control_layout.addStretch()
        
        self.show_approximation_label = QLabel("Показать линию аппроксимации" if self.language == "russian" else "Show approximation line")
        control_layout.addWidget(self.show_approximation_label)
        self.show_approximation_checkbox = QCheckBox()
        self.show_approximation_checkbox.setChecked(False)
        self.show_approximation_checkbox.stateChanged.connect(self.toggle_approximation_line)
        control_layout.addWidget(self.show_approximation_checkbox)
        
        layout.addWidget(self.spectrum_plot_toolbar)
        layout.addLayout(control_layout)
        layout.addWidget(self.spectrum_plot)
        
        return widget
    
    def create_averaging_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        
        self.averaging_plot = AveragingPlot(language=self.language, theme=self.theme)
        
        self.averaging_plot_toolbar = NavigationToolbar(self.averaging_plot, widget)
        layout.addWidget(self.averaging_plot_toolbar)
        
        input_container = QWidget()
        input_container.setFixedHeight(60)
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(5)
        
        center_container = QWidget()
        center_layout = QHBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        left_spacer = QWidget()
        left_spacer.setFixedWidth(int(self.width() * 0.2))
        center_layout.addWidget(left_spacer)
        
        input_widget = QWidget()
        input_widget.setFixedWidth(int(self.width() * 0.35))
        input_widget_layout = QVBoxLayout(input_widget)
        input_widget_layout.setContentsMargins(0, 0, 0, 0)
        input_widget_layout.setSpacing(5)
        
        self.measurement_count_label = QLabel("Количество измерений для усреднения:" if self.language == "russian" else "Measurement count for averaging:")
        input_widget_layout.addWidget(self.measurement_count_label)
        
        self.measurement_count_input = QLineEdit()
        self.measurement_count_input.setText(str(self.measurement_count))
        self.measurement_count_input.textChanged.connect(self.update_measurement_count)
        input_widget_layout.addWidget(self.measurement_count_input)
        
        center_layout.addWidget(input_widget)
        
        right_spacer = QWidget()
        right_spacer.setFixedWidth(int(self.width() * 0.2))
        center_layout.addWidget(right_spacer)
        
        input_layout.addWidget(center_container)
        layout.addWidget(input_container)
        layout.addWidget(self.averaging_plot)
        
        return widget
    
    def toggle_approximation_line(self, state):
        if state == Qt.Checked:
            self.spectrum_plot.set_approximation_visible(True)
        else:
            self.spectrum_plot.set_approximation_visible(False)
    
    def update_measurement_count(self):
        try:
            count = int(self.measurement_count_input.text())
            if count > 0:
                self.measurement_count = count
        except ValueError:
            pass
    
    def on_lines_changed(self):
        positions = self.time_plot.get_line_positions()

        for key, value in positions.items():
            print(f"{key}: {value:.3f}")
        
        if hasattr(self, 'parent_application'):
            self.parent_application.on_lines_changed(positions)
    
    def reset_parameters(self):
        self.laser_wavelength_input.setText("532")
        self.monochromator_start_input.setText("400")
        self.monochromator_end_input.setText("700")
        self.step_input.setText("5")
    
    def start_experiment(self):
        if self.experiment_thread and self.experiment_thread.isRunning():
            return
        
        try:
            params = {
                'laser_wavelength': float(self.laser_wavelength_input.text()),
                'start_wavelength': float(self.monochromator_start_input.text()),
                'end_wavelength': float(self.monochromator_end_input.text()),
                'step': float(self.step_input.text())
            }
            
            if hasattr(self, 'parent_application'):
                self.parent_application.start_experiment(params, self.measurement_count)
                
        except ValueError as error:
            print(f"Ошибка в параметрах: {error}")
    
    def start_calibration(self):
        if self.calibration_thread and self.calibration_thread.isRunning():
            return
        
        try:
            start_wl = float(self.monochromator_start_input.text())
            end_wl = float(self.monochromator_end_input.text())
            step = float(self.step_input.text())
            
            if hasattr(self, 'parent_application'):
                self.parent_application.start_calibration(start_wl, end_wl, step)
                
        except ValueError as error:
            print(f"Ошибка в параметрах калибровки: {error}")
    
    def stop_calibration(self):
        if self.calibration_thread and self.calibration_thread.isRunning():
            self.calibration_thread.stop_calibration()
    
    def update_calibration_progress(self, progress):
        self.calibration_progress.setValue(progress)
    
    def update_calibration_plot(self, wavelengths, energies):
        self.averaging_plot.set_data(wavelengths, energies)
        self.calibration_data = {'wavelengths': wavelengths, 'energies': energies}
    
    def set_calibration_controls_visible(self, calibrating):
        pass
    
    def set_experiment_controls_enabled(self, enabled):
        self.start_experiment_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)
    
    def get_settings_parameters(self):
        return {
            'laser_wavelength': self.laser_wavelength_input.text(),
            'monochromator_start': self.monochromator_start_input.text(),
            'monochromator_end': self.monochromator_end_input.text(),
            'step': self.step_input.text()
        }
    
    def get_line_positions(self):
        return self.time_plot.get_line_positions()
    
    def set_time_data(self, x_data, y_data):
        self.time_plot.set_data(x_data, y_data)
    
    def set_spectrum_data(self, x_data, y_data, approximation_data=None):
        self.spectrum_plot.set_data(x_data, y_data, approximation_data)
    
    def switch_tab(self, index):
        self.current_tab = index
        self.content_stack.setCurrentIndex(index)
        
        for i in range(4):
            button = self.menu.layout().itemAt(i).widget()

            if i == index:
                button.setStyleSheet(self.get_active_tab_style())
            else:
                button.setStyleSheet(self.get_inactive_tab_style())
    
    def update_styles(self):
        if self.theme == "light":
            self.setStyleSheet("background-color: white;")
        else:
            self.setStyleSheet("background-color: #2b2b2b; color: white;")
    
    def update_interface(self):
        self.update_styles()
        self.update_panel()
        self.update_menu()
        self.update_tabs_content()
        
        self.time_plot.update_language(self.language)
        self.time_plot.update_theme(self.theme)
        self.spectrum_plot.update_language(self.language)
        self.spectrum_plot.update_theme(self.theme)
        self.averaging_plot.update_language(self.language)
        self.averaging_plot.update_theme(self.theme)
    
    def update_panel(self):
        if self.theme == "light":
            self.panel.setStyleSheet("background-color: lightblue;")
            control_style = "background-color: lightskyblue;"
        else:
            self.panel.setStyleSheet("background-color: #404040; color: white;")
            control_style = "background-color: #606060; color: white;"
        
        buttons = []
        for i in range(3):
            button = self.panel.layout().itemAt(self.panel.layout().count() - 3 + i).widget()
            buttons.append(button)
            button.setStyleSheet(control_style)
    
    def update_menu(self):
        layout = self.menu.layout()
        
        tabs_text = ["Настройка", "Обработка", "Визуализация", "Усреднение"] if self.language == "russian" else ["Setting", "Processing", "Visualization", "Averaging"]

        for i in range(4):
            button = layout.itemAt(i).widget()
            button.setText(tabs_text[i])
            button.setFixedSize(110, 18)
        
        self.theme_label.setText("Тема:" if self.language == "russian" else "Theme:")
        self.language_label.setText("Язык:" if self.language == "russian" else "Language:")
        
        current_theme_text = self.theme_combo.currentText()
        current_language_text = self.language_combo.currentText()
        
        self.theme_combo.blockSignals(True)
        self.language_combo.blockSignals(True)
        
        if self.language == "russian":
            self.theme_combo.clear()
            self.theme_combo.addItems(["Светлая", "Тёмная"])
        else:
            self.theme_combo.clear()
            self.theme_combo.addItems(["Light", "Dark"])
        
        self.language_combo.clear()
        self.language_combo.addItems(["Русский", "English"])
        
        self.theme_combo.setCurrentText(current_theme_text)
        self.language_combo.setCurrentText(current_language_text)
        
        self.theme_combo.blockSignals(False)
        self.language_combo.blockSignals(False)
        
        self.switch_tab(self.current_tab)
    
    def update_tabs_content(self):
        self.settings_tab.findChild(QGroupBox).setTitle("Параметры эксперимента" if self.language == "russian" else "Experiment parameters")
        self.laser_wavelength_label.setText("Длина волны лазера (нм):" if self.language == "russian" else "Laser wavelength (nm):")
        self.monochromator_start_label.setText("Начальная длина волны (нм):" if self.language == "russian" else "Start wavelength (nm):")
        self.monochromator_end_label.setText("Конечная длина волны (нм):" if self.language == "russian" else "End wavelength (nm):")
        self.step_label.setText("Шаг монохроматора (нм):" if self.language == "russian" else "Monochromator step (nm):")
        self.calibrate_button.setText("Автокалибровка" if self.language == "russian" else "Auto-calibration")
        self.reset_button.setText("Сброс параметров" if self.language == "russian" else "Reset parameters")
        self.start_experiment_button.setText("Запуск эксперимента" if self.language == "russian" else "Start experiment")
        
        self.show_approximation_label.setText("Показать линию аппроксимации" if self.language == "russian" else "Show approximation line")
        self.measurement_count_label.setText("Количество измерений для усреднения:" if self.language == "russian" else "Measurement count for averaging:")
    
    def change_language(self, language_text):
        if language_text == "Русский":
            self.language = "russian"
        elif language_text == "English":
            self.language = "english"
        
        self.update_interface()
    
    def change_theme(self, theme_text):
        if theme_text == "Светлая" or theme_text == "Light":
            self.theme = "light"
        elif theme_text == "Тёмная" or theme_text == "Dark":
            self.theme = "dark"
        
        self.update_interface()
    
    def get_active_tab_style(self):
        if self.theme == "light":
            return "background-color: #0078D4; color: white;"
        else:
            return "background-color: #0078D4; color: white;"
    
    def get_inactive_tab_style(self):
        if self.theme == "light":
            return "background-color: lightblue;"
        else:
            return "background-color: #404040; color: white;"
    
    def get_group_box_style(self):
        if self.theme == "light":
            return "QGroupBox { border: 2px solid gray; border-radius: 5px; margin-top: 1ex; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }"
        else:
            return "QGroupBox { border: 2px solid #666666; border-radius: 5px; margin-top: 1ex; color: white; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; color: white; }"
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_position = event.globalPos()
            self.window_position = self.pos()
            self.window_size = self.size()
            position = event.pos()
            width = self.width()
            height = self.height()
            
            if position.y() <= 40:
                self.dragging = True
                return
            
            self.resize_direction = None

            if position.x() <= self.margin and position.y() <= self.margin:
                self.resize_direction = 'top_left'
            elif position.x() >= width - self.margin and position.y() <= self.margin:
                self.resize_direction = 'top_right'
            elif position.x() <= self.margin and position.y() >= height - self.margin:
                self.resize_direction = 'bottom_left'
            elif position.x() >= width - self.margin and position.y() >= height - self.margin:
                self.resize_direction = 'bottom_right'
            elif position.x() <= self.margin:
                self.resize_direction = 'left'
            elif position.x() >= width - self.margin:
                self.resize_direction = 'right'
            elif position.y() <= self.margin:
                self.resize_direction = 'top'
            elif position.y() >= height - self.margin:
                self.resize_direction = 'bottom'
    
    def mouseMoveEvent(self, event):
        position = event.pos()
        width = self.width()
        height = self.height()
        
        if hasattr(self, 'dragging') and self.dragging:
            delta = event.globalPos() - self.mouse_position
            self.move(self.window_position + delta)
        elif hasattr(self, 'resize_direction') and self.resize_direction:
            delta = event.globalPos() - self.mouse_position
            new_x = self.window_position.x()
            new_y = self.window_position.y()
            new_width = self.window_size.width()
            new_height = self.window_size.height()
            
            if self.resize_direction in ['left', 'top_left', 'bottom_left']:
                new_x = self.window_position.x() + delta.x()
                new_width = self.window_size.width() - delta.x()
            elif self.resize_direction in ['right', 'top_right', 'bottom_right']:
                new_width = self.window_size.width() + delta.x()
            
            if self.resize_direction in ['top', 'top_left', 'top_right']:
                new_y = self.window_position.y() + delta.y()
                new_height = self.window_size.height() - delta.y()
            elif self.resize_direction in ['bottom', 'bottom_left', 'bottom_right']:
                new_height = self.window_size.height() + delta.y()
            
            minimum_size = self.minimumSize()

            if new_width >= minimum_size.width() and new_height >= minimum_size.height():
                self.move(new_x, new_y)
                self.resize(new_width, new_height)
        else:
            if position.y() <= 40:
                self.setCursor(QCursor(Qt.ArrowCursor))
            elif position.x() <= self.margin and position.y() <= self.margin:
                self.setCursor(QCursor(Qt.SizeFDiagCursor))
            elif position.x() >= width - self.margin and position.y() <= self.margin:
                self.setCursor(QCursor(Qt.SizeBDiagCursor))
            elif position.x() <= self.margin and position.y() >= height - self.margin:
                self.setCursor(QCursor(Qt.SizeBDiagCursor))
            elif position.x() >= width - self.margin and position.y() >= height - self.margin:
                self.setCursor(QCursor(Qt.SizeFDiagCursor))
            elif position.x() <= self.margin:
                self.setCursor(QCursor(Qt.SizeHorCursor))
            elif position.x() >= width - self.margin:
                self.setCursor(QCursor(Qt.SizeHorCursor))
            elif position.y() <= self.margin:
                self.setCursor(QCursor(Qt.SizeVerCursor))
            elif position.y() >= height - self.margin:
                self.setCursor(QCursor(Qt.SizeVerCursor))
            else:
                self.setCursor(QCursor(Qt.ArrowCursor))
    
    def mouseReleaseEvent(self, event):
        if hasattr(self, 'dragging'):
            delattr(self, 'dragging')
        if hasattr(self, 'resize_direction'):
            delattr(self, 'resize_direction')
        if hasattr(self, 'mouse_position'):
            delattr(self, 'mouse_position')
    
    def create_panel(self):
        panel = QWidget()
        panel.setFixedHeight(40)
        panel.setMouseTracking(True)

        if self.theme == "light":
            panel.setStyleSheet("background-color: lightblue;")
        else:
            panel.setStyleSheet("background-color: #404040; color: white;")
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 0, 10, 0)

        icon_label = QLabel()
        icon_pixmap = QIcon("icon.ico").pixmap(20, 20)
        icon_label.setPixmap(icon_pixmap)
        layout.addWidget(icon_label)
        layout.addSpacing(5)

        self.title_label = QLabel("Обнаружение ИК-люминесценции веществ" if self.language == "russian" else "Detection of IR-luminescence of substances")
        layout.addWidget(self.title_label)
        
        layout.addStretch()

        minimize_button = QPushButton("🗕")
        minimize_button.setFixedSize(20, 20)
        minimize_button.clicked.connect(self.showMinimized)

        maximize_button = QPushButton("🗖")
        maximize_button.setFixedSize(20, 20)
        maximize_button.clicked.connect(self.toggle_maximize)

        close_button = QPushButton("🗙")
        close_button.setFixedSize(20, 20)
        close_button.clicked.connect(self.close)

        if self.theme == "light":
            control_style = "background-color: lightskyblue;"
        else:
            control_style = "background-color: #606060; color: white;"
        
        minimize_button.setStyleSheet(control_style)
        maximize_button.setStyleSheet(control_style)
        close_button.setStyleSheet(control_style)
        
        layout.addWidget(minimize_button)
        layout.addWidget(maximize_button)
        layout.addWidget(close_button)

        return panel

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def create_menu(self):
        widget = QWidget()
        widget.setFixedHeight(40)
        widget.setMouseTracking(True)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)

        tabs_text = ["Настройка", "Обработка", "Визуализация", "Усреднение"] if self.language == "russian" else ["Setting", "Processing", "Visualization", "Averaging"]

        for i, text in enumerate(tabs_text):
            button = QPushButton(text)
            button.setFixedSize(110, 18)
            button.clicked.connect(lambda checked, index=i: self.switch_tab(index))
            layout.addWidget(button)
        
        layout.addStretch()

        theme_layout = QHBoxLayout()
        self.theme_label = QLabel("Тема:" if self.language == "russian" else "Theme:")
        theme_layout.addWidget(self.theme_label)
        self.theme_combo = QComboBox()
        self.theme_combo.setFixedWidth(120)

        if self.language == "russian":
            self.theme_combo.addItems(["Светлая", "Тёмная"])
        else:
            self.theme_combo.addItems(["Light", "Dark"])
        
        self.theme_combo.setCurrentText("Светлая" if self.theme == "light" else "Тёмная")
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_combo)
        
        language_layout = QHBoxLayout()
        self.language_label = QLabel("Язык:" if self.language == "russian" else "Language:")
        language_layout.addWidget(self.language_label)
        self.language_combo = QComboBox()
        self.language_combo.setFixedWidth(120)
        self.language_combo.addItems(["Русский", "English"])
        self.language_combo.setCurrentText("Русский" if self.language == "russian" else "English")
        self.language_combo.currentTextChanged.connect(self.change_language)
        language_layout.addWidget(self.language_combo)
        
        layout.addLayout(theme_layout)
        layout.addLayout(language_layout)
        
        return widget

    def setup_minimum_size(self):
        from PyQt5.QtWidgets import QApplication

        screen_geometry = QApplication.primaryScreen().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        minimum_width = screen_width // 2
        minimum_height = screen_height // 2
        self.setMinimumSize(minimum_width, minimum_height)
