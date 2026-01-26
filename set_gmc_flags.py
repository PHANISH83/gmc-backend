"""
Set GMC Active Flags
Sets 'gmc_active' = True for the first 25 products, and False for the rest.
"""
import json

def main():
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            products = data.get('products', [])
            
        print(f"Total products: {len(products)}")
        
        limit = 25
        count_active = 0
        
        for i, p in enumerate(products):
            if i < limit:
                p['gmc_active'] = "yes"
                count_active += 1
            else:
                p['gmc_active'] = "no"
                
        # Save back
        with open('products.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        print(f"Updated products.json")
        print(f"Active: {count_active}")
        print(f"Inactive: {len(products) - count_active}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
