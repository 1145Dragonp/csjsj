import sys
import os
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLineEdit, 
                             QVBoxLayout, QWidget, QProgressBar, QLabel, QMessageBox, 
                             QGridLayout, QDialog)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon, QGuiApplication

class RedstoneCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.expression = ""
        self.second_input = False  # 标志是否是第二次输入
        self.initUI()

    def initUI(self):
        self.setWindowTitle("赤石计算机")
        self.setGeometry(100, 100, 400, 400)
        
        # --- 设置窗口图标 ---
        # 检查同级目录下是否有 icon.ico 文件
        if os.path.exists('icon.ico'):
            self.setWindowIcon(QIcon('icon.ico'))
        
        self.center()

        # 中央部件和主布局
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 输入框
        self.input_field = QLineEdit(self)
        self.input_field.setReadOnly(True)
        self.input_field.setAlignment(Qt.AlignRight)
        self.input_field.setStyleSheet("font-size: 24pt; padding: 5px;")
        self.input_field.setFixedHeight(50)
        main_layout.addWidget(self.input_field)

        # 按钮网格
        self.createButtonGrid(main_layout)

    def createButtonGrid(self, parent_layout):
        """创建计算器按钮网格"""
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

    def buttonClicked(self):
        sender = self.sender()
        text = sender.text()
        
        if text == 'C':
            self.expression = ""
            self.input_field.setText("")
            self.second_input = False
            
        elif text == '=':
            self.calculate()
            
        else:
            if self.second_input:
                # 修复逻辑：如果刚出结果，且按的是运算符
                if text in ['+', '-', '*', '/']:
                    # 保留刚才的结果作为左值
                    if self.input_field.text():
                        self.expression = self.input_field.text() + text
                else:
                    # 如果按的是数字，则覆盖清零
                    self.expression = text
                self.second_input = False
            else:
                self.expression += text
                
            self.input_field.setText(self.expression)

    def calculate(self):
        if not self.expression:
            return

        # 创建并配置进度对话框
        self.progress_dialog = QDialog(self)
        self.progress_dialog.setWindowTitle("计算进度")
        self.progress_dialog.setFixedSize(300, 100)
        self.progress_dialog.setWindowModality(Qt.ApplicationModal)
        
        # --- 为进度条对话框也设置相同的图标 ---
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

        # 启动进度条
        self.update_progress()

    def center_dialog(self, dialog):
        """将对话框居中显示在屏幕中央"""
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - dialog.width()) // 2
        y = (screen_geometry.height() - dialog.height()) // 2
        dialog.move(x, y)

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
            # 安全计算
            result = eval(self.expression)
            result += random.randint(1, 3)
            
            if result > 250:
                self.progress_bar.setValue(50)
                self.status_label.setText("算力不足")
                QMessageBox.warning(self, "警告", "算力不够")
                self.progress_dialog.close()
                return

            self.result = result
            self.finalize_calculation()
            
        except SyntaxError:
            self.handle_calculation_error("无效的表达式")
        except Exception as e:
            self.handle_calculation_error(f"计算错误: {str(e)}")

    def finalize_calculation(self):
        """完成计算后的UI更新"""
        self.progress_bar.setValue(100)
        self.status_label.setText("计算完成")
        self.input_field.setText(str(self.result))
        self.expression = ""
        self.second_input = True
        # 延迟关闭，给用户一点视觉反馈时间
        QTimer.singleShot(500, self.progress_dialog.close)

    def handle_calculation_error(self, message):
        """处理计算错误"""
        self.status_label.setText("错误")
        self.progress_bar.setVisible(False)
        QMessageBox.warning(self, "错误", message)
        self.progress_dialog.close()

    def center(self):
        """将主窗口居中"""
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def keyPressEvent(self, event):
        key = event.key()
        text = event.text()

        key_map = {
            Qt.Key_Enter: self.calculate,
            Qt.Key_Return: self.calculate,
            Qt.Key_Equal: self.calculate,
            Qt.Key_C: self.clear_input,
        }

        if key in key_map:
            key_map[key]()
        elif text in '0123456789+-*/':
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

    def clear_input(self):
        self.expression = ""
        self.input_field.setText("")
        self.second_input = False

def main():
    # --- 关键修复：自动定位 Qt 插件路径 ---
    if getattr(sys, 'frozen', False):
        qt_dir = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt5', 'plugins')
    else:
        import PyQt5
        qt_dir = os.path.join(os.path.dirname(PyQt5.__file__), 'Qt5', 'plugins')
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_dir

    app = QApplication(sys.argv)
    calculator = RedstoneCalculator()
    calculator.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()