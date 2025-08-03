import win32gui
import PyQt6
from app.get_game_window import find_window_by_title
from app.send_window_event import focus_window, simulate_tab

print(PyQt6.__file__)

def get_mumu_child_windows(parent_hwnd):
    child_handles = {}
    def callback(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        print(f"Child HWND: {hwnd}, Title: {title}")
        child_handles[title] = hwnd
        return True

    win32gui.EnumChildWindows(parent_hwnd, callback, None)
    return child_handles



if __name__ == '__main__':
    print('mumu player')
    window_title = 'A1'
    mumu_hwnd = find_window_by_title(window_title)
    print(f'player window handle: {mumu_hwnd}')
    child_handles = get_mumu_child_windows(mumu_hwnd)
    nemu_hwnd = child_handles['nemudisplay']
    print(f'nemu handle: {nemu_hwnd}')
    focus_window(nemu_hwnd)
    for i in range(2):
        simulate_tab()
