
import ast
import time
from PyQt6.QtCore import QSettings, QDateTime

from app.game_scenario import to_screen_coord
from app.log_factory import create_logger
from app.v2.resolver import Resolver

LOGGER = create_logger(name='AutoOpenGame')

class AutoOpenGame:
    """
    if it is main tab, try to open pre-configured game icon in main tab. 
    Next, auto login scenario check will try to login 
    Next, check game auto is OFF will try to turn ON game auto
    Time to check duration should be long like 10 minutes/30 minutes/60 minutes
    """
    def __init__(self, settings: QSettings):
        self.check_duration_seconds = settings.value('Detection/GameExitDurationSeconds', defaultValue=60, type=int)
        points = settings.value('Detection/GameShortcutPoints', defaultValue="", type=str)
        self.game_shortcut_points = ast.literal_eval(points)

        indexes = settings.value('Detection/GameShortcutIndexesToCheck', defaultValue=[0], type=list)
        self.game_shortcut_indexes = [int(idx) for idx in indexes]

        self.main_tab_point = [int(x) for x in settings.value('Detection/MainTabPoints', type=list)]
        self.game_shortcut_indexes = [int(idx) for idx in indexes]
        

        # state check start_time
        self.auto_open_check_start_time = {}

    def check_game_exit(self, hwnd, game_window):
        start_time = self.auto_open_check_start_time.get(hwnd)
        if start_time is None:
            self.auto_open_check_start_time[hwnd] = QDateTime.currentDateTime()
            return
        else:
            elapsed = start_time.secsTo(QDateTime.currentDateTime())
            if elapsed < self.check_duration_seconds:
                return
            
        # process check game exit and try re-open game tab
        LOGGER.info(f'===time to check game tab crashed - elapsed seconds: {elapsed}, window: {game_window.title}')
        for idx in self.game_shortcut_indexes:
            shortcut_point = self.game_shortcut_points[idx]
            LOGGER.info(f'simulate click game shortcut_point: {shortcut_point}, window: {game_window.title}')
            self.open_game_tab(shortcut_point, game_window)
            #reset start time
            self.auto_open_check_start_time[hwnd] = None

    def open_game_tab(self, shortcut_point, game_window):
        screen_point = to_screen_coord(shortcut_point, game_window)
        # click game icon
        Resolver.do_single_click((screen_point,))
        time.sleep(0.2)
        # click back to main tab
        LOGGER.debug(f'Simulate click main tab point {self.main_tab_point}')
        screen_point = to_screen_coord(self.main_tab_point, game_window)
        Resolver.do_single_click((screen_point,))
        time.sleep(0.2)
