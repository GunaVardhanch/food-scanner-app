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
        BGR image as loaded by cv2.imread(), or an RGB array from PIL/camera.

    Returns
    -------
    str | None
        The decoded barcode string (e.g. "8901234567890") on success,
        or ``None`` if no barcode could be detected.

    Notes
    -----
    - Two independent decoders are tried in order (pyzbar → OpenCV).
    - Pre-processing (grayscale + adaptive threshold + upscale) is applied
      to improve detection on blurry or low-contrast images.
    - No nutrition text, ingredients, or any other label content is read.
    """
    if image is None or image.size == 0:
        logger.warning("extract_barcode_from_image: received empty image.")
        return None

    # Prepare several variants of the image to maximise detection rate
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
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _prepare_variants(image: np.ndarray) -> list[tuple[str, np.ndarray]]:
    """
    Return a list of (label, processed_image) tuples.
    Each variant is a different pre-processing path.
    """
    variants: list[tuple[str, np.ndarray]] = []

    # 1. Original colour image
    variants.append(("original", image))

    # 2. Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    variants.append(("gray", gray))

    # 3. Sharpened grayscale
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharp = cv2.filter2D(gray, -1, kernel)
    variants.append(("sharp", sharp))

    # 4. Upscaled × 2 (helps with small/distant barcodes)
    h, w = gray.shape[:2]
    if max(h, w) < 1200:
        up = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        variants.append(("upscaled", up))

    # 5. Adaptive threshold (handles uneven lighting)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    variants.append(("adaptive_thresh", thresh))

    return variants


def _try_pyzbar(image: np.ndarray) -> Optional[str]:
    """Try pyzbar decoder. Returns first valid barcode string or None."""
    if not _PYZBAR_AVAILABLE:
        return None
    try:
        decoded_objects = pyzbar_decode(image)
        for obj in decoded_objects:
            raw = obj.data.decode("utf-8", errors="ignore").strip()
            if raw and _looks_like_gtin(raw):
                return raw
        # If nothing matched strict GTIN, return first result anyway
        for obj in decoded_objects:
            raw = obj.data.decode("utf-8", errors="ignore").strip()
            if raw:
                return raw
    except Exception as exc:
        logger.debug("pyzbar decode error: %s", exc)
    return None


def _try_opencv(image: np.ndarray) -> Optional[str]:
    """Try OpenCV BarcodeDetector. Returns first valid barcode string or None."""
    if not _OPENCV_AVAILABLE or _OPENCV_DETECTOR is None:
        return None
    try:
        # Convert to 3-channel if grayscale (OpenCV detector expects BGR)
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        ok, decoded_info, decoded_type, _ = _OPENCV_DETECTOR.detectAndDecodeMulti(image)
        if ok:
            for code, ctype in zip(decoded_info, decoded_type):
                if code and ctype in ("EAN_13", "EAN_8", "UPC_A", "UPC_E", "CODE_128"):
                    return code.strip()
    except Exception as exc:
        logger.debug("OpenCV BarcodeDetector error: %s", exc)
    return None


def _looks_like_gtin(s: str) -> bool:
    """
    Sanity check: a valid GTIN is 8, 12, 13, or 14 digits.
    Indian EAN-13 barcodes typically start with 890.
    """
    return s.isdigit() and len(s) in (8, 12, 13, 14)
