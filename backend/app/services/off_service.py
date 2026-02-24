import requests
from typing import Optional, Dict, Any

class OpenFoodFactsService:
    BASE_URL = "https://world.openfoodfacts.org"
    SEARCH_URL = f"{BASE_URL}/cgi/search.pl"
    PRODUCT_V2_URL = f"{BASE_URL}/api/v2/product"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "FoodScannerApp - Windows - Version 1.0 - https://github.com/yourusername/food-scanner-app"
        })

    def get_product_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Fetch product details by barcode."""
        try:
            url = f"{self.PRODUCT_V2_URL}/{barcode}"
            params = {
                "fields": "product_name,ingredients_text,nutriments,image_url,nutrition_grades,additives_tags"
            }
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 1:
                    return data.get("product")
            return None
        except Exception as e:
            print(f"Error fetching product by barcode: {e}")
            return None

    def search_products(self, query: str, page: int = 1) -> Dict[str, Any]:
        """Search for products by name/query."""
        try:
            params = {
                "search_terms": query,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page": page,
                "page_size": 10,
                "fields": "product_name,code,image_small_url,nutrition_grades"
            }
            response = self.session.get(self.SEARCH_URL, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {"products": [], "count": 0}
        except Exception as e:
            print(f"Error searching products: {e}")
            return {"products": [], "count": 0}

off_service = OpenFoodFactsService()
