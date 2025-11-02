import cv2
import numpy as np
import pytesseract

# IMPORTANT: If Tesseract is not in your system's PATH, you must uncomment and set the path here:
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\chinv\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
TMP_DIR = "data/tmp"

def read_text_from_image(image, lower_color, upper_color, roi_crop_box=None):
    # crop roi -> convert PIL img to numpy array image (BGR)
    # -> create hsv -> create mask
    # -> invert BGR img using mask
    print(f'OCR with lower hsv: {lower_color} , upper hsv: {upper_color}')
    # screenshot.save(os.path.join(TMP_DIR, f"screenshot_origin.png"))
    process_img = image
    if roi_crop_box is not None:
        process_img = image.crop(roi_crop_box)

    try:
        # Convert the PIL image to a NumPy array (RGB format)
        bgr_img = cv2.cvtColor(np.array(process_img), cv2.COLOR_RGB2BGR)

        # Apply Color Filter (HSV Mask for Green Text) ---
        hsv_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)

        # Create mask: White where the color is green, black otherwise
        mask_img = cv2.inRange(hsv_img, lower_color, upper_color)

        # Define a kernel (e.g., 2x2 or 3x3 square)
        # kernel = np.ones((2, 2), np.uint8) 

        # Apply Erosion: Removes isolated noise pixels/small borders
        # Use 1 iteration for a subtle cleanup.
        # mask_img = cv2.erode(mask_img, kernel, iterations=1)

        # Apply Dilation (Optional): Helps reconnect broken letters after erosion
        # mask_img = cv2.dilate(mask_img, kernel, iterations=1)

        # invert bgr image with mask will produce image suitable for OCR or OpenCV detection as well.
        # inverted_img = cv2.bitwise_and(bgr_img, bgr_img, mask=mask_img)

        # Convert BGR to RGB and show using QPixmap
        # rgb_img = cv2.cvtColor(inverted_img, cv2.COLOR_BGR2RGB)

        # Dynamic ROI refinement based on the mask (Find the tight bounding box) ---
        contours, _ = cv2.findContours(mask_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            print("No green text (contours) detected within the top-right region.")
            final_img_for_ocr = mask_img # Fallback to the full mask
        else:
            # Find the bounding box that encompasses ALL found green text contours
            x_min, y_min, x_max, y_max = bgr_img.shape[1], bgr_img.shape[0], 0, 0
            
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
                x2_dynamic = min(bgr_img.shape[1], x_max + padding)
                y2_dynamic = min(bgr_img.shape[0], y_max + padding)

                # Dynamically crop the mask to only the detected green text area
                final_img_for_ocr = mask_img[y1_dynamic:y2_dynamic, x1_dynamic:x2_dynamic]
                print(f"Dynamically cropped ROI: ({x1_dynamic}, {y1_dynamic}) to ({x2_dynamic}, {y2_dynamic}) relative to initial crop.")
            else:
                print("Contours found but bounding box was invalid. Using full mask.")
                final_img_for_ocr = mask_img
                
        # Final Image for Tesseract (the dynamically cropped mask) ---
        gray_img = final_img_for_ocr

        # Save the filtered image for debugging (as requested by the user)
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # debug_path = os.path.join(TMP_DIR, f"screenshot_inverted.png")
        # cv2.imwrite(os.path.join(TMP_DIR, f"screenshot_cropped_bgr.png"), bgr_img)
        # cv2.imwrite(os.path.join(TMP_DIR, f"screenshot_mask.png"), mask_img)
        # cv2.imwrite(os.path.join(TMP_DIR, f"screenshot_rgb.png"), rgb_img)
        # cv2.imwrite(os.path.join(TMP_DIR, f"screenshot_inverted.png"), inverted_img)
        # print(f"Debug image saved to: {debug_path}")

        # Run Tesseract OCR ---
        # UPDATED: Use the Vietnamese language model ('vie') for better accuracy on map names.
        # Tesseract needs the 'vie' language pack installed.
        config = '--psm 7 --oem 3 -l vie'
        text: str = pytesseract.image_to_string(gray_img, config=config).strip()
        return text
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
