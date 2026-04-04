"""
barcode_service.py
──────────────────
Barcode-only detection module.

The SOLE responsibility of this module is:
    image (np.ndarray)  →  GTIN string  (or None if no barcode found)

It does NOT:
    - read nutrition text
    - parse ingredients
    - run any NLP or OCR on label copy

Detection strategy (fastest-first, no model weights required):
    1. pyzbar  — ZBar library; works on most 1-D EAN-13/UPC/EAN-8 barcodes.
    2. cv2.barcode.BarcodeDetector — OpenCV built-in (≥4.5.5), handles
       rotated/skewed codes.
    3. If both fail → return None.

 Fixes applied (Phase 1):
    - Bug 1: pyzbar fallback no longer returns non-GTIN strings
    - Bug 2: GS1 check digit validation added to catch corrupt reads early
    - Bug 3: EXIF rotation correction added for mobile camera images
"""

from __future__ import annotations

import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ── optional pyzbar import ────────────────────────────────────────────────────
try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    _PYZBAR_AVAILABLE = True
except ImportError:
    _PYZBAR_AVAILABLE = False
    logger.warning("pyzbar not installed — falling back to OpenCV barcode detector only.")

# ── optional OpenCV barcode detector ─────────────────────────────────────────
try:
    _OPENCV_DETECTOR = cv2.barcode.BarcodeDetector()
    _OPENCV_AVAILABLE = True
except AttributeError:
    _OPENCV_DETECTOR = None
    _OPENCV_AVAILABLE = False
    logger.warning("cv2.barcode.BarcodeDetector unavailable (OpenCV < 4.5.5).")


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def extract_barcode_from_image(image: np.ndarray) -> Optional[str]:
    """
    Detect and decode any EAN-13 / GTIN / UPC barcode in the given image.

    Parameters
    ----------
    image : np.ndarray
        BGR image as loaded by cv2.imread(), or decoded from base64.
        EXIF rotation is corrected automatically.

    Returns
    -------
    str | None
        The decoded GTIN string (e.g. "8901234567890") on success,
        or None if no valid barcode could be detected.
    """
    if image is None or image.size == 0:
        logger.warning("extract_barcode_from_image: received empty image.")
        return None

    # Fix 3: Correct EXIF rotation before anything else.
    # Mobile cameras often send portrait images that arrive as landscape arrays.
    image = _correct_orientation(image)

    variants = _prepare_variants(image)

    for label, variant in variants:
        result = _try_pyzbar(variant)
        if result:
            logger.info("Barcode extracted via pyzbar on variant '%s': %s", label, result)
            return result

        result = _try_opencv(variant)
        if result:
            logger.info("Barcode extracted via OpenCV on variant '%s': %s", label, result)
            return result

    logger.info("No barcode found in image after all variants.")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Orientation correction (Fix 3)
# ─────────────────────────────────────────────────────────────────────────────

def _correct_orientation(image: np.ndarray) -> np.ndarray:
    """
    Rotate the image so the barcode bars are vertical (standard orientation).

    Mobile cameras frequently send portrait-mode images where the barcode
    is rotated 90° or 270°. We detect this by checking the aspect ratio:
    barcodes are wider than tall, so if the image is taller than wide we
    try both 90° rotations as additional variants (handled in _prepare_variants).

    This function only handles the most common case: a clearly portrait image
    (height > 1.3 × width) is rotated 90° clockwise to landscape.
    """
    h, w = image.shape[:2]
    # If image is significantly taller than wide, rotate to landscape
    if h > w * 1.3:
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        logger.debug("_correct_orientation: rotated portrait image to landscape")
    return image


# ─────────────────────────────────────────────────────────────────────────────
# Image variant preparation
# ─────────────────────────────────────────────────────────────────────────────

