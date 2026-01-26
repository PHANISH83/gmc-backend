"""
Delete All Products from Google Merchant Center
Run this script to REMOVE all products in products.json from your GMC account.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import os
from dotenv import load_dotenv
from gmc_manager import GMCManager

load_dotenv()

def main():
    merchant_id = os.getenv('GMC_MERCHANT_ID')
    
    print("=" * 60)
    print("DELETE ALL PRODUCTS FROM GOOGLE MERCHANT CENTER")
    print("=" * 60)
    
    confirm = input("Are you sure you want to delete all products? (Type 'YES' to confirm): ")
    if confirm.strip() != 'YES':
        print("Aborted.")
        return

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
            print(f"\n[INFO] Found {len(products)} products to delete")
    except Exception as e:
        print(f"[ERROR] Failed to load products.json: {e}")
        return
    
    success_count = 0
    
    print("\n" + "-" * 60)
    print("Starting deletion...")
    print("-" * 60)
    
    for i, product in enumerate(products, 1):
        sku = product['code']
        
        # We constructed offerId as SKU-Country in the push script
        # e.g. PRD-00001-US
        
        # 1. Delete US Version
        offer_id_us = f"{sku}-US"
        success_us, msg_us = gmc.delete_product(offer_id_us, 'US')
        
        # 2. Delete AU Version
        offer_id_au = f"{sku}-AU"
        success_au, msg_au = gmc.delete_product(offer_id_au, 'AU')

        status_str = []
        if success_us: status_str.append("US: Deleted")
        else: status_str.append(f"US: {msg_us[:20]}")
        
        if success_au: status_str.append("AU: Deleted")
        else: status_str.append(f"AU: {msg_au[:20]}")
        
        print(f"[{i:02d}/{len(products)}] {sku} -> " + " | ".join(status_str))
        
        if success_us or success_au:
            success_count += 1
            
    print("\n" + "=" * 60)
    print("DELETION COMPLETE!")
    print(f"Processed: {success_count} products")
    print("=" * 60)

if __name__ == '__main__':
    main()
