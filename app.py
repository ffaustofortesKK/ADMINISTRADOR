import streamlit as st

st.set_page_config(
    page_title="FF Karaoke — ADM & Prestadores",
    page_icon="🎤",
    layout="wide"
)

# Base de dados em memória
if "prestadores_cadastrados" not in st.session_state:
    st.session_state.prestadores_cadastrados = {
        "t-t": {"senha": "123", "aprovado": True}
    }

if "prestador_logado" not in st.session_state:
    st.session_state.prestador_logado = ""

if "admin_geral" not in st.session_state:
    st.session_state.admin_geral = False

# Capturar parâmetros do URL
query_params = st.query_params
prestador_url = query_params.get("prestador", None)
painel_tipo = query_params.get("painel", None)
pagina_url = query_params.get("page", None)

base_url = "https://appadm.streamlit.app"

# Estilização Global CSS
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

# 1. TELA / TV
if prestador_url and painel_tipo == "tela":
    chave_fila = f"fila_karaoke_{prestador_url}"
    if chave_fila not in st.session_state:
        st.session_state[chave_fila] = []
    st.markdown(f'<div class="card-title">🎤 FILA DE ESPERA — {prestador_url.upper()}</div>', unsafe_allow_html=True)

# 2. PAINEL DO CLIENTE
elif prestador_url and painel_tipo == "cliente":
    chave_fila = f"fila_karaoke_{prestador_url}"
    if chave_fila not in st.session_state:
        st.session_state[chave_fila] = []
    st.markdown(f'<div class="card-header">🎤 FFKARAOKE — PEDIR MÚSICA ({prestador_url.upper()})</div>', unsafe_allow_html=True)

# 3. PÁGINA DIRETA DE REGISTO (Via ?page=register)
elif pagina_url == "register":
    st.markdown("### 📝 Registo de Novo Prestador — FF Karaoke")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_reg_direto"):
            n_novo = st.text_input("Escolha o seu Nome / Alcunha:")
            s_novo = st.text_input("Crie uma Senha:", type="password")
            botao_reg = st.form_submit_button("Efetuar Registo")
            
            if botao_reg:
                n_limpo = n_novo.strip().lower()
                if n_limpo and s_novo:
                    if n_limpo not in st.session_state.prestadores_cadastrados:
                        st.session_state.prestadores_cadastrados[n_limpo] = {
                            "senha": s_novo,
                            "aprovado": False
                        }
                        st.success("Registo efetuado com sucesso! A sua conta aguarda aprovação do Administrador.")
                    else:
                        st.warning("Este nome já está registado.")
                else:
                    st.error("Preencha todos os campos.")
        
        st.markdown("---")
        if st.button("⬅️ Voltar ao Início / Login"):
            st.query_params.clear()
            st.rerun()

# 4. PORTAL PRINCIPAL / ADM / LOGIN
else:
    st.markdown("### 🛠️ Sistema de Gestão — FF Karaoke")
    st.markdown("---")

    # A. Painel do Administrador Geral (Master)
    if st.session_state.admin_geral:
        st.success("👨‍💻 MODO DE ADMINISTRAÇÃO MASTER ATIVO")
        if st.button("🚪 Sair do ADM Master"):
            st.session_state.admin_geral = False
            st.rerun()

        st.subheader("📋 Gestão e Aprovação de Prestadores")
        
        prestadores = st.session_state.prestadores_cadastrados
        if len(prestadores) == 0:
            st.info("Nenhum prestador registado.")
        else:
            for nome, dados in prestadores.items():
                col_info, col_acao = st.columns([3, 1])
                with col_info:
                    status = "✅ Aprovado" if dados.get("aprovado") else "⏳ Pendente de Aprovação"
                    st.write(f"🎤 **Prestador:** `{nome}` | Estado: **{status}**")
                with col_acao:
                    if not dados.get("aprovado"):
                        if st.button(f"Aprovar {nome}", key=f"apr_{nome}"):
                            st.session_state.prestadores_cadastrados[nome]["aprovado"] = True
                            st.success(f"Prestador {nome} aprovado!")
                            st.rerun()
                    else:
                        if st.button(f"Bloquear {nome}", key=f"bloq_{nome}"):
                            st.session_state.prestadores_cadastrados[nome]["aprovado"] = False
                            st.rerun()
        st.markdown("---")

    # B. Painel do Prestador Logado
    elif st.session_state.prestador_logado:
        prestador_atual = st.session_state.prestador_logado
        chave_fila = f"fila_karaoke_{prestador_atual}"
        if chave_fila not in st.session_state:
            st.session_state[chave_fila] = []

        link_cliente_prest = f"{base_url}/?prestador={prestador_atual}&painel=cliente"
        link_tv_prest = f"{base_url}/?prestador={prestador_atual}&painel=tela"

        st.markdown(f"### 🎤 Painel do Prestador: {prestador_atual.upper()}")
        
        if st.button("🚪 Terminar Sessão"):
            st.session_state.prestador_logado = ""
            st.rerun()

        st.markdown("---")
        col_l, col_q = st.columns([4, 1])
        with col_l:
            st.markdown(f'<div class="link-box"><span>🏷️ <b>Cliente:</b> <a href="{link_cliente_prest}" target="_blank" style="color: #FFD700;">{link_cliente_prest}</a></span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="link-box"><span>📺 <b>TV:</b> <a href="{link_tv_prest}" target="_blank" style="color: #FFD700;">{link_tv_prest}</a></span></div>', unsafe_allow_html=True)
        with col_q:
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={link_cliente_prest}", width=110)

        if st.button("🧹 Limpar Fila deste Prestador"):
            st.session_state[chave_fila] = []
            st.success("Fila limpa!")

    # C. Ecrã Inicial (Login / Atalho para Registo / Master)
    else:
        aba_login, aba_master = st.tabs(["🔑 Entrar", "👨‍💻 ADM Master"])

        with aba_login:
            st.subheader("Aceder ao seu Painel")
            
            # Atalho direto para quem abrir o link de registo
            st.info("Ainda não tem conta? Pode aceder diretamente ao formulário em: [Registar Novo Prestador](/?page=register)")
            
            with st.form("form_login_prest"):
                n_log = st.text_input("Nome / Alcunha:")
                s_log = st.text_input("Senha:", type="password")
                if st.form_submit_button("Entrar"):
                    n_limpo = n_log.strip().lower()
                    if n_limpo in st.session_state.prestadores_cadastrados:
                        dados_p = st.session_state.prestadores_cadastrados[n_limpo]
                        if dados_p["senha"] == s_log:
                            if dados_p.get("aprovado", False):
                                st.session_state.prestador_logado = n_limpo
                                st.success("Login efetuado com sucesso!")
                                st.rerun()
                            else:
                                st.warning("A sua conta aguarda aprovação pelo Administrador.")
                        else:
                            st.error("Senha incorreta.")
                    else:
                        st.error("Prestador não encontrado.")

        with aba_master:
            st.subheader("Acesso Restrito do Administrador")
            with st.form("form_master"):
                senha_m = st.text_input("Senha Master:", type="password")
                if st.form_submit_button("Entrar como Master"):
                    if senha_m == "123":
                        st.session_state.admin_geral = True
                        st.rerun()
                    else:
                        st.error("Senha Master incorreta.")
