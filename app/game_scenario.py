

import time
from app.detect_game_widget import detect_pattern, read_image_file
from app.log_factory import create_logger


LOGGER = create_logger()

from PyQt6.QtCore import QObject, pyqtSignal, QSettings

class GameScenario(QObject):
    DETECT_RETRY=3
    solve_action_requested = pyqtSignal(str, int, tuple)  # solve_action_type, window_handle_no, points tuple

    def __init__(self, settings: QSettings):
        super().__init__()
        self.images = []
        self._settings = settings

    def _settings(self) -> QSettings:
        return self._settings
    
    def parse_list_int(self, val: list) -> list[int]:
        return [int(x.strip()) for x in val]
    
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
    def __init__(self, settings):
        super().__init__(settings=settings)
        image_files = settings.value("Detection/ShopStuckimg", "data/img/shop/shop-1.png,data/img/shop/bag-1.png")
        self.images = [read_image_file(f) for f in image_files]
        self.lower_color_range = self.parse_list_int(settings.value("Color/ShopStuckLowerColorRange", [19,19,0]))
        self.upper_color_range = self.parse_list_int(settings.value("Color/ShopStuckUpperColorRange", [255,255,255]))
        
    def detect_and_solve(self, game_window, screenshot):
        try:
            match1 = self._detect_medicine_shop(self.images[0], screenshot)
            if match1:
                LOGGER.info(f'Found medicine shop stuck - {game_window.title}')
                self._close_medicine_shop(game_window, match1)
                
            match2 = self._detect_medicine_bag(self.images[1], screenshot)
            if match2:
                self._close_medicine_bag(game_window, match2)
        except Exception as e:
            LOGGER.error(f'An error occured during  detect & solve medicine stuck: {e}')

    def _detect_medicine_shop(self, pattern_img, screenshot):
        return self.detect(pattern_img, screenshot,
                           lower_color_range=self.lower_color_range,
                           upper_color_range=self.upper_color_range,
                           threshold=0.6
                           )

    def _detect_medicine_bag(self, pattern_img, screenshot):
        return self.detect(pattern_img, screenshot,
                           lower_color_range=self.lower_color_range,
                           upper_color_range=self.upper_color_range,
                           threshold=0.6
                           )
    
    def _close_medicine_shop(self, game_window, match):
        (x, y), w, h = match
        screen_x = game_window.left + x
        screen_y = game_window.top + y
        start_x, start_y = screen_x + w//4, screen_y + h//2
        LOGGER.info(f"🎯 Found med shop stuck at ({screen_x}, {screen_y}), size: {w}x{h} - {game_window.title}")
        self.solve_action_requested.emit('close_medicine_shop', game_window._hWnd, (start_x, start_y))
    
    def _close_medicine_bag(self, game_window, match):
        (x, y), w, h = match
        screen_x = game_window.left + x
        screen_y = game_window.top + y
        start_x, start_y = screen_x + 3*w//4, screen_y + h//2
        LOGGER.info(f"🎯 Found med bag stuck at ({screen_x}, {screen_y}), size: {w}x{h} - {game_window.title}")
        self.solve_action_requested.emit('close_medicine_bag', game_window._hWnd, (start_x, start_y))

class TownStuckGameScenario(GameScenario):
    move_around_x_offset = 120
    move_around_y_offset = 120
    
    def __init__(self, settings: QSettings):
        super().__init__(settings=settings)
        self.TOWN_STUCK_SECONDS = settings.value("Detection/TownStuckTimeout", 20, type=int)
        self.COOLDOWN_SECONDS = settings.value("Detection/CooldownSeconds", 10, type=int) # prevent immediate re-match
        image_files = settings.value("Detection/TownStuckimg", "data/img/town/DuongChau-sm1.png,data/img/town/DuongChau-sm2.png")
        self.images = [read_image_file(f) for f in image_files]
        self.lower_color_range = self.parse_list_int(settings.value("Color/TownStuckLowerColorRange", [38,206,0]))
        self.upper_color_range = self.parse_list_int(settings.value("Color/TownStuckUpperColorRange", [94,255,165]))
        self.first_match_timestamp = {}
        self.last_solved_timestamp = {}
        
    def detect_and_solve(self, game_window, screenshot):
        try:
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
        except Exception as e:
            LOGGER.error(f'An error occured during  detect & solve town stuck: {e}')

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
        LOGGER.info(f'Try to solve town stuck: move around - {game_window.title}')
        start_x = game_window.left + self.move_around_x_offset
        start_y = game_window.bottom - self.move_around_y_offset
        self.solve_action_requested.emit('move_around_abit', game_window._hWnd, (start_x, start_y))


