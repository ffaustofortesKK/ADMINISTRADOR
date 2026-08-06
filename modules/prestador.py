import streamlit as st
import requests

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

def get_pedidos_prestador(token):
    try:
        response = requests.get(f"{FIREBASE_URL}/pedidos/{token}.json")
        if response.status_code == 200 and response.json():
            data = response.json()
            if isinstance(data, dict):
                return [{"id": k, **v} for k, v in data.items()]
        return []
    except Exception:
        return []

def atualizar_estado_pedido(token, pedido_id, novo_estado):
    try:
        requests.patch(f"{FIREBASE_URL}/pedidos/{token}/{pedido_id}.json", json={"estado": novo_estado})
    except Exception:
        pass

def show_provider_panel():
    query_params = st.query_params
    token = query_params.get("token", None)

    if not token:
        st.error("Acesso não autorizado. Por favor, aceda através do link válido fornecido na sua aprovação.")
        return

    st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffeb3b !important; }
    * { color: #ffeb3b !important; }
    .link-row {
        background: linear-gradient(180deg, #111, #050505);
        border: 1px solid #ffeb3b;
        border-radius: 8px;
        padding: 12px 18px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0px 0px 10px rgba(255,235,59,0.1);
        max-width: 600px;
    }
    .link-title {
        color: #ffeb3b !important;
        font-weight: bold;
        font-size: 15px;
    }
    .btn-link {
        background-color: #1a1a1a;
        color: #ffeb3b !important;
        border: 1px solid #ffeb3b;
        border-radius: 6px;
        padding: 6px 20px;
        text-decoration: none;
        font-weight: bold;
        font-size: 14px;
        transition: all 0.3s ease;
    }
    .btn-link:hover {
        background-color: #ffeb3b;
        color: #000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.subheader("🎤 Painel do Prestador — FF Karaoke")
    st.markdown("---")

    base_domain = "https://appadm.streamlit.app"
    link_registo_cliente = f"{base_domain}/?page=client_register&provider={token}"
    link_tela_cliente = f"{base_domain}/?page=client_screen&provider={token}"

    # Secção de Links para os Clientes
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="link-row">
            <div class="link-title">📝 Registo do Cliente</div>
            <div><a href="{link_registo_cliente}" target="_blank" class="btn-link">link</a></div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="link-row">
            <div class="link-title">📺 Tela de Vídeos</div>
            <div><a href="{link_tela_cliente}" target="_blank" class="btn-link">link</a></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🎵 Gestão de Pedidos dos Clientes em Tempo Real")

    pedidos = get_pedidos_prestador(token)
    if not pedidos:
        st.info("A aguardar novos pedidos de músicas dos clientes...")
        return

    for p in pedidos:
        p_id = p.get("id")
        cliente = p.get("cliente", "Desconhecido")
        musica_obj = p.get("musica", {})
        titulo_musica = musica_obj.get("titulo", "Música sem título")
        estado = p.get("estado", "pendente")

        with st.container():
            col_info, col_acao = st.columns([3, 1])
            with col_info:
                st.write(f"👤 **Cliente:** `{cliente}` | 🎶 **Música:** `{titulo_musica}` | 📌 **Estado:** `{estado.upper()}`")
            with col_acao:
                if estado == "pendente":
                    if st.button("Aprovar", key=f"aprov_{p_id}"):
                        atualizar_estado_pedido(token, p_id, "aprovado")
                        st.rerun()
                elif estado == "aprovado":
                    if st.button("Terminar Atuação", key=f"term_{p_id}"):
                        atualizar_estado_pedido(token, p_id, "terminado")
                        st.rerun()
        st.divider()
