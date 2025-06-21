import os
from PyQt6.QtCore import QObject, QTimer, pyqtSlot, QThread, pyqtSignal, QSettings
from PIL import Image

from app.detect_game_widget import get_window_screenshot
from app.get_game_window import find_window
from app.log_factory import create_logger
from app.game_scenario import StuckBuyingGameScenario, TownStuckGameScenario

LOGGER = create_logger()

class DetectionWorker(QObject):
    solve_action_requested = pyqtSignal(str, int, tuple)

    def __init__(self, settings: QSettings):
        super().__init__()
        self.settings=settings
        self.WINDOW_TITLE_PATTERN = settings.value("Detection/GameWindowTitlePattern", "VoLamViet")
        CHECK_INTERVAL = settings.value("Detection/CheckInterval", 30, type=int)
        self.CHECK_INTERVAL_MS = CHECK_INTERVAL * 1000  # 30 seconds
        self.timer = None  # Will be created after moving to thread
        self.game_windows = None
        self.game_scenarios = [StuckBuyingGameScenario(settings), TownStuckGameScenario(settings) ]
        for scenario in self.game_scenarios:
            scenario.setParent(self)
            scenario.solve_action_requested.connect(self.solve_action_requested)
        
    @pyqtSlot()
    def setup(self):
        self.timer = QTimer(self)
        self.timer.setInterval(self.CHECK_INTERVAL_MS)
        self.timer.timeout.connect(self.run_detection)
        LOGGER.info("DetectionWorker setup complete")
        LOGGER.info(f"Timer thread: {QThread.currentThread()}, Worker thread: {self.thread()}")

    @pyqtSlot()
    def start(self):
        LOGGER.info("DetectionWorker received START signal")
        self.running = True
        self.detect_window()

        if self.game_windows:
            
            LOGGER.info(f"starting Timer, its thread: {QThread.currentThread()}, Worker thread: {self.thread()}")
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

        LOGGER.debug("Running detection loop")

        try:
            LOGGER.debug("Running detection")
            for game_window in self.game_windows:
                screenshot = self.capture_window(game_window)
                for scenario in self.game_scenarios:
                    r = scenario.detect_and_solve(game_window, screenshot)
                    if r is True:
                        self.save_screenshot(game_window, screenshot)
        except Exception as e:
            LOGGER.error(f"Detection error: {e}")
            
    def save_screenshot(self, game_window, screenshot):
        folder = "data/screenshot"
        os.makedirs(folder, exist_ok=True)  # Ensure the directory exists
        filename = os.path.join(folder, f"{game_window.title}.png")
        img = Image.fromarray(screenshot)
        img.save(filename)

    def detect_window(self):
        self.game_windows = find_window(self.WINDOW_TITLE_PATTERN)
        if not self.game_windows:
            LOGGER.info("No open game windows")
        else:
            LOGGER.info(f"Detected {len(self.game_windows)} game windows")

    def capture_window(self, game_window):
        try:
            return get_window_screenshot(game_window)
        except Exception as e:
            self.game_windows.remove(game_window)
            LOGGER.error(f'This window may had been exited, remove from processing list: {game_window.title}')
