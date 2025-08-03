import os
from PyQt6.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout,
    QLineEdit, QListWidget, QTextEdit, QMessageBox,
    QWidget, QFileDialog, QApplication
)


import pygetwindow as gw
import pyautogui
from datetime import datetime

from app.flow_layout import FlowLayout
from app.pattern.image_select_dialog import ImageSelectDialog
from app.v2.window_util import WindowUtil

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
        windows = WindowUtil.find_game_windows(self.selected_window)
        if not windows:
            return
        win = windows[0]
        win.activate()
        pyautogui.sleep(1)  # wait for window to activate

        screenshot = WindowUtil.screen_shot(win)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.image_path = os.path.join(TMP_DIR, f"{self.selected_window}-{timestamp}.png")
        screenshot.save(self.image_path, format="PNG")

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
            x, y = pos
            r, g, b = color
            self.pattern_points.append((*pos, *color))
            self.point_output.append(f"{x,y,r,g,b}")

        dialog = ImageSelectDialog(parent=self, image_path=self.image_path, on_point_selected=on_point_selected)
        dialog.exec()
