

import os
from PyQt6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QTextEdit, QGridLayout,
    QMessageBox, QSizePolicy, QScrollArea, QApplication
)
from PyQt6.QtGui import QPixmap, QMouseEvent, QPen, QPainter
from PyQt6.QtCore import Qt, QRect
import cv2
from PIL import Image

TMP_DIR = "data/tmp"
os.makedirs(TMP_DIR, exist_ok=True)


class ImageSelectRectDialog(QDialog):
    """
    A dialog open image file as input path then user can select rectangle
    Return tuple of rectangle with coordinate relative to the origin image size. 
    """
    def __init__(self, parent, image_path, on_selected):
        super().__init__(parent)
        self.setWindowTitle("Select Image Region")
        self.image_path = image_path
        self.on_selected = on_selected
        self.points = []
        self.select_color = Qt.GlobalColor.blue
        self.first = None
        self.second = None
        self.temp_rect = None
        self.selected_rect = None
        self.origin_pixmap = QPixmap(image_path)
        self.image_size = self.origin_pixmap.size()
            
        self.image_holder = QLabel(self)
        # Set fixed size and policies
        self.image_holder.setPixmap(self.origin_pixmap)
        
        self.image_holder.setScaledContents(False)
        self.image_holder.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.image_holder.setFixedSize(self.image_size) # Use setFixedSize as you did initially
        self.image_holder.adjustSize() # Force size hint update
        self.image_holder.mousePressEvent = self.on_mouse_click
        self.image_holder.mouseMoveEvent = self.on_mouse_move
        self.image_holder.mouseReleaseEvent = self.on_mouse_release # Added release for better UX

        # Wrap label in a scroll area so dialog is still usable if image is large
        scroll = QScrollArea()
        scroll.setWidget(self.image_holder)
        scroll.setWidgetResizable(False)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.status = QTextEdit()
        self.status.setPlainText('Status: Click and drag to select region')
        self.status.setReadOnly(True)
        self.status.setFixedHeight(60)  # fixed height prevents layout stretching

        layout = QGridLayout()
        layout.addWidget(scroll, 0, 0)
        layout.addWidget(self.status, 1, 0)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 0)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        self.setLayout(layout)

        # Optionally size dialog to image or constrain it
        self.resize(self.image_size.width() + 40, self.image_size.height() + 100)

    def draw_rect(self, first, second):
        if first is None or second is None:
            return

        # --- FIX 4: Draw on a copy of the ORIGINAL pixmap (always use original) ---
        pixmap_copy = self.origin_pixmap.copy()
        painter = QPainter(pixmap_copy)
        pen = QPen(self.select_color, 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)

        rect = QRect(first, second).normalized() # normalized ensures x/y/w/h are positive

        painter.drawRect(rect)
        painter.end()

        # Update label display
        self.image_holder.setPixmap(pixmap_copy)
        self.temp_rect = rect

    def on_mouse_move(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton and self.first is not None:
            # Only draw while the left button is pressed (dragging)
            self.draw_rect(self.first, event.pos())

    def on_mouse_click(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Start of a drag operation
            self.first = event.pos()
            self.second = None
            self.status.setPlainText(f'Selecting region from: ({self.first.x()}, {self.first.y()})')

    def on_mouse_release(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.first is not None:
            # End of the drag operation
            self.second = event.pos()
            
            # Finalize the drawn rectangle
            final_rect = QRect(self.first, self.second).normalized()
            
            # Revert to a clean pixmap and draw the final rect
            self.draw_rect(final_rect.topLeft(), final_rect.bottomRight()) 
            
            # The coordinates in final_rect are already relative to the image
            x = final_rect.x()
            y = final_rect.y()
            w = final_rect.width()
            h = final_rect.height()
            
            self.selected_rect = (x, y, w, h)
            self.status.setPlainText(f'Region selected (x, y, w, h): ({x}, {y}, {w}, {h})')
            # img_w = self.image_size.width
            # img_h = self.image_size.height
            self.on_selected(self.selected_rect, (self.image_size.width(), self.image_size.height())) # Inform the parent
            # self.on_selected(self.selected_rect, (img_w, img_h)) # Inform the parent
            
            # Reset points for next selection
            self.first = None
            self.second = None
            
        elif event.button() == Qt.MouseButton.LeftButton:
             # Just a single click without a drag
             self.status.setPlainText('Status: Click and drag to select region')