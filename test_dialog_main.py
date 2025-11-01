import os
import sys
from PyQt6.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QListWidget, QTextEdit, QMessageBox,
    QWidget, QFileDialog, QApplication, QGridLayout
)
from PyQt6.QtCore import QSize, QTimer

# --- External Dependencies ---
# These are required for window and screenshot functions
import pygetwindow as gw
import pyautogui
from datetime import datetime
from PIL import Image

from app.ocr.ocr_util import detect_map_name
from app.v3.window_util import WindowUtil


class ImageSelectDialog(QDialog):
    def __init__(self, parent, image_path, on_point_selected): 
        super().__init__(parent)
        self.setWindowTitle("Image Selection Mock")
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel(f"Mock Dialog for image: {os.path.basename(image_path)}"))
        QTimer.singleShot(100, self.accept) 

# --- NEW: OCR Utility Import ---
from app.flow_layout import FlowLayout
from app.log_factory import create_logger

# --- Setup ---img/maps/PhuongTuong/VLV-A2-20251017_222733.png
TMP_DIR = "data/tmp/"
os.makedirs(TMP_DIR, exist_ok=True)
LOGGER = create_logger(name='TestDialog')

class TestDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test scenario - Map OCR")
        self.resize(600, 400)

        self.test_actions = [
            'IN_TOWN', 'BAG_OPEN', 'SHOP_OPEN', 'AUTO_OFF', 'LOGIN_SCREEN_1',
            'LOGIN_SCREEN_2', 'LOGIN_SCREEN_3', 'LOGIN_WARN', 'SERVER_CONNECT_WARN',
            'READ_TEXT_FROM_IMG'
        ]

        self.selected_scenario = None
        self.pattern_name_input = QLineEdit(self)
        self.pattern_name_input.setPlaceholderText("Enter pattern name or window title filter (e.g., VLV-A2)")
        
        # 1. Initialize the button
        self.test_button = QPushButton('Test OCR')
        
        # 2. Assign an object name and connect the signal
        self.test_button.setObjectName('test_button')
        self.test_button.setEnabled(False)
        self.test_button.clicked.connect(self.on_test)

        # 3. Apply the Style Sheet for highlight/gray state
        self.test_button.setStyleSheet("""
            /* Style for the ENABLED state (Highlight) */
            QPushButton#test_button:enabled {
                background-color: #4CAF50; /* Vibrant Green */
                color: #FFFFFF;
                border: 2px solid #388E3C;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
            }
            /* Style for the DISABLED state (Grayed out) */
            QPushButton#test_button:disabled {
                background-color: #555555; /* Darker Gray */
                color: #AAAAAA; /* Gray text */
                border: 1px solid #777777;
                padding: 10px;
                border-radius: 8px;
            }
        """)

        self.window_list = QListWidget(self)
        self.scenario_list = QListWidget(self)
        for item in self.scenarios:
            self.scenario_list.addItem(item)

        self.capture_button = QPushButton("Capture Image", self)
        self.capture_button.setEnabled(False)
        self.capture_button.clicked.connect(self.capture_window_image)

        self.window_list.itemSelectionChanged.connect(self.on_window_selected)
        self.scenario_list.itemSelectionChanged.connect(self.on_scenario_selected)

        self.point_output = QTextEdit(self)
        self.point_output.setReadOnly(True)
        self.point_output.setPlaceholderText("Detected map name will appear here after 'Test OCR'.")

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
        button_flow.addWidget(self.select_image_button)
        button_flow.addWidget(self.change_image_button)

        layout = QVBoxLayout()
        list_layout = QHBoxLayout()

        window_list_layout = QVBoxLayout()
        window_list_layout.addWidget(self.window_list)
        window_list_layout.addWidget(self.capture_button)
        window_list_layout.addWidget(self.refresh_button)
        list_layout.addLayout(window_list_layout)

        scenario_layout = QVBoxLayout()
        scenario_layout.addWidget(self.scenario_list)
        scenario_layout.addWidget(self.test_button)
        list_layout.addLayout(scenario_layout)

        layout.addLayout(list_layout)

        layout.addWidget(self.pattern_name_input)
        layout.addWidget(button_container)
        layout.addWidget(QLabel("OCR Output / Captured Points:"))
        layout.addWidget(self.point_output)

        self.setLayout(layout)

        self.selected_window = None
        self.image_path = None
        self.pattern_points = []

        self.populate_window_list()

    def populate_window_list(self):
        self.window_list.clear()
        title_filter = self.pattern_name_input.text().strip().lower()
        
        try:
            for win in gw.getAllTitles():
                if win.strip() and (title_filter in win.lower()):
                    self.window_list.addItem(win)
        except Exception as e:
            LOGGER.info(f"Error listing windows: {e}")
        
        if not self.window_list.count():
             self.window_list.addItem("No windows found. Try running Mumu Player.")

    def on_test(self):
        """
        Runs the OCR detection on the latest captured image and reports the result.
        """
        if not self.image_path:
            QMessageBox.warning(self, "Image Missing", "Please capture a window image first.")
            return

        self.point_output.clear()
        self.point_output.append(f"Running OCR detection on: {os.path.basename(self.image_path)}...")
        
        # Call the OCR utility function
        detected_text = detect_map_name(self.image_path, LOGGER)
        
        if detected_text and not detected_text.startswith("OCR_ERROR"):
            result_message = f"Detected Map Name: '{detected_text}'"
            self.point_output.append("--- RESULT ---")
            self.point_output.append(result_message)
            QMessageBox.information(self, "OCR Test Result", result_message)
        else:
            error_message = f"Detection Failed: {detected_text}"
            self.point_output.append(error_message)
            QMessageBox.critical(self, "OCR Test Failed", error_message)
            
        LOGGER.info(f'Test {self.selected_scenario} on window {self.selected_window} result: {detected_text}')

    def on_window_selected(self):
        selected_items = self.window_list.selectedItems()
        if selected_items:
            self.selected_window = selected_items[0].text()
            self.capture_button.setEnabled(True)
            # Enable Test button if a window is selected AND an image is already available
            self.test_button.setEnabled(self.selected_window is not None and self.image_path is not None)

    def on_scenario_selected(self):
        selected_items = self.scenario_list.selectedItems()
        if selected_items:
            self.selected_scenario = selected_items[0].text()
            # Test button is enabled based on image and window selection
            self.test_button.setEnabled(self.selected_window is not None and self.image_path is not None)


    def capture_window_image(self):
        windows = WindowUtil.find_game_windows(self.selected_window)
        if not windows:
            QMessageBox.warning(self, "Window Not Found", f"Could not find window titled: {self.selected_window}")
            return
        
        win = windows[0]
        try:
            win.activate()
            pyautogui.sleep(1)

            screenshot = WindowUtil.screen_shot(win)
            if not screenshot:
                QMessageBox.critical(self, "Capture Error", "Failed to capture screenshot.")
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            scenario_part = self.selected_scenario if self.selected_scenario else "Capture"
            file_name = f"{scenario_part}-{timestamp}.png"
            self.image_path = os.path.join(TMP_DIR, file_name)
            screenshot.save(self.image_path, format="PNG")

            self.select_image_button.setEnabled(True)
            # Enable Test button now that an image is available
            self.test_button.setEnabled(self.selected_window is not None and self.image_path is not None)

            QMessageBox.information(self, "Capture Done", f"Window image saved to {self.image_path}. Ready for OCR Test.")
        except Exception as e:
            QMessageBox.critical(self, "Capture/Window Error", f"An error occurred during capture: {e}")


    def show_select_image_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Select image file",
            directory="data/img/maps/PhuongTuong",
            filter="Image Files (*.png *.jpg *.bmp *.jpeg)"
        )

        if file_path:
            LOGGER.info(f"Selected image: {file_path}")
            self.image_path = file_path
            self.test_button.setEnabled(self.image_path is not None)
        else:
            LOGGER.info("No file selected.")

    def select_points_on_image(self):
        if not self.image_path:
            QMessageBox.warning(self, "No Image", "Please capture an image first.")
            return

        def on_point_selected(pos, color):
            x, y = pos
            r, g, b = color
            self.pattern_points.append((*pos, *color))
            self.point_output.append(f"Point: {x,y} | Color: {r,g,b}")

        dialog = ImageSelectDialog(parent=self, image_path=self.image_path, on_point_selected=on_point_selected)
        dialog.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    dialog = TestDialog()
    dialog.exec()
