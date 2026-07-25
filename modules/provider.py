import streamlit as st

def show_provider_panel():
    query_params = st.query_params
    token = query_params.get("token", None)

    if not token:
        st.error("Acesso não autorizado. Por favor, aceda através do link válido fornecido na sua aprovação.")
        return

    st.subheader("🎤 Painel do Prestador — FF Karaoke")
    st.markdown("---")

    base_domain = "https://appadm.streamlit.app"
    
    link_registo_cliente = f"{base_domain}/?page=client_register&provider={token}"
    link_tela_cliente = f"{base_domain}/?page=client_screen&provider={token}"

    # --- LINHA 1: Link de Registo do Cliente ---
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<div style='padding-top: 8px; font-weight: bold; color: #D4AF37;'>📝 1. Link de Registo do Cliente</div>", unsafe_allow_html=True)
    with col2:
        st.link_button("🔗 Link", link_registo_cliente, use_container_width=True)

    # --- LINHA 2: Link da Tela de Vídeos ---
    col3, col4 = st.columns([3, 1])
    with col3:
        st.markdown("<div style='padding-top: 8px; font-weight: bold; color: #D4AF37;'>📺 2. Link da Tela de Vídeos</div>", unsafe_allow_html=True)
    with col4:
        st.link_button("🔗 Link", link_tela_cliente, use_container_width=True)
