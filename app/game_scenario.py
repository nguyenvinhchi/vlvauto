

import ast
import time
import cv2
import numpy as np
import win32gui
from app.detect_game_widget import detect_pattern, read_image_file
from app.log_factory import create_logger
from app.send_window_event import simulate_click, simulate_mouse_move_around
from app.v2.check_pixel import PixelUtil
from app.v2.resolver import Resolver
from app.v2.window_util import WindowUtil


LOGGER = create_logger()

from PyQt6.QtCore import QObject, QSettings, QDateTime

def to_str_time(timestamp: QDateTime):
    if timestamp is None: return None
    return timestamp

def to_screen_coord(point, game_window):
    return point[0] + game_window.left, point[1] + game_window.top

LAST_SEEN_LOGIN = 'last_seen_login'
LAST_SEEN_TOWN_STUCK = 'last_seen_town_stuck'

class GameScenario(QObject):
    DETECT_RETRY=3
    CLOSE_MEDICINE_BAG = "close_medicine_bag"
    CLOSE_MEDICINE_SHOP = "close_medicine_shop"
    MOVE_AROUND_ABIT = "move_around_abit"
    AUTO_LOGIN = "auto_login"
    ACOUNT_LOGINED_WARNING = "account_logined_warning"
    SELECT_SERVER_TO_LOGIN = "select_server_to_login"
    SELECT_CHARACTER_TO_LOGIN = "select_character_to_login"
    CRASH_DIALOG = "crash_dialog"
    SERVER_CONNECT="server_connect_warn"

    def __init__(self, settings: QSettings, worker_parent):
        super().__init__()
        self.worker_parent = worker_parent
        self.game_data = {}
        self._settings = settings

    def _settings(self) -> QSettings:
        return self._settings
    
    def parse_list_int(self, val: list) -> list[int]:
        return [int(x.strip()) for x in val]
    
    def detect_and_solve(self, game_window, screenshot, game_tab_id="0") -> str:
        raise('Not implemented')

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

    def get_game_data(self, game_tab_id, key: str):
        return self.game_data.get(game_tab_id, {}).get(key)

    def set_game_data(self, game_tab_id, key, value):
        self.game_data.setdefault(game_tab_id, {})[key] = value

    def resolve_scenario(self, resolve_action: str, game_window, points: tuple):
        screen_points = [to_screen_coord(p, game_window) for p in points]
        LOGGER.info(f"Received resolve action request: {resolve_action} - points: {points}")
        WindowUtil.focus(game_window)
        if resolve_action in (self.CLOSE_MEDICINE_BAG, self.CLOSE_MEDICINE_SHOP):
            Resolver.do_single_click(screen_points)
        elif resolve_action == self.MOVE_AROUND_ABIT:
            Resolver.do_move_around(*screen_points[0])
        elif resolve_action == self.AUTO_LOGIN:
            Resolver.do_login_user_pass(screen_points)

        elif resolve_action == self.ACOUNT_LOGINED_WARNING:
            Resolver.do_single_click(screen_points)

        elif resolve_action == self.SELECT_SERVER_TO_LOGIN:
            Resolver.do_select_server(screen_points)

        elif resolve_action == self.SELECT_CHARACTER_TO_LOGIN:
            Resolver.do_select_character(screen_points)

        elif resolve_action == self.SERVER_CONNECT:
            Resolver.do_single_click(screen_points)
        else:
            LOGGER.info(f"{resolve_action} is not supported yet")


