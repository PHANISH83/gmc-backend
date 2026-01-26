import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import pandas as pd
import database
from gmc_manager import GMCManager
import json
import os
import threading
import time
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, static_folder='website')
# Allow CORS for all origins (update with specific Vercel URL in production)
CORS(app, resources={r"/*": {"origins": "*"}})

# CONFIGURATION
MERCHANT_ID = os.getenv('GMC_MERCHANT_ID')

print("=" * 60)
print("GMC INFINITE-BATCH SERVER - One-Way Push Mode")
print("=" * 60)

# INITIALIZATION
# Initialize Database
database.init_db()

# Initialize GMC Manager
gmc_bot = None
try:
    if os.getenv('GOOGLE_CREDENTIALS'):
        # Create temp file from env var
        with open('service_account.json', 'w') as f:
            f.write(os.getenv('GOOGLE_CREDENTIALS'))
    
    # Strictly require service account
    gmc_bot = GMCManager(MERCHANT_ID, 'service_account.json')
    print("✅ GMC Manager initialized successfully")
except Exception as e:
    print(f"❌ GMC Init failed: {e}")
    # We still allow server to start but key features will fail


# GLOBAL STATE (To track the background job)
job_status = {
    "state": "IDLE",        # IDLE, PROCESSING, COMPLETED, ERROR
    "total_rows": 0,
    "processed_count": 0,
    "success_count": 0,
    "fail_count": 0,
    "skip_count": 0,
    "last_error": None,
    "current_sku": None,
    "errors": []
}

def load_product_db():
    """
    Performance Optimization: Loads the entire JSON into a fast lookup dictionary.
    Format: { 'PRD-00001': {data}, 'PRD-00002': {data}... }
    """
    lookup_db = {}
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle list inside "products" key or direct list
            products = data.get('products', data) 
            
            for p in products:
                sku = str(p.get('code'))
                
                # Logic to find weight
                weight_val = 1000
                if 'variants' in p and len(p['variants']) > 0:
                    weight_val = p['variants'][0].get('weight', 1000)
                    if p['variants'][0].get('weightunit') == 'kg':
                        weight_val = weight_val * 1000

                lookup_db[sku] = {
                    'objectID': sku,
                    'code': sku,
                    'title': p['productname'],
                    'productname': p['productname'],
                    'description': p.get('indepthdescn', p.get('briedfdescn', '')),
                    'indepthdescn': p.get('indepthdescn', ''),
                    'briedfdescn': p.get('briedfdescn', ''),
                    'image': p.get('featured_img', ''),
                    'featured_img': p.get('featured_img', ''),
                    'brand': p.get('brand', 'Generic'),
                    'category': p.get('category', ''),
                    'weight': weight_val,
                    'slug': p.get('produrltitle', sku)
                }
        print(f"📚 Database Loaded: {len(lookup_db)} products in memory.")
        return lookup_db
    except Exception as e:
        print(f"❌ DB Load Error: {e}")
        return {}

