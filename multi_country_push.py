"""
Multi-Country Batch Push - Scalable GMC Sync
Reads country_config.json and pushes products to ALL enabled countries.
Uses regional_prices from products.json for accurate pricing.
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

def load_country_config():
    """Load country configuration."""
    with open('country_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_enabled_countries(config):
    """Get list of enabled countries from config."""
    return {
        code: cfg for code, cfg in config.get('countries', {}).items() 
        if cfg.get('enabled', False)
    }

def format_product_for_country(product, country_code, country_cfg, gmc):
    """Format a product for a specific country."""
    
    # Get regional price if available, otherwise calculate
    regional = product.get('regional_prices', {}).get(country_code, {})
    
    if regional:
        price = regional.get('price', 0)
        currency = regional.get('currency', country_cfg['currency'])
    else:
        # Fallback: calculate from USD price
        usd_price = product.get('usd_price', product.get('minprice', 0) * 0.012)
        price = round(usd_price * country_cfg['multiplier'], 2)
        currency = country_cfg['currency']
    
    # Get weight from variants
    weight = 1000
    if product.get('variants') and len(product['variants']) > 0:
        variant = product['variants'][0]
        weight = variant.get('weight', 1) * 1000
    
    # Build product data for GMC
    product_data = {
        'objectID': product['code'],
        'productname': product['productname'],
        'description': product.get('indepthdescn', product.get('briedfdescn', '')),
        'briedfdescn': product.get('briedfdescn', ''),
        'indepthdescn': product.get('indepthdescn', ''),
        'featured_img': product.get('featured_img', ''),
        'additional_images': product.get('additional_images', []),
        'brand': product.get('brand', 'Generic'),
        'produrltitle': product.get('produrltitle', product['code']),
        'price': price,
        'weight': weight
    }
    
    # Use GMC manager to format (handles shipping, images, etc.)
    body = gmc.format_product(product_data, country_code, currency)
    
    # Override price with our calculated regional price
    body['price'] = {
        'value': f"{price:.2f}",
        'currency': currency
    }
    
    # Override shipping with country-specific shipping
    shipping_cost = country_cfg.get('shipping_cost', 9.99)
    body['shipping'] = [{
        'country': country_code,
        'service': 'Standard Shipping',
        'price': {'value': str(shipping_cost), 'currency': currency}
    }]
    
    return body

def main():
    merchant_id = os.getenv('GMC_MERCHANT_ID')
    
    if not merchant_id or merchant_id == 'YOUR_GMC_ID_HERE':
        print("[ERROR] GMC_MERCHANT_ID not set in .env file!")
        return
    
    print("=" * 70)
    print("MULTI-COUNTRY BATCH PUSH - Scalable GMC Sync")
    print("=" * 70)
    
    # Load configuration
    config = load_country_config()
    enabled_countries = get_enabled_countries(config)
    
    print(f"\n[CONFIG] Base exchange rate: INR -> USD = {config.get('base_exchange_from_inr', 0.012)}")
    print(f"[CONFIG] Enabled countries: {list(enabled_countries.keys())}")
    
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
    
    # Filter active products (gmc_active = yes)
    active_products = [p for p in products if str(p.get('gmc_active', 'yes')).lower() == 'yes']
    print(f"\n[INFO] Active products: {len(active_products)} (gmc_active=yes)")
    
    if not active_products:
        print("No active products to push.")
        return
    
    # Format products for ALL enabled countries
    print("\n[INFO] Formatting products for all countries...")
    all_product_bodies = []
    
    for country_code, country_cfg in enabled_countries.items():
        country_bodies = []
        for product in active_products:
            try:
                body = format_product_for_country(product, country_code, country_cfg, gmc)
                country_bodies.append(body)
            except Exception as e:
                print(f"[WARN] Error formatting {product['code']} for {country_code}: {e}")
        
        all_product_bodies.extend(country_bodies)
        print(f"   {country_code}: {len(country_bodies)} products ({country_cfg['currency']})")
    
    print(f"\n[INFO] Total products to push: {len(all_product_bodies)}")
    print(f"       ({len(active_products)} products × {len(enabled_countries)} countries)")
    
    # Push using batch API
    print("\n" + "-" * 70)
    print("Pushing via Batch API (this is much faster!)...")
    print("-" * 70)
    
    start_time = time.time()
    success, fail, errors = gmc.batch_push(all_product_bodies)
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 70)
    print("MULTI-COUNTRY BATCH UPLOAD COMPLETE!")
    print("=" * 70)
    print(f"✓ Success: {success}")
    print(f"✗ Failed:  {fail}")
    print(f"⏱ Time:    {elapsed:.2f} seconds")
    print(f"🌍 Countries: {list(enabled_countries.keys())}")
    print("=" * 70)
    
    if errors and len(errors) > 0:
        print(f"\n[ERRORS] {len(errors)} errors occurred:")
        for e in errors[:5]:  # Show first 5
            print(f"  - {e}")

if __name__ == '__main__':
    main()
