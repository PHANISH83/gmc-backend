"""
Disable Products - The Smart Way
Sets gmc_active to "no" in products.json AND removes from GMC.
This is reversible: just set back to "yes" and run push_all_products.py

Usage:
  python disable_products.py PRD-00001 PRD-00002 PRD-00003
  OR
  python disable_products.py --file disable_list.csv
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

def main():
    merchant_id = os.getenv('GMC_MERCHANT_ID')
    
    print("=" * 60)
    print("DISABLE PRODUCTS (Set gmc_active to 'no')")
    print("=" * 60)
    
    # Parse arguments
    args = sys.argv[1:]
    
    if not args:
        print("\nUsage:")
        print("  python disable_products.py PRD-00001 PRD-00002")
        print("  python disable_products.py --file disable_list.csv")
        return
    
    # Get SKUs from args or file
    if args[0] == '--file':
        if len(args) < 2:
            print("❌ Please specify a CSV file")
            return
        df = pd.read_csv(args[1])
        skus = [str(s).strip() for s in df['SKU'].tolist()]
    else:
        skus = [s.strip() for s in args]
    
    print(f"\n📋 Products to disable: {len(skus)}")
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
    deleted_from_gmc = 0
    
    for target_sku in skus:
        # 1. Update products.json
        found = False
        for p in products:
            if str(p.get('code')) == target_sku:
                p['gmc_active'] = 'no'
                found = True
                break
        
        if found:
            updated += 1
            print(f"  ✓ {target_sku} -> gmc_active = 'no'")
        else:
            print(f"  ⚠ {target_sku} not found in products.json")
        
        # 2. Delete from GMC
        s1, _ = gmc.delete_product(f"{target_sku}-US", 'US')
        s2, _ = gmc.delete_product(f"{target_sku}-AU", 'AU')
        
        if s1 or s2:
            deleted_from_gmc += 1
    
    # Save products.json
    with open('products.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ Updated {updated} products in products.json")
    print(f"✅ Removed {deleted_from_gmc} products from GMC")
    print("=" * 60)
    print("\n💡 To re-enable: Change 'no' to 'yes' in products.json, then run push_all_products.py")

if __name__ == '__main__':
    main()
