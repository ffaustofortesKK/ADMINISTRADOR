import time
import urllib.parse
from datetime import datetime
import requests
import streamlit as st

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

# --- Funções Auxiliares ---
def limpar_nome_musica(musica_field):
    if isinstance(musica_field, dict):
        return musica_field.get("titulo") or musica_field.get("nome") or musica_field.get("title") or "Música sem título"
    return str(musica_field) if musica_field else "Música sem título"

def atualizar_estado_pedido(token, pedido_id, novo_estado):
    try:
        requests.patch(f"{FIREBASE_URL}/pedidos/{token}/{pedido_id}.json", json={"estado": novo_estado}, timeout=5)
    except: pass

def terminar_todas_musicas_ativas(token, pedidos):
    for p in pedidos:
        if p.get("estado") == "aprovado":
            atualizar_estado_pedido(token, p.get("id"), "terminado")

# --- Fragmento Sem Argumentos ---
@st.fragment(run_every=3)
def renderizar_gestao_fila_prestador():
    # Recupera o token do session_state (definido na função principal)
    token = st.session_state.get("current_provider_token")
    if not token:
        st.error("Token de prestador não encontrado.")
        return

    url_firebase = f"{FIREBASE_URL}/pedidos/{token}.json?_t={time.time()}"
    try:
        response = requests.get(url_firebase, timeout=5)
        pedidos = []
        if response.status_code == 200 and response.json():
            data = response.json()
            if isinstance(data, dict):
                pedidos = [{"id": k, **v} for k, v in data.items()]
            elif isinstance(data, list):
                pedidos = [{"id": str(idx), **item} for idx, item in enumerate(data) if item]
        
        pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
        pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))

        st.markdown("### 📋 Gestão de Fila")
        
        if not pedidos_ativos:
            st.info("Nenhum pedido na fila.")
            return

        for p in pedidos_ativos:
            titulo = limpar_nome_musica(p.get("musica", {}))
            estado = p.get("estado")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{'🎵 A Tocar' if estado == 'aprovado' else '⏳ Pendente'}: {titulo}")
            with col2:
                if estado == "pendente":
                    if st.button("Aprovar", key=f"apr_{p['id']}"):
                        terminar_todas_musicas_ativas(token, pedidos)
                        atualizar_estado_pedido(token, p['id'], 'aprovado')
                        st.rerun()
                elif estado == "aprovado":
                    if st.button("Terminar", key=f"ter_{p['id']}"):
                        atualizar_estado_pedido(token, p['id'], 'terminado')
                        st.rerun()
                        
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")

# --- Função Principal ---
def show_provider_panel_custom(provider_token):
    # Guardamos o token no state para o fragmento aceder
    st.session_state["current_provider_token"] = provider_token
    
    st.title("Painel do Prestador")
    st.write(f"Gestão ativa para o token: {provider_token}")
    
    # Chamada SEM argumentos (evita o erro de keyword argument)
    renderizar_gestao_fila_prestador()
