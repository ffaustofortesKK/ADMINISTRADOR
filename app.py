import sys
import os
import time
import datetime
from datetime import datetime, timedelta
import requests
import urllib.parse
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import cloudinary
import cloudinary.api
import cloudinary.uploader
import cloudinary.search

# Configuração estrita do caminho absoluto para evitar erros de importação
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

utils_path = os.path.join(current_dir, "utils")
if utils_path not in sys.path:
    sys.path.insert(0, utils_path)

modules_path = os.path.join(current_dir, "modules")
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

# Configuração do Cloudinary com as credenciais oficiais
cloudinary.config(
    cloud_name="yhwgjh7g",
    api_key="852434629995691",
    api_secret="TU_ejil7wKYY15xHjDcRVfbk6Ow",
    secure=True
)

# Importações seguras com fallbacks para garantir robustez da aplicação
try:
    from utils.db_manager import init_db, get_all_providers
except Exception:
    def init_db(): pass
    def get_all_providers(): 
        return pd.DataFrame(columns=['token', 'approved', 'data_registo', 'nome_prestador', 'tempo_plano'])

try:
    from modules.admin import show_admin_panel
except Exception:
    def show_admin_panel(): st.error("Módulo 'modules.admin' não encontrado.")

try:
    from modules.client import show_client_page
except Exception:
    def show_client_page(): st.error("Módulo 'modules.client' não encontrado.")

try:
    from modules.register import show_register_page as original_show_register_page
except Exception:
    original_show_register_page = None

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

st.set_page_config(
    page_title="FFKaraoke - Gestão de Acessos",
    page_icon="🎤",
    layout="wide"
)

# --- BLOQUEIO TOTAL E RADICAL DO BOTÃO GERENCIAR APLICATIVO E ELEMENTOS CLOUD ---
st.markdown("""
    <style>
    div[data-testid="stToolbar"], header, footer, 
    div[data-testid="stDecoration"], #MainMenu, 
    .stAppViewerBadge, div[class*="viewerBadge"], 
    iframe[src*="analytics"], div[class*="settings"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    </style>

    <script>
    function annihilateManageButton() {
        const walkDOM = (node) => {
            if (node.shadowRoot) {
                walkDOM(node.shadowRoot);
            }
            let children = node.children || node.childNodes;
            for (let i = 0; i < children.length; i++) {
                let child = children[i];
                if (child.nodeType === 1) {
                    let text = child.innerText || child.textContent || "";
                    let titleAttr = child.getAttribute ? (child.getAttribute('title') || '') : '';
                    let ariaLabel = child.getAttribute ? (child.getAttribute('aria-label') || '') : '';
                    
                    if (
                        text.includes("Gerenciar") || 
                        text.includes("Manage app") || 
                        text.includes("Hosted with") ||
                        titleAttr.includes("Manage app") ||
                        ariaLabel.includes("Manage app")
                    ) {
                        let target = child.closest('div[style*="position: fixed"]') || child.parentElement || child;
                        target.remove();
                    }
                    walkDOM(child);
                }
            }
        };
        walkDOM(document.body);
    }
    setInterval(annihilateManageButton, 300);
    </script>
""", unsafe_allow_html=True)

try:
    init_db()
except Exception:
    pass

