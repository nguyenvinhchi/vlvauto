
import ast
import os
import time
from typing import List
from PyQt6.QtCore import QSettings



from app.game_scenario import GameScenario
from app.log_factory import create_logger
from app.v2.auto_open_game import AutoOpenGame
from app.v2.check_game_auto import CheckAutoIsOn
from app.v2.check_pixel import PixelUtil
from app.v2.window_util import WindowUtil
LOGGER = create_logger(name='GameTabIterate')

class GameTabIterate(CheckAutoIsOn, AutoOpenGame):
    MAIN_WINDOW = "main_window"
    GAME_WINDOW = "game_window"
    LOGIN_WINDOW = "login_window"
    LOGIN_WARN_WINDOW = "login_warn_window"
    UNKNOWN_WINDOW = "unknown_window"
    MAX_TAB_ITERATION = 8
    SEPARATOR = "__"

    def __init__(self, settings: QSettings, *args, **kwargs):
        CheckAutoIsOn.__init__(self, settings=settings)
        AutoOpenGame.__init__(self, settings=settings)
        self.settings = settings
        points = settings.value('Detection/GameWindowMainPoints', type=str)
        self.game_window_main_points = ast.literal_eval(points)


    def check_game_scenario(self, game_window, screenshot, game_tab_id="0"):
        for scenario in self.get_game_scenarios():
            scenario.detect_and_solve(game_window, screenshot, game_tab_id)

    def is_running(self):
        pass # implement in worker

    def iterate_game_tab(self, game_window):
        if not self.is_running():
            return
        
        hwnd = WindowUtil.get_hwnd(game_window)
        title = game_window.title
        WindowUtil.focus(game_window)
        WindowUtil.send_trl_tab(game_window)

        max_initial_tab_attempts = 10 # Max Ctrl+Tab presses to find main tab initially
        main_tab_found = self.find_main_tab(game_window, max_initial_tab_attempts)

        if not main_tab_found:
            print(f"Worker WARNING: Could not find main MuMu tab after {max_initial_tab_attempts} attempts for window '{game_window.title}'. Skipping this window.")
            return # Skip to next game window if main tab not found
        else:
            self.check_game_exit(hwnd, game_window)

        # Phase 2: Iterate through game tabs until main tab is seen again
        print(f"===Worker: Starting game tab processing for window '{title}'...")
        game_tabs_processed_in_cycle = 0
        max_game_tab_processing_iterations = 20 # Safeguard to prevent infinite loop

        # Move from main tab to the first game tab (or back to main if no game tabs)
        for _ in range(max_game_tab_processing_iterations):
            if not self.is_running():
                return
            time.sleep(3)
            WindowUtil.send_trl_tab(game_window)
            time.sleep(3) # Short delay for tab switch
            # Check if we've cycled back to the main tab
            if self.is_main_window(game_window):
                print(f"Worker: Cycled back to main tab. Finished processing game tabs for window '{title}'. Total game tabs processed in this cycle: {game_tabs_processed_in_cycle}.")
                return # Exit the game tab processing loop
            
            game_tabs_processed_in_cycle += 1
            game_tab_id = f'{hwnd}{self.SEPARATOR}{title}{self.SEPARATOR}{game_tabs_processed_in_cycle}'
            print(f"===Processing game tab '{game_tab_id}")
            screenshot = WindowUtil.screen_shot(game_window)
            file_name = os.path.join("tmp", game_tab_id + ".png")
            screenshot.save(file_name)
            self.check_game_scenario(game_window, screenshot, game_tab_id)
            self.detect_game_auto_off(game_window, screenshot)
        else:
            print(f"Worker WARNING: Exceeded max game tab processing iterations ({max_game_tab_processing_iterations}) for window '{game_window.title}'. May not have processed all tabs.")

    def find_main_tab(self, game_window, max_initial_tab_attempts):
        main_tab_found = False
        for attempt in range(max_initial_tab_attempts):
            if not self.is_running():
                return
            if self.is_main_window(game_window):
                main_tab_found = True
                print(f"Worker: Main MuMu tab found after {attempt + 1} attempts.")
                return True
            
            WindowUtil.send_trl_tab(game_window)
            time.sleep(0.1)
            print(f"Worker: Ctrl+Tab pressed, checking next tab for main tab...")
        return main_tab_found
        

    def is_main_window(self, game_window, tolerance: int = 5) -> str:
        WindowUtil.focus(game_window)
        screenshot = WindowUtil.screen_shot(game_window)
        for point_data in self.game_window_main_points:
            x_offset, y_offset, expected_r, expected_g, expected_b = point_data
            expected_rgb = (expected_r, expected_g, expected_b)

            # Get the color of the pixel relative to the window's top-left
            actual_rgb = screenshot.getpixel((x_offset, y_offset))

            if not PixelUtil.is_color_match(actual_rgb, expected_rgb):
                #print(f"Worker: Pixel at ({x_offset},{y_offset}) color mismatch. Expected {expected_rgb}, Got {actual_rgb}. probably game tab.")
                return False # Not the main tab
            
            #print("===Worker: All configured pixel checks passed. At main MuMu tab.")
            return True # All pixels match, likely the main tab
        
    def get_game_scenarios(self) -> List[GameScenario]:
        raise('Should implement in woker')