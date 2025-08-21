import ast
import time
from PyQt6.QtCore import QSettings

from app.log_factory import create_logger
from app.v2.resolver import Resolver
from app.v2.window_util import WindowUtil

LOGGER = create_logger(name='CheckAutoIsOn')

class CheckAutoIsOn:
    def __init__(self, settings: QSettings):
        points = settings.value('Detection/GameAutoOn', type=str)
        self.game_auto_on_points = ast.literal_eval(points)

        points = settings.value('Detection/GameAutoOff', type=str)
        self.game_auto_off_points = ast.literal_eval(points)

        points = settings.value('Detection/GameAutoButtonPoints', type=str)
        self.game_auto_points = (ast.literal_eval(points),)


    def detect_game_auto_off(self, game_window):
        WindowUtil.focus(game_window)
        time.sleep(4)
        screenshot = WindowUtil.screen_shot(game_window)
        if WindowUtil.check_pixel_pattern(game_window, screenshot, pixel_points_config=self.game_auto_off_points, color_tolerance=5):
            LOGGER.info(f'===game auto is off => simulate click to {self.game_auto_points}, window: {game_window.title}')
            screen_points = [WindowUtil.to_screen_coord(p, game_window) for p in self.game_auto_points]
            Resolver.do_single_click(screen_points)