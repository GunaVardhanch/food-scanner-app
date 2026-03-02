import requests
import json

gtin = "3017620422003"
url = f"https://world.openfoodfacts.org/api/v2/product/{gtin}"
response = requests.get(url)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Product found: {data.get('status') == 1}")
    if data.get('status') == 1:
        print(json.dumps(data.get('product', {}).get('product_name'), indent=2))
else:
    print(response.text)
