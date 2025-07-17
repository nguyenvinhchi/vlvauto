import os
import shutil
import sys
import cv2
import pytesseract
import win32gui
from PIL import Image, ImageDraw, ImageFont

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QThread, Qt, pyqtSignal, QTimer, pyqtSlot, QMetaObject, QSettings

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QHBoxLayout
)

from app.detect_game_widget import get_window_screenshot_by_handle
from app.detection_worker import DetectionWorker
from app.get_game_window import find_window_by_title
from app.log_factory import create_logger
from app.resource_util import resource_path
from app.send_window_event import focus_window, simulate_click, simulate_mouse_move_around, simulate_tab

LOGGER = create_logger(name='MainWindow')
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\chinv\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

def get_exe_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(".")

def get_bundled_data_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'data')
    return os.path.join(get_exe_dir(), 'data')

def ensure_data_dir_exists():
    exe_dir = get_exe_dir()
    target_data_dir = os.path.join(exe_dir, 'data')

    if not os.path.exists(target_data_dir):
        print("📁 First-time run: copying bundled data...")
        bundled_data_dir = get_bundled_data_path()
        shutil.copytree(bundled_data_dir, target_data_dir)
        print(f"✅ Data directory created at: {target_data_dir}")
    else:
        print(f"📂 Data directory already exists at: {target_data_dir}")

    return target_data_dir

class DraggableButton(QPushButton):
    def mousePressEvent(self, event):
        self.parent().mousePressEvent(event)
        super().mousePressEvent(event)  # ensure button still registers click

    def mouseMoveEvent(self, event):
        self.parent().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.parent().mouseReleaseEvent(event)
        super().mouseReleaseEvent(event)  # finalize button click

def get_mumu_child_windows(parent_hwnd):
    child_handles = {}
    def callback(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        print(f"Child HWND: {hwnd}, Title: {title}")
        child_handles[title] = hwnd
        return True

    win32gui.EnumChildWindows(parent_hwnd, callback, None)
    return child_handles

def extract_title_from_top(img_np, crop_height=50):
    h = img_np.shape[0]
    top_crop = img_np[0:crop_height, :, :]
    pil_img = Image.fromarray(top_crop)
    text = pytesseract.image_to_string(pil_img, config='--psm 7')
    return text.strip()

def extract_text_relative(img_np, rel_top=0.011, rel_left=0.1, rel_width=0.1, rel_height=0.05):
    """
    Extract text from a region defined by relative coordinates.

    :param img_np: Full screenshot (numpy array)
    :param rel_top: Top offset as a fraction of image height
    :param rel_left: Left offset as a fraction of image width
    :param rel_width: Width as a fraction of image width
    :param rel_height: Height as a fraction of image height
    :return: Extracted text string
    """
    h, w = img_np.shape[:2]
    top = int(rel_top * h)
    left = int(rel_left * w)
    height = int(rel_height * h)
    width = int(rel_width * w)

    crop = img_np[top:top+height, left:left+width]

    # Optional: Convert to grayscale + threshold for better OCR
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    # Step 3: Invert
    inverted = cv2.bitwise_not(gray)
    # Step 4: Optional - threshold to sharpen contrast
    #  Adaptive Thresholding
    binary = cv2.adaptiveThreshold(
        inverted,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )
    # Step 5: Resize (Tesseract performs better on larger text)
    scale = 2.5
    enlarged = cv2.resize(binary, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)

    # Step 6: Optional denoise (preserve edges)
    denoised = cv2.medianBlur(enlarged, 3)
    cv2.imwrite("data/screenshot/test.png", denoised)

    pil_img = Image.fromarray(denoised)
    text = pytesseract.image_to_string(pil_img, config='--psm 7')  # Assume single line of text
    return text.strip()

def sanitize_filename(text):
    return "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in text)


WINDOW_W = 80
WINDOW_H = 50

class AutoMainWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.running = False
        self._drag_pos = None  # For dragging window
        self.settings = QSettings("data/config.ini", QSettings.Format.IniFormat)
        self.init_ui()


    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(WINDOW_W, WINDOW_H)

        central_widget = QWidget(self)
        central_widget.setObjectName("central_widget")
        central_widget.setStyleSheet("#central_widget { background-color: transparent; }")
        layout = QHBoxLayout(self)

        self.start_button = DraggableButton(" ▶️ ", self)
        self.start_button.clicked.connect(self.on_start)
        layout.addWidget(self.start_button)

        self.exit_button = DraggableButton("❌", self)
        self.exit_button.clicked.connect(self.close)
        layout.addWidget(self.exit_button)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.apply_dark_theme()
        self.setup_tray_icon()
        self.setWindowTitle("VLV Auto")
        self.setMouseTracking(True)

        central_widget.mousePressEvent = self.child_mousePressEvent
        central_widget.mouseMoveEvent = self.child_mouseMoveEvent
        central_widget.mouseReleaseEvent = self.child_mouseReleaseEvent

    def on_start(self):
        LOGGER.info("Start button clicked")
        # print('nemudisplay')
        print('MuMuPlayer')
        # # Create white image
        # img = Image.new('RGB', (400, 100), color='white')
        # draw = ImageDraw.Draw(img)

        # # Optional: Use a system font
        # try:
        #     font = ImageFont.truetype("arial.ttf", 36)  # Windows default font
        # except:
        #     font = ImageFont.load_default()

        # # Draw black text
        # draw.text((10, 30), "Test OCR Text", fill='black', font=font)

        # # Save (optional)
        # img.save("test_ocr.png")

        # # OCR it
        # text = pytesseract.image_to_string(img, config='--psm 7')
        # print(f"🔤 OCR result: '{text}'")
        
        window_title = 'A1-tl0-nm1'
        mumu_hwnd = find_window_by_title(window_title)
        print(f'player window handle: {mumu_hwnd}')
        child_handles = get_mumu_child_windows(mumu_hwnd)
        nemu_hwnd = child_handles['MuMuPlayer']
        focus_window(nemu_hwnd)
        for i in range(1):
            print(f"\n🔁 Tab {i + 1}:")
            simulate_tab()
            screenshot = get_window_screenshot_by_handle(nemu_hwnd)
            # Extract name using OCR
            tab_title = extract_text_relative(screenshot)
            filename_base = sanitize_filename(tab_title) or f"tab_{i+1}"
            filename = os.path.join("data/screenshot", f"{filename_base}.png")
            Image.fromarray(screenshot).save(filename)
            print(f"✅ Saved: {filename}")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def child_mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def child_mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def child_mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()

    def closeEvent(self, event):
        LOGGER.info("Closing window...")
        QApplication.quit()
        LOGGER.info("App exit")


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


if __name__ == "__main__":
    ensure_data_dir_exists()
    app = QApplication(sys.argv)
    window = AutoMainWindow()
    window.show()
    sys.exit(app.exec())
