
import ast
import os
import time
from typing import List
from PyQt6.QtCore import QSettings



from app.game_scenario import GameScenario
from app.log_factory import create_logger
from app.v2.auto_open_game import AutoOpenGame
from app.v2.check_game_auto import CheckAutoIsOn
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

        # points = settings.value('Detection/GameWindowMainPoints2', type=str)
        # self.game_window_main_points2 = ast.literal_eval(points)


    def check_game_scenario(self, game_window, screenshot, game_tab_id="0"):
        for scenario in self.get_game_scenarios():
            r = scenario.detect_and_solve(game_window, screenshot, game_tab_id)
            if r == "LOGINED":
                print(f'Finish login scenario => check if game auto off')
                self.detect_game_auto_off(game_window)
                
    def is_running(self):
        pass # implement in worker

    def iterate_game_tab(self, game_window):
        if not self.is_running():
            return
        
        hwnd = WindowUtil.get_hwnd(game_window)
        title = game_window.title
        WindowUtil.focus(game_window)
        # WindowUtil.send_trl_tab(game_window)

        max_initial_tab_attempts = 4 # Max Ctrl+Tab presses to find main tab initially
        main_tab_found = self.find_main_tab(game_window, max_initial_tab_attempts)

        if not main_tab_found:
            return # Skip to next game window if main tab not found
        else:
            self.check_game_exit(hwnd, game_window)

        # Phase 2: Iterate through game tabs until main tab is seen again
        print(f"===Worker: Starting game tab processing for window '{title}'...")
        game_tabs_processed_in_cycle = 0
        max_game_tab_processing_iterations = 7 # Safeguard to prevent infinite loop

        # Move from main tab to the first game tab (or back to main if no game tabs)
        for _ in range(max_game_tab_processing_iterations):
            if not self.is_running():
                return
            WindowUtil.send_trl_tab(game_window)
            time.sleep(1)
            screenshot = WindowUtil.screen_shot(game_window)

            # Check if we've cycled back to the main tab
            if self.is_main_window(game_window, screenshot):
                return # Exit the game tab processing loop
            
            game_tabs_processed_in_cycle += 1
            game_tab_id = f'{hwnd}{self.SEPARATOR}{title}{self.SEPARATOR}{game_tabs_processed_in_cycle}'
            print(f"===Processing game tab '{game_tab_id}")
            # screenshot = WindowUtil.screen_shot(game_window)
            # file_name = os.path.join("tmp", game_tab_id + ".png")
            # screenshot.save(file_name)
            self.check_game_scenario(game_window, screenshot, game_tab_id)
            time.sleep(2)
        else:
            print(f"Exceeded max game tab processing iterations ({max_game_tab_processing_iterations}) for window '{game_window.title}'. May not have processed all tabs.")

    def find_main_tab(self, game_window, max_initial_tab_attempts):
        for attempt in range(max_initial_tab_attempts):
            if not self.is_running():
                return False
            # WindowUtil.focus(game_window)
            screenshot = WindowUtil.screen_shot(game_window)
            # file_name = os.path.join("tmp", game_window.title + "_" +  str(attempt) + ".png")
            # screenshot.save(file_name)
            if self.is_main_window(game_window, screenshot):
                print(f"Main MuMu tab found after {attempt + 1} attempts.")
                return True
            
            WindowUtil.send_trl_tab(game_window)
            time.sleep(1)
            print(f"Ctrl+Tab pressed, checking next tab for main tab...")
        print(f'No main window found after {max_initial_tab_attempts} attempts, window: {game_window.title}')
        return False
        

    def is_main_window(self, game_window, screenshot, tolerance: int = 5) -> str:
        return WindowUtil.check_pixel_pattern(game_window, 
                                             screenshot, 
                                             pixel_points_config=self.game_window_main_points, debug_name="CHECK-MAIN",
                                             color_tolerance=tolerance) 
        
    def get_game_scenarios(self) -> List[GameScenario]:
        raise('Should implement in woker')