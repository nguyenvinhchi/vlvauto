
import time
import pyautogui
import pygetwindow

class WindowUtil:
    @staticmethod
    def find_game_windows(title: str):
        """
        Scans for game windows based on the predefined title pattern.
        Stores the found window objects in self.game_windows and logs them.
        """
        try:
            # Find all windows that contain the WINDOW_TITLE_PATTERN in their title
            # all_windows = find_window(self.WINDOW_TITLE_PATTERN)
            all_windows = pygetwindow.getWindowsWithTitle(title)

            if all_windows:
                detected_titles = [win.title for win in all_windows]
                log_message = f"Detected {len(all_windows)} game windows: {', '.join(detected_titles)}"
                print(f"Worker: {log_message}")
                return all_windows
            else:
                log_message = f"No game windows found with title pattern: '{title}'"
                print(f"Worker: {log_message}")

        except Exception as e:
            log_message = f"Error finding windows: {e}"
            print(f"Worker: {log_message}")
            
    @staticmethod
    def send_trl_tab(window):
        pyautogui.hotkey('ctrl', 'tab')
        time.sleep(1)

    @staticmethod
    def focus(window):
        try:
            window.activate()
            time.sleep(1)
        except:
            print(f'Failed to focus window: {window.title}')

    @staticmethod
    def screen_shot(window):
        try:
            screenshot = pyautogui.screenshot(region=(
                    window.left, window.top, window.width, window.height
                ))
            return screenshot
        except:
            print(f'Failed to screenshot window: {window.title}')

    @staticmethod
    def screen_shot_whole_screen():
        try:
            screenshot = pyautogui.screenshot()
            return screenshot
        except:
            print(f'Failed to screenshot whole screen')

    @staticmethod
    def get_hwnd(window):
        return window._hWnd