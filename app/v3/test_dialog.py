import os
from PyQt6.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QListWidget, QTextEdit, QMessageBox,
    QWidget, QFileDialog
)
from PyQt6.QtCore import ( QSettings 
)

import pygetwindow as gw
import pyautogui
from datetime import datetime

from app.flow_layout import FlowLayout
from app.log_factory import create_logger
from app.pattern.image_select_dialog import ImageSelectDialog
from app.v2.window_util import WindowUtil
from app.v3.game_scenario import AccountLoginedWarningScenario, AutoOffGameScenario, BagOpenGameScenario, GameScenario, LoginSelectCharacterScenario, LoginSelectServerScenario, ServerConnectWarnScenario, ShopOpenGameScenario, TownStuckGameScenario, UserPassLoginScenario

TMP_DIR = "data/tmp"
os.makedirs(TMP_DIR, exist_ok=True)
LOGGER = create_logger(name='TestDialog')

IN_TOWN = 'IN_TOWN'
BAG_OPEN = 'BAG_OPEN'
SHOP_OPEN = 'SHOP_OPEN'
AUTO_OFF = 'AUTO_OFF'
LOGIN_SCREEN_1 = 'LOGIN_SCREEN_1'
LOGIN_SCREEN_2 = 'LOGIN_SCREEN_2'
LOGIN_SCREEN_3 = 'LOGIN_SCREEN_3'
LOGIN_WARN = 'LOGIN_WARN'
SERVER_CONNECT_WARN = 'SERVER_CONNECT_WARN'

