import streamlit as st

st.set_page_config(
    page_title="FF Karaoke - Sistema Completo",
    page_icon="🎤",
    layout="wide"
)

# Estilização Global CSS (Tema Escuro e Dourado)
st.markdown("""
<style>
body {
    background: #070707;
    color: white;
}
.main {
    background: #070707;
}
.card-title {
    background: linear-gradient(180deg, #111, #050505);
    border: 2px solid #D4AF37;
    border-radius: 15px;
    padding: 15px;
    text-align: center;
    color: #D4AF37;
    font-weight: bold;
    font-size: 24px;
    box-shadow: 0px 0px 20px rgba(212,175,55,.25);
    margin-bottom: 20px;
}
.card-next {
    background: linear-gradient(180deg, #1a0b2e, #0a0412);
    border: 2px solid #9C27B0;
    border-radius: 15px;
    padding: 25px;
    text-align: center;
    box-shadow: 0px 0px 30px rgba(156,39,176,0.4);
    margin-bottom: 15px;
}
.item-fila {
    background: linear-gradient(180deg, #111, #050505);
    border: 2px solid #D4AF37;
    border-radius: 12px;
    padding: 15px 20px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    box-shadow: 0px 0px 15px rgba(212,175,55,.15);
}
.badge-num {
    background: #D4AF37;
    color: black;
    font-weight: bold;
    border-radius: 50%;
    width: 35px;
    height: 35px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-right: 15px;
    font-size: 18px;
}
.player-box {
    background: linear-gradient(180deg, #111, #050505);
    border: 2px solid #D4AF37;
    border-radius: 20px;
    height: 600px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: 0px 0px 25px rgba(212,175,55,.25);
    text-align: center;
    padding: 20px;
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

# Menu Lateral de Navegação
st.sidebar.title("🎛️ Navegação FF Karaoke")
opcao = st.sidebar.selectbox("Escolha o Painel:", ["Tela (Pública/Fila)", "Painel do Cliente"])

st.sidebar.markdown("---")
st.sidebar.info("Sistema integrado de gestão de karaoke.")

# Lógica para mostrar o painel escolhido
if opcao == "Tela (Pública/Fila)":
    col_fila, col_video = st.columns([1, 1])

    with col_fila:
        st.markdown('<div class="card-title">🎤 FILA DE ESPERA</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="card-next">
            <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                <span style="background: #D4AF37; color: black; font-weight: bold; border-radius: 50%; width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; margin-right: 10px;">1</span>
                <span style="color: #D4AF37; letter-spacing: 3px; font-weight: bold;">— Á Seguir —</span>
            </div>
            <h1 style="color: #FFD700; margin: 0; font-size: 36px; text-shadow: 0px 0px 10px rgba(255,215,0,0.5);">DANIEL AMORES</h1>
        </div>
        """, unsafe_allow_html=True)

        participantes = [
            ("2", "MARIA SOUSA"),
            ("3", "JOÃO PEDRO"),
            ("4", "ANA LÚCIA"),
            ("5", "CARLOS MENDES"),
            ("6", "PATRÍCIA LEAL")
        ]

        for num, nome in participantes:
            st.markdown(f"""
            <div class="item-fila">
                <div class="badge-num">{num}</div>
                <div style="font-size: 20px; font-weight: bold; color: white;">👤 {nome}</div>
            </div>
            """, unsafe_allow_html=True)

    with col_video:
        st.markdown('<div class="card-title">📺 VÍDEO CLIPE (FUNDO)</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="player-box">
            <div style="font-size: 50px; margin-bottom: 15px;">📺</div>
            <p style="color: #ccc; font-size: 18px; max-width: 350px; line-height: 1.5;">
                Aguardando o prestador selecionar um vídeo clipe no painel de controle...
            </p>
        </div>
        """, unsafe_allow_html=True)

elif opcao == "Painel do Cliente":
    st.markdown('<div class="card-header">🎤 FFKARAOKE — PEDIR MÚSICA</div>', unsafe_allow_html=True)

    with st.form("form_cliente"):
        st.subheader("Insira os seus dados para participar")
        
        nome_cantor = st.text_input("O seu Nome / Alcunha:")
        nome_musica = st.text_input("Nome da Música ou Artista pretendido:")
        
        enviar_pedido = st.form_submit_button("📤 Enviar Pedido para a Fila")
        
        if enviar_pedido:
            if nome_cantor.strip() and nome_musica.strip():
                st.success(f"Obrigado, **{nome_cantor}**! O seu pedido para a música **'{nome_musica}'** foi enviado com sucesso.")
            else:
                st.error("Por favor, preencha o seu nome e o nome da música antes de enviar.")
