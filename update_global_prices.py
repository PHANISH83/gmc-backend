"""
Update Global Prices - Scalable Multi-Country Pricing
Reads country_config.json and calculates regional prices for all products.
Optionally fetches real-time exchange rates.
"""
import json
import os
from datetime import datetime

# Optional: Uncomment to use real-time rates
# import requests

def load_country_config():
    """Load country configuration from JSON file."""
    config_path = os.path.join(os.path.dirname(__file__), 'country_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_live_exchange_rates(base_currency='USD'):
    """
    Optional: Fetch real-time exchange rates from a free API.
    Uncomment and use this to replace static multipliers.
    """
    # Free APIs:
    # - https://open.er-api.com/v6/latest/USD (no API key needed)
    # - https://api.exchangerate-api.com/v4/latest/USD
    
    # try:
    #     response = requests.get(f"https://open.er-api.com/v6/latest/{base_currency}")
    #     data = response.json()
    #     if data.get('result') == 'success':
    #         return data['rates']
    # except Exception as e:
    #     print(f"[WARN] Could not fetch live rates: {e}")
    
    return None  # Return None to use config multipliers

def calculate_regional_price(base_usd_price, country_config, live_rates=None):
    """
    Calculate price for a specific country.
    Uses live rates if available, otherwise uses config multiplier.
    """
    currency = country_config['currency']
    
    if live_rates and currency in live_rates:
        # Use real-time rate
        rate = live_rates[currency]
    else:
        # Use configured multiplier
        rate = country_config['multiplier']
    
    return round(base_usd_price * rate, 2)

def update_global_prices(use_live_rates=False):
    """
    Update all products with regional prices for each configured country.
    """
    # Load configuration
    config = load_country_config()
    countries = config.get('countries', {})
    base_exchange = config.get('base_exchange_from_inr', 0.012)
    
    # Optionally fetch live rates
    live_rates = None
    if use_live_rates:
        live_rates = get_live_exchange_rates()
        if live_rates:
            print("[INFO] Using real-time exchange rates")
        else:
            print("[INFO] Falling back to configured multipliers")
    
    # Load products
    with open('products.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    products = data.get('products', [])
    print(f"[INFO] Processing {len(products)} products")
    
    # Get enabled countries
    enabled_countries = {code: cfg for code, cfg in countries.items() if cfg.get('enabled', False)}
    print(f"[INFO] Enabled countries: {list(enabled_countries.keys())}")
    
    # Update each product
    for product in products:
        # Get base price in INR
        inr_price = float(product.get('minprice', 0))
        
        # Convert to USD (base currency)
        usd_price = round(inr_price * base_exchange, 2)
        product['usd_price'] = usd_price
        
        # Calculate regional prices
        product['regional_prices'] = {}
        
        for country_code, country_cfg in countries.items():
            local_price = calculate_regional_price(usd_price, country_cfg, live_rates)
            
            product['regional_prices'][country_code] = {
                'price': local_price,
                'currency': country_cfg['currency'],
                'symbol': country_cfg['symbol'],
                'formatted': f"{country_cfg['symbol']}{local_price}",
                'shipping': country_cfg['shipping_cost']
            }
    
    # Update metadata
    data['pricing_metadata'] = {
        'last_updated': datetime.now().isoformat(),
        'base_currency': 'USD',
        'inr_to_usd_rate': base_exchange,
        'enabled_countries': list(enabled_countries.keys()),
        'total_countries_configured': len(countries)
    }
    
    # Save updated products
    with open('products.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Global prices updated for {len(products)} products")
    print(f"✅ Configured {len(countries)} countries ({len(enabled_countries)} enabled)")
    
    # Show sample
    if products:
        sample = products[0]
        print(f"\n📊 Sample: {sample.get('productname', 'Unknown')[:40]}...")
        print(f"   Base (INR): ₹{sample.get('minprice', 0)}")
        print(f"   Base (USD): ${sample.get('usd_price', 0)}")
        for code in list(enabled_countries.keys())[:5]:
            rp = sample.get('regional_prices', {}).get(code, {})
            print(f"   {code}: {rp.get('formatted', 'N/A')}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Update global product prices')
    parser.add_argument('--live', action='store_true', help='Use live exchange rates')
    args = parser.parse_args()
    
    update_global_prices(use_live_rates=args.live)
