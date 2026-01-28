"""
Multi-Country Batch Push - Using NEW Merchant API
Replaces Content API with the modern Merchant API (v1beta)
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import os
import time
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.shopping.merchant_products_v1beta import ProductInputsServiceClient
from google.shopping.merchant_products_v1beta import ProductInput, InsertProductInputRequest
from google.shopping.merchant_products_v1beta.types import Attributes
from google.type import money_pb2

load_dotenv()

def load_country_config():
    """Load country configuration with data source IDs."""
    with open('country_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_enabled_countries(config):
    """Get list of enabled countries from config."""
    return {
        code: cfg for code, cfg in config.get('countries', {}).items() 
        if cfg.get('enabled', False) and cfg.get('data_source_id')
    }

def format_product_for_merchant_api(product, country_code, country_cfg, merchant_id):
    """Format a product for the Merchant API."""
    
    offer_id = f"{product['code']}-{country_code}"
    title = product.get('productname', 'Unknown Product')
    slug = product.get('produrltitle', product['code'])
    
    # Get regional price
    regional = product.get('regional_prices', {}).get(country_code, {})
    price = regional.get('price', 0)
    currency = country_cfg['currency']
    
    # Image handling
    image = product.get('featured_img', '')
    if 'unsplash.com' in image and 'fm=jpg' not in image:
        image = image.replace('?', '?fm=jpg&') if '?' in image else f"{image}?fm=jpg"
    if not image or 'example.com' in image:
        image = "https://images.unsplash.com/photo-1606923829579-0cb981a83e2e?w=800&h=800&fit=crop&fm=jpg"
    
    # Additional images (filter valid ones)
    additional_images = [img for img in product.get('additional_images', []) if img and img != image][:10]
    
    # Shipping cost
    shipping_cost = country_cfg.get('shipping_cost', 9.99)
    
    # Price in micros (API uses micros = value * 1,000,000)
    price_micros = int(price * 1_000_000)
    shipping_micros = int(shipping_cost * 1_000_000)
    
    # Build ProductInput for Merchant API
    product_input = ProductInput(
        offer_id=offer_id,
        content_language="en",
        feed_label=country_code,
        attributes={
            "title": title,
            "description": product.get('indepthdescn', product.get('briedfdescn', title))[:5000],
            "link": f"https://gmc-dashboard.vercel.app/products/{slug}",
            "image_link": image,
            "additional_image_links": additional_images,
            "availability": "in_stock",
            "condition": "new",
            "brand": product.get('brand', 'Generic'),
            "identifier_exists": False,
        }
    )
    
    return product_input, price, currency, shipping_cost

def main():
    merchant_id = os.getenv('GMC_MERCHANT_ID')
    account = f"accounts/{merchant_id}"
    
    if not merchant_id:
        print("[ERROR] GMC_MERCHANT_ID not set in .env file!")
        return
    
    print("=" * 70)
    print("MERCHANT API PUSH - New Google Merchant API")
    print("=" * 70)
    
    # Load credentials
    credentials = service_account.Credentials.from_service_account_file(
        'service_account.json',
        scopes=['https://www.googleapis.com/auth/content']
    )
    
    # Initialize client
    client = ProductInputsServiceClient(credentials=credentials)
    print(f"[API] Merchant API client ready (Account: {merchant_id})")
    
    # Load configuration
    config = load_country_config()
    enabled_countries = get_enabled_countries(config)
    
    print(f"[CONFIG] Enabled countries: {list(enabled_countries.keys())}")
    
    # Load products
    with open('products.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        products = data.get('products', [])
    
    # Filter active products
    active_products = [p for p in products if str(p.get('gmc_active', 'yes')).lower() == 'yes']
    print(f"[INFO] Active products: {len(active_products)}")
    
    if not active_products:
        print("No active products to push.")
        return
    
    # Push products
    print("\n" + "-" * 70)
    print("Pushing products via Merchant API...")
    print("-" * 70)
    
    start_time = time.time()
    total_success = 0
    total_fail = 0
    errors = []
    
    for country_code, country_cfg in enabled_countries.items():
        data_source = f"accounts/{merchant_id}/dataSources/{country_cfg['data_source_id']}"
        country_success = 0
        country_fail = 0
        
        for product in active_products:
            try:
                product_input, price, currency, shipping = format_product_for_merchant_api(
                    product, country_code, country_cfg, merchant_id
                )
                
                request = InsertProductInputRequest(
                    parent=account,
                    product_input=product_input,
                    data_source=data_source
                )
                
                response = client.insert_product_input(request=request)
                country_success += 1
                
            except Exception as e:
                country_fail += 1
                error_msg = str(e)[:80]
                if len(errors) < 10:
                    errors.append(f"{product['code']}-{country_code}: {error_msg}")
        
        total_success += country_success
        total_fail += country_fail
        print(f"  {country_code}: ✓ {country_success} | ✗ {country_fail}")
    
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 70)
    print("MERCHANT API PUSH COMPLETE!")
    print("=" * 70)
    print(f"✓ Success: {total_success}")
    print(f"✗ Failed:  {total_fail}")
    print(f"⏱ Time:    {elapsed:.2f} seconds")
    print(f"🌍 Countries: {list(enabled_countries.keys())}")
    print("=" * 70)
    
    if errors:
        print(f"\n[ERRORS] First {len(errors)} errors:")
        for e in errors:
            print(f"  - {e}")

if __name__ == '__main__':
    main()
