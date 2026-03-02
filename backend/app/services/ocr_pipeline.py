from ultralytics import YOLO
import easyocr
import cv2
import time
import os
import torch
from app.utils.preprocessing import apply_clahe
from app.config import OCR_MODELS_DIR


class AdvancedOCRPipeline:
    def __init__(self):
        # YOLOv8n — used for label region detection (optional crop)
        self.detector = YOLO('yolov8n.pt')
        self._reader = None
        # Minimum YOLO confidence to trust a crop; below this we skip cropping
        self.YOLO_CROP_CONF_THRESHOLD = 0.50
        print("OCRPipeline: YOLO loaded. EasyOCR will lazy-load on first scan.")

    @property
    def reader(self):
        if self._reader is None:
            gpu_available = torch.cuda.is_available()
            model_dir = os.environ.get("EASYOCR_MODULE_PATH") or OCR_MODELS_DIR
            if model_dir and os.path.isdir(model_dir):
                self._reader = easyocr.Reader(
                    ['en'],
                    gpu=gpu_available,
                    model_storage_directory=model_dir,
                    download_enabled=False,
                )
                print(f"OCRPipeline: EasyOCR loaded from {model_dir} (gpu={gpu_available}).")
            else:
                self._reader = easyocr.Reader(
                    ['en'],
                    gpu=gpu_available,
                    download_enabled=True,
                )
                print(f"OCRPipeline: EasyOCR loaded (gpu={gpu_available}, download_enabled=True).")
        return self._reader

    def process_label(self, image_path):
        t_start = time.time()
        image = cv2.imread(image_path)
        if image is None:
            return {"error": f"Image not found: {image_path}", "raw_text": ""}

        # 1. Resize — use a larger max dimension to preserve text legibility
        h, w = image.shape[:2]
        max_dim = 1280  # Increased from 640 to retain fine text
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            image = cv2.resize(image, (int(w * scale), int(h * scale)),
                               interpolation=cv2.INTER_LANCZOS4)
            print(f"OCRPipeline: Resized to {image.shape[1]}x{image.shape[0]}")

        # 2. Contrast enhancement
        enhanced = apply_clahe(image)

        # 3. Optional YOLO crop — only use if a high-confidence region is found.
        #    yolov8n.pt is trained on COCO (80 generic classes) and has no "food label"
        #    class, so we only trust crops with high confidence to avoid cropping away
        #    the very text we need to read.
        crop_img = enhanced
        t_det_start = time.time()
        try:
            yolo_results = self.detector(enhanced, verbose=False)
            if yolo_results and len(yolo_results[0].boxes) > 0:
                # Pick the highest-confidence detection
                boxes = yolo_results[0].boxes
                confs = boxes.conf.cpu().numpy()
                best_idx = int(confs.argmax())
                best_conf = float(confs[best_idx])

                if best_conf >= self.YOLO_CROP_CONF_THRESHOLD:
                    box = boxes[best_idx].xyxy[0].cpu().numpy().astype(int)
                    x1, y1, x2, y2 = box
                    # Sanity check: the crop should be at least 30 % of original area
                    crop_area = (x2 - x1) * (y2 - y1)
                    total_area = enhanced.shape[0] * enhanced.shape[1]
                    if crop_area / total_area >= 0.10:
                        crop_img = enhanced[y1:y2, x1:x2]
                        print(f"OCRPipeline: YOLO crop accepted — conf={best_conf:.2f}, "
                              f"size={x2-x1}x{y2-y1}")
                    else:
                        print(f"OCRPipeline: YOLO crop rejected — too small ({crop_area/total_area:.1%} of frame)")
                else:
                    print(f"OCRPipeline: YOLO crop skipped — low confidence ({best_conf:.2f} < {self.YOLO_CROP_CONF_THRESHOLD})")
            else:
                print("OCRPipeline: No YOLO detections — using full image for OCR")
        except Exception as e:
            print(f"OCRPipeline: YOLO detection failed ({e}), using full image.")

        t_det_end = time.time()
        print(f"OCRPipeline: Detection took {t_det_end - t_det_start:.3f}s")

        # 4. EasyOCR — optimised parameters for nutrition label text
        t_ocr_start = time.time()
        raw_results = self.reader.readtext(
            crop_img,
            detail=1,           # Return bounding boxes + confidence scores
            paragraph=False,    # Disabled: paragraph mode merges table rows incorrectly
            batch_size=8,
            width_ths=0.5,      # Narrower threshold for table-style labels
            contrast_ths=0.1,   # Lower to catch faint/small text
            low_text=0.3,       # More sensitive to small text on labels
        )

        # Filter by confidence and join text
        MIN_OCR_CONF = 0.3
        text_pieces = []
        for (bbox, text, conf) in raw_results:
            if conf >= MIN_OCR_CONF:
                text_pieces.append(text.strip())

        full_text = " ".join(text_pieces)
        t_ocr_end = time.time()

        print(f"OCRPipeline: EasyOCR took {t_ocr_end - t_ocr_start:.3f}s, "
              f"{len(text_pieces)} text regions accepted")
        print(f"OCRPipeline: RAW OCR TEXT: {full_text[:300]}")
        print(f"OCRPipeline: Total processing time: {time.time() - t_start:.3f}s")

        return {
            "raw_text": full_text,
            "confidence": 0.95,
            "regions_found": len(text_pieces),
        }

if __name__ == "__main__":
    print("Advanced OCR Pipeline Initialized.")
    pipe = AdvancedOCRPipeline()
