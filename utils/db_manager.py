import sqlite3
import pandas as pd
import secrets
import os
from datetime import datetime, timedelta

BASE_DIR = os.getcwd()
DB_NAME = os.path.join(BASE_DIR, "database.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela de prestadores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            duration_hours INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            approved INTEGER DEFAULT 0,
            payment_ref TEXT DEFAULT ''
        )
    ''')
    
    # Tabela de catálogo de músicas disponíveis (exemplo pré-carregado ou gerido)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS catalog_songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist TEXT NOT NULL
        )
    ''')
    
    # Tabela de pedidos de karaoke feitos pelos clientes aos prestadores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS client_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_token TEXT NOT NULL,
            client_name TEXT NOT NULL,
            song_choice TEXT NOT NULL,
            request_type TEXT NOT NULL, -- 'catalogo' ou 'customizado'
            status TEXT DEFAULT 'Pendente',
            created_at TEXT NOT NULL
        )
    ''')
    
    # Inserir algumas músicas de exemplo se a tabela estiver vazia
    cursor.execute('SELECT COUNT(*) FROM catalog_songs')
    if cursor.fetchone()[0] == 0:
        sample_songs = [
            ("A Minha Terra", "Artista Local"),
            ("Perfume", "Yuri da Cunha"),
            ("Ai Bem", "Paulo Flores"),
            ("Boas Vibrações", "C4 Pedro"),
            ("The Way You Look At Me", "Christian Bautista"),
            ("Shape of You", "Ed Sheeran")
        ]
        cursor.executemany('INSERT INTO catalog_songs (title, artist) VALUES (?, ?)', sample_songs)

    conn.commit()
    conn.close()

def create_provider_request(name, duration_hours, payment_ref=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    token = secrets.token_hex(16)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO providers (name, token, duration_hours, created_at, approved, payment_ref)
        VALUES (?, ?, ?, ?, 0, ?)
    ''', (name, token, duration_hours, created_at, payment_ref))
    
    conn.commit()
    conn.close()
    return token

def approve_provider(provider_id, payment_ref=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT duration_hours FROM providers WHERE id = ?', (provider_id,))
    res = cursor.fetchone()
    if res:
        duration_hours = res[0]
        now = datetime.now()
        expires_at = (now + timedelta(hours=duration_hours)).strftime("%Y-%m-%d %H:%M:%S")
        created_at = now.strftime("%Y-%m-%d %H:%M:%S")
        
        if payment_ref.strip():
            cursor.execute('''
                UPDATE providers 
                SET approved = 1, created_at = ?, expires_at = ?, payment_ref = ? 
                WHERE id = ?
            ''', (created_at, expires_at, payment_ref, provider_id))
        else:
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
        df = pd.DataFrame(columns=['id', 'name', 'token', 'duration_hours', 'created_at', 'expires_at', 'approved', 'payment_ref'])
    conn.close()
    return df

def get_catalog_songs():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM catalog_songs", conn)
    conn.close()
    return df

def add_client_request(provider_token, client_name, song_choice, request_type):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO client_requests (provider_token, client_name, song_choice, request_type, status, created_at)
        VALUES (?, ?, ?, ?, 'Pendente', ?)
    ''', (provider_token, client_name, song_choice, request_type, created_at))
    conn.commit()
    conn.close()

def get_client_requests(provider_token):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM client_requests WHERE provider_token = ? ORDER BY id DESC", conn, params=(provider_token,))
    conn.close()
    return df
