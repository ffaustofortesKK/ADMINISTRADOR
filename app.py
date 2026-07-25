import streamlit as st

st.set_page_config(
    page_title="FF Karaoke",
    page_icon="🎤",
    layout="wide"
)

# Inicializar a Fila de Espera global na memória
if "fila_karaoke" not in st.session_state:
    st.session_state.fila_karaoke = []

if "confirmar_envio" not in st.session_state:
    st.session_state.confirmar_envio = False
    st.session_state.temp_cantor = ""
    st.session_state.temp_musica = ""

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
.card-title, .card-header {
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
.link-box {
    background: #111;
    border: 1px solid #D4AF37;
    border-radius: 10px;
    padding: 12px 20px;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0px 0px 10px rgba(212,175,55,0.15);
}
.stButton button {
    background: linear-gradient(180deg, #D4AF37, #AA8C2C);
    color: black;
    font-weight: bold;
    border-radius: 10px;
    width: 100%;
    padding: 10px;
    border: none;
    box-shadow: 0px 0px 15px rgba(212,175,55,0.4);
}
</style>
""", unsafe_allow_html=True)

# Painel de Administração / Início (ADM)
st.markdown("### 🎤 Bem-vindo, t t!")
st.markdown("---")

link_cliente = "https://appcliente.streamlit.app/?prestador=t-t"
link_tv = "https://ffktela.streamlit.app/?prestador=t-t"

col_links, col_qr = st.columns([4, 1])

with col_links:
    st.markdown(f"""
    <div class="link-box">
        <span>🏷️ <b>Cliente:</b> <a href="{link_cliente}" target="_blank" style="color: #FFD700;">{link_cliente}</a></span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="link-box">
        <span>📺 <b>TV:</b> <a href="{link_tv}" target="_blank" style="color: #FFD700;">{link_tv}</a></span>
    </div>
    """, unsafe_allow_html=True)
    
with col_qr:
    qr_url_cliente = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={link_cliente}"
    st.image(qr_url_cliente, width=110)

st.markdown("🎬 **Playlist de Vídeos Clipes (Fundo da TV)**")
st.info("Aqui poderá gerir os vídeos para a TV.")

if st.button("🧹 Limpar Fila de Espera"):
    st.session_state.fila_karaoke = []
    st.success("Fila limpa com sucesso!")
