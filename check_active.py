import json

with open('products.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    products = data.get('products', [])
    active = [p for p in products if str(p.get('gmc_active', '')).lower() == 'yes']
    inactive = [p for p in products if str(p.get('gmc_active', '')).lower() != 'yes']
    print(f'Total products: {len(products)}')
    print(f'GMC Active (yes): {len(active)}')
    print(f'GMC Inactive: {len(inactive)}')
    print()
    print('Active products (first 10):')
    for p in active[:10]:
        name = p.get('productname', 'Unknown')[:40]
        print(f"  - {p['code']}: {name}...")
