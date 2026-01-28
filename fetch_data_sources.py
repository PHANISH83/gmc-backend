"""
Fetch Data Sources - Automatically gets all Data Source IDs from Merchant Center
No manual clicking needed!
"""
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.shopping.merchant_datasources_v1beta import DataSourcesServiceClient

load_dotenv()

def get_all_data_sources():
    """Fetch all data sources from Merchant Center via API."""
    
    merchant_id = os.getenv('GMC_MERCHANT_ID')
    account = f"accounts/{merchant_id}"
    
    # Authenticate
    credentials = service_account.Credentials.from_service_account_file(
        'service_account.json',
        scopes=['https://www.googleapis.com/auth/content']
    )
    
    # Create client
    client = DataSourcesServiceClient(credentials=credentials)
    
    print(f"Fetching data sources for Merchant ID: {merchant_id}")
    print("=" * 60)
    
    # List all data sources
    data_sources = {}
    
    try:
        request = {"parent": account}
        
        for ds in client.list_data_sources(request=request):
            # Parse the data source name to get ID
            # Format: accounts/{account_id}/dataSources/{datasource_id}
            ds_id = ds.name.split('/')[-1]
            
            # Get feed label (country) from primary product data source
            feed_label = None
            if hasattr(ds, 'primary_product_data_source') and ds.primary_product_data_source:
                feed_label = ds.primary_product_data_source.feed_label
            
            data_sources[feed_label or ds_id] = {
                'id': ds_id,
                'name': ds.name,
                'display_name': ds.display_name if hasattr(ds, 'display_name') else 'N/A',
                'feed_label': feed_label
            }
            
            print(f"  [{feed_label or 'N/A'}] ID: {ds_id}")
            print(f"       Name: {ds.display_name if hasattr(ds, 'display_name') else ds.name}")
            print()
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return None
    
    print("=" * 60)
    print(f"Total data sources found: {len(data_sources)}")
    
    # Save to config file
    import json
    with open('data_sources.json', 'w') as f:
        json.dump(data_sources, f, indent=2)
    print(f"\n✅ Saved to data_sources.json")
    
    return data_sources

if __name__ == '__main__':
    get_all_data_sources()
