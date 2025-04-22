

import io
import sys
import logging
from logging.handlers import RotatingFileHandler
import time
from app.overlay_window import show_overlay_box
from app.send_window_event import focus_window, simulate_click, simulate_mouse_move_around
from app.detect_game_widget import detect_pattern, read_image_file

log_level = logging.INFO
LOGGER = logging.getLogger("auto-tool")
LOGGER.setLevel(log_level)

# Wrap sys.stdout with UTF-8 encoding
try:
    stream = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
except Exception:
    stream = sys.stdout  # Fallback if frozen

stream_handler = logging.StreamHandler(stream)
stream_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
LOGGER.addHandler(stream_handler)

# ---- File handler ----
# Rotating file handler
file_handler = RotatingFileHandler(
    "log/auto-tool.log",  # log file path
    mode='a',
    maxBytes=1 * 1024 * 1024,  # 1MB
    backupCount=3,            # keep 3 backups: auto-tool.log.1, .2, .3
    encoding='utf-8',
    delay=False
)
file_handler.setLevel(log_level)
file_handler.setFormatter(formatter)
LOGGER.addHandler(file_handler)


# LOGGER.basicConfig(
#     level=LOGGER.INFO,  # or DEBUG, WARNING, ERROR, CRITICAL
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     handlers=[
#         LOGGER.FileHandler("log/vlv_auto_log.log"),  # Save to file
#         LOGGER.StreamHandler()  # Also print to console
#     ]
# )

class GameScenario:
    DETECT_RETRY=3
    def __init__(self):
        self.images = []
        self.game_window = None

    def detect_and_solve(self, game_window, screenshot):
        pass

    def detect(self, pattern_img, screenshot,
                  lower_color_range = [53, 53, 8], 
                  upper_color_range = [71, 255, 255], 
                  threshold=0.7):
        for i in range(0, self.DETECT_RETRY):
            match = detect_pattern(pattern_img, screenshot, 
                                   lower_color_range=lower_color_range,
                                   upper_color_range=upper_color_range,
                                   threshold=threshold
                                   )
            # print(f'detect stuck retry={i+1}, match={match}')
            if match: return match

    def solve(self):
        pass

class StuckBuyingGameScenario(GameScenario):
    lower_color_range = [19, 0, 0]
    upper_color_range = [45, 75, 135]
    def __init__(self):
        super().__init__()
        self.images = [
            read_image_file('app/images/vlv-stuck-buying-med-shop_1_masked.png'),
            read_image_file('app/images/vlv-stuck-buying-med-bag_1_masked.png')
        ]
        
    def detect_and_solve(self, game_window, screenshot):
        match1 = self._detect_medicine_shop(self.images[0], screenshot)
        if match1:
            LOGGER.info(f'Found medicine shop stuck - {game_window.title}')
            self._close_medicine_shop(game_window, match1)
            
        # match2 = self._detect_medicine_bag(self.images[1], screenshot)
        # if match2:
        #     self._close_medicine_bag(game_window, match2)

    def _detect_medicine_shop(self, pattern_img, screenshot):
        return self.detect(pattern_img, screenshot,
                           lower_color_range=self.lower_color_range,
                           upper_color_range=self.upper_color_range)

    def _detect_medicine_bag(self, pattern_img, screenshot):
        return self.detect(pattern_img, screenshot,
                           lower_color_range=self.lower_color_range,
                           upper_color_range=self.upper_color_range)
    
    def _close_medicine_shop(self, game_window, match):
        (x, y), w, h = match
        screen_x = game_window.left + x
        screen_y = game_window.top + y
        # print(f"🎯 Found at ({screen_x}, {screen_y}), size: {w}x{h}")
        show_overlay_box(screen_x, screen_y, w, h)
        # simulate click
        # 🧠 FOCUS FIRST
        focus_window(game_window._hWnd)

        # ✅ Click after focusing
        LOGGER.info(f'Try to solve medicine shop stuck: click Close button - {game_window.title}')
        simulate_click(screen_x + w//4, screen_y + h//2)
    
    def _close_medicine_bag(self, game_window, match):
        (x, y), w, h = match
        screen_x = game_window.left + x
        screen_y = game_window.top + y
        LOGGER.info(f"🎯 Found at ({screen_x}, {screen_y}), size: {w}x{h} - {game_window.title}")
        show_overlay_box(screen_x, screen_y, w, h)
        # simulate click
        # 🧠 FOCUS FIRST
        focus_window(game_window._hWnd)

        # ✅ Click after focusing
        simulate_click(screen_x + 3*w//4, screen_y + h//2)

class TownStuckGameScenario(GameScenario):
    TOWN_STUCK_SECONDS = 20
    COOLDOWN_SECONDS = 10  # prevent immediate re-match
    # lower_color_range = [53, 53, 8]
    # upper_color_range = [71, 255, 255]
    lower_color_range = [38, 206, 0]
    upper_color_range = [94, 255, 165]
    
    def __init__(self):
        super().__init__()
        self.images = [
            read_image_file('app/images/vlv-DuongChau-smallmap_1_masked.png'),
            read_image_file('app/images/vlv-DuongChau-smallmap_2_masked.png')
        ]
        self.first_match_timestamp = {}
        self.last_solved_timestamp = {}
        
    def detect_and_solve(self, game_window, screenshot):
        elapsed_seconds = self._get_stuck_elaped_seconds(game_window, screenshot)

        # it's time to solve the stuck
        if elapsed_seconds is not None:
            LOGGER.debug(f"Town stuck elaped time: {elapsed_seconds} - {game_window.title}")

            # Cooldown check
            now = time.time()
            if now - self.last_solved_timestamp.get(game_window.title, 0) < self.COOLDOWN_SECONDS:
                LOGGER.debug(f"⏳ In cooldown period, skipping... - {game_window.title}")
                return
            
            if elapsed_seconds >= self.TOWN_STUCK_SECONDS:
                # reset first match time
                LOGGER.info(f'stuck in town for {elapsed_seconds}, try to solve - {game_window.title}')
                self._solve_town_stuck(game_window)
                self.first_match_timestamp[game_window.title] = 0
                self.last_solved_timestamp[game_window.title] = now

    def _detect_town_stuck(self, pattern_img, screenshot_img):
        return detect_pattern(pattern_img, screenshot_img,
                              lower_color_range=self.lower_color_range,
                              upper_color_range=self.upper_color_range,
                              threshold=0.6
                              )

    def _get_stuck_elaped_seconds(self, game_window, screenshot):
        for pattern_img in self.images:
            match = self._detect_town_stuck(pattern_img, screenshot)
            if match is None:
                continue

            if self.first_match_timestamp.get(game_window.title, 0) is 0:
                self.first_match_timestamp[game_window.title] = time.time()
                return 0
            else:
                elapsed = time.time() - self.first_match_timestamp.get(game_window.title, 0)
                LOGGER.info(f'Found Town stuck, elapsed seconds: {elapsed} - {game_window.title}')
                return elapsed

        # No match found, reset
        self.first_match_timestamp[game_window.title] = 0
        return None

    def _solve_town_stuck(self, game_window):
        focus_window(game_window._hWnd)
        LOGGER.info(f'Try to solve town stuck: move around - {game_window.title}')
        simulate_mouse_move_around(game_window)


