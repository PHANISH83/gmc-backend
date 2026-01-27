"""
Assign Multiple Product Images
Each product gets 4 unique images based on its category/type
"""
import json

# Category-based images from Unsplash (4 images per category)
CATEGORY_IMAGES = {
    'rice': [
        "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1594756202469-9ff9799b2e4e?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1550828520-4cb496926fc9?w=800&h=800&fit=crop&fm=jpg",
    ],
    'salt': [
        "https://images.unsplash.com/photo-1518110925495-5fe2fda0442c?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1544025162-d76978e8e5a4?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1628627256541-a9eb3b1d1c4e?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1599940824399-b87987ceb72a?w=800&h=800&fit=crop&fm=jpg",
    ],
    'oil': [
        "https://images.unsplash.com/photo-1526947425960-945c6e72858f?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1509358271058-aedd22b2da55?w=800&h=800&fit=crop&fm=jpg",
    ],
    'turmeric': [
        "https://images.unsplash.com/photo-1615485500704-8e990f9900f7?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1606923829579-0cb981a83e2e?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1505253716362-afaea1d3d1af?w=800&h=800&fit=crop&fm=jpg",
    ],
    'honey': [
        "https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1471943311424-646960669fbc?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=800&h=800&fit=crop&fm=jpg",
    ],
    'default': [
        "https://images.unsplash.com/photo-1606923829579-0cb981a83e2e?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1509358271058-aedd22b2da55?w=800&h=800&fit=crop&fm=jpg",
        "https://images.unsplash.com/photo-1599940824399-b87987ceb72a?w=800&h=800&fit=crop&fm=jpg",
    ]
}

def get_category(product_name):
    """Determine category from product name"""
    name = product_name.lower()
    if 'rice' in name or 'basmati' in name:
        return 'rice'
    elif 'salt' in name:
        return 'salt'
    elif 'oil' in name or 'coconut' in name:
        return 'oil'
    elif 'turmeric' in name or 'spice' in name or 'powder' in name:
        return 'turmeric'
    elif 'honey' in name:
        return 'honey'
    return 'default'

def get_batch_number(product_name):
    """Extract batch number from product name"""
    name = product_name.lower()
    if 'batch 1' in name:
        return 0
    elif 'batch 2' in name:
        return 1
    elif 'batch 3' in name:
        return 2
    elif 'batch 4' in name:
        return 3
    elif 'batch 5' in name:
        return 0
    elif 'batch 6' in name:
        return 1
    elif 'batch 7' in name:
        return 2
    elif 'batch 8' in name:
        return 3
    return 0

def main():
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            products = data.get('products', [])
            
        print(f"Total products: {len(products)}")
        updated = 0
        
        for p in products:
            name = p.get('productname', '')
            category = get_category(name)
            batch = get_batch_number(name)
            
            images = CATEGORY_IMAGES.get(category, CATEGORY_IMAGES['default'])
            # Get image based on batch number (cycles through 4 images)
            img_url = images[batch % len(images)]
            
            # Set main image
            p['featured_img'] = img_url
            
            # Set additional images array (4 images)
            p['additional_images'] = images
            
            # Update variant images too
            if 'variants' in p:
                for j, v in enumerate(p['variants']):
                    v['featured_img'] = images[j % len(images)]
            
            updated += 1
            print(f"  {p['code']}: {category} -> Batch {batch+1} image")
                
        # Save back
        with open('products.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        print(f"\n✅ Updated {updated} products with category-based images")
        print("Each product now has 4 additional images in 'additional_images' field")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
