import cv2
import numpy as np

def apply_clahe(image):
    """
    Apply Contrast Limited Adaptive Histogram Equalization to enhance text visibility.
    """
    if len(image.shape) == 3:
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L-channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        
        # Merge back and convert to BGR
        limg = cv2.merge((cl, a, b))
        final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        return final
    else:
        # Grayscale
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        return clahe.apply(image)

def correct_perspective(image, points):
    """
    Correct perspective based on 4 points (useful for labels on curved surfaces).
    points: array of 4 points [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
    """
    pts = np.array(points, dtype="float32")
    
    # Compute width and height
    (tl, tr, br, bl) = pts
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    M = cv2.getPerspectiveTransform(pts, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    
    return warped

if __name__ == "__main__":
    print("Preprocessing module ready.")
    # Example usage (test with dummy image if needed)
    # img = cv2.imread('sample_label.jpg')
    # enhanced = apply_clahe(img)
    # cv2.imwrite('enhanced_label.jpg', enhanced)
