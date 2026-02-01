import sys
import os
import random
import subprocess

# ========== 路径保险方案 ==========
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# ====================================

from PyQt5.QtWidgets import (QMainWindow, QPushButton, QLineEdit, 
                             QVBoxLayout, QHBoxLayout, QWidget, QProgressBar, 
                             QLabel, QMessageBox, QGridLayout, QDialog, QSlider,
                             QApplication)
from PyQt5.QtCore import QTimer, Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QIcon, QGuiApplication, QDesktopServices
from settings_window import SettingsManager, SettingsWindow

class RedstoneCalculator(QMainWindow):
    voice_toggled = pyqtSignal(bool)
    opacity_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.expression = ""
        self.second_input = False
        self.saved_values = []
        self.pending_command = None
        self.has_result = False
        self.waiting_for_f = False
        
        # 初始化设置管理器
        self.settings_manager = SettingsManager()
        
        self.initUI()
        self.initTray()
        self.apply_settings()

    def initUI(self):
        self.setWindowTitle("赤石计算机")
        self.setGeometry(100, 100, 400, 500)
        
        if os.path.exists('icon.ico'):
            self.setWindowIcon(QIcon('icon.ico'))
        
        self.center()
        
        self.f_label = QLabel("")
        self.f_label.setStyleSheet("color: gray; font-size: 14pt; font-weight: bold;")
        self.f_label.setFixedWidth(40)
        
        self.load_saved_values()

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.f_label)
        self.input_field = QLineEdit(self)
        self.input_field.setReadOnly(True)
        self.input_field.setAlignment(Qt.AlignRight)
        self.input_field.setStyleSheet("font-size: 24pt; padding: 5px;")
        self.input_field.setFixedHeight(50)
        input_layout.addWidget(self.input_field)
        main_layout.addLayout(input_layout)

        self.createButtonGrid(main_layout)

    def createButtonGrid(self, parent_layout):
        button_grid = QGridLayout()
        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '×',  
            '1', '2', '3', '-',
            '0', '.', '=', '+',
            'F', 'F-', '⌫', 'C'
        ]
        positions = [(i, j) for i in range(5) for j in range(4)]
        
        for position, name in zip(positions, buttons):
            button = QPushButton(name)
            button.setFixedSize(80, 60)
            button.setStyleSheet("font-size: 18pt;")
            button.clicked.connect(self.buttonClicked)
            button_grid.addWidget(button, *position)

        parent_layout.addLayout(button_grid)

    def initTray(self):
        from sp import SystemTrayManager
        self.tray_manager = SystemTrayManager(self)
        self.spt = self.settings_manager.get('spt', 0)

    def apply_settings(self):
        """应用保存的设置（静默模式）"""
        opacity = self.settings_manager.get('opacity', 10)
        self.set_opacity(opacity, silent=True)
        
        voice_enabled = self.settings_manager.get('voice_enabled', 1) == 1
        if hasattr(self, 'tray_manager'):
            self.tray_manager.voice_enabled = voice_enabled

    def buttonClicked(self):
        sender = self.sender()
        text = sender.text()

        # 清空
        if text == 'C':
            if self.pending_command == 'F-':
                self.clear_all_values()
                self.pending_command = None
            else:
                self.expression = ""
                self.input_field.setText("")
                self.second_input = False
                self.has_result = False
                self.waiting_for_f = False
                self.speak("清空")
            return

        # 计算结果
        elif text == '=':
            self.calculate()
            self.waiting_for_f = False
            return

        # 删除模式
        elif text == 'F-':
            self.pending_command = 'F-'
            self.speak("准备删除")
            return
        
        # 退格
        elif text == '⌫':
            self.backspace()
            return

        # 数字键
        if text.isdigit():
            if self.pending_command == 'F-':
                index = int(text)
                self.delete_value(index)
                self.pending_command = None
                return

            if self.pending_command == 'F':
                index = int(text)
                self.recall_value(index)
                self.pending_command = None
                self.waiting_for_f = False
                return

            if self.has_result:
                self.expression = text
                self.has_result = False
            else:
                if self.second_input:
                    self.expression = text
                    self.second_input = False
                else:
                    self.expression += text
            self.input_field.setText(self.expression)
            self.speak(text)
            self.waiting_for_f = False
            return

        # 小数点
        elif text == '.':
            if self.has_result:
                self.expression = "0."
                self.has_result = False
            else:
                if self.second_input:
                    self.expression = "0."
                    self.second_input = False
                else:
                    if '.' not in self.expression.split()[-1]:
                        self.expression += '.'
            self.input_field.setText(self.expression)
            self.speak("点")
            self.waiting_for_f = False

        # 运算符
        elif text in ['+', '-', '×', '/']:
            self.waiting_for_f = True
            
            op = self.translateOp(text)
            if self.has_result:
                self.expression = self.input_field.text() + op
                self.has_result = False
            elif self.second_input:
                self.expression = self.input_field.text() + op
            else:
                self.expression += op
            self.input_field.setText(self.expression)
            self.second_input = False
            
            op_text = text
            if op_text == '×': speak_text = "乘"
            elif op_text == '/': speak_text = "除"
            else: speak_text = op_text
            self.speak(speak_text)
            return

        # F功能键
        elif text == 'F':
            if self.waiting_for_f:
                self.pending_command = 'F'
                self.speak("准备调用")
            else:
                if self.input_field.text(): 
                    self.save_current_value()
            return 

    

    def open_settings(self):
        """打开设置窗口（从托盘调用）"""
        from settings_window import SettingsWindow
        
        self.settings_window = SettingsWindow(self.settings_manager, self)
        self.settings_window.settings_saved.connect(self.on_settings_saved)
        self.settings_window.exec_()

    def open_about(self):
        """打开关于网页"""
        url = QUrl("https://www.example.com")  # 替换为您的网页地址
        QDesktopServices.openUrl(url)
        self.speak("正在打开关于页面")

    def on_settings_saved(self, new_settings):
        """设置保存回调"""
        self.apply_settings()
        self.spt = new_settings.get('spt', 0)
        
        if hasattr(self, 'tray_manager'):
            self.tray_manager.voice_enabled = (new_settings.get('voice_enabled', 1) == 1)

    def translateOp(self, text):
        op_map = {'×': '*', '/': '/', '+': '+', '-': '-'} 
        return op_map.get(text, text)

    def recall_value(self, index):
        if 1 <= index <= len(self.saved_values):
            value = self.saved_values[index - 1]
            value_str = str(value)
            self.expression += value_str
            self.input_field.setText(self.expression)
            self.speak(f"调出数值{index}")
        else:
            QMessageBox.warning(self, "错误", f"没有保存第 {index} 个数值")

    def delete_value(self, index):
        if 1 <= index <= len(self.saved_values):
            removed = self.saved_values.pop(index - 1)
            self.save_values()
            self.update_f_label()
            self.speak(f"删除数值{index}")
        else:
            QMessageBox.warning(self, "错误", f"无法删除第 {index} 个数值")

    def clear_all_values(self):
        self.saved_values.clear()
        self.save_values()
        self.update_f_label()
        self.speak("全部清除")

    def save_current_value(self):
        try:
            value_str = self.input_field.text()
            if value_str: 
                if '.' in value_str:
                    value = float(value_str)
                else:
                    value = int(value_str)
                self.saved_values.append(value)
                self.save_values()
                self.update_f_label()
                self.speak(f"已保存为F{len(self.saved_values)}")
        except:
            pass

    def update_f_label(self):
        count = len(self.saved_values)
        if count > 0:
            self.f_label.setText(f"F{count}")
        else:
            self.f_label.setText("")

    def speak(self, text):
        if hasattr(self, 'tray_manager') and self.tray_manager.voice_enabled and text:
            cmd = ['PowerShell', '-Command', 
                   f'Add-Type -AssemblyName System.Speech; '
                   f'$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                   f'$s.Speak("{text}")']
            try:
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                pass

    def save_values(self):
        try:
            with open('saved_data', 'w', encoding='utf-8') as f:
                for value in self.saved_values:
                    f.write(str(value) + '\n')
        except Exception as e:
            print(f"保存失败: {e}")

    def load_saved_values(self):
        try:
            if os.path.exists('saved_data'):
                with open('saved_data', 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    self.saved_values = []
                    for line in lines:
                        line = line.strip()
                        if line:
                            try:
                                if '.' in line:
                                    self.saved_values.append(float(line))
                                else:
                                    self.saved_values.append(int(line))
                            except:
                                pass
            self.update_f_label()
        except Exception as e:
            print(f"读取失败: {e}")
            self.saved_values = []
            self.update_f_label()

    def calculate(self):
        if not self.expression:
            return

        self.progress_dialog = QDialog(self)
        self.progress_dialog.setWindowTitle("计算进度")
        self.progress_dialog.setFixedSize(300, 100)
        self.progress_dialog.setWindowModality(Qt.ApplicationModal)
        
        if os.path.exists('icon.ico'):
            self.progress_dialog.setWindowIcon(QIcon('icon.ico'))

        dialog_layout = QVBoxLayout()
        self.status_label = QLabel("正在导入中", self.progress_dialog)
        self.status_label.setAlignment(Qt.AlignCenter)
        dialog_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar(self.progress_dialog)
        dialog_layout.addWidget(self.progress_bar)
        self.progress_bar.setValue(0)

        self.progress_dialog.setLayout(dialog_layout)
        self.center_dialog(self.progress_dialog)
        self.progress_dialog.show()

        self.update_progress()

    def update_progress(self):
        self.status_label.setText("正在处理中")
        self.progress_value = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.increment_progress)
        self.timer.start(100)

    def increment_progress(self):
        self.progress_value += 10
        self.progress_bar.setValue(self.progress_value)
        if self.progress_value >= 100:
            self.timer.stop()
            self.process_step()

    def process_step(self):
        try:
            result = eval(self.expression)
            result += random.randint(1, 3)
            if result > 250:
                self.progress_bar.setValue(50)
                self.status_label.setText("算力不足")
                QMessageBox.warning(self, "警告", "算力不够")
                self.progress_dialog.close()
                self.speak("算力不够")
                return
            self.result = result
            self.finalize_calculation()
        except:
            self.handle_calculation_error("计算错误")

    def finalize_calculation(self):
        self.progress_bar.setValue(100)
        self.status_label.setText("计算完成")
        self.input_field.setText(str(self.result))
        
        self.has_result = True
        self.expression = str(self.result)
        self.waiting_for_f = False
        
        self.speak(f"等于 {self.result}")
        
        QTimer.singleShot(500, self.progress_dialog.close)

    def handle_calculation_error(self, message):
        self.status_label.setText("错误")
        self.progress_bar.setVisible(False)
        QMessageBox.warning(self, "错误", message)
        self.progress_dialog.close()
        self.speak("计算出错")

    def center_dialog(self, dialog):
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - dialog.width()) // 2
        y = (screen_geometry.height() - dialog.height()) // 2
        dialog.move(x, y)

    def center(self):
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def closeEvent(self, event):
        if event:
            event.ignore()
            self.hide()
            # 根据spt值决定是否提示
            if hasattr(self, 'tray_manager') and self.spt == 1:
                self.tray_manager.show_message("赤石计算机", "程序已最小化到系统托盘")

    def backspace(self):
        if self.expression and not self.has_result:
            self.expression = self.expression[:-1]
            self.input_field.setText(self.expression)

    def set_opacity(self, value, silent=False):
        opacity = value / 10.0
        self.setWindowOpacity(opacity)
        if not silent:
            self.speak(f"透明度{int(opacity * 100)}")

    def toggle_voice(self, checked):
        if hasattr(self, 'tray_manager'):
            self.tray_manager.voice_enabled = checked
            self.voice_toggled.emit(checked)
            self.speak("语音播报已开启" if checked else "语音播报已关闭")






