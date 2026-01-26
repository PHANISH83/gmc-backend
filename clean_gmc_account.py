"""
Clean GMC Account - FORCE DELETE ALL
This script fetches all products directly from Google Merchant Center and deletes them.
Ref: User screenshot showing 'SW-xxx' products that are not in local json.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
from dotenv import load_dotenv
from gmc_manager import GMCManager

load_dotenv()

def main():
    merchant_id = os.getenv('GMC_MERCHANT_ID')
    
    print("=" * 60)
    print("FORCE CLEAN GMC ACCOUNT (DELETE EVERYTHING)")
    print("=" * 60)
    
    # Initialize GMC Manager
    try:
        gmc = GMCManager(merchant_id, 'service_account.json')
    except Exception as e:
        print(f"[ERROR] Failed to initialize GMC: {e}")
        return

    print("Fetching product list from Google... (this may take a moment)")
    try:
        products = gmc.list_all_products()
        count = len(products)
        print(f"\n[INFO] Found {count} products in GMC account.")
        
        if count == 0:
            print("Account is already empty.")
            return

        # Preview some products
        print("\nSample products found:")
        for p in products[:5]:
            print(f"- {p.get('offerId')} : {p.get('title')}")
            
    except Exception as e:
        print(f"[ERROR] Failed to list products: {e}")
        return

    print("\n" + "!" * 60)
    print(f"WARNING: This will delete ALL {count} products from GMC.")
    print("!" * 60)
    
    confirm = input(f"Type 'DELETE {count}' to confirm: ")
    if confirm.strip() != f"DELETE {count}":
        print("Aborted.")
        return
    
    print("\nStarting deletion...")
    success_count = 0
    
    for i, p in enumerate(products, 1):
        offer_id = p.get('offerId')
        # The productId format in the list response is typically online:en:COUNTRY:OFFERID
        # But our delete_product method expects the raw offerId and country.
        # We can extract them from the productId in the response resource.
        
        full_id = p.get('id') # e.g. online:en:US:SW-010
        parts = full_id.split(':')
        
        if len(parts) >= 4:
            country = parts[2]
            real_offer_id = parts[3]
            
            # Using our manager's delete helper
            success, msg = gmc.delete_product(real_offer_id, country)
            
            status = "Deleted" if success else f"Failed: {msg}"
            print(f"[{i:02d}/{count}] {full_id} -> {status}")
            
            if success:
                success_count += 1
        else:
            print(f"[{i:02d}/{count}] {full_id} -> Skipping (Invalid ID format)")

    print("\n" + "=" * 60)
    print("CLEANUP COMPLETE!")
    print(f"Deleted: {success_count} / {count}")
    print("=" * 60)

if __name__ == '__main__':
    main()
