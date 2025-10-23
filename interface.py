import sys
import numpy as np
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import (
    QMainWindow, QHBoxLayout, QVBoxLayout, QPushButton, 
    QWidget, QLabel, QStackedWidget, QProgressBar,
    QLineEdit, QTextEdit, QGroupBox, QComboBox
)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

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
        self.fig = Figure(figsize=(10, 6))
        super().__init__(self.fig)
        self.setParent(parent)
        self.language = language
        self.theme = theme
        
        self.ax = self.fig.add_subplot(111)
        self.x_data = np.array([])
        self.y_data = np.array([])
        
        self.lines = {
            'background': {'left': None, 'right': None},
            'signal': {'left': None, 'right': None}
        }
        
        self.text_annotations = {}
        self.dragging_line = None
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
            self.fig.patch.set_facecolor('#2b2b2b')
            self.ax.set_facecolor('#404040')
            self.ax.spines['bottom'].set_color('white')
            self.ax.spines['top'].set_color('white')
            self.ax.spines['left'].set_color('white')
            self.ax.spines['right'].set_color('white')
            self.ax.xaxis.label.set_color('white')
            self.ax.yaxis.label.set_color('white')
            self.ax.title.set_color('white')
            self.ax.tick_params(axis='x', colors='white')
            self.ax.tick_params(axis='y', colors='white')
        else:
            self.fig.patch.set_facecolor('white')
            self.ax.set_facecolor('white')
            self.ax.spines['bottom'].set_color('black')
            self.ax.spines['top'].set_color('black')
            self.ax.spines['left'].set_color('black')
            self.ax.spines['right'].set_color('black')
            self.ax.xaxis.label.set_color('black')
            self.ax.yaxis.label.set_color('black')
            self.ax.title.set_color('black')
            self.ax.tick_params(axis='x', colors='black')
            self.ax.tick_params(axis='y', colors='black')
    
    def setup_plot(self):
        x_label = 'Время' if self.language == "russian" else 'Time'
        y_label = 'Интенсивность' if self.language == "russian" else 'Intensity'
        title = 'Интенсивность сигнала от времени' if self.language == "russian" else 'Signal intensity vs time'
        
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.ax.set_title(title)
        self.ax.grid(True, alpha=0.3)
        self.create_lines()
    
    def create_lines(self):
        self.lines['background']['left'] = self.ax.axvline(
            self.line_positions['background_left'], 
            color='red', linestyle='--', alpha=0.7, linewidth=2,
            picker=True, pickradius=5
        )
        
        self.lines['background']['right'] = self.ax.axvline(
            self.line_positions['background_right'], 
            color='red', linestyle='--', alpha=0.7, linewidth=2,
            picker=True, pickradius=5
        )
        
        self.lines['signal']['left'] = self.ax.axvline(
            self.line_positions['signal_left'], 
            color='blue', linestyle='--', alpha=0.7, linewidth=2,
            picker=True, pickradius=5
        )
        
        self.lines['signal']['right'] = self.ax.axvline(
            self.line_positions['signal_right'], 
            color='blue', linestyle='--', alpha=0.7, linewidth=2,
            picker=True, pickradius=5
        )
        
        self.create_text_annotations()
    
    def create_text_annotations(self):
        bg_left_text = 'Фон\nлевый' if self.language == "russian" else 'Background\nleft'
        bg_right_text = 'Фон\nправый' if self.language == "russian" else 'Background\nright'
        sig_left_text = 'Сигнал\nлевый' if self.language == "russian" else 'Signal\nleft'
        sig_right_text = 'Сигнал\nправый' if self.language == "russian" else 'Signal\nright'
        
        if len(self.y_data) == 0:
            y_min, y_max = 0, 1
        else:
            y_min, y_max = np.min(self.y_data), np.max(self.y_data)
            if y_min == y_max:
                y_min, y_max = 0, 1
        
        text_y = y_min + 0.9 * (y_max - y_min)
        
        bbox_facecolor = '#404040' if self.theme == "dark" else 'white'
        
        for key in list(self.text_annotations.keys()):
            if self.text_annotations[key] is not None:
                try:
                    self.text_annotations[key].remove()
                except:
                    pass
        
        self.text_annotations['background_left'] = self.ax.text(
            self.line_positions['background_left'], text_y, bg_left_text,
            color='red', ha='center', va='bottom', fontsize=9, weight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor=bbox_facecolor, alpha=0.8, edgecolor='red')
        )
        self.text_annotations['background_right'] = self.ax.text(
            self.line_positions['background_right'], text_y, bg_right_text,
            color='red', ha='center', va='bottom', fontsize=9, weight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor=bbox_facecolor, alpha=0.8, edgecolor='red')
        )
        self.text_annotations['signal_left'] = self.ax.text(
            self.line_positions['signal_left'], text_y, sig_left_text,
            color='blue', ha='center', va='bottom', fontsize=9, weight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor=bbox_facecolor, alpha=0.8, edgecolor='blue')
        )
        self.text_annotations['signal_right'] = self.ax.text(
            self.line_positions['signal_right'], text_y, sig_right_text,
            color='blue', ha='center', va='bottom', fontsize=9, weight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor=bbox_facecolor, alpha=0.8, edgecolor='blue')
        )
    
    def connect_events(self):
        self.mpl_connect('button_press_event', self.on_press)
        self.mpl_connect('motion_notify_event', self.on_motion)
        self.mpl_connect('button_release_event', self.on_release)
    
    def on_press(self, event):
        if event.inaxes != self.ax:
            return
        
        for line_type in ['background', 'signal']:
            for side, line in self.lines[line_type].items():
                if line.contains(event)[0]:
                    self.dragging_line = (line_type, side)
                    return
    
    def on_motion(self, event):
        if self.dragging_line is None or event.inaxes != self.ax:
            return
        
        line_type, side = self.dragging_line
        line = self.lines[line_type][side]
        
        line.set_xdata([event.xdata, event.xdata])
        self.line_positions[f'{line_type}_{side}'] = event.xdata
        
        text_key = f'{line_type}_{side}'
        if text_key in self.text_annotations and self.text_annotations[text_key] is not None:
            self.text_annotations[text_key].set_x(event.xdata)
        
        self.draw_idle()
        
        if hasattr(self, 'parent_window'):
            self.parent_window.on_lines_changed()
    
    def on_release(self, event):
        self.dragging_line = None
    
    def set_data(self, x_data, y_data):
        self.x_data = x_data
        self.y_data = y_data
        
        self.ax.clear()
        self.apply_theme()
        if len(x_data) > 0 and len(y_data) > 0:
            self.ax.plot(x_data, y_data, 'b-', linewidth=1)
        
        x_label = 'Время' if self.language == "russian" else 'Time'
        y_label = 'Интенсивность' if self.language == "russian" else 'Intensity'
        title = 'Интенсивность сигнала от времени' if self.language == "russian" else 'Signal intensity vs time'
        
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.ax.set_title(title)
        self.ax.grid(True, alpha=0.3)
        
        if len(x_data) > 0:
            x_range = x_data[-1] - x_data[0]
            self.line_positions = {
                'background_left': x_data[0] + 0.1 * x_range,
                'background_right': x_data[0] + 0.2 * x_range,
                'signal_left': x_data[0] + 0.6 * x_range,
                'signal_right': x_data[0] + 0.7 * x_range
            }
        
        self.create_lines()
        self.draw_idle()
    
    def get_line_positions(self):
        return self.line_positions.copy()
    
    def update_language(self, language):
        old_language = self.language
        self.language = language
        
        if old_language != language:
            x_label = 'Время' if self.language == "russian" else 'Time'
            y_label = 'Интенсивность' if self.language == "russian" else 'Intensity'
            title = 'Интенсивность сигнала от времени' if self.language == "russian" else 'Signal intensity vs time'
            
            self.ax.set_xlabel(x_label)
            self.ax.set_ylabel(y_label)
            self.ax.set_title(title)
            
            self.create_text_annotations()
            self.draw_idle()
    
    def update_theme(self, theme):
        old_theme = self.theme
        self.theme = theme
        
        if old_theme != theme:
            self.apply_theme()
            self.create_text_annotations()
            self.draw_idle()

