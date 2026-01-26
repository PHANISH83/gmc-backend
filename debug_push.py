"""
Debug GMC push - writes detailed output to log file
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import os
from dotenv import load_dotenv
from gmc_manager import GMCManager

load_dotenv()

log_lines = []

def log(msg):
    print(msg)
    log_lines.append(msg)

merchant_id = os.getenv('GMC_MERCHANT_ID')
log(f'Merchant ID: {merchant_id}')

# Test GMC initialization
try:
    gmc = GMCManager(merchant_id, 'service_account.json')
    log('GMC initialized OK')
except Exception as e:
    log(f'GMC init error: {e}')
    with open('push_debug.log', 'w', encoding='utf-8') as f:
        f.write('\n'.join(log_lines))
    exit()

# Load products
with open('products.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    products = data.get('products', [])
    log(f'Total products: {len(products)}')

# Try first 3 products
for i, p in enumerate(products[:3]):
    log(f'\n--- Product {i+1} ---')
    log(f'Code: {p["code"]}')
    log(f'Name: {p["productname"]}')
    log(f'Price: {p.get("minprice", 0)}')
    
    product_data = {
        'objectID': p['code'],
        'title': p['productname'],
        'description': p.get('indepthdescn', '')[:500],
        'price': p.get('minprice', 0),
        'image': p.get('featured_img', ''),
        'sku': p['code'],
        'brand': p.get('brand', 'Generic'),
        'category': p.get('category', ''),
        'weight': 500,
        'weight_unit': 'g',
        'slug': p.get('produrltitle', p['code'])
    }
    
    try:
        us_body = gmc.format_product(product_data, 'US', 'USD')
        log(f'Formatted body: {json.dumps(us_body, indent=2)}')
        
        success, msg = gmc.push_to_google(us_body)
        log(f'Push result: success={success}')
        log(f'Message: {msg}')
    except Exception as e:
        log(f'Exception: {e}')

# Write log file
with open('push_debug.log', 'w', encoding='utf-8') as f:
    f.write('\n'.join(log_lines))

log('\nLog written to push_debug.log')
