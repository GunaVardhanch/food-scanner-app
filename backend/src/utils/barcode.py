import cv2
from pyzbar import pyzbar
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def extract_barcode(image_path: str) -> Optional[str]:
    """
    Extracts GTIN (barcode) from an image file.
    Supports EAN-13, UPC-A, etc.
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Barcode: Could not read image at {image_path}")
            return None

        # Convert to grayscale for better detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Decode barcodes
        barcodes = pyzbar.decode(gray)
        
        if not barcodes:
            # Try a slightly enhanced version if first attempt fails
            # (e.g., contrast adjustment could go here)
            return None

        # Return the first detected barcode data
        barcode_data = barcodes[0].data.decode("utf-8")
        barcode_type = barcodes[0].type
        logger.info(f"Barcode: Detected {barcode_type} - {barcode_data}")
        
        return barcode_data

    except Exception as e:
        logger.error(f"Barcode extraction error: {e}")
        return None

if __name__ == "__main__":
    # Test stub
    import sys
    if len(sys.argv) > 1:
        print(f"Result: {extract_barcode(sys.argv[1])}")
