import streamlit as st

def show_client_page():
    query_params = st.query_params
    provider_token = query_params.get("provider", "Desconhecido")

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

    # Inicializar o estado da sessão do cliente
    if "client_name" not in st.session_state:
        st.session_state.client_name = ""
    if "client_registered" not in st.session_state:
        st.session_state.client_registered = False
    if "can_request" not in st.session_state:
        st.session_state.can_request = True

    # PASSO 1: Como gostaria de ser chamado?
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

    # Controlo de fila / estado (só pode pedir outro após terminar)
    if not st.session_state.can_request:
        st.warning("⏳ O seu pedido anterior ainda está em reprodução ou na fila.")
        st.info("Assim que terminar de cantar, receberá a notificação: **'Já pode voltar a pedir outra música.'**")
        
        if st.button("🔄 Simular Fim de Atuação (Desbloquear)"):
            st.session_state.can_request = True
            st.rerun()
        return

    # PASSO 2: Pesquisar Música
    st.markdown("### 🔍 Pesquisar Música")
    
    # Lista de músicas de exemplo ligadas ao Cloudinary
    musicas_disponiveis = [
        {"titulo": "A Minha Terra — Artista Exemplo"},
        {"titulo": "Amor Eterno — Kizomba Hits"},
        {"titulo": "Festa no Bairro — Kuduro Style"},
    ]

    pesquisa = st.text_input("Escreva o título da música pretendida:")
    
    musica_escolhida = None
    if pesquisa:
        resultados = [m for m in musicas_disponiveis if pesquisa.lower() in m['titulo'].lower()]
        if resultados:
            opcoes_titulos = [m['titulo'] for m in resultados]
            escolha_titulo = st.selectbox("Selecione a música encontrada:", opcoes_titulos)
            musica_escolhida = next(m for m in resultados if m['titulo'] == escolha_titulo)
        else:
            st.warning("Nenhuma música encontrada com esse título.")

    # PASSO 3: Enviar e Confirmação (Mudar ou Manter)
    if musica_escolhida:
        st.markdown(f"**Música selecionada:** `{musica_escolhida['titulo']}`")
        
        confirmacao = st.radio("Pretende manter esta escolha ou mudar?", ["Manter", "Mudar"], horizontal=True)
        
        if confirmacao == "Manter":
            if st.button("🚀 Enviar Pedido"):
                st.success("Seu pedido foi enviado.")
                st.session_state.can_request = False
                st.rerun()
