import streamlit as st

def show_cliente_panel():
    # Estilização CSS personalizada com o tema dourado e escuro
    st.markdown("""
    <style>
    body {
        background: #070707;
        color: white;
    }
    .main {
        background: #070707;
    }
    .card-header {
        background: linear-gradient(180deg, #111, #050505);
        border: 2px solid #D4AF37;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        color: #D4AF37;
        font-weight: bold;
        font-size: 26px;
        box-shadow: 0px 0px 20px rgba(212,175,55,.25);
        margin-bottom: 25px;
    }
    .stTextInput input {
        background-color: #111 !important;
        color: white !important;
        border: 1px solid #D4AF37 !important;
        border-radius: 10px !important;
    }
    .stButton button {
        background: linear-gradient(180deg, #D4AF37, #AA8C2C);
        color: black;
        font-weight: bold;
        border-radius: 10px;
        width: 100%;
        padding: 12px;
        border: none;
        box-shadow: 0px 0px 15px rgba(212,175,55,0.4);
    }
    .stButton button:hover {
        background: linear-gradient(180deg, #FFD700, #D4AF37);
        color: black;
    }
    </style>
    """, unsafe_allow_html=True)

    # Cabeçalho Principal
    st.markdown("""
    <div class="card-header">
        🎤 FFKARAOKE — PEDIR MÚSICA
    </div>
    """, unsafe_allow_html=True)

    # Formulário de Pedido do Cliente
    with st.form("form_cliente"):
        st.subheader("Insira os seus dados para participar")
        
        nome_cantor = st.text_input("O seu Nome / Alcunha:")
        nome_musica = st.text_input("Nome da Música ou Artista pretendido:")
        
        enviar_pedido = st.form_submit_button("📤 Enviar Pedido para a Fila")
        
        if enviar_pedido:
            if nome_cantor.strip() and nome_musica.strip():
                st.success(f"Obrigado, **{nome_cantor}**! O seu pedido para a música **'{nome_musica}'** foi enviado com sucesso para o prestador.")
            else:
                st.error("Por favor, preencha o seu nome e o nome da música antes de enviar.")
