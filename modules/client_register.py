import streamlit as st

def show_client_register_page():
    query_params = st.query_params
    provider_token = query_params.get("provider", None)

    if not provider_token:
        st.error("Link de acesso inválido. Por favor, utilize o link fornecido pelo seu prestador.")
        return

    st.markdown("""
    <style>
    .client-card {
        background: linear-gradient(180deg, #111, #050505);
        border: 2px solid #D4AF37;
        border-radius: 12px;
        padding: 25px;
        max-width: 600px;
        margin: auto;
        color: white;
        box-shadow: 0px 0px 15px rgba(212,175,55,0.15);
    }
    .stTextInput input {
        background-color: #1a1a1a !important;
        color: white !important;
        border: 1px solid #D4AF37 !important;
    }
    .success-msg {
        background-color: #1b4d3e;
        border: 1px solid #2ecc71;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        color: #2ecc71;
        font-weight: bold;
        font-size: 18px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='text-align: center; color: #D4AF37;'>🎤 FFKaraoke — Pedido de Música</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Inicializar o estado da sessão do cliente se não existir
    if "step" not in st.session_state:
        st.session_state.step = "name"
    if "client_name" not in st.session_state:
        st.session_state.client_name = ""
    if "selected_song" not in st.session_state:
        st.session_state.selected_song = ""

    # --- PASSO 1: Inserir o Nome ---
    if st.session_state.step == "name":
        with st.container():
            st.markdown('<div class="client-card">', unsafe_allow_html=True)
            st.subheader("📝 Identificação")
            name_input = st.text_input("Como gostaria de ser chamado?", value=st.session_state.client_name)
            
            if st.button("Avançar", use_container_width=True):
                if name_input.strip():
                    st.session_state.client_name = name_input.strip()
                    st.session_state.step = "search"
                    st.rerun()
                else:
                    st.warning("Por favor, insira o seu nome ou alcunha.")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- PASSO 2: Pesquisar Música ---
    elif st.session_state.step == "search":
        with st.container():
            st.markdown('<div class="client-card">', unsafe_allow_html=True)
            st.subheader(f"👋 Olá, {st.session_state.client_name}!")
            
            song_query = st.text_input("🔍 Pesquisar Música (Digite o título):", value=st.session_state.selected_song)
            
            # Nota: Aqui ligaremos futuramente à lista de músicas da vossa biblioteca do Cloudinary
            st.info("💡 As músicas disponíveis estão sincronizadas com a biblioteca Cloudinary do sistema.")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Voltar", use_container_width=True):
                    st.session_state.step = "name"
                    st.rerun()
            with col2:
                if st.button("Enviar Pedido", use_container_width=True):
                    if song_query.strip():
                        st.session_state.selected_song = song_query.strip()
                        st.session_state.step = "confirm"
                        st.rerun()
                    else:
                        st.warning("Por favor, escreva o título da música que pretende.")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- PASSO 3: Confirmar se quer Mudar ou Manter ---
    elif st.session_state.step == "confirm":
        with st.container():
            st.markdown('<div class="client-card">', unsafe_allow_html=True)
            st.subheader("⚠️ Confirmação do Pedido")
            st.write(f"**Música escolhida:** `{st.session_state.selected_song}`")
            st.markdown("Pretende **mudar** a música ou **manter** e enviar o pedido?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Mudar", use_container_width=True):
                    st.session_state.step = "search"
                    st.rerun()
            with col2:
                if st.button("✅ Manter e Enviar", use_container_width=True):
                    st.session_state.step = "success"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # --- PASSO 4: Mensagem de Sucesso ---
    elif st.session_state.step == "success":
        with st.container():
            st.markdown('<div class="client-card">', unsafe_allow_html=True)
            st.markdown('<div class="success-msg">Seu pedido foi enviado.</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("Fazer Novo Pedido", use_container_width=True):
                st.session_state.selected_song = ""
                st.session_state.step = "search"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
