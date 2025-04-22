# screen_capture_util.py
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(1)  # or try (2)

import tkinter as tk
import mss
import numpy as np
import cv2
import time
import win32api

def get_true_screen_resolution():
    width = win32api.GetSystemMetrics(0)
    height = win32api.GetSystemMetrics(1)
    return width, height

def start_capture_rectangle():
    CaptureTool().run()

class CaptureTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide initially
        self.root.attributes("-alpha", 0.3)
        self.root.attributes("-topmost", True)
        # self.root.attributes("-fullscreen", True)
        self.root.overrideredirect(True)
        self.root.configure(bg='black')

        # Defer canvas setup until fullscreen is properly applied
        self.root.after(200, self.setup_fullscreen)

        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.start_x = self.start_y = 0
        self.rect = None

    def setup_fullscreen(self):
        screen_width, screen_height = get_true_screen_resolution()
        # screen_width = self.root.winfo_screenwidth()
        # screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.deiconify()  # Show the window now

        self.canvas = tk.Canvas(self.root, cursor="cross", bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.update_idletasks()  # <-- force layout recalculation

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)


    def screen_to_canvas_coords(self, x_root, y_root):
        # Convert absolute screen position to canvas-relative
        return (
            x_root - self.root.winfo_rootx(),
            y_root - self.root.winfo_rooty()
        )

    def on_mouse_down(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root

        cx, cy = self.screen_to_canvas_coords(event.x_root, event.y_root)
        self.rect = self.canvas.create_rectangle(cx, cy, cx, cy, outline='red', width=2)

    def on_mouse_drag(self, event):
        cx1, cy1 = self.screen_to_canvas_coords(self.start_x, self.start_y)
        cx2, cy2 = self.screen_to_canvas_coords(event.x_root, event.y_root)
        self.canvas.coords(self.rect, cx1, cy1, cx2, cy2)

    def on_mouse_up(self, event):
        end_x = event.x_root
        end_y = event.y_root

        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        print(f'x1, y1: {x1},{y1}, x2, y2: {x2}, {y2}')
        w = abs(int(x2 - x1))
        h = abs(int(y2 - y1))

        self.capture_area(int(x1), int(y1), w, h)
        self.root.destroy()

    def capture_area(self, x, y, width, height):
        print(f"📸 Capturing area: ({x}, {y}, {width}, {height})")
        with mss.mss() as sct:
            monitor = {"left": x, "top": y,  "width": width, "height": height}
            screenshot = np.array(sct.grab(monitor))

            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            # gray2 = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            # lab = cv2.cvtColor(screenshot, cv2.COLOR_BGR2LAB)
            # hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)

            cv2.imwrite("app/images/captured/test_truecolor.png", screenshot)
            # cv2.imwrite("app/images/captured/test_gray.png", gray2)
            # cv2.imwrite("app/images/captured/test_lab_L.png", lab[:, :, 0])
            # cv2.imwrite("app/images/captured/test_hsv_V.png", hsv[:, :, 2])

            filename = f"app/images/captured/captured_template_{int(time.time())}.png"
            pattern = "vlv-close-button"
            filename = f"app/images/captured/{pattern}_{int(time.time())}.png"

            # cv2.imwrite(filename, screenshot)
            cv2.imwrite(filename, gray)
            print(f"✅ Saved as: {filename}")

    # @staticmethod
    # def get_window_screenshot(window):
    #     region = {
    #         "top": window.top,
    #         "left": window.left,
    #         "width": window.width,
    #         "height": window.height
    #     }
    #     return CaptureTool.get_screenshot(region)

    # @staticmethod
    # def get_screenshot(region):
    #     with mss.mss() as sct:
    #         return np.array(sct.grab(region))
    
    def run(self):
        self.root.mainloop()
