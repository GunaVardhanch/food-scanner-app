import tensorflow as tf
from tensorflow.keras import layers, models

def build_crnn_model(img_width=200, img_height=50):
    """
    CRNN (Convolutional Recurrent Neural Network)
    Perfect for OCR: Reading ingredient names from food labels.
    CNN + RNN (LSTM) + CTC Loss
    """
    
    # 1. Input Layer
    inputs = layers.Input(shape=(img_width, img_height, 1), name="image")
    
    # --- PART 1: Convolutional Layers (CNN) ---
    # Extracts visual features of characters
    x = layers.Conv2D(32, (3, 3), activation="relu", padding="same")(inputs)
    x = layers.MaxPooling2D((2, 2))(x)
    
    x = layers.Conv2D(64, (3, 3), activation="relu", padding="same")(x)
    x = layers.MaxPooling2D((2, 2))(x)
    
    # --- PART 2: Reshaping for RNN ---
    # We need to treat the image as a sequence of vertical strips (reading from left to right)
    new_shape = ((img_width // 4), (img_height // 4) * 64)
    x = layers.Reshape(target_shape=new_shape)(x)
    x = layers.Dense(64, activation="relu")(x)
    x = layers.Dropout(0.2)(x)
    
    # --- PART 3: Recurrent Layers (RNN/LSTM) ---
    # Remembers context (e.g., if it sees 'M-A-L-T', the next letters are likely 'O-D-E-X-T-R-I-N')
    x = layers.Bidirectional(layers.LSTM(128, return_sequences=True))(x)
    x = layers.Bidirectional(layers.LSTM(64, return_sequences=True))(x)
    
    # --- PART 4: Output Layer ---
    # Number of possible characters (A-Z, 0-9, special chars) + 1 for 'blank'
    num_chars = 37 
    output = layers.Dense(num_chars, activation="softmax", name="dense_output")(x)
    
    model = models.Model(inputs=inputs, outputs=output, name="CRNN_OCR_Model")
    return model

# Create the model
ocr_model = build_crnn_model()

print("\n--- CRNN (CNN + RNN) ARCHITECTURE FOR OCR ---")
ocr_model.summary()

print("\n--- WHY WE USE THIS FOR FOOD LABELS ---")
print("1. CNN: Looks at the image and sees the shapes of letters (e.g., curves for 'O').")
print("2. Reshape: Cuts the image into vertical slices from left to right.")
print("3. LSTM (RNN): Understands the sequence of letters to correctly spell complex words like 'Maltodextrin'.")
print("4. ADVANTAGE: Much more accurate than a standard CNN for reading sentences/words on curved packets.")
