import streamlit as st
import pandas as pd

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

    # Inicializar o estado da sessão do cliente no Streamlit
    if "client_name" not in st.session_state:
        st.session_state.client_name = ""
    if "client_registered" not in st.session_state:
        st.session_state.client_registered = False
    if "can_request" not in st.session_state:
        st.session_state.can_request = True  # True se puder pedir, False se estiver à espera que termine de cantar

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

    # Saudação ao cliente registado
    st.success( bem-vindo(a), **{st.session_state.client_name}**!)

    # Verificar se o cliente já tem um pedido pendente ou a tocar (bloqueio até terminar de cantar)
    if not st.session_state.can_request:
        st.warning("⏳ O seu pedido anterior ainda está na fila ou a ser reproduzido.")
        st.info("Assim que terminar de cantar, receberá a notificação: **'Já pode voltar a pedir outra música.'**")
        
        # Botão para simular que o prestador deu alta / terminou a música (para teste do fluxo)
        if st.button("🔄 Simular Fim de atuação (Desbloquear)"):
            st.session_state.can_request = True
            st.rerun()
        return

    # PASSO 2: Pesquisar e Pedir Música
    st.markdown("### 🔍 Pesquisar Música")
    
    # Simulação da lista de músicas ligadas à biblioteca Cloudinary do utilizador
    # Numa implementação avançada, pode carregar os assets via API do Cloudinary ou de uma tabela de base de dados.
    musicas_disponiveis = [
        {"titulo": "A Minha Terra — Artista Exemplo", "url": "https://res.cloudinary.com/c-779ad1178ec5bba6e37e6c8874b33a/video/upload/exemplo1.mp4"},
        {"titulo": "Amor Eterno — Kizomba Hits", "url": "https://res.cloudinary.com/c-779ad1178ec5bba6e37e6c8874b33a/video/upload/exemplo2.mp4"},
        {"titulo": "Festa no Bairro — Kuduro Style", "url": "https://res.cloudinary.com/c-779ad1178ec5bba6e37e6c8874b33a/video/upload/exemplo3.mp4"},
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
            st.warning("Nenhuma música encontrada com esse título na biblioteca Cloudinary.")

    # PASSO 3: Opção Enviar e Confirmação (Mudar ou Manter)
    if musica_escolhida:
        st.markdown(f"**Música selecionada:** `{musica_escolhida['titulo']}`")
        
        # Confirmação antes de submeter definitivamente
        confirmacao = st.radio("Pretende manter esta escolha ou mudar?", ["Manter", "Mudar"], horizontal=True)
        
        if confirmacao == "Manter":
            if st.button("🚀 Enviar Pedido"):
                # Guardar o pedido na base de dados associada ao prestador (provider_token)
                # O pedido irá para o painel do prestador para aprovação
                st.success("Seu pedido foi enviado.")
                st.session_state.can_request = False # Bloqueia novos pedidos até acabar de cantar
                st.rerun()
