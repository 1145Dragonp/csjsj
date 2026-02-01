import os
from PyQt5.QtWidgets import (QSystemTrayIcon, QMenu, QAction, QStyle, QApplication)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

class SystemTrayManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.voice_enabled = main_window.settings_manager.get('voice_enabled', 1) == 1
        
        self.tray_icon = QSystemTrayIcon(main_window)
        if os.path.exists('icon.ico'):
            self.tray_icon.setIcon(QIcon('icon.ico'))
        else:
            self.tray_icon.setIcon(main_window.style().standardIcon(QStyle.SP_ComputerIcon))
        
        self.create_menu()
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_activated)

    def create_menu(self):
        tray_menu = QMenu()
        
        # 关于（新增）
        about_action = QAction("关于", self.main_window)
        about_action.triggered.connect(self.main_window.open_about)
        tray_menu.addAction(about_action)

        # 设置
        settings_action = QAction("⚙️ 设置", self.main_window)
        settings_action.triggered.connect(self.main_window.open_settings)
        tray_menu.addAction(settings_action)

        # 退出
        tray_menu.addSeparator()
        quit_action = QAction("退出", self.main_window)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)

    def on_activated(self, reason):
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self.main_window.showNormal()
            self.main_window.activateWindow()

    def show_message(self, title, message):
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 2000)

    def quit_application(self):
        """完全退出应用"""
        self.tray_icon.hide()
        QApplication.instance().quit()
