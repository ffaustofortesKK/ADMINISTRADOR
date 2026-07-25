import sqlite3
import pandas as pd

DB_FILE = "karaoke_admin.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            payment_ref TEXT,
            duration_hours INTEGER,
            token TEXT UNIQUE,
            approved INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_provider(name, phone, payment_ref, duration_hours, token):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO providers (name, phone, payment_ref, duration_hours, token, approved)
        VALUES (?, ?, ?, ?, ?, 0)
    ''', (name, phone, payment_ref, duration_hours, token))
    conn.commit()
    conn.close()

def get_all_providers():
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql("SELECT * FROM providers", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def approve_provider(provider_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT duration_hours FROM providers WHERE id = ?", (provider_id,))
    res = cursor.fetchone()
    hours = res[0] if res else 2
    
    cursor.execute('''
        UPDATE providers 
        SET approved = 1, expires_at = datetime('now', '+' || ? || ' hours')
        WHERE id = ?
    ''', (hours, provider_id))
    
    conn.commit()
    conn.close()
