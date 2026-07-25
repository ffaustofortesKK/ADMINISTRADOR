import streamlit as st
from utils.firebase_db import get_musicas_cloudinary, enviar_pedido_cliente

def show_client_page():
    query_params = st.query_params
    provider_token = query_params.get("provider", None)

    if not provider_token:
        st.error("Link de cliente inválido. Falta o identificador do prestador.")
        return

    st.markdown("""
    <style>
    .client-card {
        background: linear-gradient(180deg, #111, #050505);
        border: 2px solid #D4AF37;
        border-radius: 12px;
        padding: 20px;
        color: white;
        box-shadow: 0px 0px 15px rgba(212,175,55,0.15);
    }
    .stTextInput input {
        background-color: #1a1a1a !important;
        color: white !important;
        border: 1px solid #D4AF37 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.subheader("🎤 FFKaraoke — Registo e Pedido de Música")
    st.markdown("---")

    if "client_name" not in st.session_state:
        st.session_state.client_name = ""
    if "client_registered" not in st.session_state:
        st.session_state.client_registered = False
    if "can_request" not in st.session_state:
        st.session_state.can_request = True

    # PASSO 1: Registo do Nome
    if not st.session_state.client_registered:
        with st.form("form_registo_cliente"):
            st.markdown("### Como gostaria de ser chamado?")
            nome_input = st.text_input("Introduza o seu nome ou alcunha:")
            btn_registar = st.form_submit_button("Avançar para o Karaoke")
            
            if btn_registar:
                if nome_input.strip():
                    st.session_state.client_name = nome_input.strip()
                    st.session_state.client_registered = True
                    st.rerun()
                else:
                    st.warning("Por favor, insira um nome válido.")
        return

    st.success(f"Bem-vindo(a), **{st.session_state.client_name}**!")

    # Controlo de estado (bloqueio até terminar de cantar)
    if not st.session_state.can_request:
        st.warning("⏳ O seu pedido anterior ainda está em reprodução ou na fila.")
        st.info("Assim que terminar de cantar, receberá a notificação: **'Já pode voltar a pedir outra música.'**")
        
        if st.button("🔄 Simular Fim de Atuação (Desbloquear)"):
            st.session_state.can_request = True
            st.rerun()
        return

    # PASSO 2: Pesquisar Música no Firebase/Cloudinary
    st.markdown("### 🔍 Pesquisar Música")
    
    musicas_disponiveis = get_musicas_cloudinary()

    pesquisa = st.text_input("Escreva o título da música pretendida:")
    
    musica_escolhida = None
    if pesquisa and musicas_disponiveis:
        resultados = [m for m in musicas_disponiveis if pesquisa.lower() in m.get('titulo', '').lower()]
        if resultados:
            opcoes_titulos = [m['titulo'] for m in resultados]
            escolha_titulo = st.selectbox("Selecione a música encontrada:", opcoes_titulos)
            musica_escolhida = next(m for m in resultados if m['titulo'] == escolha_titulo)
        else:
            st.warning("Nenhuma música encontrada com esse título na base de dados.")
    elif pesquisa and not musicas_disponiveis:
        st.info("Ainda não existem músicas registadas na base de dados do Firebase.")

    # PASSO 3: Enviar e Confirmação (Mudar ou Manter)
    if musica_escolhida:
        st.markdown(f"**Música selecionada:** `{musica_escolhida['titulo']}`")
        
        confirmacao = st.radio("Pretende manter esta escolha ou mudar?", ["Manter", "Mudar"], horizontal=True)
        
        if confirmacao == "Manter":
            if st.button("🚀 Enviar Pedido"):
                sucesso = enviar_pedido_cliente(provider_token, st.session_state.client_name, musica_escolhida)
                if sucesso:
                    st.success("Seu pedido foi enviado.")
                    st.session_state.can_request = False
                    st.rerun()
                else:
                    st.error("Erro ao enviar o pedido. Tente novamente.")
