import sys
import os

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog, QLabel, QSizePolicy, QDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QEventLoop
from PyQt6.QtGui import QPainter, QPen, QGuiApplication, QColor, QPixmap

from imageutil.image_transform import TransformColorDialog
from imageutil.screen_capture_overlay import ScreenCaptureOverlay

class ScreenCaptureWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Capture Tool")
        self.setGeometry(50, 50, 150, 90)
        # self.resize(800, 600)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        # self.setFixedSize(200, 170)

        self.temp_img_path = 'tmp/captured.png'
        self.status_text = "capture tool"

        self.origin_image = None
        self.transformed_image = None
        
        self.transform_lower_color = [38, 206, 0]
        self.transform_upper_color = [94, 255, 165]

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        capture_button = QPushButton("📸 Capture", self)
        capture_button.clicked.connect(self.on_capture_image)

        preview_button = QPushButton("Preview", self)
        preview_button.clicked.connect(self.show_preview)

        transform_button = QPushButton("Convert color", self)
        transform_button.clicked.connect(self.show_transform_color)
        layout.addWidget(capture_button)
        layout.addWidget(preview_button)
        layout.addWidget(transform_button)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.offset)

    def on_capture_image(self):
        overlay = ScreenCaptureOverlay()
        self.show_widget(overlay)

    def show_widget(self, widget: QWidget):
        widget.show()
        
        # Use a nested event loop until the window is closed
        loop = QEventLoop()
        widget.destroyed.connect(loop.quit)
        loop.exec()
        print("Widget loop exited.")

    def show_preview(self):
        if not os.path.exists(self.temp_img_path):
            QMessageBox.warning(self, "Image Not Found", f"The image file was not found:\n{self.temp_img_path}")
            return
        pixmap = QPixmap(self.temp_img_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Error", f"Failed to load image:\n{self.temp_img_path}")
            return

        # Create a dialog to show the image
        dialog = QDialog(self)
        dialog.setWindowTitle("Preview Captured Image")

        label = QLabel()
        label.setPixmap(pixmap)
        label.resize(pixmap.size())  # Keep original size

        layout = QVBoxLayout(dialog)
        layout.addWidget(label)
        dialog.setLayout(layout)
        dialog.resize(pixmap.width(), pixmap.height())
        dialog.exec()

    def show_transform_color(self):
        if not os.path.exists(self.temp_img_path):
            QMessageBox.warning(self, "Image Not Found", f"Image not found:\n{self.temp_img_path}")
            return

        dialog = TransformColorDialog(
            image_path=self.temp_img_path,
            lower=self.transform_lower_color,
            upper=self.transform_upper_color,
            save_path='tmp/filtered.png',
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save updated HSV range if needed
            self.lower = dialog.lower
            self.transform_upper_color = dialog.upper
            QMessageBox.information(self, "Saved", "Filtered image saved to tmp/filtered.png")


    def on_save_image(self):
        # Step 1: Let user choose the save directory
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Save Screenshot")
        if not folder_path:
            return  # User canceled
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScreenCaptureWindow()
    window.show()
    sys.exit(app.exec())
