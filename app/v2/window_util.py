
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
        # time.sleep(0.1)

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
    
    @staticmethod
    def check_pixel_pattern(game_window, screenshot, pixel_points_config, debug_name=None, color_tolerance=7):
            """
            Generic method to check a pixel pattern against a given window.
            Returns a tuple: (bool is_match, list overlay_points).
            """
            
            title = 'whole screen'
            if game_window:
                title = game_window.title
                
            if debug_name:
                print(f"===Debug: Checking {debug_name} for '{title}'...")
            
            try:
                # Ensure the window is active before taking a screenshot for reliability

                all_match = True
                
                for point_data in pixel_points_config:
                    x, y, expected_r, expected_g, expected_b = point_data
                    # x, y = WindowUtil.to_screen_coord((x_offset, y_offset), game_window)
                    expected_rgb = (expected_r, expected_g, expected_b)

                    # Get the color of the pixel relative to the window's top-left
                    actual_rgb = screenshot.getpixel((x, y))
                    if not WindowUtil.is_color_match(actual_rgb, expected_rgb, color_tolerance):
                        all_match = False
                        break # No need to check further if one pixel doesn't match

                if all_match:
                    if debug_name:
                        print(f"Pixel check passed: {debug_name} at ({x},{y}), expected {expected_rgb}, got {actual_rgb}.")
                else:
                    if debug_name:
                        screen_x, screen_y = WindowUtil.to_screen_coord((x, y), game_window)
                        print(f"screen coordinate: {debug_name} at ({screen_x},{screen_y}), expected {expected_rgb}, got {actual_rgb}.")
                        print(f"Pixel check not match: {debug_name} at ({x},{y}), expected {expected_rgb}, got {actual_rgb}.")

                return all_match

            except Exception as e:
                print(f"Worker: Error during {debug_name} detection for '{title}': {e}")
                return False
            
    @staticmethod
    def is_color_match(actual_rgb, expected_rgb, tolerance=5):
        """
        Checks if an actual RGB color is within a given tolerance of an expected RGB color.
        """
        return (
            abs(actual_rgb[0] - expected_rgb[0]) <= tolerance and
            abs(actual_rgb[1] - expected_rgb[1]) <= tolerance and
            abs(actual_rgb[2] - expected_rgb[2]) <= tolerance
        )
    
    @staticmethod
    def to_screen_coord(point, game_window):
        return point[0] + game_window.left, point[1] + game_window.top