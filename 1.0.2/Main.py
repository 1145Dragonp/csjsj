import sys
import os
import random
import subprocess
import ctypes
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLineEdit, 
                             QVBoxLayout, QHBoxLayout, QWidget, QProgressBar, QLabel, QMessageBox, 
                             QGridLayout, QDialog, QSystemTrayIcon, QMenu, QAction, 
                             QSlider, QStyle, QWidgetAction)
from PyQt5.QtCore import QTimer, Qt, QUrl
from PyQt5.QtGui import QIcon, QGuiApplication, QDesktopServices

class RedstoneCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.expression = ""
        self.second_input = False
        self.saved_values = []
        self.pending_command = None
        self.has_result = False
        self.waiting_for_f = False
        
        self.initUI()
        self.initTray()

    def initUI(self):
        self.setWindowTitle("赤石计算机")
        self.setGeometry(100, 100, 400, 500) 
        
        if os.path.exists('icon.ico'):
            self.setWindowIcon(QIcon('icon.ico'))
        
        self.center()
        
        # --- 初始化 F 标签 ---
        self.f_label = QLabel("")
        self.f_label.setStyleSheet("color: gray; font-size: 14pt; font-weight: bold;")
        self.f_label.setFixedWidth(40)
        
        # --- 加载数据 ---
        self.load_saved_values()

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- 输入框区域 ---
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.f_label)
        self.input_field = QLineEdit(self)
        self.input_field.setReadOnly(True)
        self.input_field.setAlignment(Qt.AlignRight)
        self.input_field.setStyleSheet("font-size: 24pt; padding: 5px;")
        self.input_field.setFixedHeight(50)
        input_layout.addWidget(self.input_field)
        main_layout.addLayout(input_layout)

        # --- 创建5x4键盘布局 ---
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
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists('icon.ico'):
            self.tray_icon.setIcon(QIcon('icon.ico'))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        tray_menu = QMenu()

        self.voice_action = QAction("🔊 语音播报: 开启", self, checkable=True, checked=True)
        self.voice_action.triggered.connect(self.toggleVoice)
        tray_menu.addAction(self.voice_action)

        opacity_menu = QMenu("调整透明度", self)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(1, 10)
        self.opacity_slider.setValue(int(self.windowOpacity() * 10))
        self.opacity_slider.valueChanged.connect(self.changeOpacity)
        slider_action = QWidgetAction(self)
        slider_action.setDefaultWidget(self.opacity_slider)
        opacity_menu.addAction(slider_action)
        tray_menu.addMenu(opacity_menu)

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.openAboutLink)
        tray_menu.addAction(about_action)

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.trayIconActivated)

    def toggleVoice(self, checked):
        if checked:
            self.voice_action.setText("🔊 语音播报: 开启")
            self.speak("语音播报已开启")
        else:
            self.voice_action.setText("🔇 语音播报: 关闭")
            self.speak("语音播报已关闭")

    def speak(self, text):
        if self.voice_action.isChecked() and text:
            cmd = ['PowerShell', '-Command', 
                   f'Add-Type -AssemblyName System.Speech; '
                   f'$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                   f'$s.Speak("{text}")']
            try:
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                pass

    def changeOpacity(self, value):
        opacity = value / 10.0
        self.setWindowOpacity(opacity)
        self.speak(f"透明度{int(opacity * 100)}")

    def openAboutLink(self):
        url = QUrl("https://www.example.com")
        QDesktopServices.openUrl(url)
        self.speak("正在打开关于页面")

    def trayIconActivated(self, reason):
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self.showNormal()
            self.activateWindow()

    def buttonClicked(self):
        sender = self.sender()
        text = sender.text()

        # --- 处理 C 键 ---
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

        # --- 处理 = 键 ---
        elif text == '=':
            self.calculate()
            self.waiting_for_f = False
            return

        # --- 处理 F- 键 ---
        elif text == 'F-':
            self.pending_command = 'F-'
            self.speak("准备删除")
            return
        
        # --- 处理退格键 ---
        elif text == '⌫':
            self.backspace()
            return

        # --- 处理数字键 (0-9) ---
        if text.isdigit():
            # 如果处于 F- 删除模式
            if self.pending_command == 'F-':
                index = int(text)
                self.delete_value(index)
                self.pending_command = None
                return

            # 如果处于 F 调用模式 (等待调用)
            if self.pending_command == 'F':
                index = int(text)
                self.recall_value(index)
                self.pending_command = None
                self.waiting_for_f = False
                return

            # 正常输入逻辑
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

        # --- 处理 . 键 ---
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

        # --- 处理运算符 (+, -, ×, /) ---
        elif text in ['+', '-', '×', '/']:
            # 关键点：按下运算符，激活等待F状态
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
            
            # 播报运算符
            op_text = text
            if op_text == '×': speak_text = "乘"
            elif op_text == '/': speak_text = "除"
            else: speak_text = op_text
            self.speak(speak_text)
            return

        # --- 处理 F 键 (修复点：去掉了 not self.has_result 的限制) ---
        elif text == 'F':
            # 如果处于等待F的状态，进入调用模式
            if self.waiting_for_f:
                self.pending_command = 'F'
                self.speak("准备调用")
            # 否则，执行保存
            else:
                # 修复：只要输入框里有内容，不管是不是刚算完的结果，都允许保存
                if self.input_field.text(): 
                    self.save_current_value()
            return 

    def translateOp(self, text):
        op_map = {'×': '*', '/': '/', '+': '+', '-': '-'} 
        return op_map.get(text, text)

    def recall_value(self, index):
        if 1 <= index <= len(self.saved_values):
            value = self.saved_values[index - 1]
            value_str = str(value)
            
            # 直接拼接到表达式
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

    def save_values(self):
        try:
            with open('saved_data', 'w', encoding='utf-8') as f:
                for value in self.saved_values:
                    f.write(str(value) + '\n')
        except Exception as e:
            print(f"保存失败: {e}")

    def load_saved_values(self):
        try:
            if os.path.exists('saved_data.'):
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
        event.ignore()
        self.hide()
        self.tray_icon.showMessage("赤石计算机", "程序已最小化到系统托盘", QSystemTrayIcon.Information, 2000)

    def backspace(self):
        if self.expression and not self.has_result:
            self.expression = self.expression[:-1]
            self.input_field.setText(self.expression)

def main():
    if os.name == 'nt':
        try:
            myappid = 'Redstone.Calculator.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass

    if getattr(sys, 'frozen', False):
        qt_dir = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt5', 'plugins')
    else:
        import PyQt5
        qt_dir = os.path.join(os.path.dirname(PyQt5.__file__), 'Qt5', 'plugins')
    
    if os.path.exists(qt_dir):
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_dir

    app = QApplication(sys.argv)
    calculator = RedstoneCalculator()
    calculator.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()