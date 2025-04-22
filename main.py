import ctypes

from app.detect_game_widget import get_window_screenshot, write_image_for_human_check


# DPI aware
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# prevent display turn off while tool running:
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
ctypes.windll.kernel32.SetThreadExecutionState(
    ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
)

import time
import tkinter as tk

from app.game_scenario import StuckBuyingGameScenario, TownStuckGameScenario
from app.get_game_window import find_window

class AutoMainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Game Auto Tool")
        self.root.geometry("200x170+50+50")
        self.root.attributes('-topmost', True)
        self.root.resizable(False, False)
        self.game_windows = []
        self.game_scenarios = [
            StuckBuyingGameScenario(),
            TownStuckGameScenario()
        ]
        self.AUTO_DETECT_MS = 30_000
        self.scheduled = None
        self.running = False  # Track whether it's running
        self.status_text = "auto vltk"
        self.WINDOW_TITLE_PATTERN = "#N"

        self._setup_ui()
        self._create_status_overlay()
        self._make_draggable()

    def _setup_ui(self):
        self.frame = tk.Frame(self.root, bg="lightgray")
        self.frame.pack(expand=True, fill="both")

        self.label = tk.Label(self.frame, text="Game Tool", bg="lightgray", font=("Arial", 10))
        self.label.pack(pady=1)

        self.start_button = tk.Button(self.frame, text="Start", command=self.on_start)
        self.start_button.pack(pady=1)

        capture_button = tk.Button(self.frame, text="Capture Image", command=self.on_capture_image)
        capture_button.pack(pady=1)

    def _make_draggable(self):
        self.frame.bind("<Button-1>", self._start_move)
        self.frame.bind("<B1-Motion>", self._do_move)

    def _start_move(self, event):
        self.x = event.x
        self.y = event.y

    def _do_move(self, event):
        x = event.x_root - self.x
        y = event.y_root - self.y
        self.root.geometry(f"+{x}+{y}")

    def _create_status_overlay(self):
        self.status_overlay = tk.Toplevel(self.root)
        self.status_overlay.overrideredirect(True)
        self.status_overlay.attributes('-topmost', True)
        status_window_width = 500
        status_window_height = 40
         # Get screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        # Centered horizontally, bottom of the screen
        x = (screen_width // 2) - (status_window_width // 2)
        y = screen_height - status_window_height - 10  # 10px above bottom edge
        self.status_overlay.geometry(f"{status_window_width}x{status_window_height}+{x}+{y}")

        # Set a transparent background color
        transparent_color = "white"
        self.status_overlay.configure(bg=transparent_color)
        self.status_overlay.wm_attributes("-transparentcolor", transparent_color)

        # Label with no background, just text
        self.status_label = tk.Label(
            self.status_overlay,
            text="Initializing...",
            fg='lime',
            bg=transparent_color,
            font=('Consolas', 12, 'normal')
        )
        self.status_label.pack()

        self._update_status()

    def _update_status(self):
        x, y = self.root.winfo_pointerx(), self.root.winfo_pointery()
        self.status_label.config(text=f"Mouse: ({x}, {y}) | {self.status_text}")

        # Recalculate position on each update to account for resolution changes
        status_window_width = 500
        status_window_height = 40
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        new_x = (screen_width // 2) - (status_window_width // 2)
        new_y = screen_height - status_window_height - 10
        self.status_overlay.geometry(f"{status_window_width}x{status_window_height}+{new_x}+{new_y}")

        self.status_overlay.after(100, self._update_status)

    def on_start(self):
        self.running = not self.running
        if self.running:
            # print("✅ Automation started")
            # self.force_active_until = time.time() + self.DETECT_HUMAN_ACTIVITY_DELAY  # Ignore mouse move for 10 seconds
            self.status_text = "▶️ Running"
            self.start_button.config(text="⏸️")
            self.on_detect_window()
            self.schedule_detect()
            # self.check_mouse_activity()
        else:
            # print("⏸️ Automation paused")
            self.status_text = "⏸️ Stopped"
            self.start_button.config(text="▶️")
            if self.scheduled:
                self.root.after_cancel(self.scheduled)
                self.scheduled = None

    def schedule_detect(self):
        if self.running:
            self.on_detect_game_item_image()
            self.scheduled = self.root.after(self.AUTO_DETECT_MS, self.schedule_detect)
        

    def on_detect_window(self):
        self.game_windows = find_window(self.WINDOW_TITLE_PATTERN)

    def on_detect_game_item_image(self):
        for game_window in self.game_windows:
            screenshot = get_window_screenshot(game_window)
            # n = time.time()
            # write_image_for_human_check(f'images/test/{game_window.title}-{n}.png', screenshot)

            for game_scenario in self.game_scenarios:
                game_scenario.detect_and_solve(game_window, screenshot)

    def on_capture_image(self):
        from app.screen_capture_util import start_capture_rectangle
        start_capture_rectangle()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AutoMainWindow()
    app.run()
