import streamlit as st

def show_provider_panel():
    # Obter o token do prestador através dos query_params
    query_params = st.query_params
    token = query_params.get("token", None)

    if not token:
        st.error("Acesso não autorizado. Por favor, aceda através do link válido fornecido na sua aprovação.")
        return

    st.markdown("""
    <style>
    .prov-card {
        background: linear-gradient(180deg, #111, #050505);
        border: 2px solid #D4AF37;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0px 0px 15px rgba(212,175,55,0.15);
        color: white;
    }
    .link-box {
        background: #1a1a1a;
        border: 1px solid #D4AF37;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
        color: white;
        word-break: break-all;
    }
    </style>
    """, unsafe_allow_html=True)

    st.subheader("🎤 Painel do Prestador — FF Karaoke")
    st.markdown("---")

    # Links personalizados para este prestador específico com base no seu token
    base_domain = "https://appadm.streamlit.app" # Substitua pelo seu domínio se necessário
    
    link_registo_cliente = f"{base_domain}/?page=client_register&provider={token}"
    link_tela_cliente = f"{base_domain}/?page=client_screen&provider={token}"

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="prov-card">
            <h3 style="color: #D4AF37; margin-top: 0;">📝 1. Link de Registo do Cliente</h3>
            <p style="color: #ccc; font-size: 14px;">Partilhe este link com os seus clientes para que eles possam preencher os dados e submeter pedidos de música/vídeo.</p>
            <div class="link-box">
                <a href="{link_registo_cliente}" target="_blank" style="color: #FFD700; font-size: 14px;">{link_registo_cliente}</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        qr_registo = f"https://api.qrserver.com/v1/create-qr-code/?size=140x140&data={link_registo_cliente}"
        st.image(qr_registo, caption="QR Code — Registo de Clientes")

    with col2:
        st.markdown(f"""
        <div class="prov-card">
            <h3 style="color: #D4AF37; margin-top: 0;">📺 2. Link da Tela de Vídeos</h3>
            <p style="color: #ccc; font-size: 14px;">Abra este link num ecrã/projetor ou num segundo monitor para exibir os vídeos pedidos pelos clientes em tempo real.</p>
            <div class="link-box">
                <a href="{link_tela_cliente}" target="_blank" style="color: #FFD700; font-size: 14px;">{link_tela_cliente}</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        qr_tela = f"https://api.qrserver.com/v1/create-qr-code/?size=140x140&data={link_tela_cliente}"
        st.image(qr_tela, caption="QR Code — Tela de Apresentação")
