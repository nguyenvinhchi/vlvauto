import ast
import time
from PyQt6.QtCore import QObject, pyqtSignal, QSettings, QTimer
import pyautogui
import pygetwindow as gw

from app.get_game_window import find_window
from app.log_factory import create_logger

LOGGER = create_logger(name='Worker_v22')

COLOR_TOLERANCE = 10 # This can also be moved to settings if desired

# Helper function to check if a pixel color matches an expected color within tolerance
def _is_color_match(actual_rgb, expected_rgb, tolerance=5):
    """
    Checks if an actual RGB color is within a given tolerance of an expected RGB color.
    """
    return (
        abs(actual_rgb[0] - expected_rgb[0]) <= tolerance and
        abs(actual_rgb[1] - expected_rgb[1]) <= tolerance and
        abs(actual_rgb[2] - expected_rgb[2]) <= tolerance
    )

class Worker(QObject):
    """
    Worker thread to perform automation tasks in the background.
    It emits signals to update the UI on the main thread.
    """
    # Signal emitted when a task starts (e.g., a scheduled check)
    task_started = pyqtSignal(str)
    # Signal emitted when a task finishes
    task_finished = pyqtSignal(str)
    # Signal emitted when the worker is busy and cannot start a new task
    worker_busy = pyqtSignal(str)
    # New signal to request overlay drawing on the main UI thread
    show_overlay = pyqtSignal(list) 

    def __init__(self, settings: QSettings):
        """
        Initializes the Worker thread.
        Sets up a flag to track if the worker is currently busy.
        """
        super().__init__()
        self.settings=settings
        self._is_running = False
        self._timer = None

        self.WINDOW_TITLE_PATTERN = settings.value("Detection/GameWindowTitlePattern", "VLV-A")
        CHECK_INTERVAL = settings.value("Detection/CheckInterval", 60, type=int)
        self.CHECK_INTERVAL_MS = CHECK_INTERVAL * 1000  # 30 seconds

        # points to login
        # points[0] -> Login button -> click
        # points[1] -> Select server -> click
        # points[2] -> Select character -> double click
        # points[3] -> warning dialog close button -> click
        points = settings.value('Detection/LoginPoints', defaultValue="((276,370),(315,223),(153,321),(353,317))",  type=str)
        self.login_points = ast.literal_eval(points) 

        # main mumu window identified by 3 points and colors
        points = settings.value('Detection/GameWindowMainPoints', type=str)
        self.game_window_main_points = ast.literal_eval(points)
        
        # game window tab in Login screen: 3 or points with colors
        points = settings.value('Detection/GameWindowLoginPoints', type=str)
        self.game_window_login_points = ast.literal_eval(points)

        self._is_busy = False
        self._is_running = True # Control the worker's main loop
        self._is_paused = False # Control pausing of the worker's tasks
        self.game_windows = [] # List to store detected game window objects

    def start_loop(self):
        if not self._is_running:
            self._is_running = True
            self.status_updated.emit("Active")
            print("Worker: Starting the scheduler loop...")
            # Use QTimer for a more robust, non-blocking interval in a QThread
            self._timer = QTimer(self)
            self._timer.timeout.connect(self.scheduler_loop)
            self._timer.start(self.CHECK_INTERVAL_MS) 
    
    def stop_loop(self):
        if self._is_running:
            self._is_running = False
            self.status_updated.emit("Inactive")
            print("Worker: Stopped the scheduler loop.")
            if self._timer:
                self._timer.stop()

    def scheduler_loop(self, task_name="Scheduled Check"):
        """
        Performs the actual automation task. This method is called as a slot
        when the 'start_worker_task' signal is emitted from the main thread.
        """
        if self._is_busy:
            self.worker_busy.emit(f"Worker is busy with another task. Skipping {task_name}.")
            return

        self._is_busy = True
        self.task_started.emit(f"Starting: {task_name}...")
        print(f"Worker: Starting {task_name}...")

        try:
            # Step 1: Scan for game windows
            self._find_game_windows()

            if not self.game_windows:
                self.task_finished.emit(f"Finished: {task_name}. No game windows to process.")
                print(f"Worker: Finished {task_name}. No game windows to process.")
                self._is_busy = False
                return # Exit if no windows found
            
           # Iterate through each detected game window
            for i, game_window in enumerate(self.game_windows):
                if not self._is_running or self._is_paused:
                    self.task_finished.emit(f"Task {task_name} interrupted during window processing.")
                    print(f"Worker: Task {task_name} interrupted.")
                    self._is_busy = False
                    return

                print(f"Worker: Processing window '{game_window.title}' ({i+1}/{len(self.game_windows)})...")
                
                # Step 2: Get focus to the window
                try:
                    game_window.activate()
                    time.sleep(1) # Give it a moment to become active
                    print(f"Worker: Activated window '{game_window.title}'.")
                except gw.PyGetWindowException as e:
                    print(f"Worker: Could not activate window '{game_window.title}': {e}. Skipping this window.")
                    continue # Skip to next window if activation fails

                # --- Dynamic Tab Iteration Phase ---
                print(f"Worker: Starting dynamic tab iteration for window '{game_window.title}'...")

                # Phase 1: Find the main tab
                main_tab_found = False
                max_initial_tab_attempts = 10 # Max Ctrl+Tab presses to find main tab initially
                
                for attempt in range(max_initial_tab_attempts):
                    if not self._is_running or self._is_paused:
                        self.task_finished.emit(f"Task {task_name} interrupted during initial tab discovery.")
                        print(f"Worker: Task {task_name} interrupted.")
                        self._is_busy = False
                        return

                    if self._is_main_mumu_tab(game_window):
                        main_tab_found = True
                        print(f"Worker: Main MuMu tab found after {attempt + 1} attempts.")
                        break
                    
                    pyautogui.hotkey('ctrl', 'tab')
                    time.sleep(1) # 1 second delay as requested
                    print(f"Worker: Ctrl+Tab pressed, checking next tab for main tab...")

                if not main_tab_found:
                    print(f"Worker WARNING: Could not find main MuMu tab after {max_initial_tab_attempts} attempts for window '{game_window.title}'. Skipping this window.")
                    continue # Skip to next game window if main tab not found

                # Phase 2: Iterate through game tabs until main tab is seen again
                print(f"Worker: Starting game tab processing for window '{game_window.title}'...")
                game_tabs_processed_in_cycle = 0
                max_game_tab_processing_iterations = 20 # Safeguard to prevent infinite loop

                # Move from main tab to the first game tab (or back to main if no game tabs)
                pyautogui.hotkey('ctrl', 'tab')
                time.sleep(0.5) # Short delay for tab switch

                for tab_process_idx in range(max_game_tab_processing_iterations):
                    if not self._is_running or self._is_paused:
                        self.task_finished.emit(f"Task {task_name} interrupted during game tab processing.")
                        print(f"Worker: Task {task_name} interrupted.")
                        self._is_busy = False
                        return
                    
                    # Check if we've cycled back to the main tab
                    if self._is_main_mumu_tab(game_window):
                        print(f"Worker: Cycled back to main tab. Finished processing game tabs for window '{game_window.title}'. Total game tabs processed in this cycle: {game_tabs_processed_in_cycle}.")
                        break # Exit the game tab processing loop
                    
                    current_game_tab_title = game_window.title
                    game_tabs_processed_in_cycle += 1
                    print(f"Worker: Processing game tab '{current_game_tab_title}' (Game Tab #{game_tabs_processed_in_cycle})...")
                    
                    # Step 5: Run game scenario detection (Game Login first)
                    if self._is_game_login_scenario(game_window):
                        print(f"Worker: Game Login scenario detected on tab '{current_game_tab_title}'. Attempting to resolve...")
                        self._resolve_window_login1(game_window) # Call the resolution method
                    else:
                        print(f"Worker: No Game Login scenario detected on tab '{current_game_tab_title}'.")
                        # You would add other scenario checks here in future MVPs
                        # e.g., if self._is_another_scenario(game_window): ...

                    pyautogui.hotkey('ctrl', 'tab')
                    time.sleep(0.5) # Short delay for tab switch
                else:
                    print(f"Worker WARNING: Exceeded max game tab processing iterations ({max_game_tab_processing_iterations}) for window '{game_window.title}'. May not have processed all tabs.")

        except Exception as e:
            print(f"Worker: Task {task_name} failed: {e}")
        finally:
            self._is_busy = False # Ensure busy flag is reset

    def stop_worker(self):
        """Stops the worker thread's event loop."""
        self._is_running = False
        self._is_busy = False # Reset busy state on stop
        self.quit() # Stop the QThread's event loop
        print("Worker: Stopping...")

    def pause_worker(self):
        """Pauses the execution of tasks within the worker."""
        self._is_paused = True
        print("Worker: Paused.")

    def resume_worker(self):
        """Resumes the execution of tasks within the worker."""
        self._is_paused = False
        print("Worker: Resumed.")

    @property
    def is_busy(self):
        """Returns True if the worker is currently executing a task."""
        return self._is_busy
    
    def _find_game_windows(self):
        """
        Scans for game windows based on the predefined title pattern.
        Stores the found window objects in self.game_windows and logs them.
        """
        self.game_windows = [] # Clear previous list
        try:
            # Find all windows that contain the WINDOW_TITLE_PATTERN in their title
            # all_windows = find_window(self.WINDOW_TITLE_PATTERN)
            all_windows = gw.getWindowsWithTitle(self.WINDOW_TITLE_PATTERN)

            if all_windows:
                self.game_windows = all_windows
                detected_titles = [win.title for win in self.game_windows]
                log_message = f"Detected {len(self.game_windows)} game windows: {', '.join(detected_titles)}"
                print(f"Worker: {log_message}")
            else:
                log_message = f"No game windows found with title pattern: '{self.WINDOW_TITLE_PATTERN}'"
                print(f"Worker: {log_message}")

        except Exception as e:
            log_message = f"Error finding windows: {e}"
            print(f"Worker: {log_message}")
            self.task_finished.emit(f"Window scan failed: {e}")

    def _check_pixel_pattern(self, game_window, pixel_points_config, debug_name="Pattern", color_tolerance=7):
        """
        Generic method to check a pixel pattern against a given window.
        Returns a tuple: (bool is_match, list overlay_points).
        """
        if not pixel_points_config:
            print(f"Worker: No {debug_name} points configured. Skipping check.")
            return False, []

        print(f"Worker: Checking {debug_name} for '{game_window.title}'...")
        
        # Prepare points for overlay (screen coordinates)
        overlay_points = []

        try:
            # Ensure the window is active before taking a screenshot for reliability
            game_window.activate()
            time.sleep(0.5) # Give OS time to activate window

            screenshot = pyautogui.screenshot(region=(
                game_window.left, game_window.top, game_window.width, game_window.height
            ))

            all_match = True
            for point_data in pixel_points_config:
                x_offset, y_offset, expected_r, expected_g, expected_b = point_data
                expected_rgb = (expected_r, expected_g, expected_b)

                # Get the color of the pixel relative to the window's top-left
                actual_rgb = screenshot.getpixel((x_offset, y_offset))

                # Add point to overlay list (convert to screen coordinates)
                screen_x = game_window.left + x_offset
                screen_y = game_window.top + y_offset
                overlay_points.append((screen_x, screen_y)) # Only need screen coords for drawing

                if not _is_color_match(actual_rgb, expected_rgb, color_tolerance):
                    print(f"Worker: {debug_name} Pixel at ({x_offset},{y_offset}) color mismatch. Expected {expected_rgb}, Got {actual_rgb}. Mismatch found.")
                    all_match = False
                    break # No need to check further if one pixel doesn't match

            if all_match:
                print(f"Worker: All {debug_name} pixel checks passed.")
            else:
                print(f"Worker: {debug_name} pixel pattern did NOT match.")

            # Return the result and the list of points
            return all_match, overlay_points

        except Exception as e:
            print(f"Worker: Error during {debug_name} detection for '{game_window.title}': {e}")
            return False, []
        
    def _is_main_mumu_tab(self, game_window):
        """
        Checks if the current game tab is the main MuMu tab by checking pixel colors
        defined in game_window_main_points from settings.
        This is crucial to avoid solving scenarios on the main (non-game) tab.
        """
        if not self.game_window_main_points:
            print("Worker: No GameWindowMainPoints configured. Cannot reliably detect main tab.")
            return False # Cannot determine, assume not main tab to be safe

        print(f"Worker: Checking if '{game_window.title}' is the main MuMu tab using configured points...")
        try:
            # Take a screenshot of the window's region
            # Ensure the window is active before taking a screenshot for reliability
            game_window.activate()
            time.sleep(0.5) # Give OS time to activate window

            screenshot = pyautogui.screenshot(region=(
                game_window.left, game_window.top, game_window.width, game_window.height
            ))

            for point_data in self.game_window_main_points:
                x_offset, y_offset, expected_r, expected_g, expected_b = point_data
                expected_rgb = (expected_r, expected_g, expected_b)

                # Get the color of the pixel relative to the window's top-left
                actual_rgb = screenshot.getpixel((x_offset, y_offset))

                if not _is_color_match(actual_rgb, expected_rgb, COLOR_TOLERANCE):
                    print(f"Worker: Pixel at ({x_offset},{y_offset}) color mismatch. Expected {expected_rgb}, Got {actual_rgb}. Not main tab.")
                    return False # Not the main tab

            print("Worker: All configured pixel checks passed. This is likely the main MuMu tab.")
            return True # All pixels match, likely the main tab

        except Exception as e:
            print(f"Worker: Error during main tab detection for '{game_window.title}': {e}")
            # If an error occurs during screenshot/pixel check, it's safer to assume it's not the main tab
            return False
        
    def _is_game_login_scenario(self, game_window):
        """
        Checks if the current game tab displays the login scenario by checking pixel colors
        defined in game_window_login_points from settings.
        If a match is found, it emits the show_overlay signal with the detected points.
        """
        is_match, points = self._check_pixel_pattern(game_window, self.game_window_login_points, "Game Login Scenario")
        if is_match:
            print("Worker: Game Login scenario detected. Showing overlay.")
            self.show_overlay.emit(points) # Emit the signal to draw the overlay
            time.sleep(2) # Give the user time to see the overlay
        return is_match
    
    def _resolve_window_login1(self, game_window):
        """
        Resolves the game login scenario by simulating clicks based on configured points.
        Assumes the game_window is already active.
        """
        print(f"Worker: Attempting to resolve login for '{game_window.title}'...")
        
        try:
            # Click points[0] (login button)
            login_btn_x, login_btn_y = self.login_points[0]
            pyautogui.click(game_window.left + login_btn_x, game_window.top + login_btn_y)
            print(f"Worker: Clicked Login Button at ({game_window.left + login_btn_x}, {game_window.top + login_btn_y})")
            time.sleep(3) # Wait for 3 seconds delay

            # Check if the worker is still running and not paused before proceeding
            if not self._is_running or self._is_paused:
                print("Worker: Login resolution interrupted during delay.")
                return

            # Click points[1] (server select button)
            server_select_x, server_select_y = self.login_points[1]
            pyautogui.click(game_window.left + server_select_x, game_window.top + server_select_y)
            print(f"Worker: Clicked Server Select Button at ({game_window.left + server_select_x}, {game_window.top + server_select_y})")
            time.sleep(5) # Wait for 5 seconds delay

            # Check if the worker is still running and not paused before proceeding
            if not self._is_running or self._is_paused:
                print("Worker: Login resolution interrupted during delay.")
                return

            # Double click points[2] (character select button)
            char_select_x, char_select_y = self.login_points[2]
            pyautogui.doubleClick(game_window.left + char_select_x, game_window.top + char_select_y)
            print(f"Worker: Double clicked Character Select Button at ({game_window.left + char_select_x}, {game_window.top + char_select_y})")
            time.sleep(3) # Give some time for character selection to load

            print(f"Worker: Login resolution sequence completed for '{game_window.title}'.")

        except Exception as e:
            print(f"Worker ERROR: Failed to resolve login for '{game_window.title}': {e}")
            self.task_finished.emit(f"Login resolution failed for '{game_window.title}': {e}")