class TestDialog(QDialog):
    town_stuck_game_scenario: TownStuckGameScenario = None
    login1_scenario: UserPassLoginScenario = None
    login2_scenario: LoginSelectServerScenario = None
    login3_scenario: LoginSelectCharacterScenario = None
    server_connect_warn_scenario: ServerConnectWarnScenario = None
    account_already_logined_scenario: AccountLoginedWarningScenario = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = parent.settings
        self.setWindowTitle("Test scenario")
        self.resize(600, 400)

        self.scenarios = [
            IN_TOWN,
            BAG_OPEN,
            SHOP_OPEN,
            AUTO_OFF,
            LOGIN_SCREEN_1,
            LOGIN_SCREEN_2,
            LOGIN_SCREEN_3,
            LOGIN_WARN,
            SERVER_CONNECT_WARN
        ]

        self.selected_scenario = None
        self.pattern_name_input = QLineEdit(self)
        self.pattern_name_input.setPlaceholderText("Enter pattern name or window title filter")

        # 1. Initialize the button
        self.test_button = self.create_test_button()
        self.test_button.clicked.connect(self.on_test)

        self.window_list = QListWidget(self)
        self.scenario_list = QListWidget(self)
        for item in self.scenarios:
            self.scenario_list.addItem(item)

        self.capture_button = QPushButton("Capture Image", self)
        self.capture_button.setEnabled(False)
        self.capture_button.clicked.connect(self.capture_window_image)

        self.window_list.itemSelectionChanged.connect(self.on_window_selected)
        self.scenario_list.itemSelectionChanged.connect(self.on_scenario_selected)

        self.point_output = QTextEdit(self)
        self.point_output.setReadOnly(True)

        self.select_image_button = QPushButton("Select Points", self)
        self.select_image_button.setEnabled(False)
        self.select_image_button.clicked.connect(self.select_points_on_image)

        self.refresh_button = QPushButton("Refresh Window List", self)
        self.refresh_button.clicked.connect(self.populate_window_list)

        self.change_image_button = QPushButton("Select existing image", self)
        self.change_image_button.clicked.connect(self.show_select_image_dialog)

        # Flow layout for buttons
        button_container = QWidget(self)
        button_flow = FlowLayout(button_container)
        button_flow.addWidget(self.select_image_button)
        button_flow.addWidget(self.change_image_button)

        layout = QVBoxLayout()
        list_layout = QHBoxLayout()

        window_list_layout = QVBoxLayout()
        window_list_layout.addWidget(self.window_list)
        window_list_layout.addWidget(self.capture_button)
        window_list_layout.addWidget(self.refresh_button)
        list_layout.addLayout(window_list_layout)

        scenario_layout = QVBoxLayout()
        scenario_layout.addWidget(self.scenario_list)
        scenario_layout.addWidget(self.test_button)
        list_layout.addLayout(scenario_layout)

        layout.addLayout(list_layout)

        layout.addWidget(self.pattern_name_input)
        layout.addWidget(button_container)
        layout.addWidget(QLabel("Captured Points (pos + RGB):"))
        layout.addWidget(self.point_output)

        self.setLayout(layout)

        self.selected_window_title = None
        self.image_path = None
        self.pattern_points = []

        self.populate_window_list()

    def create_test_button(self):
         # 1. Initialize the button
        test_button = QPushButton('Test')
        
        # 2. Assign an object name so the style sheet can target it specifically
        test_button.setObjectName('test_button')
        
        test_button.setEnabled(False)

        # 3. Apply the Style Sheet
        test_button.setStyleSheet("""
            /* Style for the ENABLED state (Highlight) */
            QPushButton#test_button:enabled {
                background-color: #4CAF50; /* Vibrant Green */
                color: #FFFFFF;
                border: 2px solid #388E3C;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
            }
            /* Style for the DISABLED state (Grayed out) */
            QPushButton#test_button:disabled {
                background-color: #555555; /* Darker Gray */
                color: #AAAAAA; /* Gray text */
                border: 1px solid #777777;
                padding: 10px;
                border-radius: 8px;
            }
        """)
        return test_button

    def populate_window_list(self):
        self.window_list.clear()
        title_filter = self.pattern_name_input.text().strip().lower()
        for win in gw.getAllTitles():
            if win.strip() and (title_filter in win.lower()):
                self.window_list.addItem(win)

    def on_test(self):
        LOGGER.info(f'test {self.selected_scenario} on window {self.selected_window_title}')
        scenario: GameScenario = self.create_scenario(name=self.selected_scenario, settings=self.settings)
        windows = WindowUtil.find_game_windows(self.selected_window_title)
        selected_window = windows[0]
        WindowUtil.focus(selected_window)
        screenshot = WindowUtil.screen_shot(selected_window)
        scenario.detect_and_solve(selected_window, screenshot)

    def on_window_selected(self):
        selected_items = self.window_list.selectedItems()
        if selected_items:
            self.selected_window_title = selected_items[0].text()
            self.capture_button.setEnabled(True)

    def on_scenario_selected(self):
        selected_items = self.scenario_list.selectedItems()
        if selected_items:
            self.selected_scenario = selected_items[0].text()
            if self.selected_window_title:
                self.test_button.setEnabled(True)

    def capture_window_image(self):
        windows = WindowUtil.find_game_windows(self.selected_window_title)
        if not windows:
            return
        win = windows[0]
        win.activate()
        pyautogui.sleep(1)  # wait for window to activate

        screenshot = WindowUtil.screen_shot(win)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.image_path = os.path.join(TMP_DIR, f"{self.selected_window_title}-{timestamp}.png")
        screenshot.save(self.image_path, format="PNG")

        self.select_image_button.setEnabled(True)
        QMessageBox.information(self, "Capture Done", f"Window image saved to {self.image_path}")

    def show_select_image_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Select image file",
            directory="data/",
            filter="Image Files (*.png *.jpg *.bmp *.jpeg)"
        )

        if file_path:
            print("Selected image:", file_path)
            self.image_path = file_path
        else:
            print("No file selected.")

    def select_points_on_image(self):
        if not self.image_path:
            QMessageBox.warning(self, "No Image", "Please capture an image first.")
            return

        def on_point_selected(pos, color):
            x, y = pos
            r, g, b = color
            self.pattern_points.append((*pos, *color))
            self.point_output.append(f"{x,y,r,g,b}")

        dialog = ImageSelectDialog(parent=self, image_path=self.image_path, on_point_selected=on_point_selected)
        dialog.exec()

    def create_scenario(self, name: str, settings: QSettings) -> GameScenario:
        if name == SHOP_OPEN:
            return ShopOpenGameScenario(settings)
        elif name == BAG_OPEN:
            return BagOpenGameScenario(settings)
        elif name == AUTO_OFF:
            return AutoOffGameScenario(settings)
        elif name == IN_TOWN:
            settings.setValue('Detection/TownStuckTimeout', 5)
            if TestDialog.town_stuck_game_scenario is None:
                TestDialog.town_stuck_game_scenario = TownStuckGameScenario(settings)
            return TestDialog.town_stuck_game_scenario
        elif name == LOGIN_SCREEN_1:
            if TestDialog.login1_scenario is None:
                TestDialog.login1_scenario = UserPassLoginScenario(settings)
            return TestDialog.login1_scenario
        elif name == LOGIN_SCREEN_2:
            if TestDialog.login2_scenario is None:
                TestDialog.login2_scenario = LoginSelectServerScenario(settings)
            return TestDialog.login2_scenario
        elif name == LOGIN_SCREEN_3:
            if TestDialog.login3_scenario is None:
                TestDialog.login3_scenario = LoginSelectCharacterScenario(settings)
            return TestDialog.login3_scenario
        elif name == SERVER_CONNECT_WARN:
            if TestDialog.server_connect_warn_scenario is None:
                TestDialog.server_connect_warn_scenario = ServerConnectWarnScenario(settings)
            return TestDialog.server_connect_warn_scenario
        elif name == LOGIN_WARN:
            if TestDialog.account_already_logined_scenario is None:
                TestDialog.account_already_logined_scenario = AccountLoginedWarningScenario(settings)
            return TestDialog.account_already_logined_scenario
        
        raise Exception(f'Scenario {name} is not supported!')