class StuckBuyingGameScenario(GameScenario):
    def __init__(self, settings, worker_parent):
        super().__init__(settings, worker_parent)
        
        points = settings.value('Detection/BuyStuckShopPoints', type=str)
        self.shop_points = ast.literal_eval(points)
        self.shop_close_points = ((self.shop_points[-1][0:2]),)
        
        points = settings.value('Detection/BuyStuckBagPoints', type=str)
        self.bag_points = ast.literal_eval(points)

        self.bag_close_points = ((self.bag_points[-1][0:2]),)
        
    def detect_and_solve(self, game_window, screenshot, game_tab_id="0"):
        try:
            if PixelUtil.check_pixel_pattern(game_window, screenshot, self.shop_points, debug_name=None):
                LOGGER.info(f'Found buy stuck - shop - {game_window.title}')
                self.resolve_scenario(self.CLOSE_MEDICINE_SHOP, game_window, self.shop_close_points)

            if PixelUtil.check_pixel_pattern(game_window, screenshot, self.bag_points, debug_name=None):
                LOGGER.info(f'Found buy stuck - bag - {game_window.title}')
                self.resolve_scenario(self.CLOSE_MEDICINE_BAG, game_window, self.bag_close_points)
        except Exception as e:
            LOGGER.error(f'An error occured during  detect & solve medicine stuck: {e}', exc_info=True)

class TownStuckGameScenario(GameScenario):
    
    def __init__(self, settings: QSettings, parent_worker):
        super().__init__(settings, parent_worker)
        self.move_around_x_offset = settings.value("Detection/TownStuckMoveOffsetX", 400, type=int)
        self.move_around_y_offset = settings.value("Detection/TownStuckMoveOffsetY", 380, type=int)
        self.TOWN_STUCK_SECONDS = settings.value("Detection/TownStuckTimeout", 20, type=int)
        self.COOLDOWN_SECONDS = settings.value("Detection/CooldownSeconds", 5, type=int) # prevent immediate re-match
        self.TOWN_NAME_THRESHOLD = settings.value("Detection/TownNameGreenThreshold", 0.7, type=float)
        images = settings.value('Detection/TownImages', type=list)
        self.town_images = [
            read_image_file(img_path) for img_path in images
        ]
        self.lower_color_range = settings.value('Detection/TownStuckLowerColorRange', type=list)
        self.upper_color_range = settings.value('Detection/TownStuckUpperColorRange', type=list)
        self.lower_color_range = np.array(self.lower_color_range, dtype=np.uint8).flatten()
        self.upper_color_range = np.array(self.upper_color_range, dtype=np.uint8).flatten()

        
    def detect_and_solve(self, game_window, screenshot, game_tab_id="0"):
        try:
            bgr_img = self.to_numpy_bgr_image(screenshot)
            elapsed_seconds = self._get_stuck_elaped_seconds(game_window, bgr_img, game_tab_id)
            # it's time to solve the stuck
            if elapsed_seconds is not None:
                LOGGER.debug(f"Town stuck elaped time: {elapsed_seconds} - {game_tab_id}")

                # Cooldown check
                if elapsed_seconds < self.COOLDOWN_SECONDS:
                    LOGGER.debug(f"⏳ In cooldown period, skipping... - {game_tab_id}")
                
                if elapsed_seconds >= self.TOWN_STUCK_SECONDS:
                    LOGGER.info(f'stuck in town for {elapsed_seconds}, try to solve - {game_tab_id}')
                    self._solve_town_stuck(game_window, game_tab_id)
                    # reset state
                    self.set_game_data(game_tab_id, LAST_SEEN_TOWN_STUCK, None)
        except Exception as e:
            LOGGER.error(f'An error occured during  detect & solve town stuck: {e}', exc_info=True)

    def to_numpy_bgr_image(self, screenshot):
        rgb_img = np.array(screenshot) # screeshot is PIL Image so we need to convert to numpy
        bgr_img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)
        return bgr_img

    def _detect_town_stuck(self, pattern_img, screenshot_img):
        
        return detect_pattern(pattern_img, screenshot_img,
                              lower_color_range=self.lower_color_range,
                              upper_color_range=self.upper_color_range,
                              threshold=self.TOWN_NAME_THRESHOLD
                              )

    def _get_stuck_elaped_seconds(self, game_window, screenshot, game_tab_id):
        for pattern_img in self.town_images:
            match = self._detect_town_stuck(pattern_img, screenshot)
            if match is None:
                continue
            
            last_seen: QDateTime = self.get_game_data(game_tab_id, LAST_SEEN_TOWN_STUCK)
            if last_seen is None:
                self.set_game_data(game_tab_id, LAST_SEEN_TOWN_STUCK, QDateTime.currentDateTime())
                return None
            else:
                duration = last_seen.secsTo(QDateTime.currentDateTime())
                LOGGER.info(f'Found Town stuck, elapsed seconds: {duration} - {game_tab_id}')
                return duration

        # No match found, reset
        self.set_game_data(game_tab_id, LAST_SEEN_TOWN_STUCK, None)
        return None

    def _solve_town_stuck(self, game_window, game_tab_id):
        LOGGER.info(f'Try to solve town stuck: move around - {game_tab_id}')
        points = ((self.move_around_x_offset, self.move_around_y_offset),)
        self.resolve_scenario(self.MOVE_AROUND_ABIT, game_window, points)


