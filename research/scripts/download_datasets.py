import os
import requests
import sys

def download_file(url, target_path):
    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        print(f"Skipping {target_path}, already exists.")
        return
        
    print(f"Downloading {url} to {target_path}...")
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Successfully downloaded to {target_path}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

if __name__ == "__main__":
    # Project Base
    SCRATCH_DIR = r"C:\Users\STUDENT\.gemini\antigravity\scratch\food-scanner-app"
    DATASET_DIR = os.path.join(SCRATCH_DIR, "dataset")

    # URLs
    OFF_URL = "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz"
    # N5K Metadata links (found via research)
    N5K_CAFE1_URL = "https://raw.githubusercontent.com/google-research-datasets/Nutrition5k/main/metadata/dish_metadata_cafe1.csv"
    N5K_CAFE2_URL = "https://raw.githubusercontent.com/google-research-datasets/Nutrition5k/main/metadata/dish_metadata_cafe2.csv"
    N5K_INGREDIENTS_URL = "https://raw.githubusercontent.com/google-research-datasets/Nutrition5k/main/metadata/ingredient_metadata.csv"
    
    # Target Paths
    off_path = os.path.join(DATASET_DIR, "openfoodfacts/products.csv.gz")
    n5k_cafe1 = os.path.join(DATASET_DIR, "nutrition5k/dish_metadata_cafe1.csv")
    n5k_cafe2 = os.path.join(DATASET_DIR, "nutrition5k/dish_metadata_cafe2.csv")
    n5k_ingredients = os.path.join(DATASET_DIR, "nutrition5k/ingredient_metadata.csv")
    
    # Download
    print("Starting dataset ingestion...")
    # Skipping large OFF CSV for now to focus on N5K metadata
    # download_file(OFF_URL, off_path) 
    download_file(N5K_CAFE1_URL, n5k_cafe1)
    download_file(N5K_CAFE2_URL, n5k_cafe2)
    download_file(N5K_INGREDIENTS_URL, n5k_ingredients)
    print("Dataset ingestion complete.")
