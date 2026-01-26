"""
Test GMC push with one product to debug any issues.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import os
from dotenv import load_dotenv
from gmc_manager import GMCManager

load_dotenv()

merchant_id = os.getenv('GMC_MERCHANT_ID')
print(f'Merchant ID: {merchant_id}')

# Test GMC initialization
try:
    gmc = GMCManager(merchant_id, 'service_account.json')
    print('GMC initialized OK')
except Exception as e:
    print(f'GMC init error: {e}')
    exit()

# Load and try one product
with open('products.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    products = data.get('products', [])
    print(f'Total products: {len(products)}')
    
    if products:
        p = products[0]
        product_data = {
            'objectID': p['code'],
            'title': p['productname'],
            'description': p.get('indepthdescn', ''),
            'price': p.get('minprice', 0),
            'image': p.get('featured_img', ''),
            'sku': p['code'],
            'brand': p.get('brand', 'Generic'),
            'category': p.get('category', ''),
            'weight': 500,
            'weight_unit': 'g',
            'slug': p.get('produrltitle', p['code'])
        }
        print(f'Testing product: {p["code"]}')
        
        us_body = gmc.format_product(product_data, 'US', 'USD')
        print(f'Formatted body:')
        print(json.dumps(us_body, indent=2))
        
        success, msg = gmc.push_to_google(us_body)
        print(f'Result: success={success}, msg={msg}')
