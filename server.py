import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from flask import Flask, jsonify, send_from_directory, send_file
from flask_cors import CORS
import database
from gmc_manager import GMCManager
import json
import os
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




# --- ENDPOINTS ---

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'gmc_ready': gmc_bot is not None
    })

# --- STATIC FILE SERVING (Keep website working) ---
@app.route('/')
def serve_home():
    return send_from_directory('website', 'index.html')



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
    print(f"\n🚀 GMC Server Running on port {port}...")
    print(f"[INFO] Website: http://localhost:{port}/")
    print(f"[INFO] Products API: http://localhost:{port}/api/products")
    app.run(host='0.0.0.0', port=port, debug=False)
