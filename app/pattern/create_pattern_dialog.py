import os
from PyQt6.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout,
    QLineEdit, QListWidget, QTextEdit, QMessageBox,
    QWidget, QFileDialog
)

import pygetwindow as gw
import pyautogui
from datetime import datetime
from PyQt6.QtGui import QGuiApplication

from app.flow_layout import FlowLayout
from app.pattern.image_select_dialog import ImageSelectDialog

TMP_DIR = "data/tmp"
os.makedirs(TMP_DIR, exist_ok=True)

class PatternCreatorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pattern Creator")
        self.resize(300, 200)

        self.pattern_name_input = QLineEdit(self)
        self.pattern_name_input.setPlaceholderText("Enter pattern name or window title filter")

        self.window_list = QListWidget(self)

        self.capture_button = QPushButton("Capture Image", self)
        self.capture_button.setEnabled(False)
        self.capture_button.clicked.connect(self.capture_window_image)

        self.window_list.itemSelectionChanged.connect(self.on_window_selected)

        self.point_output = QTextEdit(self)
        self.point_output.setReadOnly(True)

        self.select_image_button = QPushButton("Select Points", self)
        self.select_image_button.setEnabled(False)
        self.select_image_button.clicked.connect(self.select_points_on_image)

        self.refresh_button = QPushButton("Refresh Window List", self)
        self.refresh_button.clicked.connect(self.populate_window_list)

        self.change_image_button = QPushButton("Select existing image", self)
        self.change_image_button.clicked.connect(self.show_select_image_dialog)

        # Flow layout for buttons
        button_container = QWidget(self)
        button_flow = FlowLayout(button_container)
        button_flow.addWidget(self.refresh_button)
        button_flow.addWidget(self.capture_button)
        button_flow.addWidget(self.select_image_button)
        button_flow.addWidget(self.change_image_button)

        layout = QVBoxLayout()
        layout.addWidget(self.pattern_name_input)
        layout.addWidget(self.window_list)
        layout.addWidget(button_container)
        layout.addWidget(QLabel("Captured Points (pos + RGB):"))
        layout.addWidget(self.point_output)

        self.setLayout(layout)

        self.selected_window = None
        self.image_path = None
        self.pattern_points = []

        self.populate_window_list()

    def populate_window_list(self):
        self.window_list.clear()
        title_filter = self.pattern_name_input.text().strip().lower()
        for win in gw.getAllTitles():
            if win.strip() and (title_filter in win.lower()):
                self.window_list.addItem(win)

    def on_window_selected(self):
        selected_items = self.window_list.selectedItems()
        if selected_items:
            self.selected_window = selected_items[0].text()
            self.capture_button.setEnabled(True)

    def capture_window_image(self):
        win = gw.getWindowsWithTitle(self.selected_window)[0]
        win.activate()
        pyautogui.sleep(1)  # wait for window to activate

        # left, top, width, height = win.left, win.top, win.width, win.height
        # print(f'window capturing size: {width}x{height}')
        # img = pyautogui.screenshot(region=(left, top, width, height))

        # # Adjust for custom DPI (e.g. 108)
        # actual_dpi = 108  # <-- set this based on your observation
        # dpi_scale = actual_dpi / 96

        # if dpi_scale != 1.0:
        #     new_size = (int(width / dpi_scale), int(height / dpi_scale))
        #     img = img.resize(new_size, Image.Resampling.LANCZOS)

        hwnd = win._hWnd  # HWND handle of the window
        screen = QGuiApplication.primaryScreen()
        if not screen:
            QMessageBox.critical(self, "Error", "No screen found.")
            return

        qt_pixmap = screen.grabWindow(hwnd)  # This grabs just the window region
        if qt_pixmap.isNull():
            QMessageBox.critical(self, "Error", "Failed to capture window image.")
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.image_path = os.path.join(TMP_DIR, f"{timestamp}.png")
        print(qt_pixmap.size())
        qt_pixmap.save(self.image_path, "PNG")

        self.select_image_button.setEnabled(True)
        QMessageBox.information(self, "Capture Done", f"Window image saved to {self.image_path}")

    def show_select_image_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Select image file",
            directory="data/",
            filter="Image Files (*.png *.jpg *.bmp *.jpeg)"
        )

        if file_path:
            print("Selected image:", file_path)
            self.image_path = file_path
        else:
            print("No file selected.")

    def select_points_on_image(self):
        if not self.image_path:
            QMessageBox.warning(self, "No Image", "Please capture an image first.")
            return

        def on_point_selected(pos, color):
            self.pattern_points.append((pos, color))
            self.point_output.append(f"{pos} RGB{color}")

        dialog = ImageSelectDialog(parent=self, image_path=self.image_path, on_point_selected=on_point_selected)
        dialog.exec()

    # def closeEvent(self, event):
    #     event.accept()
    #     self.deleteLater()  # optional cleanup
    #     print('Closing creat pattern dialog')

