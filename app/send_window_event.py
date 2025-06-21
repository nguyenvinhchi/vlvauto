import win32api
import win32con
import win32gui
import time

from app.log_factory import create_logger

LOGGER = create_logger(name='MainWindow')

def focus_window(hwnd):
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # Restore if minimized
        win32gui.SetForegroundWindow(hwnd)              # Bring to front
        window_title = win32gui.GetWindowText(hwnd)
        LOGGER.info(f"✅ Window focused: '{window_title}")
        time.sleep(0.2)  # slight delay to let it register
    except Exception as e:
        print(f"❌ Could not focus window: {e}")


def simulate_click(x, y):
    # Move cursor (optional, for debug)
    win32api.SetCursorPos((x, y))

    # Send mouse down and up at screen position
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    time.sleep(0.01)  # slight delay
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

    # print(f"🖱️ Simulated click at: ({x}, {y})")

def simulate_mouse_drag(start_x, start_y, direction='up', distance=40):
    # Move cursor to starting position
    win32api.SetCursorPos((start_x, start_y))
    time.sleep(0.05)

    # Press both left and right buttons down
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    # time.sleep(0.05)

    # Move mouse slightly in desired direction
    if direction == 'up':
        win32api.SetCursorPos((start_x, start_y - distance))
    elif direction == 'down':
        win32api.SetCursorPos((start_x, start_y + distance))
    elif direction == 'left':
        win32api.SetCursorPos((start_x - distance, start_y))
    elif direction == 'right':
        win32api.SetCursorPos((start_x + distance, start_y))

    # Hold position for 2 seconds
    time.sleep(0.5)

    # Release both mouse buttons
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

    # print(f"🖱️ Drag simulated {direction} from ({start_x}, {start_y})")


def simulate_mouse_move_around(start_x, start_y):
    simulate_mouse_drag(start_x, start_y, direction='up')
    simulate_mouse_drag(start_x, start_y, direction='down')
    simulate_mouse_drag(start_x, start_y, direction='right')
    simulate_mouse_drag(start_x, start_y, direction='left')

