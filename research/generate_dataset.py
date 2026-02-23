import os
import cv2
import numpy as np
import random
from PIL import Image, ImageDraw, ImageFont

# Configuration
DATASET_DIR = "dataset/ocr_synth"
LABEL_FILE = "dataset/labels.txt"
IMG_WIDTH = 200
IMG_HEIGHT = 50
NUM_SAMPLES = 500  # Small set for demonstration

ingredients = [
    "Maltodextrin", "Palm Oil", "Sugar", "Salt", "Wheat Flour",
    "Soy Lecithin", "INS 319", "E621", "Monosodium Glutamate",
    "Citric Acid", "Cocoa Butter", "Milk Solids", "Vanilla Extract"
]

def create_dirs():
    if not os.path.exists(DATASET_DIR):
        os.makedirs(DATASET_DIR)

def generate_sample(text, index):
    # Create blank grayscale image
    img = Image.new('L', (IMG_WIDTH, IMG_HEIGHT), color=255)
    draw = ImageDraw.Draw(img)
    
    # Try to load a font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
        
    # Draw text with slight random offset
    # Get text bounding box: (left, top, right, bottom)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = random.randint(5, max(5, IMG_WIDTH - tw - 5))
    y = random.randint(5, max(5, IMG_HEIGHT - th - 5))
    draw.text((x, y), text, font=font, fill=0)
    
    # Convert to numpy for distortions
    img_np = np.array(img)
    
    # Add random rotation
    angle = random.uniform(-5, 5)
    M = cv2.getRotationMatrix2D((IMG_WIDTH/2, IMG_HEIGHT/2), angle, 1)
    img_np = cv2.warpAffine(img_np, M, (IMG_WIDTH, IMG_HEIGHT), borderValue=255)
    
    # Add gaussian noise
    noise = np.random.normal(0, 5, img_np.shape).astype(np.uint8)
    img_np = cv2.add(img_np, noise)
    
    # Save image
    img_path = os.path.join(DATASET_DIR, f"sample_{index}.png")
    cv2.imwrite(img_path, img_np)
    return img_path

def main():
    create_dirs()
    print(f"Generating {NUM_SAMPLES} samples...")
    
    with open(LABEL_FILE, "w") as f:
        for i in range(NUM_SAMPLES):
            text = random.choice(ingredients)
            img_path = generate_sample(text, i)
            f.write(f"{img_path}\t{text}\n")
            
    print(f"Dataset generated in {DATASET_DIR}")
    print(f"Labels saved to {LABEL_FILE}")

if __name__ == "__main__":
    main()
