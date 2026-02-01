import sys
import os
import random
import subprocess
import ctypes  # 用于修复任务栏图标
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLineEdit, 
                             QVBoxLayout, QWidget, QProgressBar, QLabel, QMessageBox, 
                             QGridLayout, QDialog, QSystemTrayIcon, QMenu, QAction, 
                             QSlider, QStyle, QWidgetAction)
from PyQt5.QtCore import QTimer, Qt, QUrl
from PyQt5.QtGui import QIcon, QGuiApplication, QDesktopServices

class RedstoneCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.expression = ""
        self.second_input = False
        self.initUI()
        self.initTray()  # 初始化托盘

    def initUI(self):
        self.setWindowTitle("赤石计算机")
        self.setGeometry(100, 100, 400, 400)
        
        # --- 设置窗口图标 ---
        if os.path.exists('icon.ico'):
            self.setWindowIcon(QIcon('icon.ico'))
        
        self.center()

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.input_field = QLineEdit(self)
        self.input_field.setReadOnly(True)
        self.input_field.setAlignment(Qt.AlignRight)
        self.input_field.setStyleSheet("font-size: 24pt; padding: 5px;")
        self.input_field.setFixedHeight(50)
        main_layout.addWidget(self.input_field)

        self.createButtonGrid(main_layout)

    def createButtonGrid(self, parent_layout):
        button_grid = QGridLayout()
        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            'C', '0', '=', '+'
        ]
        positions = [(i, j) for i in range(4) for j in range(4)]
        
        for position, name in zip(positions, buttons):
            button = QPushButton(name)
            button.setFixedSize(80, 80)
            button.setStyleSheet("font-size: 18pt;")
            button.clicked.connect(self.buttonClicked)
            button_grid.addWidget(button, *position)

        parent_layout.addLayout(button_grid)

    def initTray(self):
        """初始化系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # --- 设置托盘图标 ---
        if os.path.exists('icon.ico'):
            self.tray_icon.setIcon(QIcon('icon.ico'))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        tray_menu = QMenu()

        # 1. 语音播报开关
        self.voice_action = QAction("🔊 语音播报: 开启", self, checkable=True, checked=True)
        self.voice_action.triggered.connect(self.toggleVoice)
        tray_menu.addAction(self.voice_action)

        # 2. 透明度设置
        opacity_menu = QMenu("调整透明度", self)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(1, 10)
        self.opacity_slider.setValue(int(self.windowOpacity() * 10))
        self.opacity_slider.valueChanged.connect(self.changeOpacity)
        
        slider_action = QWidgetAction(self)
        slider_action.setDefaultWidget(self.opacity_slider)
        opacity_menu.addAction(slider_action)
        tray_menu.addMenu(opacity_menu)

        # 3. 关于
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.openAboutLink)
        tray_menu.addAction(about_action)

        # 4. 退出
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.trayIconActivated)

    def toggleVoice(self, checked):
        """切换语音开关状态"""
        if checked:
            self.voice_action.setText("🔊 语音播报: 开启")
            self.speak("语音播报已开启")
        else:
            self.voice_action.setText("🔇 语音播报: 关闭")
            self.speak("语音播报已关闭")

    def speak(self, text):
        """使用 Windows PowerShell 调用系统语音播报"""
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
        """改变窗口透明度"""
        opacity = value / 10.0
        self.setWindowOpacity(opacity)
        self.speak(f"透明度{int(opacity * 100)}")

    def openAboutLink(self):
        """打开关于链接"""
        url = QUrl("https://github.com/1145Dragonp/")
        QDesktopServices.openUrl(url)
        self.speak("正在打开关于页面")

    def trayIconActivated(self, reason):
        """处理托盘图标点击事件"""
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self.showNormal()
            self.activateWindow()

    def buttonClicked(self):
        sender = self.sender()
        text = sender.text()
        
        if text == 'C':
            self.expression = ""
            self.input_field.setText("")
            self.second_input = False
            self.speak("清空")
        elif text == '=':
            self.calculate()
            self.speak("等于")
        else:
            if self.second_input:
                if text in ['+', '-', '*', '/']:
                    if self.input_field.text():
                        self.expression = self.input_field.text() + text
                else:
                    self.expression = text
                self.second_input = False
            else:
                self.expression += text
            self.input_field.setText(self.expression)
            self.speak(text)

    def calculate(self):
        if not self.expression:
            return

        self.progress_dialog = QDialog(self)
        self.progress_dialog.setWindowTitle("计算进度")
        self.progress_dialog.setFixedSize(300, 100)
        self.progress_dialog.setWindowModality(Qt.ApplicationModal)
        
        # 为进度条对话框也设置相同的图标
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
        self.expression = ""
        self.second_input = True
        QTimer.singleShot(500, self.progress_dialog.close)
        self.speak(f"结果是{self.result}")

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
        """重写关闭事件，点击关闭按钮时隐藏到托盘而不是退出"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage("赤石计算机", "程序已最小化到系统托盘", QSystemTrayIcon.Information, 2000)

def main():
    # === 修复 Windows 任务栏图标 ===
    if os.name == 'nt':
        try:
            myappid = 'Redstone.Calculator.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass

    # === 修复 Qt 插件路径 ===
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