class UserPassLoginScenario(GameScenario):
    def __init__(self, settings, worker_parent):
        super().__init__(settings, worker_parent)

        self.login_check_confirm_duration = settings.value('Detection/LoginCheckConfirmDurationSeconds', 60, type=int)

        points = settings.value('Detection/LoginPoints', type=str)
        self.login_points = ast.literal_eval(points)

        points = settings.value('Detection/UserPassLoginPoints', type=str)
        self.user_pass_login_points = ast.literal_eval(points)

    def detect_and_solve(self, game_window, screenshot, game_tab_id="0"):
        try:
            if self.should_login(game_window, screenshot, game_tab_id):
                self.resolve_scenario(self.AUTO_LOGIN, game_window, self.login_points)
                self.set_game_data(game_tab_id, LAST_SEEN_LOGIN, None)

        except Exception as e:
            LOGGER.error(f'An error occured during  detect & solve login window: {e}', exc_info=True)

    def should_login(self, game_window, screenshot, game_tab_id):
        if PixelUtil.check_pixel_pattern(game_window, screenshot, self.user_pass_login_points):
            LOGGER.info(f"Found User pass login window: {game_tab_id}")
            if self.get_game_data(game_tab_id, LAST_SEEN_LOGIN) is None:
                self.set_game_data(game_tab_id, LAST_SEEN_LOGIN, QDateTime.currentDateTime())
                return False
            else:
                duration = self.get_game_data(game_tab_id, LAST_SEEN_LOGIN).secsTo(QDateTime.currentDateTime())
                LOGGER.info(f"Login waiting: {game_tab_id} - duration: {duration} seconds")
                if duration >= self.login_check_confirm_duration:
                    LOGGER.info(f"Found login window: {game_tab_id} - duration: {duration} seconds")
                    self.set_game_data(game_tab_id, LAST_SEEN_LOGIN, None)
            return True
        return False

# Taikhoan dang dang nhap warn
class AccountLoginedWarningScenario(GameScenario):
    def __init__(self, settings: QSettings, parent_worker):
        super().__init__(settings, parent_worker)
        points = settings.value('Detection/GameWindowAccountLoginedWarnPoints', type=str)
        self.login_warn_points = ast.literal_eval(points)
        self.close_warn_points = ((self.login_warn_points[-1][0:2]),)
        # print(self.close_warn_points)
    
    def detect_and_solve(self, game_window, screenshot, game_tab_id="0"):
        try:
            if PixelUtil.check_pixel_pattern(game_window, screenshot, self.login_warn_points, 
                                             debug_name="AccountLoginedWarning"):
                LOGGER.info(f"Found login window - Tai khoan dang dang nhap: {game_tab_id}")
                self.resolve_scenario(self.ACOUNT_LOGINED_WARNING, game_window, self.close_warn_points)
        
        except Exception as e:
            LOGGER.error(f'An error occured during  detect & solve login window: {e}', exc_info=True)


