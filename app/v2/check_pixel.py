
class PixelUtil:
    @staticmethod
    def check_pixel_pattern(game_window, screenshot, pixel_points_config, debug_name=None, color_tolerance=7):
            """
            Generic method to check a pixel pattern against a given window.
            Returns a tuple: (bool is_match, list overlay_points).
            """

            if debug_name:
                print(f"===Debug: Checking {debug_name} for '{game_window.title}'...")
            

            try:
                # Ensure the window is active before taking a screenshot for reliability

                all_match = True
                for point_data in pixel_points_config:
                    x_offset, y_offset, expected_r, expected_g, expected_b = point_data
                    expected_rgb = (expected_r, expected_g, expected_b)

                    # Get the color of the pixel relative to the window's top-left
                    actual_rgb = screenshot.getpixel((x_offset, y_offset))
                    if not PixelUtil.is_color_match(actual_rgb, expected_rgb, color_tolerance):
                        all_match = False
                        break # No need to check further if one pixel doesn't match

                # gx, gy = x_offset + game_window.left, y_offset + game_window.top

                if all_match:
                    if debug_name:
                        print(f"Pixel check passed: {debug_name} at ({x_offset},{y_offset}), expected {expected_rgb}, got {actual_rgb}.")
                else:
                    if debug_name:
                        print(f"Pixel check not match: {debug_name} at ({x_offset},{y_offset}), expected {expected_rgb}, got {actual_rgb}.")

                return all_match

            except Exception as e:
                print(f"Worker: Error during {debug_name} detection for '{game_window.title}': {e}")
                return False
            
        # Helper function to check if a pixel color matches an expected color within tolerance
    def is_color_match(actual_rgb, expected_rgb, tolerance=5):
        """
        Checks if an actual RGB color is within a given tolerance of an expected RGB color.
        """
        return (
            abs(actual_rgb[0] - expected_rgb[0]) <= tolerance and
            abs(actual_rgb[1] - expected_rgb[1]) <= tolerance and
            abs(actual_rgb[2] - expected_rgb[2]) <= tolerance
        )