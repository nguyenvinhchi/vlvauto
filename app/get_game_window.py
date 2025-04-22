import pygetwindow as gw

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
