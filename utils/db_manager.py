import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import os

# Garantir o caminho absoluto para a base de dados na raiz do projeto
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'karaoke_database.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            payment_ref TEXT,
            expires_at TEXT,
            token TEXT UNIQUE,
            approved INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_provider(name, phone, payment_ref, hours, token):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    expires_at = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO providers (name, phone, payment_ref, expires_at, token, approved)
        VALUES (?, ?, ?, ?, ?, 0)
    ''', (name, phone, payment_ref, expires_at, token))
    
    conn.commit()
    conn.close()

def get_all_providers():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM providers", conn)
    except Exception:
        df = pd.DataFrame(columns=['id', 'name', 'phone', 'payment_ref', 'expires_at', 'token', 'approved'])
    conn.close()
    return df

def approve_provider(token):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE providers SET approved = 1 WHERE token = ?", (token,))
    conn.commit()
    conn.close()
