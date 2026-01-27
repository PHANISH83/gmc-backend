"""
Add UK Price Field
Adds a uk_price field to all products = minprice * 1.2
"""
import json

def main():
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            products = data.get('products', [])
            
        print(f"Total products: {len(products)}")
        updated = 0
        
        for p in products:
            base_price = float(p.get('minprice', 0))
            uk_price = round(base_price * 1.2, 2)
            p['uk_price'] = uk_price
            updated += 1
                
        # Save back
        with open('products.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        print(f"✅ Added uk_price field to {updated} products")
        print(f"Formula: uk_price = minprice * 1.2")
        
        # Show sample
        print("\nSample (first 5 active products):")
        active = [p for p in products if str(p.get('gmc_active', '')).lower() == 'yes']
        for p in active[:5]:
            print(f"  {p['code']}: ${p['minprice']} -> £{p['uk_price']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
