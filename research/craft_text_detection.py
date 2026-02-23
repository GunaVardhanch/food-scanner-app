import tensorflow as tf
from tensorflow.keras import layers, models

def build_craft_model():
    """
    CRAFT: Character Region Awareness for Text Detection
    A simplified VGG-16 based U-Net architecture to detect text in dense environments.
    Outputs:
    1. Region Score (Character existence)
    2. Affinity Score (Connection between characters)
    """
    
    # Base VGG16-like structure
    inputs = layers.Input(shape=(768, 768, 3))
    
    # Downsampling (Feature Extraction)
    c1 = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(inputs)
    p1 = layers.MaxPooling2D((2, 2))(c1) # 384x384
    
    c2 = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(p1)
    p2 = layers.MaxPooling2D((2, 2))(c2) # 192x192
    
    c3 = layers.Conv2D(256, (3, 3), activation='relu', padding='same')(p2)
    p3 = layers.MaxPooling2D((2, 2))(c3) # 96x96
    
    # Upsampling (Localization)
    u2 = layers.UpSampling2D((2, 2))(c3) # 192x192
    u2 = layers.concatenate([u2, c2])
    u2 = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(u2)
    
    u1 = layers.UpSampling2D((2, 2))(u2) # 384x384
    u1 = layers.concatenate([u1, c1])
    u1 = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(u1)
    
    # Two heatmaps as output
    region_score = layers.Conv2D(1, (1, 1), activation='sigmoid', name='region_score')(u1)
    affinity_score = layers.Conv2D(1, (1, 1), activation='sigmoid', name='affinity_score')(u1)
    
    model = models.Model(inputs=inputs, outputs=[region_score, affinity_score])
    return model

if __name__ == "__main__":
    craft = build_craft_model()
    craft.summary()
    print("\n--- CRAFT FOR FOOD LABEL DETECTION ---")
    print("1. Region Score: Highlights individual letters/numbers.")
    print("2. Affinity Score: Highlights the gaps between letters to group them into words.")
    print("3. Advantage: Extremely robust for curved labels where standard rectangle boxes fail.")
