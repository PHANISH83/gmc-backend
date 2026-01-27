"""
Batch Push Products - 10x Faster Syncing
Uses Google's custombatch API to push thousands of products in seconds.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import os
import time
from dotenv import load_dotenv
from gmc_manager import GMCManager

load_dotenv()

EXCHANGE_RATE_USD = 0.012  # 1 INR -> USD

def get_product_data(product):
    """Format a product for GMC upload."""
    weight = 1000
    if product.get('variants') and len(product['variants']) > 0:
        variant = product['variants'][0]
        weight = variant.get('weight', 1) * 1000
    
    return {
        'objectID': product['code'],
        'title': product['productname'],
        'productname': product['productname'],
        'description': product.get('indepthdescn', product.get('briedfdescn', '')),
        'briedfdescn': product.get('briedfdescn', ''),
        'indepthdescn': product.get('indepthdescn', ''),
        'price': product.get('minprice', 0),
        'image': product.get('featured_img', ''),
        'featured_img': product.get('featured_img', ''),
        'brand': product.get('brand', 'Generic'),
        'slug': product.get('produrltitle', product['code']),
        'produrltitle': product.get('produrltitle', product['code']),
        'weight': weight
    }

def main():
    merchant_id = os.getenv('GMC_MERCHANT_ID')
    
    if not merchant_id or merchant_id == 'YOUR_GMC_ID_HERE':
        print("[ERROR] GMC_MERCHANT_ID not set in .env file!")
        return
    
    print("=" * 60)
    print("BATCH PUSH - 10x Faster Syncing")
    print("=" * 60)
    
    # Initialize GMC Manager
    try:
        gmc = GMCManager(merchant_id, 'service_account.json')
    except Exception as e:
        print(f"[ERROR] Failed to initialize GMC: {e}")
        return
    
    # Load products
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            products = data.get('products', [])
    except Exception as e:
        print(f"[ERROR] Failed to load products.json: {e}")
        return
    
    # Filter active products
    active_products = [p for p in products if str(p.get('gmc_active', 'yes')).lower() == 'yes']
    print(f"\n[INFO] Found {len(active_products)} active products (gmc_active=yes)")
    
    if not active_products:
        print("No active products to push.")
        return
    
    # Format all products for GMC
    print("[INFO] Formatting products for GMC...")
    product_bodies = []
    
    for p in active_products:
        product_data = get_product_data(p)
        
        # === US Market ===
        inr_price = float(p.get('minprice', 0))
        usd_price = round(inr_price * EXCHANGE_RATE_USD, 2)
        product_data['price'] = usd_price
        
        body_us = gmc.format_product(product_data, 'US', 'USD')
        body_us['price']['value'] = str(usd_price)
        product_bodies.append(body_us)
        
        # === UK Market ===
        uk_price = float(p.get('uk_price', inr_price * 1.2))
        uk_price_converted = round(uk_price * EXCHANGE_RATE_USD * 0.79, 2)  # USD to GBP approx
        product_data['price'] = uk_price_converted
        
        body_uk = gmc.format_product(product_data, 'GB', 'GBP')
        body_uk['price']['value'] = str(uk_price_converted)
        # Add UK shipping
        body_uk['shipping'] = [{
            'country': 'GB',
            'service': 'Standard Shipping',
            'price': {'value': '7.99', 'currency': 'GBP'}
        }]
        product_bodies.append(body_uk)
    
    print(f"[INFO] Prepared {len(product_bodies)} products for batch upload (US + UK)")

    
    # Push using batch API
    print("\n" + "-" * 60)
    print("Pushing via Batch API (this is much faster!)...")
    print("-" * 60)
    
    start_time = time.time()
    success, fail, errors = gmc.batch_push(product_bodies)
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 60)
    print("BATCH UPLOAD COMPLETE!")
    print("=" * 60)
    print(f"✓ Success: {success}")
    print(f"✗ Failed:  {fail}")
    print(f"⏱ Time:    {elapsed:.2f} seconds")
    print("=" * 60)
    
    if errors:
        print(f"\n[ERRORS] {len(errors)} errors occurred:")
        for e in errors[:5]:  # Show first 5
            print(f"  - {e}")

if __name__ == '__main__':
    main()
