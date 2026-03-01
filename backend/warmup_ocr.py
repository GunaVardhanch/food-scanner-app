import os
import sys

# Add src to path if needed (depending on where this is run)
sys.path.append(os.path.join(os.getcwd(), "backend"))

from src.models.ocr.ocr_pipeline import AdvancedOCRPipeline

def main():
    print("--- Food Scanner OCR Warmup ---")
    print("Initializing OCR Pipeline to pre-download models...")
    
    try:
        pipeline = AdvancedOCRPipeline()
        # Accessing .reader triggers the lazy loading
        _ = pipeline.reader
        print("Success: OCR Models (EasyOCR) are loaded and ready.")
    except Exception as e:
        print(f"Error during warmup: {e}")

if __name__ == "__main__":
    main()