def custom_show_register_page():
    url_fundo_painel = "https://cdn.phototourl.com/free/2026-08-03-694a4a2e-9914-4da8-93b2-87538a4805ab.png"
    url_logotipo = "https://cdn.phototourl.com/free/2026-08-03-8b13edf5-0257-491d-ab78-f0d5329ffc15.jpg"
    
    st.markdown(f"""
    <style>
    .stApp {{
        background: url("{url_fundo_painel}") no-repeat center center fixed !important;
        background-size: cover !important;
    }}
    
    .block-container {{
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
        padding-left: 4rem !important;
        padding-right: 4rem !important;
        background: rgba(0, 0, 0, 0.90) !important;
        border-radius: 12px;
        margin-top: 2rem;
        margin-bottom: 2rem;
        border: 4px solid #FFC107 !important;
        color: #ffffff !important;
    }}

    h1, h2, h3, h4, h5, h6, p, label, span, div {{
        color: #ffffff !important;
        font-weight: bold !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
    }}
    
    .stTextInput input, .stSelectbox select, div[data-baseweb="select"] {{
        background-color: #111111 !important;
        color: #ffffff !important;
        border: 2px solid #FFC107 !important;
        font-weight: bold !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    if "token_pendente_prestador" in st.session_state and st.session_state["token_pendente_prestador"]:
        token_atual = st.session_state["token_pendente_prestador"]
        nome_prestador_temp = st.session_state.get("nome_pendente_prestador", "Prestador")
        
        aprovado = False
        try:
            df_prov = get_all_providers()
            if not df_prov.empty and 'token' in df_prov.columns:
                match = df_prov[df_prov['token'] == token_atual]
                if not match.empty:
                    if int(match.iloc[0].get('approved', 0)) == 1:
                        aprovado = True
        except Exception:
            pass

        if aprovado:
            st.markdown(f"""
                <div style="text-align: center; padding: 40px; font-family: monospace;">
                    <h1 style="color: #FFC107; font-size: 38px; margin-bottom: 20px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">SEJA BEM VINDO, {nome_prestador_temp.upper()}!</h1>
                    <p style="color: #ffffff; font-size: 20px; font-weight: bold; margin-bottom: 30px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">O seu registo foi aprovado com sucesso!</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 Entrar no Painel", use_container_width=True):
                st.query_params["prestador"] = token_atual
                if "token_pendente_prestador" in st.session_state:
                    del st.session_state["token_pendente_prestador"]
                st.rerun()
            return
        
        st.markdown(f"""
            <style>
            @keyframes spinMic {{
                0% {{ transform: rotate(0deg) scale(1); }}
                50% {{ transform: rotate(180deg) scale(1.15); filter: drop-shadow(0 0 15px #FFC107); }}
                100% {{ transform: rotate(360deg) scale(1); }}
            }}
            @keyframes marqueeWait {{
                0% {{ transform: translateX(100vw); }}
                100% {{ transform: translateX(-100%); }}
            }}
            .waiting-container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 30px 20px;
                text-align: center;
                font-family: monospace;
            }}
            .logo-wait {{
                width: 130px;
                height: 130px;
                border-radius: 50%;
                border: 4px solid #FFC107;
                object-fit: cover;
                margin-bottom: 25px;
                box-shadow: 0 0 25px rgba(255, 193, 7, 0.4);
            }}
            .mic-spinning {{
                font-size: 70px;
                display: inline-block;
                animation: spinMic 2.5s infinite linear;
                margin: 20px 0;
            }}
            .wait-footer {{
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100vw;
                background: #111;
                border-top: 4px solid #FFC107;
                padding: 12px 0;
                z-index: 99999;
                overflow: hidden;
                white-space: nowrap;
            }}
            .wait-track {{
                display: inline-block;
                white-space: nowrap;
                animation: marqueeWait 18s linear infinite;
                color: #FFC107;
                font-size: 16px;
                font-weight: bold;
                font-family: monospace;
                text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
            }}
            </style>

            <div class="waiting-container">
                <img src="{url_logotipo}" class="logo-wait" />
                <h2 style="color: #FFC107; margin-bottom: 10px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">REGISTO SUBMETIDO COM SUCESSO!</h2>
                <p style="color: #ffffff; font-size: 15px; max-width: 600px; margin: 0 auto; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Aguardando validação e aprovação pelo Administrador...</p>
                <div class="mic-spinning">🎤</div>
                <p style="color: #ffffff; font-size: 14px; margin-top: 15px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Token do Pedido: <b>{token_atual}</b></p>
            </div>

            <div class="wait-footer">
                <div class="wait-track">
                    Seja bem vindo ao Grupo FF Karaoke, aguarde aprovação do seu registo ou ligue para 921204050 para confirmar. &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; • &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Seja bem vindo ao Grupo FF Karaoke, aguarde aprovação do seu registo ou ligue para 921204050 para confirmar.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        time.sleep(3)
        st.rerun()
        return

    if original_show_register_page:
        try:
            original_show_register_page()
            return
        except Exception:
            pass

    st.markdown("<h1>🎤 FFKaraoke - Registo de Prestador</h1>", unsafe_allow_html=True)
    st.markdown("<p>Preencha os seus dados e escolha a duração pretendida para solicitar o seu acesso.</p>", unsafe_allow_html=True)
    
    with st.form("form_registo_prestador_custom"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome")
        with col2:
            sobrenome = st.text_input("Sobrenome")
            
        telefone = st.text_input("Número de Telefone")
        duracao = st.selectbox(
            "Duração Pretendida", 
            options=[
                "2 Horas - 12 Mil Kwanzas", 
                "3 Horas - 15 Mil Kwanzas", 
                "4 Horas - 20 Mil Kwanzas"
            ]
        )
        
        submitted = st.form_submit_button("Enviar Permissão")
        if submitted:
            if not nome or not telefone:
                st.error("Por favor, preencha todos os campos obrigatórios.")
            else:
                referencia_fake = "Plano Selecionado Direto"
                try:
                    from utils.db_manager import save_provider_request
                    token_gerado = save_provider_request(nome, sobrenome, telefone, referencia_fake, duracao)
                    st.session_state["token_pendente_prestador"] = token_gerado
                    st.session_state["nome_pendente_prestador"] = f"{nome} {sobrenome}".strip()
                    st.rerun()
                except Exception as e:
                    import uuid
                    token_gerado = str(uuid.uuid4())[:8]
                    nome_completo = f"{nome} {sobrenome}".strip()
                    dados_reg = {
                        "nome_prestador": nome_completo,
                        "telefone": telefone,
                        "referencia": referencia_fake,
                        "tempo_plano": duracao,
                        "approved": 0,
                        "token": token_gerado,
                        "data_registo": str(datetime.now())
                    }
                    try:
                        requests.put(f"{FIREBASE_URL}/prestadores_pendentes/{token_gerado}.json", json=dados_reg, timeout=10)
                        st.session_state["token_pendente_prestador"] = token_gerado
                        st.session_state["nome_pendente_prestador"] = nome_completo
                        st.rerun()
                    except Exception as err:
                        st.error(f"Erro ao submeter registo: {err}")

def atualizar_estado_pedido(provider_token, pedido_id, novo_estado):
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}/estado.json"
        response = requests.put(url, json=novo_estado, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

def terminar_todas_musicas_ativas(provider_token, pedidos):
    for p in pedidos:
        if p.get("estado") in ["aprovado", "pendente"]:
            atualizar_estado_pedido(provider_token, p.get("id"), "terminado")

def definir_video_fundo(provider_token, url_clipe):
    try:
        url = f"{FIREBASE_URL}/config/{provider_token}/video_fundo.json"
        requests.put(url, json=url_clipe, timeout=10)
    except Exception:
        pass

def obter_video_fundo(provider_token):
    try:
        url = f"{FIREBASE_URL}/config/{provider_token}/video_fundo.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json() or ""
    except Exception:
        pass
    return ""

def listar_videos_pasta_clipes():
    videos_encontrados = []
    try:
        resultado = cloudinary.search.Search()\
            .expression('resource_type:video AND asset_folder=clipes')\
            .max_results(500)\
            .execute()
            
        for recurso in resultado.get("resources", []):
            url_secure = recurso.get("secure_url", "")
            if url_secure:
                if "/upload/" in url_secure and "f_auto,q_auto" not in url_secure:
                    url_secure = url_secure.replace("/upload/", "/upload/f_auto,q_auto/")
                
                filename = recurso.get("filename", "")
                public_id = recurso.get("public_id", "")
                nome_amigavel = filename if filename else public_id.split("/")[-1]
                
                videos_encontrados.append({"nome": nome_amigavel, "url": url_secure})
    except Exception as e:
        try:
            resultado_alt = cloudinary.api.resources(
                resource_type="video",
                type="upload",
                max_results=500
            )
            for recurso in resultado_alt.get("resources", []):
                public_id = recurso.get("public_id", "")
                if "clipes" in public_id.lower():
                    url_secure = recurso.get("secure_url", "")
                    if url_secure:
                        if "/upload/" in url_secure and "f_auto,q_auto" not in url_secure:
                            url_secure = url_secure.replace("/upload/", "/upload/f_auto,q_auto/")
                        nome_amigavel = public_id.split("/")[-1]
                        videos_encontrados.append({"nome": nome_amigavel, "url": url_secure})
        except Exception as err:
            print(f"Erro crítico ao listar vídeos do Cloudinary: {err}")
            
    return videos_encontrados

def limpar_nome_musica(musica_raw):
    if isinstance(musica_raw, dict):
        titulo = musica_raw.get("titulo", musica_raw.get("nome", "Karaoke"))
    else:
        titulo = str(musica_raw)
    
    titulo = titulo.strip('"\'')
    if titulo.lower().endswith('.cdg'):
        titulo = titulo[:-4]
    return titulo.strip()

def obter_url_video_cloudinary(musica_obj, titulo_limpo):
    if isinstance(musica_obj, dict):
        url_direta = musica_obj.get("url_cloudinary", "") or musica_obj.get("url", "")
        if url_direta and "http" in url_direta:
            if "res.cloudinary.com" in url_direta and "/upload/" in url_direta and "f_auto,q_auto" not in url_direta:
                return url_direta.replace("/upload/", "/upload/f_auto,q_auto/")
            return url_direta

    cloud_name = "yhwgjh7g"
    encoded_title = urllib.parse.quote(titulo_limpo + ".mp4")
    return f"https://res.cloudinary.com/{cloud_name}/video/upload/f_auto,q_auto/{encoded_title}"

@st.fragment(run_every=3)
def renderizar_gestao_fila_prestador(provider_token):
    try:
        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json?_t={time.time()}"
        response = requests.get(url_firebase, timeout=10)
        
        pedidos = []
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            
        pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
        pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
        
        tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)
        pendentes = [p for p in pedidos_ativos if p.get("estado") == "pendente"]

        if pendentes:
            st.markdown("""
                <div style="background-color: rgba(0,0,0,0.95); border: 4px solid #FFC107; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
                    <div style="color: #ffffff; font-family: monospace; font-size: 15px; font-weight: bold; margin-bottom: 5px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Confirmação de Pedido</div>
                    <div style="color: #ffffff; font-family: monospace; font-size: 18px; font-weight: bold; margin-bottom: 10px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">QUER CANTAR</div>
            """, unsafe_allow_html=True)
            
            for p in pendentes:
                titulo_p = limpar_nome_musica(p.get("musica", {}))
                cliente_p = p.get("cliente", "Convidado")
                st.markdown(f"""
                    <div style="color: #ffffff; font-family: monospace; font-size: 15px; margin-bottom: 15px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">
                        <b>{titulo_p}</b> <span style="color: #ffffff; font-size: 13px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">({cliente_p})</span>
                    </div>
                """, unsafe_allow_html=True)
                
                col_btn_dummy1, col_center_btn, col_btn_dummy2 = st.columns([1, 1.2, 1])
                with col_center_btn:
                    if st.button("✅ Sim", key=f"conf_sim_{p.get('id')}", use_container_width=True):
                        terminar_todas_musicas_ativas(provider_token, pedidos)
                        atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                        st.success(f"Música '{titulo_p}' enviada para a tela!")
                        st.rerun()
                    if st.button("❌ Não", key=f"conf_nao_{p.get('id')}", use_container_width=True):
                        atualizar_estado_pedido(provider_token, p.get('id'), 'terminado')
                        st.warning("Pedido recusado/cancelado.")
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 📋 Estado da Fila e Controlo de Reprodução")

        if pedidos_ativos:
            for idx, p in enumerate(pedidos_ativos, start=1):
                titulo_musica = limpar_nome_musica(p.get("musica", {}))
                cliente_nome = p.get("cliente", "Convidado")
                estado_atual = p.get("estado")
                
                is_playing = (estado_atual == "aprovado")
                cor_borda = "#4CAF50" if is_playing else "#FFC107"
                badge_texto = "🎵 A TOCAR AGORA" if is_playing else f"⏳ Fila #{idx}"
                
                with st.container():
                    st.markdown(f"""
                        <div style="background: rgba(0,0,0,0.95); border: 4px solid {cor_borda}; border-radius: 8px; padding: 12px 15px; margin-bottom: 10px; font-family: monospace;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="color: #ffffff; font-weight: bold; font-size: 14px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">{badge_texto}</span>
                                <span style="color: #ffffff; font-size: 13px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Cliente: <b>{cliente_nome}</b></span>
                            </div>
                            <div style="color: #ffffff; font-size: 16px; font-weight: bold; margin-bottom: 8px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">
                                🎶 {titulo_musica}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col_acao1, col_acao2, col_acao3 = st.columns(3)
                    with col_acao1:
                        if not is_playing:
                            if st.button("▶️ Tocar Agora", key=f"play_linha_{p.get('id')}", use_container_width=True):
                                terminar_todas_musicas_ativas(provider_token, pedidos)
                                atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                                st.success(f"A avançar para: {titulo_musica}")
                                st.rerun()
                    with col_acao2:
                        if is_playing:
                            if st.button("⏹️ Terminar Atual", key=f"term_linha_{p.get('id')}", use_container_width=True):
                                terminar_todas_musicas_ativas(provider_token, pedidos)
                                st.success("Música terminada!")
                                st.rerun()
                    with col_acao3:
                        if st.button("❌ Remover", key=f"rem_linha_{p.get('id')}", use_container_width=True):
                            atualizar_estado_pedido(provider_token, p.get('id'), 'terminado')
                            st.warning("Música removida da fila.")
                            st.rerun()
                    st.markdown("<hr style='margin: 5px 0 15px 0; border-color: #333;'>", unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background-color: rgba(0,0,0,0.95); border: 4px solid #FFC107; border-radius: 8px; padding: 15px; color: #ffffff; width: 100%; font-family: monospace; font-size: 14px; margin-bottom: 20px; text-align: center; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">
                    NENHUM PEDIDO NA LISTA NESTE MOMENTO.<br>À ESPERA DE NOVOS PEDIDOS...
                </div>
            """, unsafe_allow_html=True)

        if tocando_agora:
            if st.button("🛑 Stop Geral (Limpar Tela)", key="stop_geral_btn", use_container_width=True):
                terminar_todas_musicas_ativas(provider_token, pedidos)
                definir_video_fundo(provider_token, "")
                st.warning("Reprodução parada e tela limpa com sucesso!")
                st.rerun()

        st.markdown("---")
        
        video_fundo_atual = obter_video_fundo(provider_token)
        lista_clipes_cloudinary = listar_videos_pasta_clipes()
        
        opcoes_labels = ["Nenhum (Ecrã Preto)"]
        mapa_url_por_label = {}
        
        for clipe in lista_clipes_cloudinary:
            label = f"📁 {clipe['nome']}"
            opcoes_labels.append(label)
            mapa_url_por_label[label] = clipe['url']
            
        index_atual = 0
        for idx, label in enumerate(opcoes_labels):
            if label != "Nenhum (Ecrã Preto)":
                url_mapeada = mapa_url_por_label.get(label, "")
                if video_fundo_atual and (video_fundo_atual in url_mapeada or url_mapeada in video_fundo_atual):
                    index_atual = idx
                    break

        with st.form(key="form_video_fundo"):
            escolha_video = st.selectbox(
                "Pesquisar Vídeo Clipe", 
                options=opcoes_labels, 
                index=index_atual
            )

            st.markdown("""
                <style>
                div[data-testid="stFormSubmitButton"] button {
                    background-color: #4CAF50 !important;
                    color: white !important;
                    border: 2px solid #2E7D32 !important;
                }
                div[data-testid="stFormSubmitButton"] button:hover {
                    background-color: #43A047 !important;
                }
                </style>
            """, unsafe_allow_html=True)

            btn_salvar_fundo = st.form_submit_button("Pesquisar Vídeo Clipe")
            if btn_salvar_fundo:
                if escolha_video == "Nenhum (Ecrã Preto)":
                    valor_a_guardar = ""
                else:
                    valor_a_guardar = mapa_url_por_label.get(escolha_video, "")
                    
                definir_video_fundo(provider_token, valor_a_guardar)
                st.success("Vídeo clipe de fundo iniciado com sucesso na tela!")
                st.rerun()
            
    except Exception as e:
        st.error(f"Erro ao carregar os pedidos do Firebase: {e}")

def show_provider_panel_custom(provider_token):
    url_logotipo = "https://cdn.phototourl.com/free/2026-08-03-8b13edf5-0257-491d-ab78-f0d5329ffc15.jpg"
    url_fundo_painel = "https://cdn.phototourl.com/free/2026-08-03-694a4a2e-9914-4da8-93b2-87538a4805ab.png"

    df_prov = get_all_providers()
    nome_prestador = "Prestador"
    tempo_plano = "2 Horas - 12 Mil Kwanzas"
    data_registo_str = None
    
    if not df_prov.empty and 'token' in df_prov.columns:
        match = df_prov[df_prov['token'] == provider_token]
        if not match.empty:
            row = match.iloc[0]
            nome_prestador = row.get('nome_prestador', row.get('nome', 'Prestador'))
            tempo_plano = row.get('tempo_plano', row.get('tempo', '2 Horas - 12 Mil Kwanzas'))
            data_registo_str = row.get('data_registo', None)

    segundos_bónus = 0
    try:
        res_ref = requests.get(f"{FIREBASE_URL}/reforcos_aprovados/{provider_token}.json", timeout=5)
        if res_ref.status_code == 200 and res_ref.json():
            dados_ref = res_ref.json()
            if isinstance(dados_ref, dict):
                for r_id, r_info in dados_ref.items():
                    t_ref = r_info.get("tempo_plano", "")
                    if "3 Horas" in t_ref:
                        segundos_bónus += 10800
                    elif "4 Horas" in t_ref:
                        segundos_bónus += 14400
                    elif "2 Horas" in t_ref:
                        segundos_bónus += 7200
    except Exception:
        pass

    segundos_base = 7200
    if "3 Horas" in tempo_plano:
        segundos_base = 10800
    elif "4 Horas" in tempo_plano:
        segundos_base = 14400
    elif "2 Horas" in tempo_plano:
        segundos_base = 7200

    segundos_totais = segundos_base + segundos_bónus
    segundos_restantes = segundos_totais
    
    if data_registo_str:
        try:
            dt_str_clean = data_registo_str.split('.')[0]
            try:
                dt_reg = datetime.strptime(dt_str_clean, "%Y-%m-%d %H:%M:%S")
            except Exception:
                dt_reg = datetime.fromisoformat(data_registo_str.replace('Z', '+00:00').split('+')[0])
                
            diff = (datetime.now() - dt_reg).total_seconds()
            segundos_restantes = max(0, int(segundos_totais - diff))
        except Exception as e:
            print(f"Erro ao calcular tempo restante: {e}")
            pass

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
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
        padding-left: 5rem !important;
        padding-right: 5rem !important;
        background: rgba(0, 0, 0, 0.90) !important;
        border-radius: 12px;
        margin-top: 2rem;
        margin-bottom: 2rem;
        border: 4px solid #FFC107 !important;
    }}

    .panel-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 4px solid #FFC107;
        padding-bottom: 12px;
        margin-bottom: 20px;
        position: relative;
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
        border: 4px solid #FFC107 !important;
        border-radius: 8px;
        padding: 12px 15px;
        text-align: left;
        box-shadow: 0 4px 15px rgba(255, 193, 7, 0.25);
        margin-bottom: 15px;
        display: block;
        width: 100%;
        max-width: 100%;
    }}
    .card-tv {{
        border: 4px solid #9c27b0 !important;
        box-shadow: 0 4px 15px rgba(156, 39, 176, 0.25);
    }}

    .qr-box {{
        background: #000;
        border: 4px solid #FFC107 !important;
        border-radius: 8px;
        padding: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
    }}
    
    .link-title {{
        font-family: monospace;
        color: #ffffff !important;
        font-size: 15px;
        font-weight: bold !important;
        margin-bottom: 4px;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.9) !important;
    }}
    .link-title-tv {{
        font-family: monospace;
        color: #ffffff !important;
        font-size: 15px;
        font-weight: bold !important;
        margin-bottom: 4px;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.9) !important;
    }}
    .link-text {{
        font-family: monospace;
        color: #ffffff !important;
    }}
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
            
    else:
        # Se for um prestador com token na query string ou fluxo normal
        prestador_token = st.query_params.get("prestador", "")
        if prestador_token:
            show_provider_panel_custom(prestador_token)
        else:
            custom_show_register_page()

def main():
    prestador_token = st.query_params.get("prestador", "")
    if prestador_token:
        show_provider_panel_custom(prestador_token)
    else:
        custom_show_register_page()

if __name__ == "__main__":
    main()
