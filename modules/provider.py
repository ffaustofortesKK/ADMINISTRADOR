import streamlit as st

def show_provider_panel():
    query_params = st.query_params
    token = query_params.get("token", None)

    if not token:
        st.error("Acesso não autorizado. Por favor, aceda através do link válido fornecido na sua aprovação.")
        return

    st.markdown("""
    <style>
    .link-row {
        background: linear-gradient(180deg, #111, #050505);
        border: 1px solid #D4AF37;
        border-radius: 8px;
        padding: 12px 15px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0px 0px 10px rgba(212,175,55,0.1);
    }
    .link-title {
        color: #D4AF37;
        font-weight: bold;
        font-size: 15px;
    }
    .link-url {
        background: #1a1a1a;
        border: 1px solid #444;
        border-radius: 6px;
        padding: 6px 12px;
        word-break: break-all;
        text-align: right;
    }
    .link-url a {
        color: #FFD700;
        text-decoration: none;
        font-size: 14px;
    }
    .link-url a:hover {
        text-decoration: underline;
    }
    </style>
    """, unsafe_allow_html=True)

    st.subheader("🎤 Painel do Prestador — FF Karaoke")
    st.markdown("---")

    base_domain = "https://appadm.streamlit.app"
    
    link_registo_cliente = f"{base_domain}/?page=client_register&provider={token}"
    link_tela_cliente = f"{base_domain}/?page=client_screen&provider={token}"

    # --- LINHA 1: Link de Registo do Cliente ---
    st.markdown(f"""
    <div class="link-row">
        <div class="link-title">📝 1. Link de Registo do Cliente</div>
        <div class="link-url">
            <a href="{link_registo_cliente}" target="_blank">{link_registo_cliente}</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- LINHA 2: Link da Tela de Vídeos ---
    st.markdown(f"""
    <div class="link-row">
        <div class="link-title">📺 2. Link da Tela de Vídeos</div>
        <div class="link-url">
            <a href="{link_tela_cliente}" target="_blank">{link_tela_cliente}</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
