import pyautogui
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
        LOGGER.debug(f"✅ Window focused: '{window_title}")
        time.sleep(0.2)  # slight delay to let it register
    except Exception as e:
        LOGGER.info(f"❌ Could not focus window: {e}")

def simulate_click(x, y, action='click'):
    # Move cursor (optional, for debug)
    # win32api.SetCursorPos((x, y))

    # win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    # time.sleep(0.01)  # slight delay
    # win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

    if action == 'click':
        # Send mouse down and up at screen position
        pyautogui.leftClick(x, y)
        print(f"🖱️ Simulated click at: ({x}, {y})")
    elif action == 'double_click':
        # Send mouse down and up at screen position
        pyautogui.doubleClick(x, y)
        print(f"🖱️ Simulated double-click at: ({x}, {y})")

def simulate_mouse_drag(start_x, start_y, direction='up', distance=60, duration=0.5):
    # Calculate the destination point
    if direction == 'up':
        end_x, end_y = start_x, start_y - distance
    elif direction == 'down':
        end_x, end_y = start_x, start_y + distance
    elif direction == 'left':
        end_x, end_y = start_x - distance, start_y
    elif direction == 'right':
        end_x, end_y = start_x + distance, start_y
    else:
        raise ValueError("Invalid direction. Choose up, down, left, or right.")

    # Perform the drag
    pyautogui.moveTo(start_x, start_y)
    pyautogui.mouseDown()
    time.sleep(1)
    pyautogui.moveTo(end_x, end_y, duration=duration)  # Smooth drag
    time.sleep(0.2)  # Optional hold at end
    pyautogui.mouseUp()  # Release button
    print(f"🖱️ Drag simulated {direction} from ({start_x}, {start_y})")

def simulate_mouse_move_around(start_x, start_y):
    simulate_mouse_drag(start_x, start_y, direction='up')
    simulate_mouse_drag(start_x, start_y, direction='down')
    simulate_mouse_drag(start_x, start_y, direction='right')
    simulate_mouse_drag(start_x, start_y, direction='left')

def simulate_tab():
    pyautogui.keyDown('ctrl')
    pyautogui.press('tab')
    pyautogui.keyUp('ctrl')