class LoginSelectServerScenario(GameScenario):
    """
    Sometimes auto login missed second step click select server to login, this is to solve the issue
    """
    def __init__(self, settings: QSettings, parent_worker):
        super().__init__(settings, parent_worker)
        points = settings.value('Detection/GameWindowLoginSelectServerPoints', type=str)
        self.game_window_select_server_points = ast.literal_eval(points)
        points = settings.value('Detection/LoginPoints', type=str)
        self.login_points = ast.literal_eval(points)
    
    def detect_and_solve(self, game_window, screenshot, game_tab_id="0"):
        try:
            LOGGER.debug(f'checking select server login scenario: {game_tab_id}')
            
            if PixelUtil.check_pixel_pattern(game_window, screenshot, self.game_window_select_server_points):
                LOGGER.info(f"=====Found login window - select server: {game_tab_id}")
                self.resolve_scenario(self.SELECT_SERVER_TO_LOGIN, game_window, self.login_points)
        
        except Exception as e:
            LOGGER.error(f'An error occured during  detect & solve login window: {e}', exc_info=True)


class LoginSelectCharacterScenario(GameScenario):
    """
    Sometimes auto login missed 3rd step click select char to login, this is to solve the issue
    """
    def __init__(self, settings: QSettings, parent_worker):
        super().__init__(settings, parent_worker)
        points = settings.value('Detection/GameWindowLoginSelectCharacterPoints', type=str)
        self.game_window_select_character_points = ast.literal_eval(points)
        points = settings.value('Detection/LoginPoints', type=str)
        self.login_points = ast.literal_eval(points)
    
    def detect_and_solve(self, game_window, screenshot, game_tab_id="0"):
        try:
            LOGGER.debug(f'checking select character login scenario: {game_tab_id}')
            
            if PixelUtil.check_pixel_pattern(game_window, screenshot, self.game_window_select_character_points):
                LOGGER.info(f"=====Found login window - select character: {game_tab_id}")
                self.resolve_scenario(self.SELECT_CHARACTER_TO_LOGIN, game_window, self.login_points)
        
        except Exception as e:
            LOGGER.error(f'An error occured during  detect & solve login window: {e}')

class ServerConnectWarnScenario(GameScenario):
    def __init__(self, settings: QSettings, parent_worker):
        super().__init__(settings, parent_worker)
        points = settings.value('Detection/GameLoginServerConnectWarnPoints', type=str)
        self.server_connect_dialog_points = ast.literal_eval(points)
        self.close_points = ((self.server_connect_dialog_points[-1][0:2]),)
        # print(self.close_warn_points)
    
    def detect_and_solve(self, game_window, screenshot, game_tab_id="0"):
        try:
            if PixelUtil.check_pixel_pattern(game_window, screenshot, self.server_connect_dialog_points, 
                                             debug_name="ServerConnect"):
                LOGGER.info(f"Found Server connect warn: {game_tab_id}")
                self.resolve_scenario(self.SERVER_CONNECT, game_window, self.close_points)
        
        except Exception as e:
            LOGGER.error(f'An error occured during  detect & solve login window: {e}', exc_info=True)

class CrashDialogScenario:
    def __init__(self, settings: QSettings, parent):
        points = settings.value('Detection/CrashDialogPoints', type=str)
        self.crash_dialog_points = ast.literal_eval(points)
        self.close_points = ((self.crash_dialog_points[-1][0:2]),)
        # print(self.close_warn_points)
    
    def resolve_crash(self, game_window):
        title = game_window.title
        try:
            LOGGER.info(f"Found Crash report: {title}")
            screen_points = [to_screen_coord(p, game_window) for p in self.close_points]
            WindowUtil.focus(game_window)
            Resolver.do_single_click(screen_points)
        
        except Exception as e:
            LOGGER.error(f'An error occured during  detect & solve crash report: {e}', exc_info=True)


class ReloadGameTabScenario:
    def __init__(self, settings: QSettings, parent):
        points = settings.value('Detection/CrashDialogPoints', type=str)
        self.crash_dialog_points = ast.literal_eval(points)
        self.close_points = ((self.crash_dialog_points[-1][0:2]),)
        # print(self.close_warn_points)
    
    def resolve_reload(self, game_window):
        title = game_window.title
        try:
            LOGGER.info(f"Found Crash report: {title}")
            screen_points = [to_screen_coord(p, game_window) for p in self.close_points]
            WindowUtil.focus(game_window)
            Resolver.do_single_click(screen_points)
        
        except Exception as e:
            LOGGER.error(f'An error occured during  detect & solve crash report: {e}', exc_info=True)