import sys
import os
import ctypes

# ========== 企业级路径保险方案 ==========
# 获取当前脚本所在目录并强制插入到sys.path最前面
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
# =========================================

from PyQt5.QtWidgets import QApplication
from cte import RedstoneCalculator

def main():
    # Windows任务栏图标修复
    if os.name == 'nt':
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Redstone.Calculator.1.0')
        except:
            pass

    # PyQt5插件路径处理
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