def background_worker(df):
    """
    The Worker Thread. Runs silently in the background.
    """
    global job_status
    job_status["state"] = "PROCESSING"
    job_status["processed_count"] = 0
    job_status["success_count"] = 0
    job_status["fail_count"] = 0
    job_status["skip_count"] = 0
    job_status["errors"] = []

    # 1. Load DB ONCE (Fast)
    product_db = load_product_db()
    
    if not product_db:
        job_status["state"] = "ERROR"
        job_status["last_error"] = "Could not load products.json"
        return

    # 2. Process Rows
    total = len(df)
    print(f"🔨 Worker started for {total} products...")

    for index, row in df.iterrows():
        sku = str(row['SKU']).strip()
        job_status["current_sku"] = sku
        
        # Check Flag (supports TRUE/YES)
        active_val = str(row.get('GMC_Active', 'FALSE')).upper()
        is_active = active_val in ['TRUE', 'YES', '1']
        
        if not is_active:
            # Just disable in local DB and skip
            database.set_flag(sku, enabled=False)
            job_status["skip_count"] += 1
            job_status["processed_count"] += 1
            continue

        # Get Details
        product_details = product_db.get(sku)
        
        if not product_details:
            # SKU in CSV but not in Backend JSON
            job_status["fail_count"] += 1
            job_status["errors"].append(f"{sku}: Not found in products.json")
            job_status["processed_count"] += 1
            continue
            
        try:
            # Get CSV Prices
            usd = str(row.get('USD', '0.00'))
            aud = str(row.get('AUD', '0.00'))
            
            # Add price to product_details for GMC formatting
            product_details['price'] = float(usd) if float(usd) > 0 else float(aud)

            # Push US
            if float(usd) > 0:
                us_body = gmc_bot.format_product(product_details, 'US', 'USD')
                us_body['price']['value'] = usd
                gmc_bot.service.products().insert(merchantId=MERCHANT_ID, body=us_body).execute()

            # Push AU
            if float(aud) > 0:
                au_body = gmc_bot.format_product(product_details, 'AU', 'AUD')
                au_body['price']['value'] = aud
                gmc_bot.service.products().insert(merchantId=MERCHANT_ID, body=au_body).execute()

            # Success
            database.set_flag(sku, enabled=True, usd=float(usd), aud=float(aud))
            job_status["success_count"] += 1

        except Exception as e:
            print(f"❌ Error {sku}: {e}")
            job_status["fail_count"] += 1
            job_status["last_error"] = str(e)
            job_status["errors"].append(f"{sku}: {str(e)[:50]}")

        # Update Progress
        job_status["processed_count"] += 1
        
        # Optional: Sleep 0.1s to be nice to Google API rate limits
        # time.sleep(0.1) 

    job_status["state"] = "COMPLETED"
    print("✅ Batch Job Finished.")

# --- ENDPOINTS ---

@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    """
    Accepts ANY size CSV. Returns immediately.
    """
    global job_status
    
    if job_status["state"] == "PROCESSING":
        return jsonify({'error': 'A job is already running. Please wait.'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    try:
        df = pd.read_csv(file)
        
        # Validation
        required = ['SKU', 'USD', 'AUD', 'GMC_Active']
        if not all(col in df.columns for col in required):
            return jsonify({'error': f'CSV needs columns: {required}'}), 400

        # Initialize Job
        job_status["total_rows"] = len(df)
        job_status["state"] = "STARTING"
        job_status["errors"] = []
        
        # Start Background Thread
        thread = threading.Thread(target=background_worker, args=(df,))
        thread.daemon = True # Ensures thread dies if server stops
        thread.start()

        return jsonify({
            'status': 'accepted', 
            'message': f'Received {len(df)} rows. Processing started in background.',
            'check_status_url': '/status'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """
    Call this to update a progress bar on the Founder's screen.
    """
    return jsonify(job_status)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'gmc_ready': gmc_bot is not None,
        'job_state': job_status["state"]
    })

# --- STATIC FILE SERVING (Keep website working) ---
@app.route('/')
def serve_home():
    return send_from_directory('website', 'index.html')

@app.route('/upload')
def serve_upload():
    return send_file('upload.html')

@app.route('/upload.html')
def serve_upload_file():
    return send_file('upload.html')

@app.route('/website/<path:filename>')
def serve_website(filename):
    return send_from_directory('website', filename)

@app.route('/<path:filename>')
def serve_root_files(filename):
    # Serve files from website folder for simple paths
    if os.path.exists(os.path.join('website', filename)):
        return send_from_directory('website', filename)
    return "Not found", 404

# --- API ENDPOINTS (for website) ---
@app.route('/api/products', methods=['GET'])
@app.route('/api/products', methods=['GET'])
def api_products():
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return jsonify({'products': data.get('products', [])})
    except Exception as e:
        print(f"Error reading products: {e}")
        return jsonify({'products': []})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"\n🚀 GMC Infinite-Batch Server Running on port {port}...")
    print(f"[INFO] Website: http://localhost:{port}/")
    print(f"[INFO] Admin Upload: http://localhost:{port}/upload")
    print(f"[INFO] Job Status: http://localhost:{port}/status")
    app.run(host='0.0.0.0', port=port, debug=False)
