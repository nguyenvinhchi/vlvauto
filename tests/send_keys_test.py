
import time
from unittest import TestCase
from app.get_game_window import find_window
from app.send_window_event import focus_window, simulate_mouse_drag, simulate_mouse_move_around

class SendKeysTest(TestCase):
    def test_send_key(self):
        WINDOW_TITLE = "#N2 JX Võ Lâm Việt - A2-nm1-tl2-ty3"  # Adjust this to match your game's window title
        windows = find_window(WINDOW_TITLE)

        if not windows:
            exit()
        for w in windows:
            print('found window')
            print(w.title)

        test_window = windows[0]  # Use the first matched window
        focus_window(test_window._hWnd)

        print("⏳ Waiting 3 seconds before sending keys...")
        time.sleep(3)  # Give you time to switch to the window

        # simulate_mouse_drag(start_x, start_y, direction='up')
        simulate_mouse_move_around(test_window)