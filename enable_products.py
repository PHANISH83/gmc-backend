"""
Enable Products - Re-activate disabled products
Sets gmc_active to "yes" in products.json AND pushes to GMC.

Usage:
  python enable_products.py PRD-00001 PRD-00002 PRD-00003
  OR
  python enable_products.py --file enable_list.csv
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import json
import pandas as pd
from dotenv import load_dotenv
from gmc_manager import GMCManager

load_dotenv()

def get_product_data(products, sku):
    """Get formatted product data for GMC."""
    for p in products:
        if str(p.get('code')) == sku:
            weight = 1000
            if p.get('variants') and len(p['variants']) > 0:
                weight = p['variants'][0].get('weight', 1) * 1000
            
            return {
                'objectID': p['code'],
                'title': p['productname'],
                'description': p.get('indepthdescn', p.get('briedfdescn', '')),
                'price': p.get('minprice', 0),
                'image': p.get('featured_img', ''),
                'brand': p.get('brand', 'Generic'),
                'slug': p.get('produrltitle', p['code']),
                'weight': weight
            }
    return None

def main():
    merchant_id = os.getenv('GMC_MERCHANT_ID')
    
    print("=" * 60)
    print("ENABLE PRODUCTS (Set gmc_active to 'yes')")
    print("=" * 60)
    
    # Parse arguments
    args = sys.argv[1:]
    
    if not args:
        print("\nUsage:")
        print("  python enable_products.py PRD-00001 PRD-00002")
        print("  python enable_products.py --file enable_list.csv")
        return
    
    # Get SKUs
    if args[0] == '--file':
        if len(args) < 2:
            print("❌ Please specify a CSV file")
            return
        df = pd.read_csv(args[1])
        skus = [str(s).strip() for s in df['SKU'].tolist()]
    else:
        skus = [s.strip() for s in args]
    
    print(f"\n📋 Products to enable: {len(skus)}")
    for sku in skus:
        print(f"  - {sku}")
    
    # Initialize GMC
    try:
        gmc = GMCManager(merchant_id, 'service_account.json')
    except Exception as e:
        print(f"[ERROR] GMC Init: {e}")
        return
    
    # Load products.json
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        products = data.get('products', [])
    except Exception as e:
        print(f"[ERROR] Loading products.json: {e}")
        return
    
    # Process each SKU
    print("\nProcessing...")
    updated = 0
    pushed_to_gmc = 0
    
    for target_sku in skus:
        # 1. Update products.json
        found = False
        for p in products:
            if str(p.get('code')) == target_sku:
                p['gmc_active'] = 'yes'
                found = True
                break
        
        if found:
            updated += 1
            print(f"  ✓ {target_sku} -> gmc_active = 'yes'")
            
            # 2. Push to GMC
            product_data = get_product_data(products, target_sku)
            if product_data:
                try:
                    us_body = gmc.format_product(product_data, 'US', 'USD')
                    gmc.push_to_google(us_body)
                    pushed_to_gmc += 1
                except Exception as e:
                    print(f"    ⚠ GMC push failed: {e}")
        else:
            print(f"  ⚠ {target_sku} not found in products.json")
    
    # Save products.json
    with open('products.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ Updated {updated} products in products.json")
    print(f"✅ Pushed {pushed_to_gmc} products to GMC")
    print("=" * 60)

if __name__ == '__main__':
    main()
