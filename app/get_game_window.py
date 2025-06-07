import pygetwindow as gw
import win32gui

def find_window(window_title: str):
    # Try to match partial titles (adjust to match your actual MuMu title)
    all_windows = gw.getWindowsWithTitle(window_title)
    if not all_windows:
        print("❌ MuMu window not found.")
        return None

    for win in all_windows:
        print(f"🪟 Found window: '{win.title}'")
        print(f"Position: ({win.left}, {win.top}), Size: ({win.width}x{win.height})")
            
    return all_windows

def find_window_by_title(title_pattern):
    def callback(hwnd, result):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            if title_pattern in window_title:
                result.append(hwnd)
    result = []
    win32gui.EnumWindows(callback, result)
    return result[0] if result else None
