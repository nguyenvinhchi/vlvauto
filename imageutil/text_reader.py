import cv2
import numpy as np

import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
class HSVColorPickerApp:
    def __init__(self, root, in_file: str, out_file: str):
        self.root = root
        self.root.title("HSV Color Picker Tool")

        # Default HSV bounds
        # self.lower = [40, 40, 40]
        # self.upper = [90, 255, 255]

        # stuck Duong Chau town detect words
        # self.lower = [53, 53, 8]
        # self.upper = [71, 255, 255]

        #stuck shop detect buttons
        # self.lower = [19, 0, 0]
        # self.upper = [45, 75, 135]

        # green text reading
        self.lower = [38, 206, 0]
        self.upper = [94, 255, 165]

        self.image_path = in_file
        self.out_file = out_file
        self.image = cv2.imread(self.image_path)
        self.hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        # Get image dimensions
        height, width = self.image.shape[:2]

        # Canvas to show result
        self.canvas = tk.Canvas(root, width=width, height=height)
        self.canvas.pack()

        # Sliders frame
        self.slider_frame = tk.Frame(root)
        self.slider_frame.pack()

        # Create sliders
        self.sliders = {}
        for i, label in enumerate(["H_low", "S_low", "V_low", "H_high", "S_high", "V_high"]):
            var = tk.IntVar(value=self.lower[i] if i < 3 else self.upper[i - 3])
            scale = tk.Scale(self.slider_frame, from_=0, to=255, orient=tk.HORIZONTAL,
                             label=label, variable=var, command=self.update_preview)
            scale.grid(row=i // 3, column=i % 3, padx=5, pady=5)
            self.sliders[label] = var

        # Save button
        self.save_button = tk.Button(root, text="💾 Save Template", command=self.save_result)
        self.save_button.pack(pady=10)

        self.filtered_image = None  # Will hold the final processed image
        self.update_preview()

    def update_preview(self, *_):
        # Get current slider values
        self.lower = [self.sliders["H_low"].get(),
                      self.sliders["S_low"].get(),
                      self.sliders["V_low"].get()]
        self.upper = [self.sliders["H_high"].get(),
                      self.sliders["S_high"].get(),
                      self.sliders["V_high"].get()]

        # Create mask & highlighted result
        mask = cv2.inRange(self.hsv, np.array(self.lower), np.array(self.upper))
        mask_inv = cv2.bitwise_not(mask)

        # dark = (self.image * 0.2).astype(np.uint8)
        # result = cv2.bitwise_and(self.image, self.image, mask=mask) + \
        #          cv2.bitwise_and(dark, dark, mask=mask_inv)
        
        black_bg = np.zeros_like(self.image)
        result = cv2.bitwise_and(self.image, self.image, mask=mask) + \
                 cv2.bitwise_and(black_bg, black_bg, mask=mask_inv)


        self.filtered_image = result  # Save result for saving to file

        # Convert to ImageTk format
        result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(result_rgb)
        image_tk = ImageTk.PhotoImage(image_pil)

        self.canvas.image = image_tk  # Prevent GC
        self.canvas.create_image(0, 0, anchor=tk.NW, image=image_tk)

    def save_result(self):
        if self.filtered_image is not None:
            cv2.imwrite(self.out_file, self.filtered_image)
            print(f"✅ Saved to {self.out_file}")
            

