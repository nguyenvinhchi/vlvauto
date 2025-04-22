
from unittest import TestCase

from app.detect_game_widget import detect_pattern, read_image_file


class DetectGameWidgetTests(TestCase):
    def test_detect_DuongChau_town_pattern(self):
        pattern_template_path = "images/input/vlv-DuongChau_2.png"
        # screenshot_image_path = "images/input/vlv-LDQ-fullmap_1.png"
        screenshot_image_path = "images/input/vlv-DuongChau-fullmap_2.png"
        pattern_img = read_image_file(pattern_template_path)
        screenshot_img = read_image_file(screenshot_image_path)
        lower_color_range = [53, 53, 8] 
        upper_color_range = [71, 255, 255]
        r = detect_pattern(pattern_img, screenshot_img, 
                           lower_color_range=lower_color_range,
                           upper_color_range=upper_color_range,
                           is_pattern_img_masked=False, 
                           is_screenshot_img_masked=False, 
                           threshold=0.7)
        if r:
            m, w, h = r
            print(f'Found matched size: {w}, {h}')
        else:
            print('Not found')

    def test_detect_buying_shop_pattern(self):
        pattern_template_path = "images/output/vlv-stuck-buying-med-shop_1_masked.png"
        screenshot_image_path = "images/input/vlv-stuck-buying-med-fullmap_1.png"
        pattern_img = read_image_file(pattern_template_path)
        screenshot_img = read_image_file(screenshot_image_path)
        lower_color_range = [19, 0, 0]
        upper_color_range = [45, 75, 135]
        r = detect_pattern(pattern_img, screenshot_img, 
                           lower_color_range=lower_color_range,
                           upper_color_range=upper_color_range,
                           is_pattern_img_masked=True, 
                           is_screenshot_img_masked=False, 
                           threshold=0.7)
        if r:
            m, w, h = r
            print(f'Found matched size: {w}, {h}')
        else:
            print('Not found')

    def test_detect_buying_bag_pattern(self):
        # pattern_template_path = "images/output/vlv-LDQ-smallmap_2_masked.png"
        # pattern_template_path = "images/output/vlv-DuongChau-smallmap_2_masked.png"
        pattern_template_path = "images/output/vlv-DuongChau-smallmap_1_masked.png"
        # screenshot_image_path = "images/input/vlv-DuongChau-fullmap_1.png"
        screenshot_image_path = "images/input/vlv-DuongChau-fullmap_4.png"
        pattern_img = read_image_file(pattern_template_path)
        screenshot_img = read_image_file(screenshot_image_path)
        lower_color_range = [38, 206, 0]
        upper_color_range = [94, 255, 165]
        r = detect_pattern(pattern_img, screenshot_img, 
                           lower_color_range=lower_color_range,
                           upper_color_range=upper_color_range,
                           is_pattern_img_masked=True, 
                           is_screenshot_img_masked=False, 
                           threshold=0.7)
        if r:
            m, w, h = r
            print(f'Found matched size: {w}, {h}')
        else:
            print('Not found')            