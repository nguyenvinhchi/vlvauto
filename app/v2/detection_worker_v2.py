import os
from typing import List
from PyQt6.QtCore import QObject, QTimer, pyqtSlot, QSettings, pyqtSignal

from app.get_game_window import find_window
from app.log_factory import create_logger
from app.game_scenario import LoginSelectCharacterScenario, LoginSelectServerScenario, AccountLoginedWarningScenario, StuckBuyingGameScenario, TownStuckGameScenario, UserPassLoginScenario
from app.v2.game_tab_iterate import GameTabIterate
from app.v2.window_util import WindowUtil

LOGGER = create_logger()

class DetectionWorkerV2(GameTabIterate, QObject):

    def __init__(self, settings: QSettings):
        super().__init__(settings)
        self.settings=settings
        self.WINDOW_TITLE_PATTERN = settings.value("Detection/GameWindowTitlePattern", "A1")
        self.inprogress_timeout_seconds = settings.value("Detection/ResolveInprogressTimeoutSeconds", 60, type=int)
        CHECK_INTERVAL = settings.value("Detection/CheckInterval", 60, type=int)
        self.CHECK_INTERVAL_MS = CHECK_INTERVAL * 1000  # 30 seconds
        self.timer = None  # Will be created after moving to thread
        self.game_windows = None
        self.inprogress_start = None
        # --- NEW FLAG ---
        self.resolve_action_inprogress = False # Controls whether detection proceeds
        self.game_scenarios = [
            StuckBuyingGameScenario(settings, self),
            UserPassLoginScenario(settings, self),
            TownStuckGameScenario(settings, self),
            AccountLoginedWarningScenario(settings, self),
            LoginSelectServerScenario(settings, self),
            LoginSelectCharacterScenario(settings, self),
        ]
        # self.game_scenarios = [StuckBuyingGameScenario(settings), 
        #                        TownStuckGameScenario(settings),
        #                        LoginScenarioV2(settings),
        #                        LoginSelectServerScenario(settings),
        #                        LoginSelectCharacterScenario(settings),
        #                        LoginServerConnectWarningScenario(settings)
        #                        ]
        for scenario in self.game_scenarios:
            scenario.setParent(self)
    
    @pyqtSlot()
    def setup(self):
        self.timer = QTimer(self)
        self.timer.setInterval(self.CHECK_INTERVAL_MS)
        self.timer.timeout.connect(self.run_detection)
        LOGGER.info("DetectionWorker setup complete")

    @pyqtSlot()
    def start(self):
        LOGGER.info("DetectionWorker received START signal")
        self.running = True
        self.detect_window()

        if self.game_windows:
            
            LOGGER.info(f"starting detection timer (default wait 30s)")
            self.timer.start()
        else:
            LOGGER.warning("No game windows found.")

    @pyqtSlot()
    def stop(self):
        LOGGER.info("DetectionWorker received STOP signal")
        self.running = False
        if self.timer:
            self.timer.stop()
        LOGGER.info("Stopped DetectionWorker")

    @pyqtSlot()
    def cleanup(self):
        LOGGER.info("Cleanup called.")
        self.stop()

    def run_detection(self):
        if not self.running or not self.game_windows:
            return

        try:
            LOGGER.debug("Running detection")
            for game_window in self.game_windows:
                    # iterate game tabs and check_game_scenario for each mumu window
                    self.iterate_game_tab(game_window)

        except Exception as e:
            LOGGER.error(f"Detection error: {e}", exc_info=True)
            
    def save_screenshot(self, screenshot, game_tab_id="0"):
        folder = "data/screenshot"
        os.makedirs(folder, exist_ok=True)  # Ensure the directory exists
        filename = os.path.join(folder, f"{game_tab_id}.png")
        screenshot.save(filename)

    def detect_window(self):
        self.game_windows = WindowUtil.find_game_windows(self.WINDOW_TITLE_PATTERN)
        if not self.game_windows:
            LOGGER.info("No open game windows")
        else:
            LOGGER.info(f"Detected {len(self.game_windows)} game windows")
    
    def get_game_scenarios(self):
        return self.game_scenarios
