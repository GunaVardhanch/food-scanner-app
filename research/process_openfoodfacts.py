import pandas as pd
import json

def parse_openfoodfacts_data(tsv_path, output_json):
    """
    Parses OpenFoodFacts TSV export to extract ingredients and target nutrients for NER training.
    """
    try:
        # Load only necessary columns to save memory
        cols = ['product_name', 'ingredients_text', 'energy-kcal_100g', 'sugars_100g', 'additives_en']
        df = pd.read_csv(tsv_path, sep='\t', usecols=cols, low_memory=False).dropna()
        
        ner_data = []
        for _, row in df.iterrows():
            # Construct a 'sentence' for NER training
            text = f"{row['product_name']} Ingredients: {row['ingredients_text']} Energy: {row['energy-kcal_100g']}kcal Sugars: {row['sugars_100g']}g"
            
            # Placeholder for label generation logic based on the structured data
            # In a real build, we'd use regex or token matching to assign B-CAL, B-SUGAR, etc.
            labels = ["O"] * len(text.split()) 
            
            ner_data.append({
                "text": text,
                "labels": labels # To be populated by label generator
            })
            
            if len(ner_data) >= 1000: # Limit for prototype
                break
                
        with open(output_json, 'w') as f:
            json.dump(ner_data, f)
        print(f"Successfully processed {len(ner_data)} products for NER.")
        
    except Exception as e:
        print(f"Error parsing OpenFoodFacts data: {e}")

if __name__ == "__main__":
    print("OpenFoodFacts parser ready.")
    # parse_openfoodfacts_data('en.openfoodfacts.org.products.csv', 'openfoodfacts_ner.json')
