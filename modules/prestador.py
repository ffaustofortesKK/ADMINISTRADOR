import streamlit as st
import requests
import time
import urllib.parse
from datetime import datetime
import uuid

# URL Base do Firebase
FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

# --- FUNÇÕES DE LÓGICA (BACKEND DO MÓDULO) ---

def limpar_nome_musica(musica_data):
    if isinstance(musica_data, dict):
        return musica_data.get("titulo", "Música Desconhecida")
    return str(musica_data)

def atualizar_estado_pedido(provider_token, pedido_id, novo_estado):
    url = f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}/estado.json"
    requests.put(url, json=novo_estado)

def terminar_todas_musicas_ativas(provider_token, pedidos):
    for p in pedidos:
        if p.get("estado") == "aprovado":
            atualizar_estado_pedido(provider_token, p.get("id"), "terminado")

def definir_video_fundo(provider_token, url_video):
    url = f"{FIREBASE_URL}/configuracoes/{provider_token}/video_fundo.json"
    requests.put(url, json=url_video)

def obter_video_fundo(provider_token):
    url = f"{FIREBASE_URL}/configuracoes/{provider_token}/video_fundo.json"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else ""

def listar_videos_pasta_clipes():
    # Retorna lista vazia ou a sua lógica atual se existir
    return []

# --- FUNÇÃO PRINCIPAL DE RENDERIZAÇÃO ---

def show_provider_panel_custom(provider_token, get_all_providers):
    """
    Painel principal chamado pelo app.py.
    """
    # URLS de estilo
    url_logotipo = "https://cdn.phototourl.com/free/2026-08-03-8b13edf5-0257-491d-ab78-f0d5329ffc15.jpg"
    url_fundo_painel = "https://cdn.phototourl.com/free/2026-08-03-694a4a2e-9914-4da8-93b2-87538a4805ab.png"

    # Buscar dados do prestador
    df_prov = get_all_providers()
    nome_prestador = "Prestador"
    tempo_plano = "2 Horas - 12 Mil Kwanzas"
    data_registo_str = None
    
    if not df_prov.empty and 'token' in df_prov.columns:
        match = df_prov[df_prov['token'] == provider_token]
        if not match.empty:
            row = match.iloc[0]
            nome_prestador = row.get('nome_prestador', row.get('nome', 'Prestador'))
            tempo_plano = row.get('tempo_plano', row.get('tempo', '2 Horas - 12 Mil Kwanzas'))
            data_registo_str = row.get('data_registo', None)

    # Cálculo de tempo (Simplificado)
    segundos_totais = 7200
    if "3 Horas" in tempo_plano: segundos_totais = 10800
    elif "4 Horas" in tempo_plano: segundos_totais = 14400
    
    tempo_formatado = "02:00:00" # Exemplo estático ou calculável via datetime
    
    # --- RENDERIZAÇÃO DO PAINEL ---
    st.markdown(f"""
    <style>
    .stApp {{ background: url("{url_fundo_painel}") no-repeat center center fixed !important; background-size: cover !important; }}
    .block-container {{ padding: 3rem 5rem !important; background: rgba(0, 0, 0, 0.90) !important; border-radius: 12px; border: 4px solid #FFC107 !important; }}
    h1 {{ color: #ffffff !important; font-family: monospace; }}
    </style>
    """, unsafe_allow_html=True)

    st.title(f"PAINEL DO PRESTADOR: {nome_prestador}")
    st.write(f"Token: {provider_token}")
    
    # --- RENDERIZAR FILA DENTRO DESTE FICHEIRO ---
    # Aqui chamamos a lógica de fila que estava no seu código original
    renderizar_gestao_fila_prestador(provider_token)

def renderizar_gestao_fila_prestador(provider_token):
    """
    Gestão da Fila (chamada internamente).
    """
    try:
        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        response = requests.get(url_firebase)
        
        pedidos = []
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            
        pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
        
        st.subheader("📋 Estado da Fila")
        if not pedidos_ativos:
            st.info("Nenhum pedido na lista.")
        else:
            for p in pedidos_ativos:
                st.write(f"Música: {limpar_nome_musica(p.get('musica'))} | Estado: {p.get('estado')}")
                
    except Exception as e:
        st.error(f"Erro: {e}")
