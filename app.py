import streamlit as st
import requests
import datetime
import time
import urllib.parse
import uuid
import pandas as pd

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="FF Karaoke Cloud",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# URL do Firebase (Base de Dados)
FIREBASE_URL = "https://ffkaraoke-cloud-default-rtdb.firebaseio.com"

# Funções Auxiliares Genéricas
def get_all_providers():
    try:
        response = requests.get(f"{FIREBASE_URL}/prestadores.json", timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()
            providers_list = [{"token": k, **v} for k, v in data.items()]
            return pd.DataFrame(providers_list)
    except Exception:
        pass
    return pd.DataFrame()

def obter_video_fundo(provider_token):
    try:
        response = requests.get(f"{FIREBASE_URL}/config_videos/{provider_token}.json", timeout=10)
        if response.status_code == 200 and response.json():
            return response.json().get("url_video", "")
    except Exception:
        pass
    return ""

def limpar_nome_musica(musica_dict_ou_str):
    if isinstance(musica_dict_ou_str, dict):
        return musica_dict_ou_str.get("titulo", "Música Desconhecida")
    return str(musica_dict_ou_str)

def custom_show_register_page():
    st.title("📝 Registo de Novo Prestador - FF Karaoke")
    with st.form("form_registo_prestador"):
        nome = st.text_input("Nome do Responsável")
        estabelecimento = st.text_input("Nome do Estabelecimento")
        contacto = st.text_input("Contacto Telefónico")
        tempo_plano = st.selectbox(
            "Plano Inicial Pretendido", 
            options=["2 Horas - 12 Mil Kwanzas", "3 Horas - 15 Mil Kwanzas", "4 Horas - 20 Mil Kwanzas"]
        )
        referencia = st.text_input("Referência de Pagamento / Nº de Comprovativo")
        btn_submeter = st.form_submit_button("Submeter Registo")
        
        if btn_submeter:
            if not nome or not estabelecimento or not referencia:
                st.error("Por favor, preencha todos os campos obrigatórios.")
            else:
                token_novo = str(uuid.uuid4())[:8]
                dados_prestador = {
                    "nome_prestador": nome,
                    "estabelecimento": estabelecimento,
                    "contacto": contacto,
                    "tempo_plano": tempo_plano,
                    "referencia": referencia,
                    "approved": 0,
                    "data_registo": str(datetime.datetime.now())
                }
                try:
                    requests.put(f"{FIREBASE_URL}/prestadores/{token_novo}.json", json=dados_prestador, timeout=10)
                    st.success(f"Registo submetido com sucesso! O seu token de acesso é: {token_novo}. Guarde-o enquanto aguarda a aprovação.")
                except Exception as err:
                    st.error(f"Erro ao submeter registo: {err}")

def show_client_page():
    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider", None)
    if not provider_token:
        st.error("Página de registo inválida. Falta o parâmetro do prestador.")
        return
    st.title("🎵 Registo de Música para Karaoke")
    st.markdown(f"**Token do Prestador:** `{provider_token}`")
    with st.form("form_registo_musica"):
        cliente = st.text_input("O seu Nome / Convidado")
        musica = st.text_input("Nome da Música / Artista")
        btn_musica = st.form_submit_button("Adicionar à Fila")
        if btn_musica:
            if not cliente or not musica:
                st.error("Por favor, preencha o seu nome e a música pretendida.")
            else:
                dados_pedido = {
                    "cliente": cliente,
                    "musica": musica,
                    "estado": "pendente",
                    "timestamp": time.time()
                }
                try:
                    pedido_id = str(uuid.uuid4())[:8]
                    requests.put(f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}.json", json=dados_pedido, timeout=10)
                    st.success("Música adicionada à fila com sucesso!")
                except Exception as err:
                    st.error(f"Erro ao adicionar música: {err}")

def renderizar_gestao_fila_prestador(provider_token):
    st.markdown("---")
    st.subheader("📋 Gestão da Fila de Músicas")
    try:
        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        response = requests.get(url_firebase, timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()
            for k, v in data.items():
                col_info, col_acao = st.columns([3, 1])
                with col_info:
                    st.markdown(f"- **{v.get('cliente')}** cantará: *{limpar_nome_musica(v.get('musica'))}* (Estado: `{v.get('estado')}`)")
                with col_acao:
                    estado_atual = v.get('estado')
                    if estado_atual == "pendente":
                        if st.button("▶️ Tocar", key=f"tocar_{k}"):
                            requests.patch(f"{FIREBASE_URL}/pedidos/{provider_token}/{k}.json", json={"estado": "aprovado"}, timeout=10)
                            st.rerun()
                    elif estado_atual == "aprovado":
                        if st.button("✔️ Concluir", key=f"concluir_{k}"):
                            requests.patch(f"{FIREBASE_URL}/pedidos/{provider_token}/{k}.json", json={"estado": "concluido"}, timeout=10)
                            st.rerun()
        else:
            st.info("Nenhum pedido na fila de momento.")
    except Exception as e:
        st.warning(f"Não foi possível carregar a fila: {e}")

def show_provider_panel_custom(provider_token):
    try:
        res = requests.get(f"{FIREBASE_URL}/prestadores/{provider_token}.json", timeout=10)
        p_data = res.json() if res.status_code == 200 and res.json() else {}
    except Exception:
        p_data = {}

    nome_prestador = p_data.get("nome_prestador", "Prestador")
    estabelecimento = p_data.get("estabelecimento", "ESTABELECIMENTO")
    tempo_plano = p_data.get("tempo_plano", "2 Horas")
    url_fundo_painel = p_data.get("url_fundo", "https://images.unsplash.com/photo-1514525253161-7a46d19cd819")
    url_logotipo = p_data.get("url_logo", "https://i.imgur.com/74a1XKt.png")
    
    data_reg_str = p_data.get("data_registo", str(datetime.datetime.now()))
    try:
        dt_reg = datetime.datetime.fromisoformat(data_reg_str)
    except Exception:
        dt_reg = datetime.datetime.now()

    segundos_totais = 7200 
    if "3" in tempo_plano:
        segundos_totais = 10800
    elif "4" in tempo_plano:
        segundos_totais = 14400

    diff = (datetime.datetime.now() - dt_reg).total_seconds()
    segundos_restantes = max(0, int(segundos_totais - diff))

    horas_restantes = segundos_restantes // 3600
    min_restantes = (segundos_restantes % 3600) // 60
    seg_restantes = segundos_restantes % 60
    tempo_formatado = f"{int(horas_restantes):02d}:{int(min_restantes):02d}:{int(seg_restantes):02d}"

    aviso_reforço_html = ""
    classe_piscar = ""
    if segundos_restantes <= 1800 and segundos_restantes > 0:
        classe_piscar = "animation: piscarRelogio 1s infinite;"
        aviso_reforço_html = """
        <div style="background: rgba(255,0,0,0.85); border: 3px solid #ffeb3b; padding: 10px; border-radius: 6px; margin-bottom: 15px; text-align: center; animation: pulseAviso 1s infinite;">
            <span style="color: #ffffff; font-size: 14px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">
                O SEU TEMPO ESTA TERMINANDO. PARA QUE NÃO PERCAS OS SEUS REGISTOS PEÇA REFORÇO DE TEMPO.
            </span>
            <div style="margin-top: 8px;">
                <a href="#reforco_seccao" style="background: #FFC107; color: #000; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 13px;">⚡ PEDIR REFORÇO AGORA</a>
            </div>
        </div>
        """

    st.markdown(f"""
    <style>
    .stApp {{
        background: url("{url_fundo_painel}") no-repeat center center fixed !important;
        background-size: cover !important;
    }}
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        background: rgba(0, 0, 0, 0.95) !important;
        border-radius: 12px;
        margin-top: 1rem;
        margin-bottom: 1rem;
        border: 4px solid #FFC107 !important;
        max-width: 1400px;
    }}
    @keyframes pulseAviso {{
        0% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.7; transform: scale(1.01); }}
        100% {{ opacity: 1; transform: scale(1); }}
    }}
    @keyframes piscarRelogio {{
        0% {{ opacity: 1; color: #FFC107; }}
        50% {{ opacity: 0.3; color: #ff5252; }}
        100% {{ opacity: 1; color: #FFC107; }}
    }}
    .card-link, .card-tv {{
        background: #000000 !important;
        border: 3px solid #FFC107 !important;
        border-radius: 8px;
        padding: 10px 14px;
        text-align: left;
        box-shadow: 0 4px 15px rgba(255, 193, 7, 0.25);
        margin-bottom: 12px;
        width: 100%;
    }}
    .card-tv {{
        border: 3px solid #9c27b0 !important;
        box-shadow: 0 4px 15px rgba(156, 39, 176, 0.25);
    }}
    .qr-box {{
        background: #000;
        border: 3px solid #FFC107 !important;
        border-radius: 8px;
        padding: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .link-title, .link-title-tv {{
        font-family: monospace;
        color: #ffffff !important;
        font-size: 13px;
        font-weight: bold !important;
        margin-bottom: 4px;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.9) !important;
    }}
    .link-text, .link-text-tv {{
        font-family: monospace;
        color: #ffffff !important;
        font-size: 11px;
        word-break: break-all;
        text-decoration: underline;
        font-weight: bold !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.9) !important;
    }}
    .top-logo {{
        width: 55px;
        height: 55px;
        border-radius: 50%;
        border: 3px solid #FFC107;
        object-fit: cover;
    }}
    h1, h2, h3, h4, h5, h6, p, label, span, div, .stMarkdown {{
        color: #ffffff !important;
        font-weight: bold !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.9) !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    col_topo_1, col_topo_2, col_topo_3 = st.columns([1.2, 3, 0.8])
    with col_topo_1:
        st.markdown(f"""
            <div style="background: #000000; border: 2px solid #FFC107; border-radius: 6px; padding: 8px; text-align: center;">
                <div style="font-family: monospace; color: #ffffff; font-size: 9px; text-transform: uppercase; letter-spacing: 1px;">TEMPO / PLANO ESCOLHIDO</div>
                <div style="font-family: monospace; color: #FFC107; font-size: 18px; font-weight: bold; {classe_piscar} margin: 2px 0;">⏱️ {tempo_formatado}</div>
                <div style="font-family: monospace; color: #fff; font-size: 10px;">({tempo_plano})</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_topo_2:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 12px; padding-top: 5px;">
                <span style="font-size: 28px;">🎤</span>
                <div>
                    <h1 style="margin: 0; color: #FFC107; font-family: monospace; font-size: 20px; text-transform: uppercase; font-weight: bold;">PAINEL DO PRESTADOR: <span style="color: #FFC107;">{estabelecimento}</span></h1>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_topo_3:
        st.markdown(f'<div style="text-align: right;"><img src="{url_logotipo}" class="top-logo" /></div>', unsafe_allow_html=True)

    st.markdown("<hr style='border-color: #FFC107; margin: 15px 0;'>", unsafe_allow_html=True)
    st.markdown(aviso_reforço_html, unsafe_allow_html=True)
    
    link_cliente_rel = f"/?page=client_register&prestador={provider_token}"
    link_tv_rel = f"/?page=client_screen&prestador={provider_token}"
    
    try:
        host_dominio = st.context.headers.get('Host', 'grupoffkaraoke.streamlit.app')
    except Exception:
        host_dominio = 'grupoffkaraoke.streamlit.app'

    link_cliente_absoluto = f"https://{host_dominio}{link_cliente_rel}"
    link_tv_absoluto = f"https://{host_dominio}{link_tv_rel}"
    
    qr_url_cliente = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={urllib.parse.quote(link_cliente_absoluto)}"

    col_links, col_qr = st.columns([2.5, 1], gap="medium")
    
    with col_links:
        st.markdown(f"""
            <div class="card-link">
                <div class="link-title">🔗 LINK DO CLIENTE (REGISTO DE MÚSICA)</div>
                <a href="{link_cliente_rel}" target="_blank" class="link-text">{link_cliente_absoluto}</a>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="card-tv">
                <div class="link-title-tv">📺 LINK DA TELA DE TV / REPRODUÇÃO</div>
                <a href="{link_tv_rel}" target="_blank" class="link-text-tv">{link_tv_absoluto}</a>
            </div>
        """, unsafe_allow_html=True)

    with col_qr:
        st.markdown("<div style='font-family: monospace; color: #ffffff; font-size: 11px; font-weight: bold; margin-bottom: 3px; text-align: center;'>QR CODE CLIENTE</div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class="qr-box">
                <img src="{qr_url_cliente}" width="110" style="border-radius: 4px;" />
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color: #333; margin: 15px 0;'>", unsafe_allow_html=True)

    st.markdown("<div id='reforco_seccao'></div>", unsafe_allow_html=True)
    if segundos_restantes <= 1800:
        st.markdown("### ⚡ Solicitar Reforço de Tempo")
        with st.form("form_reforco_prestador"):
            referencia_comprovativo = st.text_input("Referência de Pagamento / Nº de Comprovativo")
            duracao_reforco = st.selectbox(
                "Duração Pretendida", 
                options=[
                    "2 Horas - 12 Mil Kwanzas", 
                    "3 Horas - 15 Mil Kwanzas", 
                    "4 Horas - 20 Mil Kwanzas"
                ]
            )
            btn_sub_reforco = st.form_submit_button("Submeter Pedido de Reforço")
            if btn_sub_reforco:
                if not referencia_comprovativo:
                    st.error("Por favor, preencha a Referência de Pagamento / Nº de Comprovativo.")
                else:
                    dados_reforco = {
                        "token": provider_token,
                        "nome_prestador": nome_prestador,
                        "estabelecimento": estabelecimento,
                        "referencia": referencia_comprovativo,
                        "tempo_plano": duracao_reforco,
                        "approved": 0,
                        "data_registo": str(datetime.datetime.now())
                    }
                    try:
                        ref_id = str(uuid.uuid4())[:8]
                        requests.put(f"{FIREBASE_URL}/reforcos_pendentes/{provider_token}/{ref_id}.json", json=dados_reforco, timeout=10)
                        st.success("Pedido de reforço submetido com sucesso! Aguarde a confirmação do Administrador.")
                    except Exception as err:
                        st.error(f"Erro ao enviar reforço: {err}")

    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
    renderizar_gestao_fila_prestador(provider_token)
    
@st.fragment(run_every=1)
def renderizar_ecra_tv(provider_token):
    try:
        video_fundo_url = obter_video_fundo(provider_token)
        
        df_prov = get_all_providers()
        estabelecimento = "ESTABELECIMENTO"
        if not df_prov.empty and 'token' in df_prov.columns:
            match = df_prov[df_prov['token'] == provider_token]
            if not match.empty:
                row = match.iloc[0]
                estabelecimento = row.get('estabelecimento', row.get('nome_estabelecimento', 'ESTABELECIMENTO')).upper()

        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json?_t={time.time()}"
        response = requests.get(url_firebase, timeout=10)
        
        tocando_agora = None
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
            tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)

        st.markdown("""
            <style>
            .stApp {
                background: #000000 !important;
            }
            .video-background {
                position: fixed;
                right: 0;
                bottom: 0;
                min-width: 100%;
                min-height: 100%;
                z-index: 0;
                object-fit: cover;
            }
            .header-estabelecimento {
                position: fixed;
                top: 20px;
                right: 30px;
                z-index: 9999;
                background: rgba(0, 0, 0, 0.85);
                border: 2px solid #FFC107;
                padding: 10px 20px;
                border-radius: 8px;
                font-family: monospace;
                color: #FFC107;
                font-size: 16px;
                font-weight: bold;
                box-shadow: 0 0 15px rgba(255, 193, 7, 0.4);
            }
            .content-overlay {
                position: relative;
                z-index: 1;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 80vh;
                text-align: center;
            }
            .card-cantor {
                background: rgba(0, 0, 0, 0.85);
                border: 4px solid #FFC107;
                border-radius: 12px;
                padding: 30px 50px;
                box-shadow: 0 0 30px rgba(255, 193, 7, 0.5);
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="header-estabelecimento">📍 {estabelecimento}</div>', unsafe_allow_html=True)

        if video_fundo_url:
            st.markdown(f"""
                <video autoplay muted loop class="video-background">
                    <source src="{video_fundo_url}" type="video/mp4">
                    O seu navegador não suporta vídeos em HTML5.
                </video>
            """, unsafe_allow_html=True)

        st.markdown('<div class="content-overlay">', unsafe_allow_html=True)
        if tocando_agora:
            cantor = tocando_agora.get("cliente", "CONVIDADO").upper()
            musica = limpar_nome_musica(tocando_agora.get("musica", {}))
            st.markdown(f"""
                <div class="card-cantor">
                    <div style="font-family: monospace; color: #FFC107; font-size: 14px; letter-spacing: 2px; margin-bottom: 10px;">A CANTAR AGORA</div>
                    <div style="font-family: monospace; color: #FFC107; font-size: 48px; font-weight: bold; text-transform: uppercase; margin-bottom: 15px; text-shadow: 3px 3px 8px rgba(0,0,0,0.9);">
                        🎤 {cantor}
                    </div>
                    <div style="font-family: monospace; color: #ffffff; font-size: 22px; font-weight: bold; text-shadow: 2px 2px 6px rgba(0,0,0,0.9);">
                        🎵 {musica}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="card-cantor">
                    <div style="font-family: monospace; color: #FFC107; font-size: 28px; font-weight: bold;">
                        ⏳ AGUARDANDO PRÓXIMA MÚSICA...
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro ao carregar a tela de TV: {e}")

def show_client_screen_page(provider_token):
    renderizar_ecra_tv(provider_token)
    
def show_client_screen():
    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider", None)

    if not provider_token:
        st.error("Tela inválida. Falta o parâmetro do prestador.")
        return

    st.markdown("""
    <style>
    .stApp { background-color: #000000; color: white; }
    </style>""", unsafe_allow_html=True)

    renderizar_ecra_tv(provider_token)

def show_provider_panel_center(token):
    st.warning(f"Painel central para o token: {token}")

def show_admin_panel():
    st.info("Painel de administração geral ativo.")

def main():
    try:
        query_params = st.query_params
        
        if "page" in query_params and query_params["page"] == "register":
            custom_show_register_page()
            return

        if "page" in query_params and query_params["page"] == "client_register":
            show_client_page()
            return

        if "page" in query_params and query_params["page"] == "client_screen":
            show_client_screen()
            return

        token = query_params.get("prestador") or query_params.get("token") or query_params.get("provider")
        
        if token:
            df = get_all_providers()
            if df.empty or 'token' not in df.columns or not (df['token'] == token).any():
                show_provider_panel_center(token)
                return
                
            prior_prestador = df[df['token'] == token]
            if not prior_prestador.empty:
                row = prior_prestador.iloc[0]
                if row.get('approved', 1) == 1:
                    show_provider_panel_custom(token)
                    return
                else:
                    st.warning("⏳ O seu registo aguarda aprovação do Administrador.")
                    return
            else:
                show_provider_panel_custom(token)
                return
            
        st.markdown("""
            <style>
            .stApp {
                background-color: #000000 !important;
                color: #ffffff !important;
                font-weight: bold !important;
            }
            .block-container {
                background-color: #000000 !important;
                border: 4px solid #FFC107 !important;
                border-radius: 12px;
                padding: 3rem !important;
            }
            h1, h2, h3, h4, h5, h6, p, span, label, div, button, input {
                font-weight: bold !important;
                text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
            }
            </style>
        """, unsafe_allow_html=True)

        if not st.session_state.get("admin_logged", False):
            st.title("🔒 FFKaraoke - Área Restrita (Administrador)")
            with st.form("form_admin_login"):
                senha = st.text_input("Palavra-passe de Administrador", type="password")
                submitted = st.form_submit_button("Entrar")
                
                if submitted:
                    if senha == "ffkaraoke2026" or senha == "admin123":
                        st.session_state["admin_logged"] = True
                        st.success("Sessão iniciada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Palavra-passe incorreta.")

        if st.session_state.get("admin_logged", False):
            st.markdown("---")
            st.subheader("⚡ Gestão de Reforços de Tempo Pendentes")
            
            try:
                res_all_ref = requests.get(f"{FIREBASE_URL}/reforcos_pendentes.json", timeout=10)
                if res_all_ref.status_code == 200 and res_all_ref.json():
                    all_refs = res_all_ref.json()
                    tem_reforcos = False
                    
                    for tok, refs_dict in all_refs.items():
                        if isinstance(refs_dict, dict):
                            for r_id, r_data in refs_dict.items():
                                if r_data.get("approved", 0) == 0:
                                    tem_reforcos = True
                                    st.markdown(f"""
                                    <div style="background: rgba(0,0,0,0.95); border: 2px solid #FFC107; padding: 12px; border-radius: 6px; margin-bottom: 10px;">
                                        <b>Prestador:</b> {r_data.get('nome_prestador')} (Token: {tok})<br>
                                        <b>Referência / Comprovativo:</b> {r_data.get('referencia')}<br>
                                        <b>Duração Solicitada:</b> {r_data.get('tempo_plano')}
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    col_s, col_n = st.columns(2)
                                    with col_s:
                                        if st.button("✅ Aprovar Reforço", key=f"aprov_ref_{tok}_{r_id}"):
                                            r_data["approved"] = 1
                                            requests.put(f"{FIREBASE_URL}/reforcos_aprovados/{tok}/{r_id}.json", json=r_data)
                                            requests.delete(f"{FIREBASE_URL}/reforcos_pendentes/{tok}/{r_id}.json")
                                            st.success("Reforço aprovado e acumulado com sucesso!")
                                            st.rerun()
                                            
                                    with col_n:
                                        if st.button("❌ Recusar Reforço", key=f"rec_ref_{tok}_{r_id}"):
                                            requests.delete(f"{FIREBASE_URL}/reforcos_pendentes/{tok}/{r_id}.json")
                                            st.warning("Reforço recusado.")
                                            st.rerun()
                                            
                    if not tem_reforcos:
                        st.info("Nenhum pedido de reforço pendente neste momento.")
                else:
                    st.info("Nenhum pedido de reforço pendente neste momento.")
                    
            except Exception as e:
                st.warning(f"Não foi possível carregar os reforços pendentes: {e}")

            show_admin_panel()
                
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar a aplicação: {e}")

if __name__ == "__main__":
    main()
