"""
Push UK Products Only - Debug Version
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import os
from dotenv import load_dotenv
from gmc_manager import GMCManager

load_dotenv()

EXCHANGE_RATE_USD = 0.012  # 1 INR -> USD

def main():
    merchant_id = os.getenv('GMC_MERCHANT_ID')
    gmc = GMCManager(merchant_id, 'service_account.json')
    
    # Load products
    with open('products.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        products = data.get('products', [])
    
    # Get first active product
    active = [p for p in products if str(p.get('gmc_active', '')).lower() == 'yes']
    
    if not active:
        print("No active products")
        return
    
    p = active[0]
    print(f"Testing with: {p['code']} - {p['productname']}")
    
    # Build UK product
    inr_price = float(p.get('minprice', 0))
    uk_price = float(p.get('uk_price', inr_price * 1.2))
    gbp_price = round(uk_price * EXCHANGE_RATE_USD * 0.79, 2)
    
    product_data = {
        'objectID': p['code'],
        'productname': p['productname'],
        'description': p.get('briedfdescn', ''),
        'featured_img': p.get('featured_img', ''),
        'brand': p.get('brand', 'Generic'),
        'produrltitle': p.get('produrltitle', p['code']),
        'price': gbp_price,
        'weight': 1000
    }
    
    body = gmc.format_product(product_data, 'GB', 'GBP')
    body['price']['value'] = str(gbp_price)
    
    print(f"\nProduct body for UK:")
    print(json.dumps(body, indent=2))
    
    # Try to push
    print("\nAttempting to push to GMC...")
    success, result = gmc.push_to_google(body)
    print(f"Success: {success}")
    print(f"Result: {result}")

if __name__ == '__main__':
    main()
