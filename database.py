import sqlite3

DB_NAME = "gmc_state.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Create table with tracking columns
    c.execute('''CREATE TABLE IF NOT EXISTS product_flags
                 (sku TEXT PRIMARY KEY, 
                  enabled BOOLEAN, 
                  last_inr_price REAL DEFAULT 0, 
                  last_usd_price REAL DEFAULT 0,
                  last_aud_price REAL DEFAULT 0)''')
    conn.commit()
    conn.close()

def set_flag(sku, enabled=True, inr=0, usd=0, aud=0):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO product_flags (sku, enabled, last_inr_price, last_usd_price, last_aud_price)
                 VALUES (?, ?, ?, ?, ?)
                 ON CONFLICT(sku) DO UPDATE SET 
                 enabled=excluded.enabled,
                 last_inr_price=excluded.last_inr_price,
                 last_usd_price=excluded.last_usd_price,
                 last_aud_price=excluded.last_aud_price''', 
                 (sku, enabled, inr, usd, aud))
    conn.commit()
    conn.close()

def get_enabled_products():
    """Returns list of SKUs that should be synced"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT sku, last_inr_price FROM product_flags WHERE enabled=1")
    rows = c.fetchall()
    conn.close()
    return rows

# Initialize on import
init_db()
