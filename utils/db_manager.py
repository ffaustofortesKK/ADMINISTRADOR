import sqlite3
import pandas as pd
import secrets
import os
from datetime import datetime, timedelta

# Obter o caminho absoluto para a pasta atual, garantindo que aponta sempre ao mesmo sítio
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(os.path.dirname(BASE_DIR), "database.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            duration_hours INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            approved INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def create_provider_request(name, duration_hours):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    token = secrets.token_hex(16)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO providers (name, token, duration_hours, created_at, approved)
        VALUES (?, ?, ?, ?, 0)
    ''', (name, token, duration_hours, created_at))
    
    conn.commit()
    conn.close()
    return token

def approve_provider(provider_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT duration_hours FROM providers WHERE id = ?', (provider_id,))
    res = cursor.fetchone()
    if res:
        duration_hours = res[0]
        now = datetime.now()
        expires_at = (now + timedelta(hours=duration_hours)).strftime("%Y-%m-%d %H:%M:%S")
        created_at = now.strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            UPDATE providers 
            SET approved = 1, created_at = ?, expires_at = ? 
            WHERE id = ?
        ''', (created_at, expires_at, provider_id))
        conn.commit()
    conn.close()

def get_all_providers():
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT * FROM providers", conn)
    except Exception:
        df = pd.DataFrame(columns=['id', 'name', 'token', 'duration_hours', 'created_at', 'expires_at', 'approved'])
    conn.close()
    return df
