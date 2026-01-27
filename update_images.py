"""
Update Product Images
Replaces placeholder image URLs with real food images from Unsplash
"""
import json

# Real food product images from Unsplash (JPG format for GMC compatibility)
FOOD_IMAGES = [
    "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=800&h=800&fit=crop&fm=jpg",  # Basmati Rice
    "https://images.unsplash.com/photo-1518110925495-5fe2fda0442c?w=800&h=800&fit=crop&fm=jpg",  # Pink Salt
    "https://images.unsplash.com/photo-1526947425960-945c6e72858f?w=800&h=800&fit=crop&fm=jpg",  # Coconut Oil
    "https://images.unsplash.com/photo-1615485500704-8e990f9900f7?w=800&h=800&fit=crop&fm=jpg",  # Turmeric
    "https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=800&h=800&fit=crop&fm=jpg",  # Honey
    "https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?w=800&h=800&fit=crop&fm=jpg",  # Spices
    "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=800&h=800&fit=crop&fm=jpg",  # Oils
    "https://images.unsplash.com/photo-1509358271058-aedd22b2da55?w=800&h=800&fit=crop&fm=jpg",  # Food items
    "https://images.unsplash.com/photo-1606923829579-0cb981a83e2e?w=800&h=800&fit=crop&fm=jpg",  # Indian spices
    "https://images.unsplash.com/photo-1599940824399-b87987ceb72a?w=800&h=800&fit=crop&fm=jpg",  # Grocery
]

def main():
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            products = data.get('products', [])
            
        print(f"Total products: {len(products)}")
        updated = 0
        
        for i, p in enumerate(products):
            # Get image based on product index (cycles through available images)
            img_url = FOOD_IMAGES[i % len(FOOD_IMAGES)]
            
            # Update product image
            p['featured_img'] = img_url
            
            # Update variant images too
            if 'variants' in p:
                for j, v in enumerate(p['variants']):
                    v['featured_img'] = img_url
            
            updated += 1
                
        # Save back
        with open('products.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        print(f"✅ Updated {updated} products with real images")
        print("Images are from Unsplash (free to use)")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
