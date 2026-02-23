import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from crnn_text_recognition import build_crnn_model

# 1. Configuration
LABEL_FILE = "dataset/labels.txt"
BATCH_SIZE = 16
IMG_WIDTH = 200
IMG_HEIGHT = 50

# Character vocabulary
characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.-"
char_to_num = layers.StringLookup(vocabulary=list(characters), mask_token=None)
num_to_char = layers.StringLookup(vocabulary=char_to_num.get_vocabulary(), mask_token=None, invert=True)

def encode_single_sample(img_path, label):
    # Read image
    img = tf.io.read_file(img_path)
    img = tf.io.decode_png(img, channels=1)
    img = tf.image.convert_image_dtype(img, tf.float32)
    img = tf.image.resize(img, [IMG_HEIGHT, IMG_WIDTH])
    img = tf.transpose(img, perm=[1, 0, 2]) # (W, H, C) for CRNN
    
    # Encode label
    label = char_to_num(tf.strings.unicode_split(label, input_encoding="UTF-8"))
    
    return {"image": img, "label": label}

def CTCLoss(y_true, y_pred):
    batch_len = tf.cast(tf.shape(y_true)[0], dtype="int64")
    input_length = tf.cast(tf.shape(y_pred)[1], dtype="int64")
    label_length = tf.cast(tf.shape(y_true)[1], dtype="int64")

    input_length = input_length * tf.ones(shape=(batch_len, 1), dtype="int64")
    label_length = label_length * tf.ones(shape=(batch_len, 1), dtype="int64")

    loss = keras.backend.ctc_batch_cost(y_true, y_pred, input_length, label_length)
    return loss

def main():
    # Load dataset
    img_paths = []
    labels = []
    with open(LABEL_FILE, "r") as f:
        for line in f:
            path, label = line.strip().split("\t")
            img_paths.append(path)
            labels.append(label)

    dataset = tf.data.Dataset.from_tensor_slices((img_paths, labels))
    dataset = (
        dataset.map(encode_single_sample, num_parallel_calls=tf.data.AUTOTUNE)
        .batch(BATCH_SIZE)
        .prefetch(buffer_size=tf.data.AUTOTUNE)
    )

    # Build model
    # Update vocabulary size in architecture
    model = build_crnn_model(img_width=IMG_WIDTH, img_height=IMG_HEIGHT)
    
    # Update the final dense layer to match our vocabulary
    # The prototype had 37, we need len(characters) + 1
    vocab_size = len(char_to_num.get_vocabulary())
    x = model.layers[-2].output # Get output of second to last layer
    output = layers.Dense(vocab_size + 1, activation="softmax", name="dense_output")(x)
    model = keras.models.Model(inputs=model.input, outputs=output)

    model.compile(optimizer=keras.optimizers.Adam(), loss=CTCLoss)

    print("Starting training...")
    # Train for a few epochs for demonstration
    model.fit(dataset, epochs=5)
    
    # Save the model
    model.save("backend/ocr_model_v1.h5")
    print("Model saved to backend/ocr_model_v1.h5")

if __name__ == "__main__":
    main()
