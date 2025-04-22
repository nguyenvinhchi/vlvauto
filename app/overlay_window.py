import tkinter as tk
import threading

def show_overlay_box(x, y, width, height, duration=3000):
    def create_overlay():
        overlay = tk.Tk()
        overlay.overrideredirect(True)  # Remove borders
        overlay.attributes('-topmost', True)
        overlay.attributes('-transparentcolor', 'pink')  # Any color you won't use

        # Transparent background
        overlay.geometry(f"{width}x{height}+{x}+{y}")
        canvas = tk.Canvas(overlay, width=width, height=height, bg='pink', highlightthickness=0)
        canvas.pack()

        # Draw blue rectangle
        canvas.create_rectangle(0, 0, width, height, outline='blue', width=3)

        # Auto close after `duration` milliseconds
        overlay.after(duration, overlay.destroy)
        overlay.mainloop()

    threading.Thread(target=create_overlay).start()
