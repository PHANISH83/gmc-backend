"""
Price Watchdog - Auto-Read from products.json
Automatically checks ALL products with gmc_active=yes, no registration needed.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import time
import schedule
import json
import os
from gmc_manager import GMCManager
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
MERCHANT_ID = os.getenv('GMC_MERCHANT_ID')
gmc_bot = GMCManager(MERCHANT_ID, 'service_account.json')
EXCHANGE_RATE_USD = 0.012  # 1 INR -> USD
EXCHANGE_RATE_AUD = 0.018  # 1 INR -> AUD

# In-memory cache of last known prices
price_cache = {}

def load_active_products():
    """Load ALL products with gmc_active=yes from products.json"""
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            products = data.get('products', data)
            # Filter only active products
            active = [p for p in products if str(p.get('gmc_active', '')).lower() == 'yes']
            return active
    except Exception as e:
        print(f"Error loading products.json: {e}")
        return []

def check_for_price_changes():
    global price_cache
    
    print(f"\n🕵️ [Watchdog] Scanning products.json for price changes...")
    
    # Read ALL active products directly from JSON
    active_products = load_active_products()
    
    if not active_products:
        print("   -> No active products (gmc_active=yes) found.")
        return
    
    print(f"   Found {len(active_products)} active products.")
    changes_found = 0
    
    for p in active_products:
        sku = p.get('code')
        current_price = float(p.get('minprice', 0))
        last_price = price_cache.get(sku, None)
        
        # First run: just cache the price
        if last_price is None:
            price_cache[sku] = current_price
            continue
        
        # Check for change
        if current_price != last_price:
            print(f"⚡ PRICE CHANGE: {sku}")
            print(f"   ₹{last_price} -> ₹{current_price}")
            
            new_usd = round(current_price * EXCHANGE_RATE_USD, 2)
            new_aud = round(current_price * EXCHANGE_RATE_AUD, 2)
            
            try:
                # Format product for GMC
                formatted = {
                    'objectID': p['code'],
                    'title': p['productname'],
                    'description': p.get('indepthdescn', p.get('briedfdescn', '')),
                    'price': current_price,
                    'image': p.get('featured_img', ''),
                    'brand': p.get('brand', 'Generic'),
                    'slug': p.get('produrltitle', p['code'])
                }
                
                # Push US only (scaling to AU later)
                us_body = gmc_bot.format_product(formatted, 'US', 'USD')
                us_body['price']['value'] = str(new_usd)
                gmc_bot.service.products().insert(merchantId=MERCHANT_ID, body=us_body).execute()
                
                # Update cache
                price_cache[sku] = current_price
                changes_found += 1
                print(f"   ✅ Synced to GMC: ${new_usd} USD")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
    
    if changes_found == 0:
        print("✅ No price changes detected.")
    else:
        print(f"✅ Updated {changes_found} products in GMC.")

# --- MAIN ---
if __name__ == '__main__':
    print("=" * 60)
    print("PRICE WATCHDOG - Auto-Read Mode")
    print("=" * 60)
    
    # Initial scan (caches all prices)
    print("\n📝 Initial scan - caching current prices...")
    active = load_active_products()
    for p in active:
        price_cache[p['code']] = float(p.get('minprice', 0))
    print(f"   Cached {len(price_cache)} products.")
    
    # Schedule every 1 minute (test mode)
    schedule.every(1).minutes.do(check_for_price_changes)
    
    print("\n" + "-" * 60)
    print("🧪 TEST MODE: Checking every 1 minute.")
    print("   Change a price in products.json and wait...")
    print("-" * 60)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
