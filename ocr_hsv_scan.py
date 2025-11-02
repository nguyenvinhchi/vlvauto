import os
import cv2
import numpy as np

import pytesseract

# --- Configuration ---
# 1. SET THIS TO YOUR CAPTURED IMAGE PATH
# You must first capture an image using your TestDialog before running this script.

image_paths = [
    "data/tmp/towns/VLV-A1-1-20251101_224743.png",
    "data/tmp/towns/VLV-A1-1-20251101_231836.png",
    "data/tmp/towns/VLV-A1-1-20251101_231932.png",
    "data/tmp/towns/VLV-A1-1-20251101_231951.png",
    "data/tmp/towns/VLV-A1-1-20251101_232035.png",
    "data/tmp/towns/VLV-A1-1-20251101_232143.png",
    "data/tmp/towns/VLV-A1-1-20251101_232251.png",
    "data/tmp/towns/VLV-A1-1-20251101_232327.png"
]

# 2. OUTPUT FOLDER
OUTPUT_SCAN_DIR = os.path.join("data/tmp", "hsv_scans")
os.makedirs(OUTPUT_SCAN_DIR, exist_ok=True)

# 3. HUE (H) RANGE - Fixed for Green
# Pure green is typically around 60. We use a narrow range to fix the color itself.
HUE_LOWER = 50
HUE_UPPER = 70

# 4. SATURATION (S) and VALUE (V) RANGES to Scan
# These are the lower bounds that will be iterated.
# Scanning from low (dull/dark) to high (vibrant/bright)
SATURATION_RANGE = range(70, 110, 10)  # e.g., 100, 120, 140, 160, 180
VALUE_RANGE = range(130, 255, 10)       # e.g., 100, 120, 140, 160, 180
def scan_hsv_ranges():
    for image_path in image_paths:
        scan_hsv(image_path)

def scan_hsv(image_path: str):
    """
    Loads the input image and applies various HSV lower-bound filters 
    to help the user visually determine the optimal Saturation and Value.
    """
    # print(f"Starting HSV scan process. Outputting to: {OUTPUT_SCAN_DIR}")
    
    # --- 1. Load Image and Define Dynamic Crop Region ---
    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"ERROR: Failed to load image. Check if {image_path} exists.", "ERROR")
            return
    except Exception as e:
        print(f"ERROR loading image: {e}", "ERROR")
        return

    # Get original dimensions
    h_orig, w_orig, _ = img.shape
    
    # Calculate dynamic crop region based on 1/4 image height and 85% width start.
    x1_p = 1438
    y1_p = 55
    x2_p = x1_p + 153
    y2_p = y1_p + 80 # 1/4 of the image height

    # Crop the Image to GENEROUS Dynamic Top-Right Region
    cropped_img = img[y1_p:y2_p, x1_p:x2_p]
    if cropped_img.size == 0:
        print("Cropped image is empty. Check dynamic crop coordinates.", "ERROR")
        return

    # Convert to HSV color space
    hsv = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2HSV)

    # --- 2. Iterate through S and V lower bounds ---
    for s_val in SATURATION_RANGE:
        for v_val in VALUE_RANGE:
            # Define lower and upper bounds for the current scan iteration
            lower_green = np.array([HUE_LOWER, s_val, v_val])
            upper_green = np.array([HUE_UPPER, 255, 255]) # Upper bounds are always max (255)

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
                    # print("Cropped image is empty.")
                    return ""

                # Create mask: White where the color is green, black otherwise
                mask = cv2.inRange(hsv, lower_green, upper_green)

                # --- 3.5. Dynamic ROI refinement based on the mask (Find the tight bounding box) ---
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                if not contours:
                    # print("No green text (contours) detected within the top-right region.")
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
                        #print(f"Dynamically cropped ROI: ({x1_dynamic}, {y1_dynamic}) to ({x2_dynamic}, {y2_dynamic}) relative to initial crop.")
                    else:
                        # print("Contours found but bounding box was invalid. Using full mask.")
                        final_img_for_ocr = mask
                        
                # --- 4. Final Image for Tesseract (the dynamically cropped mask) ---
                gray_img = final_img_for_ocr

                # --- 5. Run Tesseract OCR ---
                # UPDATED: Use the Vietnamese language model ('vie') for better accuracy on map names.
                # Tesseract needs the 'vie' language pack installed.
                config = '--psm 7 --oem 3 -l vie'
                text = pytesseract.image_to_string(gray_img, config=config).strip()
                # if len(text) > 5:
                #     print(f"====text: {text}")

                if text in ("Phượng Tường", "Dương Châu", "Đại Lý", "Lâm An", "Thành Đô", "Tương Dương", "Biện Kinh"):
                    print(f'======{text} - OCR SUCCESS - lower: {lower_green} - upper: {upper_green}')
                    # Save the filtered image for debugging (as requested by the user)
                    # filename = f"filtered_H{HUE_LOWER}-{HUE_UPPER}_S{s_val}_V{v_val}.png"
                    # debug_path = os.path.join(OUTPUT_SCAN_DIR, filename)
                    # cv2.imwrite(debug_path, final_img_for_ocr)
                    # print(f"Generated {filename}")


            except pytesseract.TesseractNotFoundError:
                print(
                    "Tesseract is not installed or not in PATH. Please install Tesseract or set 'pytesseract.pytesseract.tesseract_cmd'."
                )
                # NOTE: If the 'vie' language pack is missing but Tesseract is found, this error will
                # not fire. We will rely on the user to ensure 'vie' is installed.
              
            except Exception as e:
                print(f"An error occurred during OCR: {e}")
            

    print(f"Scan complete. Review files in {OUTPUT_SCAN_DIR} to find the best S and V values.")


if __name__ == "__main__":
    scan_hsv_ranges()
