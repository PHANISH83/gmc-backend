"""
Push All 55 Products to Google Merchant Center
Run this script to upload all products from products.json to your GMC account.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import os
from dotenv import load_dotenv
from gmc_manager import GMCManager

load_dotenv()

def get_product_data(product):
    """Format a product for GMC upload."""
    # Get weight from first variant if available
    weight = 1000  # Default 1kg in grams
    weight_unit = 'g'
    if product.get('variants') and len(product['variants']) > 0:
        variant = product['variants'][0]
        weight = variant.get('weight', 1) * 1000  # Convert kg to g
        weight_unit = 'g'
    
    return {
        'objectID': product['code'],
        'title': product['productname'],
        'description': product.get('indepthdescn', product.get('briedfdescn', '')),
        'price': product.get('minprice', 0),
        'image': product.get('featured_img', ''),
        'sku': product['code'],
        'brand': product.get('brand', 'Generic'),
        'category': product.get('category', ''),
        'weight': weight,
        'weight_unit': weight_unit,
        'slug': product.get('produrltitle', product['code'])
    }

def main():
    merchant_id = os.getenv('GMC_MERCHANT_ID')
    
    if not merchant_id or merchant_id == 'YOUR_GMC_ID_HERE':
        print("[ERROR] GMC_MERCHANT_ID not set in .env file!")
        print("Please add your Merchant ID to the .env file")
        return
    
    print("=" * 60)
    print("PUSHING ALL PRODUCTS TO GOOGLE MERCHANT CENTER")
    print("=" * 60)
    print(f"Merchant ID: {merchant_id}")
    
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
            print(f"\n[INFO] Found {len(products)} products in products.json")
    except Exception as e:
        print(f"[ERROR] Failed to load products.json: {e}")
        return
    
    # Push each product
    success_count = 0
    fail_count = 0
    
    print("\n" + "-" * 60)
    print("Starting upload...")
    print("-" * 60)
    
    for i, product in enumerate(products, 1):
        sku = product.get('code', f'product-{i}')
        
        # --- FLAG CHECK ---
        # User wants "yes"/"no" control.
        # Check if flag exists and is explicitly "no" (case-insensitive)
        gmc_flag = str(product.get('gmc_active', 'yes')).lower()
        
        if gmc_flag == 'no' or gmc_flag == 'false':
             print(f"[{i:02d}/{len(products)}] - {sku} - Skipped (gmc_active=no)")
             continue
        # ------------------

        product_data = get_product_data(product)
        
        try:
            # Push to US market (USD)
            us_body = gmc.format_product(product_data, 'US', 'USD')
            us_success, us_msg = gmc.push_to_google(us_body)
            
            if us_success:
                print(f"[{i:02d}/{len(products)}] ✓ {sku} - {product['productname'][:40]}...")
                success_count += 1
            else:
                print(f"[{i:02d}/{len(products)}] ✗ {sku} - Error: {us_msg[:50]}")
                fail_count += 1
                
        except Exception as e:
            print(f"[{i:02d}/{len(products)}] ✗ {sku} - Exception: {str(e)[:50]}")
            fail_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("UPLOAD COMPLETE!")
    print("=" * 60)
    print(f"✓ Success: {success_count}")
    print(f"✗ Failed:  {fail_count}")
    print(f"Total:     {len(products)}")
    print("=" * 60)
    print("\nCheck your Google Merchant Center dashboard to verify products.")

if __name__ == '__main__':
    main()
