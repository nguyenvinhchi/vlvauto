
import time
from unittest import TestCase

import cv2

from app.detect_game_widget import get_window_screenshot
from app.get_game_window import find_window


class ScreenCaptureTest(TestCase):
    def test_capture_screen1(self):
        start_time = time.time()
        capture_after_seconds = 10
        window_title = '#N2 JX Võ Lâm Việt - A1-tl1-tl2'
        windows = find_window(window_title)
        if not windows:
            raise Exception('no window to capture')
        
        while time.time() - start_time < capture_after_seconds:
            time.sleep(0.1)
        screenshot_img = get_window_screenshot(windows[0])
        cv2.imwrite('images/output/window_captured.png', screenshot_img)
