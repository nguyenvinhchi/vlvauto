
import cv2
import numpy
import pytesseract


def ocr_read_text_from_img(image_path: str,
                           hsv_lower:numpy.array,
                           hsv_upper:numpy.array,
                           crop_rect=None
                           ):
    try:
        # --- 1. Load Image and Define Dynamic Crop Region ---
        img = cv2.imread(image_path)
        if img is None:
            print(f"Failed to load image from {image_path}")
            return ""

        # Get original dimensions
        h_orig, w_orig, _ = img.shape
        
        processing_img = img
        # Calculate dynamic crop region based on 1/4 image height.
        # UPDATED: X-axis now starts at 85% width for a tighter crop, as requested.
        if crop_rect:
            # x1, y1, x2, y2 = crop_rect
            x1 = int(w_orig * 0.85)
            y1 = 0
            x2 = w_orig
            y2 = int(h_orig * 0.25) # 1/4 of the image height
            cropped_img = img[y1:y2, x1:x2]
            if cropped_img.size == 0:
                print("Cropped image is empty.")
                return ""
            print(f"Initial dynamic crop: ({x1},{y1}) to ({x2},{y2})")
            processing_img = cropped_img
        cv2.imshow("Origin image (might cropped)", processing_img)
        cv2.waitKey(0) # Waits indefinitely until a key is pressed

        hsv = cv2.cvtColor(processing_img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, hsv_lower, hsv_upper)
        
        # --- 3.5. Dynamic ROI refinement based on the mask (Find the tight bounding box) ---
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            print("No text (contours) detected.")
            final_img_for_ocr = mask # Fallback to the full mask
        else:
            # Find the bounding box that encompasses ALL found green text contours
            x_min, y_min, x_max, y_max = processing_img.shape[1], processing_img.shape[0], 0, 0
            
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
                x2_dynamic = min(processing_img.shape[1], x_max + padding)
                y2_dynamic = min(processing_img.shape[0], y_max + padding)

                # Dynamically crop the mask to only the detected green text area
                final_img_for_ocr = mask[y1_dynamic:y2_dynamic, x1_dynamic:x2_dynamic]
                print(f"Dynamically cropped ROI: ({x1_dynamic}, {y1_dynamic}) to ({x2_dynamic}, {y2_dynamic}) relative to initial crop.")
            else:
                print("Contours found but bounding box was invalid. Using full mask.")
                final_img_for_ocr = mask
            
        # --- 4. Final Image for Tesseract (the dynamically cropped mask) ---
        gray_img = final_img_for_ocr
        
        cv2.imshow("Gray image to ocr", gray_img)
        cv2.waitKey(0) # Waits indefinitely until a key is pressed

        # --- 5. Run Tesseract OCR ---
        # UPDATED: Use the Vietnamese language model ('vie') for better accuracy on map names.
        # Tesseract needs the 'vie' language pack installed.
        config = '--psm 7 --oem 3 -l vie'
        text = pytesseract.image_to_string(gray_img, config=config).strip()
        print(f"Tesseract Output: '{text}'")
        
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