class SpectrumPlot(FigureCanvas):
    def __init__(self, parent=None, language="russian", theme="light"):
        self.fig = Figure(figsize=(10, 6))
        super().__init__(self.fig)
        self.setParent(parent)
        self.language = language
        self.theme = theme
        
        self.ax = self.fig.add_subplot(111)
        self.x_data = np.array([])
        self.y_data = np.array([])
        
        self.apply_theme()
        self.setup_plot()
    
    def apply_theme(self):
        if self.theme == "dark":
            self.fig.patch.set_facecolor('#2b2b2b')
            self.ax.set_facecolor('#404040')
            self.ax.spines['bottom'].set_color('white')
            self.ax.spines['top'].set_color('white')
            self.ax.spines['left'].set_color('white')
            self.ax.spines['right'].set_color('white')
            self.ax.xaxis.label.set_color('white')
            self.ax.yaxis.label.set_color('white')
            self.ax.title.set_color('white')
            self.ax.tick_params(axis='x', colors='white')
            self.ax.tick_params(axis='y', colors='white')
        else:
            self.fig.patch.set_facecolor('white')
            self.ax.set_facecolor('white')
            self.ax.spines['bottom'].set_color('black')
            self.ax.spines['top'].set_color('black')
            self.ax.spines['left'].set_color('black')
            self.ax.spines['right'].set_color('black')
            self.ax.xaxis.label.set_color('black')
            self.ax.yaxis.label.set_color('black')
            self.ax.title.set_color('black')
            self.ax.tick_params(axis='x', colors='black')
            self.ax.tick_params(axis='y', colors='black')
    
    def setup_plot(self):
        x_label = 'Длина волны (нм)' if self.language == "russian" else 'Wavelength (nm)'
        y_label = 'Интенсивность' if self.language == "russian" else 'Intensity'
        title = 'Спектр ИК-люминесценции' if self.language == "russian" else 'IR-luminescence spectrum'
        
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.ax.set_title(title)
        self.ax.grid(True, alpha=0.3)
    
    def set_data(self, x_data, y_data):
        self.x_data = x_data
        self.y_data = y_data
        
        self.ax.clear()
        self.apply_theme()
        if len(x_data) > 0 and len(y_data) > 0:
            self.ax.plot(x_data, y_data, 'g-', linewidth=2)
        
        x_label = 'Длина волны (нм)' if self.language == "russian" else 'Wavelength (nm)'
        y_label = 'Интенсивность' if self.language == "russian" else 'Intensity'
        title = 'Спектр ИК-люминесценции' if self.language == "russian" else 'IR-luminescence spectrum'
        
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.ax.set_title(title)
        self.ax.grid(True, alpha=0.3)
        self.draw_idle()
    
    def update_language(self, language):
        old_language = self.language
        self.language = language
        
        if old_language != language:
            x_label = 'Длина волны (нм)' if self.language == "russian" else 'Wavelength (nm)'
            y_label = 'Интенсивность' if self.language == "russian" else 'Intensity'
            title = 'Спектр ИК-люминесценции' if self.language == "russian" else 'IR-luminescence spectrum'
            
            self.ax.set_xlabel(x_label)
            self.ax.set_ylabel(y_label)
            self.ax.set_title(title)
            self.draw_idle()
    
    def update_theme(self, theme):
        old_theme = self.theme
        self.theme = theme
        
        if old_theme != theme:
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

