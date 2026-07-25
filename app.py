import streamlit as st

st.set_page_config(
    page_title="FF Karaoke — Gestão e Prestadores",
    page_icon="🎤",
    layout="wide"
)

# Inicializar bases de dados em memória
if "prestadores_cadastrados" not in st.session_state:
    st.session_state.prestadores_cadastrados = {
        "t-t": {"senha": "123", "ativo": True}
    }

if "autenticado_adm" not in st.session_state:
    st.session_state.autenticado_adm = False

if "prestador_logado" not in st.session_state:
    st.session_state.prestador_logado = ""

# Capturar parâmetros do URL para telas e clientes
query_params = st.query_params
prestador_url = query_params.get("prestador", None)
painel_tipo = query_params.get("painel", None)

base_url = "https://administrador.streamlit.app"  # Ajuste para o seu link real se necessário

# Estilização Global CSS (Tema Escuro e Dourado)
st.markdown("""
<style>
body { background: #070707; color: white; }
.main { background: #070707; }
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

# -------------------------------------------------------------------------
# 1. TELA / TV (Via ?prestador=...&painel=tela)
# -------------------------------------------------------------------------
if prestador_url and painel_tipo == "tela":
    chave_fila = f"fila_karaoke_{prestador_url}"
    if chave_fila not in st.session_state:
        st.session_state[chave_fila] = []

    col_fila, col_video = st.columns([1, 1])

    with col_fila:
        st.markdown(f'<div class="card-title">🎤 FILA DE ESPERA — {prestador_url.upper()}</div>', unsafe_allow_html=True)
        fila = st.session_state[chave_fila]

        if len(fila) > 0:
            primeiro = fila[0]
            st.markdown(f"""
            <div class="card-next">
                <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                    <span style="background: #D4AF37; color: black; font-weight: bold; border-radius: 50%; width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; margin-right: 10px;">1</span>
                    <span style="color: #D4AF37; letter-spacing: 3px; font-weight: bold;">— Á Seguir —</span>
                </div>
                <h1 style="color: #FFD700; margin: 0; font-size: 32px; text-shadow: 0px 0px 10px rgba(255,215,0,0.5);">{primeiro['cantor']}</h1>
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
                    <div style="font-size: 18px; font-weight: bold; color: white;">👤 {item['cantor']} <span style="font-size: 14px; color: #aaa; font-weight: normal;">({item['musica']})</span></div>
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
                Aguardando o prestador selecionar um vídeo clipe no painel de controle...
            </p>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 2. PAINEL DO CLIENTE (Via ?prestador=...&painel=cliente)
# -------------------------------------------------------------------------
elif prestador_url and painel_tipo == "cliente":
    chave_fila = f"fila_karaoke_{prestador_url}"
    if chave_fila not in st.session_state:
        st.session_state[chave_fila] = []

    if "confirmar_envio" not in st.session_state:
        st.session_state.confirmar_envio = False
        st.session_state.temp_cantor = ""
        st.session_state.temp_musica = ""

    st.markdown(f'<div class="card-header">🎤 FFKARAOKE — PEDIR MÚSICA ({prestador_url.upper()})</div>', unsafe_allow_html=True)

    if not st.session_state.confirmar_envio:
        with st.form("form_cliente"):
            st.subheader("Insira os seus dados para participar")
            nome_cantor = st.text_input("O seu Nome / Alcunha:")
            nome_musica = st.text_input("Nome da Música ou Artista pretendido:")
            
            if st.form_submit_button("Continuar ➡️"):
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
                st.session_state[chave_fila].append({
                    "cantor": st.session_state.temp_cantor.upper(),
                    "musica": st.session_state.temp_musica.title()
                })
                st.success(f"Pedido enviado com sucesso para a fila de {prestador_url}!")
                st.session_state.confirmar_envio = False
                st.session_state.temp_cantor = ""
                st.session_state.temp_musica = ""
                st.rerun()
        with col_nao:
            if st.button("❌ NÃO, Voltar"):
                st.session_state.confirmar_envio = False
                st.rerun()

# -------------------------------------------------------------------------
# 3. PORTAL PRINCIPAL: GESTÃO, ADM E REGISTO DE PRESTADORES
# -------------------------------------------------------------------------
else:
    st.markdown("### 🛠️ Sistema de Gestão — FF Karaoke (ADM)")
    st.markdown("---")

    # Se já iniciou sessão com sucesso num prestador específico
    if st.session_state.prestador_logado:
        prestador_atual = st.session_state.prestador_logado
        chave_fila = f"fila_karaoke_{prestador_atual}"
        if chave_fila not in st.session_state:
            st.session_state[chave_fila] = []

        link_cliente_prestador = f"{base_url}/?prestador={prestador_atual}&painel=cliente"
        link_tv_prestador = f"{base_url}/?prestador={prestador_atual}&painel=tela"

        st.markdown(f"### 🎤 Painel do Prestador: {prestador_atual.upper()}")
        
        if st.button("🚪 Terminar Sessão (Voltar ao ADM Geral)"):
            st.session_state.prestador_logado = ""
            st.session_state.autenticado_adm = False
            st.rerun()

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
            qr_url_cliente = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={link_cliente_prestador}"
            st.image(qr_url_cliente, width=110)

        st.markdown("🎬 **Playlist de Vídeos Clipes (Fundo da TV)**")
        st.info(f"Gerindo a sessão de karaoke para o prestador: **{prestador_atual}**")

        if st.button("🧹 Limpar Fila deste Prestador"):
            st.session_state[chave_fila] = []
            st.success("Fila limpa com sucesso!")

    else:
        # Ecrã de Login e Registo de Prestadores com Senha de ADM
        aba_login, aba_registo = st.tabs(["🔑 Entrar (Prestador Existente)", "📝 Registar Novo Prestador"])

        with aba_login:
            st.subheader("Aceder ao seu Painel")
            with st.form("form_login"):
                nome_login = st.text_input("Nome / Alcunha do Prestador:")
                senha_login = st.text_input("Senha de Acesso:", type="password")
                botao_login = st.form_submit_button("Entrar")
                
                if botao_login:
                    nome_limpo = nome_login.strip().lower()
                    if nome_limpo in st.session_state.prestadores_cadastrados:
                        if st.session_state.prestadores_cadastrados[nome_limpo]["senha"] == senha_login:
                            st.session_state.prestador_logado = nome_limpo
                            st.session_state.autenticado_adm = True
                            st.success(f"Bem-vindo, {nome_login}!")
                            st.rerun()
                        else:
                            st.error("Senha incorreta.")
                    else:
                        st.error("Prestador não encontrado. Registe-se na aba ao lado.")

        with aba_registo:
            st.subheader("Registar Novo Prestador")
            with st.form("form_registo"):
                novo_nome = st.text_input("Escolha o seu Nome / Alcunha (ex: artur):")
                nova_senha = st.text_input("Crie uma Senha:", type="password")
                botao_reg = st.form_submit_button("Criar Conta")
                
                if botao_reg:
                    nome_limpo = novo_nome.strip().lower()
                    if nome_limpo and nova_senha:
                        if nome_limpo not in st.session_state.prestadores_cadastrados:
                            st.session_state.prestadores_cadastrados[nome_limpo] = {
                                "senha": nova_senha,
                                "ativo": True
                            }
                            st.success(f"Conta para '{novo_nome}' criada com sucesso! Já pode fazer login na aba ao lado.")
                        else:
                            st.warning("Este nome de prestador já está registado.")
                    else:
                        st.error("Preencha todos os campos corretamente.")
