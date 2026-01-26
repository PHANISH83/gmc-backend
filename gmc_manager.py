import os
import json
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GMCManager:
    def __init__(self, merchant_id, key_file_path):
        self.merchant_id = merchant_id
        if not os.path.exists(key_file_path):
            raise FileNotFoundError(f"Missing Key File: {key_file_path}")
            
        self.creds = service_account.Credentials.from_service_account_file(
            key_file_path, scopes=['https://www.googleapis.com/auth/content']
        )
        self.service = build('content', 'v2.1', credentials=self.creds)
        print(f"[GMC] Engine ready (Merchant ID: {merchant_id})")

    def extract_weight_from_label(self, variant_label):
        """Extract weight/volume from variant label like '250 ml', '100 g', '5ltr'"""
        if not variant_label:
            return '500', 'g'
        
        match = re.search(r'(\d+(?:\.\d+)?)\s*(ml|g|kg|ltr|l|gm)\b', variant_label, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            unit = match.group(2).lower()
            
            if unit in ['kg']:
                value *= 1000
                unit = 'g'
            elif unit in ['ltr', 'l']:
                value *= 1000
                unit = 'ml'
            elif unit == 'gm':
                unit = 'g'
                
            return str(int(value)), unit
        return '500', 'g'

    def _get_price_from_algolia(self, data, country, currency):
        """Get price from data - supports both Algolia format and direct price."""
        # First try Algolia's prices object
        country_map = {
            'US': 'USA', 'AU': 'Australia', 'GB': 'UK', 'DE': 'Germany',
            'CA': 'Canada', 'AE': 'UAE', 'FR': 'France', 'IT': 'Italy'
        }
        country_name = country_map.get(country, country)
        prices = data.get('prices', {})
        price = prices.get(country_name, {}).get('price', 0)
        
        # Fallback to direct price field if no Algolia prices
        if price == 0:
            price = data.get('price', 0)
        
        return price

    def format_product(self, data, country, currency):
        """Format Algolia data for Google Merchant Center."""
        offer_id = f"{data['objectID']}-{country}"
        
        # Get title (use 'name' field from Algolia, fallback to 'title')
        title = data.get('name', data.get('title', 'Unknown Product'))
        
        # Get price from Algolia's pre-calculated prices
        price = self._get_price_from_algolia(data, country, currency)
        
        # Link with currency parameter
        slug = data.get('slug', data['objectID'])
        link = f"https://thedesifood.com/product/{slug}?currency={currency}"

        # Build image URL
        image = data.get('image', '')
        if image and not image.startswith('http'):
            image = f"https://thedesifood.com{image}"

        # Extract weight
        variant_label = data.get('variant_label', '')
        weight_value, weight_unit = self.extract_weight_from_label(variant_label)

        body = {
            'offerId': offer_id,
            'title': title,
            'description': data.get('description', title),
            'link': link,
            'imageLink': image,
            'contentLanguage': 'en',
            'targetCountry': country,
            'channel': 'online',
            'availability': 'in stock',
            'condition': 'new',
            'brand': data.get('brand', 'Unknown'),
            'price': {
                'value': f"{price:.2f}",
                'currency': currency
            },
            'shippingWeight': {'value': weight_value, 'unit': weight_unit},
            'itemGroupId': slug.split('-')[0] if slug else data['objectID'],
            'identifierExists': 'no'  # No GTIN per founder's instruction
        }

        return body

    def push_to_google(self, body):
        """Push a single product to Google."""
        try:
            result = self.service.products().insert(
                merchantId=self.merchant_id, 
                body=body
            ).execute()
            return True, result.get('id', 'OK')
        except HttpError as e:
            try:
                error_msg = json.loads(e.content)['error']['message']
            except:
                error_msg = str(e)
            return False, error_msg

    def delete_product(self, offer_id, country):
        """Delete a product from Google Merchant Center."""
        # specific_id format: online:en:US:PRD-00001-US
        product_id = f"online:en:{country}:{offer_id}"
        
        try:
            self.service.products().delete(
                merchantId=self.merchant_id, 
                productId=product_id
            ).execute()
            return True, "Deleted"
        except HttpError as e:
            try:
                error_msg = json.loads(e.content)['error']['message']
            except:
                error_msg = str(e)
            
            if "item not found" in error_msg.lower():
                return True, "Already deleted"
                
            return False, error_msg

    def list_all_products(self):
        """List all products in the Merchant Center account."""
        products = []
        request = self.service.products().list(merchantId=self.merchant_id)
        
        while request is not None:
            result = request.execute()
            if 'resources' in result:
                products.extend(result['resources'])
            request = self.service.products().list_next(previous_request=request, previous_response=result)
            
        return products

    def batch_push(self, product_bodies, batch_size=5000):
        """
        Push multiple products in a single API call using custombatch.
        Up to 10,000 products per batch. Returns (success_count, fail_count, errors)
        """
        total_success = 0
        total_fail = 0
        all_errors = []
        
        # Process in chunks
        for i in range(0, len(product_bodies), batch_size):
            chunk = product_bodies[i:i + batch_size]
            
            # Build batch request
            entries = []
            for idx, body in enumerate(chunk):
                entries.append({
                    'batchId': i + idx,
                    'merchantId': self.merchant_id,
                    'method': 'insert',
                    'product': body
                })
            
            batch_request = {'entries': entries}
            
            try:
                result = self.service.products().custombatch(body=batch_request).execute()
                
                # Process results
                for entry in result.get('entries', []):
                    if entry.get('errors'):
                        total_fail += 1
                        all_errors.append({
                            'batchId': entry.get('batchId'),
                            'errors': entry.get('errors')
                        })
                    else:
                        total_success += 1
                        
            except HttpError as e:
                # If entire batch fails
                total_fail += len(chunk)
                try:
                    error_msg = json.loads(e.content)['error']['message']
                except:
                    error_msg = str(e)
                all_errors.append({'batch_error': error_msg})
        
        return total_success, total_fail, all_errors

