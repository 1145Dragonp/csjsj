import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QSlider, QCheckBox, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

# ==================== 设置管理器 ====================
class SettingsManager:
    def __init__(self, filename='set.txt'):
        self.filename = filename
        self.defaults = {
            'spt': 0,           # 托盘提示开关
            'voice_enabled': 1, # 语音播报
            'opacity': 10       # 透明度(1-10)
        }
        self.settings = self.load_settings()

    def load_settings(self):
        """从set.txt加载设置，不存在则创建"""
        if not os.path.exists(self.filename):
            self.save_settings(self.defaults)
            return self.defaults.copy()
        
        settings = self.defaults.copy()
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        if key in settings:
                            settings[key] = int(value)
        except Exception as e:
            print(f"加载设置失败: {e}")
            return self.defaults.copy()
        
        return settings

    def save_settings(self, settings=None):
        """保存设置到set.txt"""
        if settings is None:
            settings = self.settings
        
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write("# 赤石计算机设置文件\n")
                f.write("# spt: 托盘提示开关 (0=关闭, 1=开启)\n")
                f.write("# voice_enabled: 语音播报 (0=关闭, 1=开启)\n")
                f.write("# opacity: 窗口透明度 (1-10)\n\n")
                
                for key, value in settings.items():
                    f.write(f"{key}={value}\n")
        except Exception as e:
            print(f"保存设置失败: {e}")

    def get(self, key, default=None):
        """获取设置值"""
        return self.settings.get(key, default)

    def set(self, key, value):
        """修改设置值"""
        if key in self.settings:
            self.settings[key] = value
            self.save_settings()


# ==================== 设置窗口 ====================
class SettingsWindow(QDialog):
    settings_saved = pyqtSignal(dict)
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.initUI()
        self.load_current_settings()

    def initUI(self):
        self.setWindowTitle("赤石设置")
        self.setFixedSize(400, 300)
        
        if os.path.exists('icon.ico'):
            self.setWindowIcon(QIcon('icon.ico'))
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 语音播报
        voice_layout = QHBoxLayout()
        voice_label = QLabel("语音播报:")
        self.voice_checkbox = QCheckBox("启用")
        voice_layout.addWidget(voice_label)
        voice_layout.addStretch()
        voice_layout.addWidget(self.voice_checkbox)
        layout.addLayout(voice_layout)

        # 透明度
        opacity_layout = QVBoxLayout()
        opacity_header = QHBoxLayout()
        opacity_label = QLabel("窗口透明度:")
        self.opacity_value_label = QLabel("100%")
        opacity_header.addWidget(opacity_label)
        opacity_header.addStretch()
        opacity_header.addWidget(self.opacity_value_label)
        opacity_layout.addLayout(opacity_header)
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(1, 10)
        self.opacity_slider.setTickPosition(QSlider.TicksBelow)
        self.opacity_slider.setTickInterval(1)
        self.opacity_slider.valueChanged.connect(self.on_opacity_change)
        opacity_layout.addWidget(self.opacity_slider)
        layout.addLayout(opacity_layout)

        # 托盘提示
        spt_layout = QHBoxLayout()
        spt_label = QLabel("托盘提示:")
        self.spt_checkbox = QCheckBox("最小化时显示提示")
        spt_layout.addWidget(spt_label)
        spt_layout.addStretch()
        spt_layout.addWidget(self.spt_checkbox)
        layout.addLayout(spt_layout)

        # 分隔线
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #ccc;")
        layout.addWidget(line)

        # 按钮
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self.save_and_close)
        save_btn.setStyleSheet("font-size: 14pt; padding: 10px;")
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.close)
        cancel_btn.setStyleSheet("font-size: 14pt; padding: 10px;")
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def load_current_settings(self):
        voice_enabled = self.settings_manager.get('voice_enabled', 1) == 1
        self.voice_checkbox.setChecked(voice_enabled)
        
        opacity = self.settings_manager.get('opacity', 10)
        self.opacity_slider.setValue(opacity)
        self.on_opacity_change(opacity)
        
        spt = self.settings_manager.get('spt', 0) == 1
        self.spt_checkbox.setChecked(spt)

    def on_opacity_change(self, value):
        self.opacity_value_label.setText(f"{value*10}%")

    def save_and_close(self):
        new_settings = {
            'voice_enabled': 1 if self.voice_checkbox.isChecked() else 0,
            'opacity': self.opacity_slider.value(),
            'spt': 1 if self.spt_checkbox.isChecked() else 0
        }
        
        self.settings_manager.settings = new_settings
        self.settings_manager.save_settings()
        self.settings_saved.emit(new_settings)
        self.close()
