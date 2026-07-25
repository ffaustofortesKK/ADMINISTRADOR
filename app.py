import streamlit as st

st.set_page_config(
    page_title="FF Karaoke — Sistema de Prestadores",
    page_icon="🎤",
    layout="wide"
)

# Inicializar bases de dados na memória do Streamlit
if "filas_por_prestador" not in st.session_state:
    st.session_state.filas_por_prestador = {}

if "confirmar_envio" not in st.session_state:
    st.session_state.confirmar_envio = False
    st.session_state.temp_cantor = ""
    st.session_state.temp_musica = ""

# Capturar parâmetros do URL
query_params = st.query_params
prestador_url = query_params.get("prestador", None)
painel_cliente_ativo = query_params.get("cliente", None)
painel_tv_ativo = query_params.get("tv", None)

# URLs base das aplicações (substitua pelos seus links reais do Streamlit se forem apps separadas, 
# ou mantenha o mesmo domínio se estiver tudo na mesma aplicação)
base_cliente = "https://appcliente.streamlit.app"
base_tv = "https://ffktela.streamlit.app"

# Estilização CSS Global
st.markdown("""
<style>
body { background: #070707; color: white; }
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
    height: 500px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: 0px 0px 25px rgba(212,175,55,.25);
    text-align: center;
    padding: 20px;
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
    padding: 10px;
    border: none;
    box-shadow: 0px 0px 15px rgba(212,175,55,0.4);
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 1. MODO CLIENTE (Acedido através do link com ?prestador=nome)
# ----------------------------------------------------
if prestador_url and not painel_tv_ativo:
    prestador_nome = prestador_url.strip()
    st.markdown(f'<div class="card-header">🎤 FFKARAOKE — PEDIR MÚSICA ({prestador_nome.upper()})</div>', unsafe_allow_html=True)

    if "fila_karaoke" not in st.session_state.filas_por_prestador:
        st.session_state.filas_por_prestador[prestador_nome] = []

    if not st.session_state.confirmar_envio:
        with st.form("form_cliente"):
            st.subheader("Insira os seus dados para participar")
            nome_cantor = st.text_input("O seu Nome / Alcunha:")
            nome_musica = st.text_input("Nome da Música ou Artista pretendido:")
            botao_avancar = st.form_submit_button("Continuar ➡️")
            
            if botao_avancar:
                if nome_cantor.strip() and nome_musica.strip():
                    st.session_state.temp_cantor = nome_cantor.strip()
                    st.session_state.temp_musica = nome_musica.strip()
                    st.session_state.confirmar_envio = True
                    st.rerun()
                else:
                    st.error("Por favor, preencha o seu nome e o nome da música.")
    else:
        st.markdown(f"""
        <div style="background: #111; border: 2px solid #D4AF37; border-radius: 15px; padding: 20px; text-align: center; margin-bottom: 20px;">
            <h3 style="color: #D4AF37;">Confirmação do Pedido</h3>
            <p style="font-size: 18px; color: white;">Cantor: <b>{st.session_state.temp_cantor.upper()}</b></p>
            <p style="font-size: 18px; color: white;">Música: <b>{st.session_state.temp_musica.title()}</b></p>
            <p style="color: #FFD700; margin-top: 15px; font-weight: bold;">Tem a certeza que deseja enviar?</p>
        </div>
        """, unsafe_allow_html=True)

        col_sim, col_nao = st.columns(2)
        with col_sim:
            if st.button("✅ SIM, Enviar"):
                if prestador_nome not in st.session_state.filas_por_prestador:
                    st.session_state.filas_por_prestador[prestador_nome] = []
                st.session_state.filas_por_prestador[prestador_nome].append({
                    "cantor": st.session_state.temp_cantor.upper(),
                    "musica": st.session_state.temp_musica.title()
                })
                st.success("Pedido enviado com sucesso para a fila do prestador!")
                st.session_state.confirmar_envio = False
                st.session_state.temp_cantor = ""
                st.session_state.temp_musica = ""
                st.rerun()
        with col_nao:
            if st.button("❌ NÃO, Voltar"):
                st.session_state.confirmar_envio = False
                st.rerun()

# ----------------------------------------------------
# 2. MODO TELA / TV (Acedido através do link com ?tv=1&prestador=nome)
# ----------------------------------------------------
elif prestador_url and painel_tv_ativo:
    prestador_nome = prestador_url.strip()
    if prestador_nome not in st.session_state.filas_por_prestador:
        st.session_state.filas_por_prestador[prestador_nome] = []
    
    fila = st.session_state.filas_por_prestador[prestador_nome]

    col_fila, col_video = st.columns([1, 1])

    with col_fila:
        st.markdown(f'<div class="card-title">🎤 FILA DE ESPERA — {prestador_nome.upper()}</div>', unsafe_allow_html=True)

        if len(fila) > 0:
            primeiro = fila[0]
            st.markdown(f"""
            <div class="card-next">
                <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                    <span style="background: #D4AF37; color: black; font-weight: bold; border-radius: 50%; width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; margin-right: 10px;">1</span>
                    <span style="color: #D4AF37; letter-spacing: 3px; font-weight: bold;">— Á Seguir —</span>
                </div>
                <h1 style="color: #FFD700; margin: 0; font-size: 32px;">{primeiro['cantor']}</h1>
                <p style="color: #ccc; margin-top: 5px; font-size: 16px;">🎵 {primeiro['musica']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="card-next">
                <div style="color: #D4AF37; letter-spacing: 3px; font-weight: bold; margin-bottom: 5px;">— Á Seguir —</div>
                <h3 style="color: #777; margin: 0;">Aguardando cantor...</h3>
            </div>
            """, unsafe_allow_html=True)

        posicoes_restantes = fila[1:6]
        for i in range(2, 7):
            idx = i - 2
            if idx < len(posicoes_restantes):
                item = posicoes_restantes[idx]
                st.markdown(f"""
                <div class="item-fila">
                    <div class="badge-num">{i}</div>
                    <div style="font-size: 18px; font-weight: bold; color: white;">👤 {item['cantor']} <span style="font-size: 14px; color: #aaa;">({item['musica']})</span></div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="item-fila" style="opacity: 0.3;">
                    <div class="badge-num">{i}</div>
                    <div style="font-size: 18px; color: #555;">— Vazio —</div>
                </div>
                """, unsafe_allow_html=True)

    with col_video:
        st.markdown('<div class="card-title">📺 VÍDEO CLIPE (FUNDO)</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="player-box">
            <div style="font-size: 50px; margin-bottom: 15px;">📺</div>
            <p style="color: #ccc; font-size: 18px; max-width: 350px; line-height: 1.5;">
                Aguardando o prestador selecionar um vídeo clipe...
            </p>
        </div>
        """, unsafe_allow_html=True)

# ----------------------------------------------------
# 3. PAINEL DO PRESTADOR (Exibe os links personalizados com o nome dele)
# ----------------------------------------------------
else:
    st.markdown("### 🎤 Painel de Registo / Identificação do Prestador")
    st.info("Insira o seu nome ou alcunha para gerar automaticamente os seus links exclusivos de cliente e TV.")
    
    with st.form("form_prestador"):
        nome_prestador_input = st.text_input("O seu Nome de Prestador (ex: artur, t-t):", value="t-t")
        gerar_links = st.form_submit_button("Gerar Meus Links Exclusivos 🚀")
        
    if gerar_links and nome_prestador_input.strip():
        p_limpo = nome_prestador_input.strip().lower().replace(" ", "-")
        
        link_cliente_prestador = f"{base_cliente}/?prestador={p_limpo}"
        link_tv_prestador = f"{base_tv}/?tv=1&prestador={p_limpo}"
        
        st.markdown(f"### 🎤 Bem-vindo, {nome_prestador_input.strip()}!")
        st.markdown("---")
        
        col_links, col_qr = st.columns([4, 1])
        
        with col_links:
            st.markdown(f"""
            <div class="link-box">
                <span>🏷️ <b>Cliente:</b> <a href="{link_cliente_prestador}" target="_blank" style="color: #FFD700;">{link_cliente_prestador}</a></span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="link-box">
                <span>📺 <b>TV:</b> <a href="{link_tv_prestador}" target="_blank" style="color: #FFD700;">{link_tv_prestador}</a></span>
            </div>
            """, unsafe_allow_html=True)
            
        with col_qr:
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={link_cliente_prestador}"
            st.image(qr_url, width=110)

        st.markdown("🎬 **Playlist de Vídeos Clipes (Fundo da TV)**")
        st.info("Gerencie aqui os seus vídeos.")
