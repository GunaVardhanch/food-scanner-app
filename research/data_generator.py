import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def generate_synthetic_label(text, width=200, height=50):
    """
    Creates a synthetic image of text to simulate a cut-out from a food label.
    """
    # Create white background
    image = Image.new('L', (width, height), color=255)
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
        
    # Draw text with some variation
    text_width = draw.textlength(text, font=font)
    x = (width - text_width) / 2
    y = (height - 24) / 2
    draw.text((x, y), text, fill=0, font=font)
    
    # Convert to numpy array and add noise/blur
    img_np = np.array(image)
    
    # Add Gaussian noise
    noise = np.random.normal(0, 10, img_np.shape).astype(np.uint8)
    img_np = cv2.add(img_np, noise)
    
    # Slight blur to simulate camera focus
    img_np = cv2.GaussianBlur(img_np, (3, 3), 0)
    
    return img_np

def prepare_dataset(output_dir="dataset/train"):
    """
    Generates a small dataset of common food ingredients and additives.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    samples = [
        "Maltodextrin", "Palm Oil", "INS 319", "E621", "Sugar",
        "Soya Lecithin", "Sodium Nitrite", "MSG", "High Fructose",
        "Acidity Regulator", "Ascorbic Acid", "Guar Gum"
    ]
    
    for i, text in enumerate(samples):
        img = generate_synthetic_label(text)
        filename = f"{output_dir}/sample_{i}.png"
        cv2.imwrite(filename, img)
        # In a real scenario, we'd save the text label to a CSV or JSON
        print(f"Generated: {filename} -> {text}")

if __name__ == "__main__":
    print("--- SYNTHETIC DATA GENERATOR FOR OCR ---")
    prepare_dataset()
    print("\nDataset generation complete. This simulates the 'Data' phase of OCR training.")
