import os
import tensorflow as tf

def convert_to_tflite(h5_model_path, output_path):
    """
    Converts a Keras H5 model to TFLite format with quantization.
    """
    if not os.path.exists(h5_model_path):
        print(f"Error: Model file {h5_model_path} not found. Create it by running train_ocr.py first.")
        return

    print(f"Converting {h5_model_path} to TFLite...")
    
    # Load the Keras model
    try:
        model = tf.keras.models.load_model(h5_model_path, compile=False)
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    # Create TFLite converter
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # 1. Enable basic optimizations
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    
    # 2. Add Float16 quantization (Balances size and accuracy)
    converter.target_spec.supported_types = [tf.float16]
    
    # Convert
    tflite_model = converter.convert()
    
    # Save
    with open(output_path, 'wb') as f:
        f.write(tflite_model)
        
    print(f"✅ Success! Optimized model saved to: {output_path}")
    print(f"File size reduced dramatically for mobile deployment.")

if __name__ == "__main__":
    H5_PATH = "backend/ocr_model_v1.h5"
    TFLITE_PATH = "backend/ocr_model_v1.tflite"
    
    convert_to_tflite(H5_PATH, TFLITE_PATH)
