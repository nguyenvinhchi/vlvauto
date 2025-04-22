

import os
import subprocess
import time
from unittest import TestCase

from app.game_scenario import StuckBuyingGameScenario
from app.get_game_window import find_window


class StuckBuyingGameScenarioTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image_path = os.path.abspath("tests/test_assets/vlv-close-button_window_truecolor.png")
        # cls.window_title = "vlv-medicine-buying-sample1"
        cls.window_title = "Photos"
        # cls.image_proc = subprocess.Popen(['start', cls.image_path], shell=True)
        os.startfile(cls.image_path)
        time.sleep(2)  # Wait for the window to appear

        # Manually rename window title (if needed), or find by partial title
        cls.window = find_window(cls.window_title)
        assert cls.window, "Test window not found"
        cls.window = cls.window[0]

    @classmethod
    def tearDownClass(cls):
        if cls.window:
            try:
                cls.window.close()
            except Exception as e:
                print(f"⚠️ Failed to close test window: {e}")

    def test_detect_and_solve(self):
        print('test start')
        scenario = StuckBuyingGameScenario()
        print(f" title: {self.window.title}")
        scenario.detect_and_solve(self.__class__.window)