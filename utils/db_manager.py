import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'karaoke_database.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Criar tabela de Prestadores se não existir
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
    
    # Garantir compatibilidade: adicionar coluna amount_paid se faltar em bases de dados antigas
    try:
        cursor.execute("ALTER TABLE providers ADD COLUMN amount_paid REAL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass # A coluna já existe
    
    # Tabela de Clientes por Prestador (Fila / Registo de Clientes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_token TEXT,
            client_name TEXT,
            song_request TEXT,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def add_provider(name, phone, payment_ref, hours, token, amount_paid=0.0):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    expires_at = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cursor.execute('''
            INSERT INTO providers (name, phone, payment_ref, expires_at, token, approved, amount_paid)
            VALUES (?, ?, ?, ?, ?, 0, ?)
        ''', (name, phone, payment_ref, expires_at, token, amount_paid))
    except sqlite3.OperationalError:
        # Fallback caso a tabela antiga ainda esteja ativa na sessão
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
        if 'amount_paid' not in df.columns:
            df['amount_paid'] = 0.0
    except Exception:
        df = pd.DataFrame(columns=['id', 'name', 'phone', 'payment_ref', 'expires_at', 'token', 'approved', 'amount_paid'])
    conn.close()
    return df

def approve_provider(token):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE providers SET approved = 1 WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def get_total_revenue():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SUM(amount_paid) FROM providers WHERE approved = 1")
        total = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        total = 0.0
    conn.close()
    return total if total else 0.0
