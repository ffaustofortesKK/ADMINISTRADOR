import time
import requests
import streamlit as st

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

# --- Fragmento com NOVO NOME para forçar o Streamlit a reconhecer a nova assinatura ---
@st.fragment(run_every=3)
def atualizar_painel_fila():
    # Buscamos o token via session_state
    token = st.session_state.get("current_token")
    if not token:
        st.error("Token não configurado.")
        return

    try:
        # Lógica de carregamento do Firebase
        response = requests.get(f"{FIREBASE_URL}/pedidos/{token}.json", timeout=5)
        pedidos = []
        if response.status_code == 200 and response.json():
            data = response.json()
            if isinstance(data, dict):
                pedidos = [{"id": k, **v} for k, v in data.items()]
            
            # Mostra a lista na UI
            st.write(f"Pedidos ativos: {len(pedidos)}")
            for p in pedidos:
                st.write(f"- {p.get('musica', 'Música')} ({p.get('estado')})")
        else:
            st.info("Sem pedidos.")
    except Exception as e:
        st.error(f"Erro: {e}")

# --- Função Principal ---
def show_provider_panel_custom(provider_token):
    # 1. Atualizamos o estado
    st.session_state["current_token"] = provider_token
    
    st.title("Painel do Prestador")
    
    # 2. Chamamos a função RENOMEADA e SEM argumentos
    atualizar_painel_fila()
