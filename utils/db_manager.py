import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'karaoke_database.db')

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            payment_ref TEXT,
            expires_at TEXT,
            token TEXT UNIQUE,
            approved INTEGER DEFAULT 0,
            amount_paid REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

def add_provider(name, phone, payment_ref, hours, token, amount_paid=0.0):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    expires_at = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO providers (name, phone, payment_ref, expires_at, token, approved, amount_paid)
        VALUES (?, ?, ?, ?, ?, 0, ?)
    ''', (name, phone, payment_ref, expires_at, token, amount_paid))
    
    conn.commit()
    conn.close()

def get_all_providers():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        df = pd.read_sql_query("SELECT * FROM providers ORDER BY id DESC", conn)
    except Exception:
        df = pd.DataFrame(columns=['id', 'name', 'phone', 'payment_ref', 'expires_at', 'token', 'approved', 'amount_paid'])
    conn.close()
    return df

def get_active_providers():
    df = get_all_providers()
    if df.empty:
        return df
    
    now = datetime.now()
    df['expires_dt'] = pd.to_datetime(df['expires_at'], errors='coerce')
    
    ativos = df[(df['approved'].astype(int) == 1) & (df['expires_dt'] > now)].copy()
    return ativos

def approve_provider(token):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE providers SET approved = 1 WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def get_total_revenue():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SUM(amount_paid) FROM providers WHERE approved = 1")
        total = cursor.fetchone()[0]
    except Exception:
        total = 0.0
    conn.close()
    return total if total else 0.0
