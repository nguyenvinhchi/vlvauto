import os
import time
import cv2
import numpy as np
import mss

from app.resource_util import resource_path

def print_image_info(name, img):
    if img is None:
        print(f"⚠️ {name} is None")
        return
    print(f"{name} shape: {img.shape}, dtype: {img.dtype}")
    if len(img.shape) == 2:
        print(f"{name} is Grayscale")
    elif len(img.shape) == 3:
        print(f"{name} has {img.shape[2]} channels")
    
def detect_pattern(pattern_img, screenshot_img, 
                  lower_color_range = [53, 53, 8], 
                  upper_color_range = [71, 255, 255], 
                  is_pattern_img_masked=True,
                  is_screenshot_img_masked=False,
                  threshold=0.70):

    # Convert template to HSV and isolate the text region
    pattern_masked = pattern_img if is_pattern_img_masked else get_masked_image(pattern_img, lower_color_range, upper_color_range)

    w, h = pattern_masked.shape[1], pattern_masked.shape[0]

    screenshot_masked = None
    if is_screenshot_img_masked:
        screenshot_masked = screenshot_img 
    else: 
        screenshot_masked = get_masked_image(screenshot_img, lower_color_range, upper_color_range)

    # print_image_info("Pattern", pattern_img)
    # print_image_info("Screenshot", screenshot_img)

    # print_image_info("pattern_masked", pattern_img)
    # print_image_info("screenshot_masked", screenshot_masked)

    # Match template
    assert screenshot_masked.shape[2] == pattern_masked.shape[2], "Channel mismatch!"
    result = cv2.matchTemplate(screenshot_masked, pattern_masked, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)

    matches = list(zip(*loc[::-1]))
    if matches:
        return matches[0], w, h
    else:
        # print(f"⚠️ Pattern not found. Saved debug images:\n- {warn_template_path}\n- {warn_screenshot_path}")
        return None

def read_image_file(image_path):
    template_resource_path = resource_path(image_path)
    image = cv2.imread(template_resource_path)
    return image

def write_image_for_human_check(img_path, img, append_name = 'masked'):
    img_dir, img_file = os.path.split(img_path)

    file_name, file_ext = os.path.splitext(img_file)

    out_path = os.path.join(img_dir, f"{file_name}_{append_name}{file_ext}")
    cv2.imwrite(out_path, img)
    return out_path

def get_window_screenshot(window):
    region = {
        "top": window.top,
        "left": window.left,
        "width": window.width,
        "height": window.height
    }
    return get_screenshot(region)

def get_screenshot(region):
    with mss.mss() as sct:
        return np.array(sct.grab(region))
    
def get_masked_image(image, 
                  lower_color_range = [53, 53, 8], 
                  upper_color_range = [71, 255, 255]
                  ):
    if image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    background_img = np.zeros_like(image)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Create mask & highlighted result
    mask = cv2.inRange(hsv, np.array(lower_color_range), np.array(upper_color_range))
    mask_inv = cv2.bitwise_not(mask)
    masked = cv2.bitwise_and(image, image, mask=mask) + \
        cv2.bitwise_and(background_img, background_img, mask=mask_inv)
    return masked