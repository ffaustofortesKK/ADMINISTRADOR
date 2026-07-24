import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import uuid
import os

DB_NAME = "database.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            duration_hours INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def create_provider_link(name, duration_hours):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    token = str(uuid.uuid4())[:8]
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expires_at = (datetime.now() + timedelta(hours=int(duration_hours))).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO providers (name, token, duration_hours, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, token, duration_hours, created_at, expires_at))
    
    conn.commit()
    conn.close()
    return token

def get_all_providers():
    init_db()
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM providers ORDER BY id DESC", conn)
    except Exception as e:
        df = pd.DataFrame(columns=['id', 'name', 'token', 'duration_hours', 'created_at', 'expires_at'])
    conn.close()
    return df