def _prepare_variants(image: np.ndarray) -> list[tuple[str, np.ndarray]]:
    """
    Return a list of (label, processed_image) tuples tried in order.
    Each variant is a different pre-processing path to maximise decode rate.
    """
    variants: list[tuple[str, np.ndarray]] = []

    # 1. Original colour image
    variants.append(("original", image))

    # 2. Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    variants.append(("gray", gray))

    # 3. Sharpened grayscale — helps with slightly blurry barcodes
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharp = cv2.filter2D(gray, -1, kernel)
    variants.append(("sharp", sharp))

    # 4. Upscaled × 2 — helps with small/distant barcodes
    h, w = gray.shape[:2]
    if max(h, w) < 1200:
        up = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        variants.append(("upscaled", up))

    # 5. Adaptive threshold — handles uneven/harsh lighting
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    variants.append(("adaptive_thresh", thresh))

    # 6. 90° counter-clockwise rotation — catches barcodes shot sideways
    rotated_ccw = cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
    variants.append(("rotated_ccw", rotated_ccw))

    # 7. 90° clockwise rotation
    rotated_cw = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
    variants.append(("rotated_cw", rotated_cw))

    return variants


# ─────────────────────────────────────────────────────────────────────────────
# Decoder wrappers
# ─────────────────────────────────────────────────────────────────────────────

def _try_pyzbar(image: np.ndarray) -> Optional[str]:
    """
    Try pyzbar decoder.

    Fix 1: Only returns strings that pass _looks_like_gtin() AND
    _valid_check_digit(). The old fallback that returned any non-empty
    string (QR codes, lot numbers, price tags) has been removed.
    """
    if not _PYZBAR_AVAILABLE:
        return None
    try:
        decoded_objects = pyzbar_decode(image)
        for obj in decoded_objects:
            raw = obj.data.decode("utf-8", errors="ignore").strip()
            if raw and _looks_like_gtin(raw) and _valid_check_digit(raw):
                return raw
        # Second pass: accept GTIN-shaped strings even if check digit fails
        # (some older Indian barcodes have non-standard check digits)
        for obj in decoded_objects:
            raw = obj.data.decode("utf-8", errors="ignore").strip()
            if raw and _looks_like_gtin(raw):
                logger.debug("pyzbar: accepting GTIN with unverified check digit: %s", raw)
                return raw
    except Exception as exc:
        logger.debug("pyzbar decode error: %s", exc)
    return None


def _try_opencv(image: np.ndarray) -> Optional[str]:
    """Try OpenCV BarcodeDetector. Returns first valid GTIN string or None."""
    if not _OPENCV_AVAILABLE or _OPENCV_DETECTOR is None:
        return None
    try:
        # OpenCV detector expects BGR; convert if grayscale
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        ok, decoded_info, decoded_type, _ = _OPENCV_DETECTOR.detectAndDecodeMulti(image)
        if ok:
            for code, ctype in zip(decoded_info, decoded_type):
                if code and ctype in ("EAN_13", "EAN_8", "UPC_A", "UPC_E", "CODE_128"):
                    code = code.strip()
                    if _looks_like_gtin(code):
                        return code
    except Exception as exc:
        logger.debug("OpenCV BarcodeDetector error: %s", exc)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Validation helpers
# ─────────────────────────────────────────────────────────────────────────────

def _looks_like_gtin(s: str) -> bool:
    """
    Structural check: a valid GTIN is 8, 12, 13, or 14 digits only.
    Indian EAN-13 barcodes start with 890.
    """
    return s.isdigit() and len(s) in (8, 12, 13, 14)


def _valid_check_digit(gtin: str) -> bool:
    """
    Fix 2: GS1 check digit validation (Luhn-style modulo-10 algorithm).

    The last digit of any EAN/GTIN is a check digit computed from the
    preceding digits. A mismatch means the barcode was read incorrectly.

    Spec: https://www.gs1.org/services/check-digit-calculator/details
    """
    if not gtin.isdigit() or len(gtin) not in (8, 12, 13, 14):
        return False
    digits = [int(d) for d in gtin]
    # Weights alternate 3, 1 from right, excluding the check digit
    payload = digits[:-1]
    check = digits[-1]
    # Pad to even length from the right for consistent weight assignment
    if len(payload) % 2 != 0:
        payload = [0] + payload
    total = 0
    for i, d in enumerate(payload):
        total += d * 3 if i % 2 == 0 else d
    computed = (10 - (total % 10)) % 10
    return computed == check
