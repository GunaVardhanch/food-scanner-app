import tensorflow as tf
from tensorflow.keras import layers, models
import matplotlib.pyplot as plt

def build_food_cnn_model(input_shape=(224, 224, 3), num_classes=3):
    """
    Builds a Convolutional Neural Network (CNN) for Food Category Classification.
    Categories could be: 0: Healthy, 1: Moderate, 2: Ultra-Processed
    """
    model = models.Sequential([
        # --- PHASE 1: Feature Extraction (CNN Layers) ---
        
        # 1st Convolutional Layer: Detects simple edges/textures
        layers.Conv2D(32, (3, 3), activation='relu', input_shape=input_shape),
        layers.MaxPooling2D((2, 2)),
        
        # 2nd Convolutional Layer: Detects more complex shapes
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        
        # 3rd Convolutional Layer: High-level feature patterns
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        
        # --- PHASE 2: Classification (Dense Layers) ---
        
        # Flatten the 3D features into a 1D vector
        layers.Flatten(),
        
        # Fully connected layer
        layers.Dense(512, activation='relu'),
        layers.Dropout(0.5), # Prevents overfitting (memorizing the data)
        
        # Output layer with Softmax (returns probabilities for each category)
        layers.Dense(num_classes, activation='softmax')
    ])

    return model

# 1. Create the model
app_model = build_food_cnn_model()

# 2. Compile the model
# Using Adam optimizer (smart gradient descent)
# Using Categorical Crossentropy (standard for multi-class classification)
app_model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# 3. Print the Architecture Overview
print("\n--- FOOD SCANNER CNN ARCHITECTURE OVERVIEW ---")
app_model.summary()

print("\n--- HOW THIS CNN WORKS IN YOUR PROJECT ---")
print("1. INPUT: The photo of the food label you snap in React.")
print("2. CONVOLUTION: Small filters slide over the image to 'see' ingredients and tables.")
print("3. POOLING: Reduces image size while keeping the most important information.")
print("4. DENSE: The 'brain' part that decides if the food is Healthy or Harmful based on visual patterns.")

# Suggestion for the user:
# To train this, you would need a folder 'dataset/' with subfolders for 'healthy', 'processed', etc.
# Then you would run: model.fit(train_data, epochs=10)
