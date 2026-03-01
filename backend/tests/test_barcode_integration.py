import requests
import base64
import os
import sys

# Constants
API_URL = "http://localhost:5000/analyze"  # Fixed route prefix
TEST_GTIN = "3017620422003"  # Nutella

def test_gtin_lookup():
    """Test directly sending a GTIN to the API."""
    print(f"Testing GTIN lookup for: {TEST_GTIN}")
    payload = {
        "gtin": TEST_GTIN
    }
    try:
        response = requests.post(API_URL, json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Product: {data.get('product_name')} ({data.get('brand')})")
            print(f"Source: {data.get('source')}")
            print(f"Health Score: {data.get('health_score')} ({data.get('score_value')})")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Failed to connect to API: {e}")

if __name__ == "__main__":
    # Check if a port was provided
    if len(sys.argv) > 1:
        API_URL = f"http://localhost:{sys.argv[1]}/analyze"
    
    test_gtin_lookup()
