import json
import random

def add_new_products():
    with open('products.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        products = data.get('products', [])

    new_products = []
    
    # Template product (using first one as base)
    template = products[0].copy()
    
    for i in range(51, 56):
        sku = f"PRD-000{i}"
        
        # Create new product based on template
        p = template.copy()
        p['id'] = i
        p['code'] = sku
        p['productname'] = f"New Product {i} - Sample Item"
        p['produrltitle'] = f"new-product-{i}"
        p['briedfdescn'] = f"Premium quality new product #{i}"
        p['indepthdescn'] = f"Full detailed description for product {i}. High quality."
        p['minprice'] = 100.0 + i
        p['featured_img'] = f"https://via.placeholder.com/400?text=Product+{i}"
        
        # Update variants too
        new_variants = []
        if 'variants' in p:
            for v in p['variants']:
                nv = v.copy()
                nv['id'] = v['id'] + (i * 100) # Simple ID shift
                nv['product_id'] = i
                nv['subproductname'] = f"New Product {i} - Variant"
                new_variants.append(nv)
            p['variants'] = new_variants

        new_products.append(p)

    # Append to main list
    data['products'].extend(new_products)
    data['metadata']['total_products'] = len(data['products'])

    # Save back
    with open('products.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    # Also save to website folder
    with open('website/products.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Added 5 new products: PRD-00051 to PRD-00055")

if __name__ == "__main__":
    add_new_products()
