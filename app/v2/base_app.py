
import os
import shutil
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QHBoxLayout
)
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QPushButton
from PyQt6.QtGui import QIcon, QAction, QCursor
from PyQt6.QtCore import QThread, Qt, QTimer, pyqtSlot, QMetaObject, QSettings, QDateTime

from app.resource_util import resource_path


class BaseApp(QWidget):
    

    def setup_tray_icon(self):
        tray_icon = QSystemTrayIcon(QIcon(resource_path("app/images/vlvauto-icon.png")))
        tray_menu = QMenu()
        show_action = QAction("Show/Hide", self)
        show_action.triggered.connect(self.toggle_visibility)
        tray_menu.addAction(show_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.quit)
        exit_action.triggered.connect(self.close)

        tray_menu.addAction(exit_action)

        tray_icon.setContextMenu(tray_menu)
        tray_icon.setToolTip("Game Auto Tool")
        tray_icon.show()
        self.tray_icon = tray_icon

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(43, 43, 43, 220);
                color: #f0f0f0;
                font-family: Arial;
                font-size: 10pt;
                border-radius: 10px;
            }
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #5a5a5a;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
    @classmethod
    def get_exe_dir(cls):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.abspath(".")

    @classmethod
    def get_bundled_data_path(cls):
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, 'data')
        return os.path.join(BaseApp.get_exe_dir(), 'data')

    @classmethod
    def ensure_data_dir_exists(cls):
        exe_dir = BaseApp.get_exe_dir()
        target_data_dir = os.path.join(exe_dir, 'data')

        if not os.path.exists(target_data_dir):
            print("📁 First-time run: copying bundled data...")
            bundled_data_dir = BaseApp.get_bundled_data_path()
            shutil.copytree(bundled_data_dir, target_data_dir)
            print(f"✅ Data directory created at: {target_data_dir}")
        else:
            print(f"📂 Data directory already exists at: {target_data_dir}")

        return target_data_dir