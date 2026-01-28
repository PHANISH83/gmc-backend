"""
Merchant API Manager - New Google Merchant API (v1)
Replaces Content API for Shopping (deprecated August 2026)

Benefits:
- 4x page size (1000 vs 250)
- Built-in async batching
- gRPC support
- Faster processing
"""
import os
import json
from google.oauth2 import service_account
from google.shopping.merchant_products_v1beta import ProductInputsServiceClient
from google.shopping.merchant_products_v1beta import ProductsServiceClient
from google.shopping.merchant_products_v1beta.types import (
    ProductInput,
    InsertProductInputRequest,
    Attributes,
    Price,
    Shipping,
    ShippingWeight,
)

class MerchantAPIManager:
    """
    Manager for the new Google Merchant API (v1beta -> v1)
    Migration from Content API for Shopping
    """
    
    def __init__(self, merchant_id, credentials_file='service_account.json', data_source_id=None):
        """Initialize the Merchant API client."""
        self.merchant_id = merchant_id
        self.account = f"accounts/{merchant_id}"
        
        # Data source is required for Merchant API
        # You need to create one in Merchant Center or via API
        self.data_source_id = data_source_id
        if data_source_id:
            self.data_source = f"accounts/{merchant_id}/dataSources/{data_source_id}"
        else:
            self.data_source = None
        
        # Load credentials
        credentials = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/content']
        )
        
        # Initialize clients
        self.product_inputs_client = ProductInputsServiceClient(credentials=credentials)
        self.products_client = ProductsServiceClient(credentials=credentials)
        
        print(f"[Merchant API] Ready (Account: {merchant_id})")
    
    def format_product(self, data, country, currency):
        """
        Format product data for Merchant API.
        Returns a ProductInput protobuf object.
        """
        offer_id = f"{data['objectID']}-{country}"
        title = data.get('productname', data.get('title', 'Unknown Product'))
        slug = data.get('produrltitle', data.get('slug', data['objectID']))
        price = float(data.get('price', 0))
        
        # Image handling
        image = data.get('featured_img', data.get('image', ''))
        if 'unsplash.com' in image and 'fm=jpg' not in image:
            image = image.replace('?', '?fm=jpg&') if '?' in image else f"{image}?fm=jpg"
        if not image or 'example.com' in image:
            image = "https://images.unsplash.com/photo-1606923829579-0cb981a83e2e?w=800&h=800&fit=crop&fm=jpg"
        
        # Additional images
        additional_images = data.get('additional_images', [])[:10]
        
        # Weight
        weight_value = float(data.get('weight', 500))
        weight_unit = 'g'
        
        # Shipping
        shipping_cost = data.get('shipping_cost', 9.99)
        
        # Build ProductInput
        product_input = ProductInput(
            name=f"{self.account}/productInputs/{offer_id}",
            offer_id=offer_id,
            content_language="en",
            feed_label=country,
            attributes=Attributes(
                title=title,
                description=data.get('description', data.get('briedfdescn', title)),
                link=f"https://gmc-dashboard.vercel.app/products/{slug}",
                image_link=image,
                additional_image_links=additional_images,
                availability="in stock",
                condition="new",
                brand=data.get('brand', 'Generic'),
                price=Price(
                    amount_micros=int(price * 1_000_000),
                    currency_code=currency
                ),
                shipping=[
                    Shipping(
                        country=country,
                        service="Standard Shipping",
                        price=Price(
                            amount_micros=int(shipping_cost * 1_000_000),
                            currency_code=currency
                        )
                    )
                ],
                shipping_weight=ShippingWeight(
                    value=weight_value,
                    unit=weight_unit
                ),
                identifier_exists=False
            )
        )
        
        return product_input
    
    def insert_product(self, product_input):
        """
        Insert a single product using productInputs.insert
        """
        if not self.data_source:
            raise ValueError("Data source ID is required. Set it in constructor or create one in Merchant Center.")
        
        try:
            request = InsertProductInputRequest(
                parent=self.account,
                product_input=product_input,
                data_source=self.data_source
            )
            
            response = self.product_inputs_client.insert_product_input(request=request)
            return True, response.name
            
        except Exception as e:
            return False, str(e)
    
    def batch_insert(self, product_inputs, batch_size=100):
        """
        Insert multiple products.
        Note: Merchant API has built-in async processing.
        """
        success = 0
        fail = 0
        errors = []
        
        for i, product_input in enumerate(product_inputs):
            ok, result = self.insert_product(product_input)
            if ok:
                success += 1
            else:
                fail += 1
                errors.append(f"{product_input.offer_id}: {result}")
            
            # Progress
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{len(product_inputs)}")
        
        return success, fail, errors
    
    def list_products(self, page_size=1000):
        """
        List products (Merchant API supports up to 1000 per page!)
        """
        products = []
        try:
            # Use the products client to list processed products
            request = {
                "parent": self.account,
                "page_size": page_size
            }
            
            for product in self.products_client.list_products(request=request):
                products.append(product)
                
        except Exception as e:
            print(f"[ERROR] Failed to list products: {e}")
        
        return products


# Compatibility layer - can use old or new API
def get_api_manager(merchant_id, credentials_file='service_account.json', use_new_api=False, data_source_id=None):
    """
    Factory function to get the appropriate API manager.
    Set use_new_api=True to use Merchant API (recommended for new projects).
    """
    if use_new_api:
        return MerchantAPIManager(merchant_id, credentials_file, data_source_id)
    else:
        from gmc_manager import GMCManager
        return GMCManager(merchant_id, credentials_file)
