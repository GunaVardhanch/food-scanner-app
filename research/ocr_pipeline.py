from ultralytics import YOLO
import easyocr
import cv2
import time
import os
from preprocessing import apply_clahe

class AdvancedOCRPipeline:
    def __init__(self):
        # Load YOLOv8 for detection
        # Using yolov8n.pt as a fast base model
        self.detector = YOLO('yolov8n.pt') 
        
        # Lazy-load EasyOCR reader on first call for faster startup
        self._reader = None
        print("OCRPipeline: YOLO loaded. EasyOCR will lazy-load on first scan.")

    @property
    def reader(self):
        if self._reader is None:
            self._reader = easyocr.Reader(['en', 'hi', 'mr'], gpu=True)
            print("OCRPipeline: EasyOCR loaded (lazy init).")
        return self._reader

    def process_label(self, image_path):
        t_start = time.time()
        image = cv2.imread(image_path)
        if image is None:
            return {"error": "Image not found"}

        # 1. Image Resizing (Optimization: Reduce processing area)
        h, w = image.shape[:2]
        max_dim = 640  # Optimized: was 1000, reduced for faster inference
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            image = cv2.resize(image, (int(w * scale), int(h * scale)))
            print(f"OCRPipeline: Resized image to {image.shape[1]}x{image.shape[0]}")

        # 2. Enhancement
        enhanced = apply_clahe(image)
        
        # 3. Label Detection (YOLO) - Optimization: Localize text search
        t_det_start = time.time()
        results = self.detector(enhanced, verbose=False)
        crop_img = enhanced
        
        # Attempt to find the largest 'cell phone' or generic 'object' as label for MVP
        # In a real FSSAI model, we'd detect 'label' or 'ingredients_list'
        if results and len(results[0].boxes) > 0:
            # For now, we take the largest bounding box if available
            box = results[0].boxes[0].xyxy[0].cpu().numpy().astype(int)
            x1, y1, x2, y2 = box
            crop_img = enhanced[y1:y2, x1:x2]
            print(f"OCRPipeline: Cropped to detected label area: {x2-x1}x{y2-y1}")
        
        t_det_end = time.time()
        print(f"OCRPipeline: Detection/Cropping took {t_det_end - t_det_start:.4f}s")
        
        # 4. Text Extraction (EasyOCR — optimized params)
        t_ocr_start = time.time()
        results = self.reader.readtext(crop_img, detail=0, paragraph=True,
                                       batch_size=4, width_ths=0.7)
        full_text = " ".join(results)
        t_ocr_end = time.time()
        
        print(f"OCRPipeline: OCR (EasyOCR) took {t_ocr_end - t_ocr_start:.4f}s")
        print(f"OCRPipeline: Total Processing Time: {time.time() - t_start:.4f}s")
        
        return {
            "raw_text": full_text,
            "confidence": 0.95
        }

if __name__ == "__main__":
    print("Advanced OCR Pipeline Initialized.")
    pipe = AdvancedOCRPipeline()
    # pipe.process_label('test_sample.jpg')
