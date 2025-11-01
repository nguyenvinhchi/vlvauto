from datetime import datetime
import os
import cv2
import numpy as np
import pytesseract
from PIL import Image

# IMPORTANT: If Tesseract is not in your system's PATH, you must uncomment and set the path here:
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\chinv\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
TMP_DIR = "data/tmp"

def detect_map_name(image_path: str) -> str:
    """
    Detects the map name text from the top-right mini-map area by dynamically locating 
    the bounding box of the green text using color filtering and contour detection.

    The initial crop region is dynamically calculated as the top-right quadrant 
    with a height equal to 1/4 of the total image height.

    Args:
        image_path (str): Full path to the captured screenshot.
        logger (object): Logger object (or function) to output debug info.

    Returns:
        str: The detected map name, or an empty string if not found.
    """

    # Define range for bright green color in HSV (adjust if text color changes)
    lower_green = np.array([50, 70, 130])
    upper_green = np.array([70, 255, 255])
    try:
        # --- 1. Load Image and Define Dynamic Crop Region ---
        img = cv2.imread(image_path)
        if img is None:
            print(f"Failed to load image from {image_path}")
            return ""

        # Get original dimensions
        h_orig, w_orig, _ = img.shape
        
        # Calculate dynamic crop region based on 1/4 image height.
        # UPDATED: X-axis now starts at 85% width for a tighter crop, as requested.
        x1_p = int(w_orig * 0.85)
        y1_p = 0
        x2_p = w_orig
        y2_p = int(h_orig * 0.25) # 1/4 of the image height

        # --- 2. Crop the Image to GENEROUS Dynamic Top-Right Region ---
        cropped_img = img[y1_p:y2_p, x1_p:x2_p]
        if cropped_img.size == 0:
            print("Cropped image is empty.")
            return ""

        print(f"Initial dynamic crop: ({x1_p},{y1_p}) to ({x2_p},{y2_p})")

        # --- 3. Apply Color Filter (HSV Mask for Green Text) ---
        hsv = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2HSV)

        # Create mask: White where the color is green, black otherwise
        mask = cv2.inRange(hsv, lower_green, upper_green)

        # --- 3.5. Dynamic ROI refinement based on the mask (Find the tight bounding box) ---
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            print("No green text (contours) detected within the top-right region.")
            final_img_for_ocr = mask # Fallback to the full mask
        else:
            # Find the bounding box that encompasses ALL found green text contours
            x_min, y_min, x_max, y_max = cropped_img.shape[1], cropped_img.shape[0], 0, 0
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # Filter out very small noise contours (e.g., less than 5 pixels wide/high)
                if w > 5 and h > 5:
                    x_min = min(x_min, x)
                    y_min = min(y_min, y)
                    x_max = max(x_max, x + w)
                    y_max = max(y_max, y + h)

            if x_max > x_min and y_max > y_min:
                # Add a small padding (e.g., 5 pixels) for better OCR recognition
                padding = 5
                
                # Clip coordinates to stay within the cropped image boundaries
                x1_dynamic = max(0, x_min - padding)
                y1_dynamic = max(0, y_min - padding)
                x2_dynamic = min(cropped_img.shape[1], x_max + padding)
                y2_dynamic = min(cropped_img.shape[0], y_max + padding)

                # Dynamically crop the mask to only the detected green text area
                final_img_for_ocr = mask[y1_dynamic:y2_dynamic, x1_dynamic:x2_dynamic]
                print(f"Dynamically cropped ROI: ({x1_dynamic}, {y1_dynamic}) to ({x2_dynamic}, {y2_dynamic}) relative to initial crop.")
            else:
                print("Contours found but bounding box was invalid. Using full mask.")
                final_img_for_ocr = mask
                
        # --- 4. Final Image for Tesseract (the dynamically cropped mask) ---
        gray_img = final_img_for_ocr

        # Save the filtered image for debugging (as requested by the user)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_path = os.path.join(TMP_DIR, f"Filtered_{timestamp}.png")
        cv2.imwrite(debug_path, gray_img)
        print(f"Debug image saved to: {debug_path}")

        # --- 5. Run Tesseract OCR ---
        # UPDATED: Use the Vietnamese language model ('vie') for better accuracy on map names.
        # Tesseract needs the 'vie' language pack installed.
        config = '--psm 7 --oem 3 -l vie'
        text = pytesseract.image_to_string(gray_img, config=config).strip()
        
        # Clean up the output (filter non-alphanumeric/non-space, convert to uppercase)
        # We must keep spaces if the map name has multiple words, but remove punctuation.
        cleaned_text = ''.join(filter(lambda c: c.isalnum() or c.isspace(), text)).upper()
        
        print(f"Raw Tesseract Output: '{text}' - lower={lower_green}, upper={upper_green}")
        print(f"Cleaned Tesseract Output: '{cleaned_text}'")
        
        return cleaned_text

    except pytesseract.TesseractNotFoundError:
        print(
            "Tesseract is not installed or not in PATH. Please install Tesseract or set 'pytesseract.pytesseract.tesseract_cmd'."
        )
        # NOTE: If the 'vie' language pack is missing but Tesseract is found, this error will
        # not fire. We will rely on the user to ensure 'vie' is installed.
        return ""
    except Exception as e:
        print(f"An error occurred during OCR: {e}")
        return ""