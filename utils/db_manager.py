import sqlite3
from datetime import datetime, timedelta
import uuid
import pandas as pd

DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            duration_hours INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

def create_provider_link(name, duration_hours):
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    
    token = str(uuid.uuid4())[:8].upper()
    created_at = datetime.now()
    expires_at = created_at + timedelta(hours=duration_hours)
    
    cursor.execute("""
        INSERT INTO providers (name, token, duration_hours, created_at, expires_at, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (name, token, duration_hours, created_at.strftime("%Y-%m-%d %H:%M:%S"), expires_at.strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()
    return token

def get_all_providers():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    df = pd.read_sql("SELECT * FROM providers", conn)
    conn.close()
    return df

def check_provider_token(token):
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM providers WHERE token = ? AND is_active = 1", (token,))
    provider = cursor.fetchone()
    conn.close()
    
    if provider:
        expires_at = datetime.strptime(provider[5], "%Y-%m-%d %H:%M:%S")
        if datetime.now() <= expires_at:
            return provider
    return None
