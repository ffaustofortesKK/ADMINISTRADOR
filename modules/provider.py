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
        padding: 12px 18px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0px 0px 10px rgba(212,175,55,0.1);
        max-width: 600px;
    }
    .link-title {
        color: #D4AF37;
        font-weight: bold;
        font-size: 15px;
    }
    .btn-link {
        background-color: #1a1a1a;
        color: #FFD700 !important;
        border: 1px solid #D4AF37;
        border-radius: 6px;
        padding: 6px 20px;
        text-decoration: none;
        font-weight: bold;
        font-size: 14px;
        transition: all 0.3s ease;
    }
    .btn-link:hover {
        background-color: #D4AF37;
        color: #000 !important;
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
        <div>
            <a href="{link_registo_cliente}" target="_blank" class="btn-link">link</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- LINHA 2: Link da Tela de Vídeos ---
    st.markdown(f"""
    <div class="link-row">
        <div class="link-title">📺 2. Link da Tela de Vídeos</div>
        <div>
            <a href="{link_tela_cliente}" target="_blank" class="btn-link">link</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
