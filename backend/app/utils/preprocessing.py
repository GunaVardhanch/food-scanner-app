"""
preprocessing.py
────────────────
Image preprocessing utilities for the label scan pipeline.

Phase 2 additions:
  - auto_perspective_correct: detects label quadrilateral and warps it flat
  - bilateral_denoise: edge-preserving denoising (better than Gaussian for text)
  - apply_clahe: unchanged, kept for contrast enhancement
  - correct_perspective: manual 4-point warp (kept for external callers)
"""

from __future__ import annotations

import cv2
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# CLAHE — contrast enhancement (original, unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def apply_clahe(image: np.ndarray) -> np.ndarray:
    """
    Apply Contrast Limited Adaptive Histogram Equalization to enhance text
    visibility on food labels.
    """
    if len(image.shape) == 3:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    else:
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        return clahe.apply(image)


# ─────────────────────────────────────────────────────────────────────────────
# Bilateral denoising (Phase 2 — 2a)
# ─────────────────────────────────────────────────────────────────────────────

def bilateral_denoise(image: np.ndarray) -> np.ndarray:
    """
    Edge-preserving denoising using a bilateral filter.

    Unlike Gaussian blur, bilateral filtering smooths noise while keeping
    sharp edges — critical for small nutrition label text where blurring
    the edge of a character destroys OCR accuracy.

    Parameters chosen for label text:
      d=9       — neighbourhood diameter (larger = more smoothing)
      sigmaColor=75  — colour range; higher = more colours blended
      sigmaSpace=75  — spatial range; higher = farther pixels influence each other
    """
    return cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)


# ─────────────────────────────────────────────────────────────────────────────
# Automatic perspective correction (Phase 2 — 2a)
# ─────────────────────────────────────────────────────────────────────────────

def auto_perspective_correct(image: np.ndarray) -> np.ndarray:
    """
    Automatically detect the largest rectangular region in the image
    (assumed to be the food label) and warp it to a flat rectangle.

    This corrects for:
      - Camera angle (label photographed at an angle)
      - Curved packaging (slight warp on cylindrical products)
      - Tilted shots

    Returns the warped image if a good quadrilateral is found,
    otherwise returns the original image unchanged.
    """
    orig = image.copy()
    h, w = image.shape[:2]

    # Work on a grayscale copy for edge detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()

    # Denoise before edge detection to reduce false contours
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Canny edge detection — thresholds tuned for label backgrounds
    edges = cv2.Canny(blurred, 50, 150)

    # Dilate edges slightly to close small gaps in label borders
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.dilate(edges, kernel, iterations=1)

    # Find contours and pick the largest quadrilateral
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    quad = None
    for cnt in contours[:5]:  # only check top-5 largest contours
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4:
            area = cv2.contourArea(approx)
            # Must cover at least 15% of the image to be the label
            if area > 0.15 * h * w:
                quad = approx.reshape(4, 2).astype("float32")
                break

    if quad is None:
        # No good quadrilateral found — return original
        return orig

    # Order points: top-left, top-right, bottom-right, bottom-left
    quad = _order_points(quad)
    warped = correct_perspective(image, quad)
    return warped


def _order_points(pts: np.ndarray) -> np.ndarray:
    """
    Order 4 points as [top-left, top-right, bottom-right, bottom-left].
    Required by cv2.getPerspectiveTransform.
    """
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # top-left: smallest sum
    rect[2] = pts[np.argmax(s)]   # bottom-right: largest sum
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right: smallest diff
    rect[3] = pts[np.argmax(diff)]  # bottom-left: largest diff
    return rect


# ─────────────────────────────────────────────────────────────────────────────
# Manual 4-point perspective warp (original, kept for external callers)
# ─────────────────────────────────────────────────────────────────────────────

def correct_perspective(image: np.ndarray, points: np.ndarray) -> np.ndarray:
    """
    Warp image to a flat rectangle given 4 corner points.
    points: float32 array of shape (4, 2) ordered [TL, TR, BR, BL].
    """
    pts = np.array(points, dtype="float32")
    (tl, tr, br, bl) = pts

    widthA  = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB  = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1],
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(pts, dst)
    return cv2.warpPerspective(image, M, (maxWidth, maxHeight))