class MainWindow(QMainWindow):
    def __init__(self, language="russian", theme="light"):
        super().__init__()
        self.language = language
        self.theme = theme
        self.margin = 8
        self.current_tab = 0
        self.processing_thread = None
        self.init_interface()
        
    def init_interface(self):
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
        
        stack.addWidget(self.settings_tab)
        stack.addWidget(self.processing_tab)
        stack.addWidget(self.visualization_tab)
        
        return stack
    
    def create_settings_tab(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        
        top_spacer = QWidget()
        top_spacer.setFixedHeight(int(self.height() * 0.2))
        main_layout.addWidget(top_spacer)
        
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        
        left_spacer = QWidget()
        left_spacer.setFixedWidth(int(self.width() * 0.25))
        center_layout.addWidget(left_spacer)
        
        group_widget = QWidget()
        group_widget.setFixedWidth(int(self.width() * 0.5))
        layout = QVBoxLayout(group_widget)
        
        group = QGroupBox("Параметры эксперимента" if self.language == "russian" else "Experiment Parameters")
        group.setStyleSheet(self.get_group_box_style())
        group_layout = QVBoxLayout()
        
        self.laser_wavelength_label = QLabel("Длина волны лазера (нм):" if self.language == "russian" else "Laser wavelength (nm):")
        group_layout.addWidget(self.laser_wavelength_label)
        
        self.laser_wavelength_input = QLineEdit()
        group_layout.addWidget(self.laser_wavelength_input)
        
        self.monochromator_upper_label = QLabel("Верхняя длина волны монохроматора (нм):" if self.language == "russian" else "Monochromator upper wavelength (nm):")
        group_layout.addWidget(self.monochromator_upper_label)
        
        self.monochromator_upper_input = QLineEdit()
        group_layout.addWidget(self.monochromator_upper_input)
        
        self.monochromator_lower_label = QLabel("Нижняя длина волны монохроматора (нм):" if self.language == "russian" else "Monochromator lower wavelength (nm):")
        group_layout.addWidget(self.monochromator_lower_label)
        
        self.monochromator_lower_input = QLineEdit()
        group_layout.addWidget(self.monochromator_lower_input)
        
        self.step_label = QLabel("Шаг монохроматора (нм):" if self.language == "russian" else "Monochromator step (nm):")
        group_layout.addWidget(self.step_label)
        
        self.step_input = QLineEdit()
        group_layout.addWidget(self.step_input)
        
        self.direction_label = QLabel("Направление сканирования:" if self.language == "russian" else "Scanning direction:")
        group_layout.addWidget(self.direction_label)
        
        self.direction_combo = QComboBox()
        if self.language == "russian":
            self.direction_combo.addItems(["Сверху вниз", "Снизу вверх"])
        else:
            self.direction_combo.addItems(["From top to bottom", "From bottom to top"])
        group_layout.addWidget(self.direction_combo)
        
        group_layout.addSpacing(30)
        
        self.reset_btn = QPushButton("Сброс параметров" if self.language == "russian" else "Reset parameters")
        self.reset_btn.clicked.connect(self.reset_parameters)
        group_layout.addWidget(self.reset_btn)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        center_layout.addWidget(group_widget)
        
        right_spacer = QWidget()
        right_spacer.setFixedWidth(int(self.width() * 0.25))
        center_layout.addWidget(right_spacer)
        
        main_layout.addWidget(center_widget)
        
        bottom_spacer = QWidget()
        bottom_spacer.setFixedHeight(int(self.height() * 0.2))
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
        layout.addWidget(self.spectrum_plot_toolbar)
        layout.addWidget(self.spectrum_plot)
        
        return widget
    
    def on_lines_changed(self):
        positions = self.time_plot.get_line_positions()
        print("Позиции линий обновлены:")
        print(f"Фон (левый): {positions['background_left']:.3f}")
        print(f"Фон (правый): {positions['background_right']:.3f}")
        print(f"Сигнал (левый): {positions['signal_left']:.3f}")
        print(f"Сигнал (правый): {positions['signal_right']:.3f}")
        
        if hasattr(self, 'parent_app'):
            self.parent_app.on_lines_changed(positions)
    
    def reset_parameters(self):
        self.laser_wavelength_input.clear()
        self.monochromator_upper_input.clear()
        self.monochromator_lower_input.clear()
        self.step_input.clear()
        self.direction_combo.setCurrentIndex(0)
    
    def get_settings_parameters(self):
        return {
            'laser_wavelength': self.laser_wavelength_input.text(),
            'monochromator_upper': self.monochromator_upper_input.text(),
            'monochromator_lower': self.monochromator_lower_input.text(),
            'step': self.step_input.text(),
            'direction': self.direction_combo.currentText()
        }
    
    def get_line_positions(self):
        return self.time_plot.get_line_positions()
    
    def set_time_data(self, x_data, y_data):
        self.time_plot.set_data(x_data, y_data)
    
    def set_spectrum_data(self, x_data, y_data):
        self.spectrum_plot.set_data(x_data, y_data)
    
    def switch_tab(self, index):
        self.current_tab = index
        self.content_stack.setCurrentIndex(index)
        
        for i in range(3):
            btn = self.menu.layout().itemAt(i).widget()
            if i == index:
                btn.setStyleSheet(self.get_active_tab_style())
            else:
                btn.setStyleSheet(self.get_inactive_tab_style())
    
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
    
    def update_panel(self):
        if self.theme == "light":
            self.panel.setStyleSheet("background-color: lightblue;")
        else:
            self.panel.setStyleSheet("background-color: #404040; color: white;")
        
        if hasattr(self, 'title_label'):
            self.title_label.setText("Обнаружение ИК-люминесценции веществ" if self.language == "russian" else "Detection of IR-luminescence of substances")
        
        buttons = []
        for i in range(3):
            button = self.panel.layout().itemAt(self.panel.layout().count() - 3 + i).widget()
            buttons.append(button)
            if self.theme == "light":
                button.setStyleSheet("background-color: lightskyblue;")
            else:
                button.setStyleSheet("background-color: #606060; color: white;")
    
    def update_menu(self):
        layout = self.menu.layout()
        
        tabs_text = ["Настройка", "Обработка", "Визуализация"] if self.language == "russian" else ["Setting", "Processing", "Visualization"]
        for i in range(3):
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
        self.settings_tab.findChild(QGroupBox).setTitle("Параметры эксперимента" if self.language == "russian" else "Experiment Parameters")
        self.laser_wavelength_label.setText("Длина волны лазера (нм):" if self.language == "russian" else "Laser wavelength (nm):")
        self.monochromator_upper_label.setText("Верхняя длина волны монохроматора (нм):" if self.language == "russian" else "Monochromator upper wavelength (nm):")
        self.monochromator_lower_label.setText("Нижняя длина волны монохроматора (нм):" if self.language == "russian" else "Monochromator lower wavelength (nm):")
        self.step_label.setText("Шаг монохроматора (нм):" if self.language == "russian" else "Monochromator step (nm):")
        self.direction_label.setText("Направление сканирования:" if self.language == "russian" else "Scanning direction:")
        self.reset_btn.setText("Сброс параметров" if self.language == "russian" else "Reset parameters")
        
        if self.language == "russian":
            self.direction_combo.clear()
            self.direction_combo.addItems(["Сверху вниз", "Снизу вверх"])
        else:
            self.direction_combo.clear()
            self.direction_combo.addItems(["From top to bottom", "From bottom to top"])
    
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
            self.mouse_pos = event.globalPos()
            self.window_pos = self.pos()
            self.window_size = self.size()
            pos = event.pos()
            width = self.width()
            height = self.height()
            
            if pos.y() <= 40:
                self.dragging = True
                return
            
            self.resize_dir = None
            if pos.x() <= self.margin and pos.y() <= self.margin:
                self.resize_dir = 'top_left'
            elif pos.x() >= width - self.margin and pos.y() <= self.margin:
                self.resize_dir = 'top_right'
            elif pos.x() <= self.margin and pos.y() >= height - self.margin:
                self.resize_dir = 'bottom_left'
            elif pos.x() >= width - self.margin and pos.y() >= height - self.margin:
                self.resize_dir = 'bottom_right'
            elif pos.x() <= self.margin:
                self.resize_dir = 'left'
            elif pos.x() >= width - self.margin:
                self.resize_dir = 'right'
            elif pos.y() <= self.margin:
                self.resize_dir = 'top'
            elif pos.y() >= height - self.margin:
                self.resize_dir = 'bottom'
    
    def mouseMoveEvent(self, event):
        pos = event.pos()
        width = self.width()
        height = self.height()
        
        if hasattr(self, 'dragging') and self.dragging:
            delta = event.globalPos() - self.mouse_pos
            self.move(self.window_pos + delta)
        elif hasattr(self, 'resize_dir') and self.resize_dir:
            delta = event.globalPos() - self.mouse_pos
            new_x = self.window_pos.x()
            new_y = self.window_pos.y()
            new_width = self.window_size.width()
            new_height = self.window_size.height()
            
            if self.resize_dir in ['left', 'top_left', 'bottom_left']:
                new_x = self.window_pos.x() + delta.x()
                new_width = self.window_size.width() - delta.x()
            elif self.resize_dir in ['right', 'top_right', 'bottom_right']:
                new_width = self.window_size.width() + delta.x()
            
            if self.resize_dir in ['top', 'top_left', 'top_right']:
                new_y = self.window_pos.y() + delta.y()
                new_height = self.window_size.height() - delta.y()
            elif self.resize_dir in ['bottom', 'bottom_left', 'bottom_right']:
                new_height = self.window_size.height() + delta.y()
            
            min_size = self.minimumSize()
            if new_width >= min_size.width() and new_height >= min_size.height():
                self.move(new_x, new_y)
                self.resize(new_width, new_height)
        else:
            if pos.y() <= 40:
                self.setCursor(QCursor(Qt.ArrowCursor))
            elif pos.x() <= self.margin and pos.y() <= self.margin:
                self.setCursor(QCursor(Qt.SizeFDiagCursor))
            elif pos.x() >= width - self.margin and pos.y() <= self.margin:
                self.setCursor(QCursor(Qt.SizeBDiagCursor))
            elif pos.x() <= self.margin and pos.y() >= height - self.margin:
                self.setCursor(QCursor(Qt.SizeBDiagCursor))
            elif pos.x() >= width - self.margin and pos.y() >= height - self.margin:
                self.setCursor(QCursor(Qt.SizeFDiagCursor))
            elif pos.x() <= self.margin:
                self.setCursor(QCursor(Qt.SizeHorCursor))
            elif pos.x() >= width - self.margin:
                self.setCursor(QCursor(Qt.SizeHorCursor))
            elif pos.y() <= self.margin:
                self.setCursor(QCursor(Qt.SizeVerCursor))
            elif pos.y() >= height - self.margin:
                self.setCursor(QCursor(Qt.SizeVerCursor))
            else:
                self.setCursor(QCursor(Qt.ArrowCursor))
    
    def mouseReleaseEvent(self, event):
        if hasattr(self, 'dragging'):
            delattr(self, 'dragging')
        if hasattr(self, 'resize_dir'):
            delattr(self, 'resize_dir')
        if hasattr(self, 'mouse_pos'):
            delattr(self, 'mouse_pos')
    
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

        button_1 = QPushButton("🗕")
        button_1.setFixedSize(20, 20)
        button_1.clicked.connect(self.showMinimized)

        button_2 = QPushButton("🗖")
        button_2.setFixedSize(20, 20)
        button_2.clicked.connect(self.toggle_maximize)

        button_3 = QPushButton("🗙")
        button_3.setFixedSize(20, 20)
        button_3.clicked.connect(self.close)

        if self.theme == "light":
            control_style = "background-color: lightskyblue;"
        else:
            control_style = "background-color: #606060; color: white;"
        
        button_1.setStyleSheet(control_style)
        button_2.setStyleSheet(control_style)
        button_3.setStyleSheet(control_style)
        
        layout.addWidget(button_1)
        layout.addWidget(button_2)
        layout.addWidget(button_3)

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

        tabs_text = ["Настройка", "Обработка", "Визуализация"] if self.language == "russian" else ["Setting", "Processing", "Visualization"]
        for i, text in enumerate(tabs_text):
            button = QPushButton(text)
            button.setFixedSize(110, 18)
            button.clicked.connect(lambda checked, idx=i: self.switch_tab(idx))
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
