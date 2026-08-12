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
import importlib

# --- 1. CONFIGURAR OS CAMINHOS PRIMEIRO ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

utils_path = os.path.join(current_dir, "utils")
if utils_path not in sys.path:
    sys.path.insert(0, utils_path)

modules_path = os.path.join(current_dir, "modules")
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

# --- 2. DEPOIS IMPORTAR OS MÓDULOS ---
from modules import prestador
importlib.reload(prestador)

# Configuração do Cloudinary com as credenciais oficiais
cloudinary.config(
    cloud_name="yhwgjh7g",
    api_key="852434629995691",
    api_secret="TU_ejil7wKYY15xHjDcRVfbk6Ow",
    secure=True
)

# Importações seguras com fallbacks para garantir robustez da aplicação
try:
    from utils.db_manager import init_db, get_all_providers, get_active_providers, approve_provider, get_total_revenue
except Exception:
    def init_db(): pass
    def get_all_providers(): 
        return pd.DataFrame(columns=['token', 'approved', 'data_registo', 'name', 'phone', 'payment_ref', 'amount_paid', 'expires_at'])
    def get_active_providers():
        return pd.DataFrame()
    def approve_provider(token): pass
    def get_total_revenue(): return 0.0

try:
    from modules.client import show_client_page
except Exception:
    def show_client_page(): st.error("Módulo 'modules.client' não encontrado.")

try:
    from modules.register import show_register_page as original_show_register_page
except Exception:
    original_show_register_page = None

# Funções auxiliares caso estejam noutros módulos
try:
    from modules.prestador import show_provider_panel_custom, show_provider_panel_center
except Exception:
    def show_provider_panel_custom(token): st.write("Painel personalizado do prestador")
    def show_provider_panel_center(token): show_provider_panel_custom(token)

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
        recusado = False
        
        try:
            df_prov = get_all_providers()
            if not df_prov.empty and 'token' in df_prov.columns:
                match = df_prov[df_prov['token'] == token_atual]
                if not match.empty:
                    estado = int(match.iloc[0].get('approved', 0))
                    if estado == 1:
                        aprovado = True
                    elif estado == -1:
                        recusado = True
        except Exception:
            pass

        # Se foi recusado pelo administrador
        if recusado:
            st.markdown(f"""
                <div style="text-align: center; padding: 40px; font-family: monospace;">
                    <h1 style="color: #ff3333; font-size: 38px; margin-bottom: 20px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">PEDIDO RECUSADO</h1>
                    <p style="color: #ffffff; font-size: 20px; font-weight: bold; margin-bottom: 30px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Lamentamos, mas o seu pedido de acesso foi recusado pelo Administrador.</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 Submeter Novo Registo", use_container_width=True):
                if "token_pendente_prestador" in st.session_state:
                    del st.session_state["token_pendente_prestador"]
                if "nome_pendente_prestador" in st.session_state:
                    del st.session_state["nome_pendente_prestador"]
                st.rerun()
            return

        # Se foi aprovado
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
        
        # Enquanto estiver pendente (Ecrã de espera isolado)
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
        
        # IMPORTANTE: O return garante que o código do formulário abaixo nunca é alcançado quando há token pendente
        return

    if "original_show_register_page" in globals() and original_show_register_page:
        try:
            original_show_register_page()
            return
        except Exception:
            pass

    # Formulário de Registo (só executa se NÃO houver token pendente na sessão)
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
                        requests.put(f"https://ffkaraoke-default-rtdb.firebaseio.com/prestadores_pendentes/{token_gerado}.json", json=dados_reg, timeout=10)
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

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import urllib.parse
import uuid

# Defina a sua URL do Firebase aqui
FIREBASE_URL = "https://SEU_FIREBASE_APP_ID.firebaseio.com"

# --- FUNÇÕES AUXILIARES ---
def get_all_providers():
    try:
        response = requests.get(f"{FIREBASE_URL}/providers.json", timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()
            return pd.DataFrame([{"id": k, **v} for k, v in data.items()])
    except Exception:
        pass
    return pd.DataFrame()

def get_active_providers():
    df = get_all_providers()
    if not df.empty and 'approved' in df.columns:
        return df[df['approved'].astype(int) == 1]
    return pd.DataFrame()

def get_total_revenue():
    df = get_all_providers()
    if not df.empty and 'amount_paid' in df.columns:
        total = 0
        for val in df['amount_paid']:
            try:
                num = ''.join(filter(str.isdigit, str(val)))
                if num:
                    total += float(num)
            except Exception:
                pass
        return total
    return 0.0

def limpar_nome_musica(musica_obj):
    if isinstance(musica_obj, dict):
        return musica_obj.get("titulo", musica_obj.get("name", "Música Desconhecida"))
    return str(musica_obj)

def atualizar_estado_pedido(provider_token, pedido_id, novo_estado):
    try:
        requests.patch(f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}.json", json={"estado": novo_estado}, timeout=10)
    except Exception:
        pass

def terminar_todas_musicas_ativas(provider_token, pedidos):
    for p in pedidos:
        if p.get("estado") == "aprovado":
            atualizar_estado_pedido(provider_token, p.get("id"), "terminado")

def obter_video_fundo(provider_token):
    try:
        resp = requests.get(f"{FIREBASE_URL}/config_video/{provider_token}.json", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return ""

def definir_video_fundo(provider_token, url_video):
    try:
        requests.put(f"{FIREBASE_URL}/config_video/{provider_token}.json", json=url_video, timeout=5)
    except Exception:
        pass

def listar_videos_pasta_clipes():
    # Exemplo estático ou integração Cloudinary
    return []

# --- FUNÇÃO DE APROVAÇÃO ROBUSTA ---
def approve_provider(token):
    try:
        encontrou = False
        dados_prestador = None
        
        for node in ["providers", "prestadores", "prestadores_pendentes"]:
            resp = requests.get(f"{FIREBASE_URL}/{node}.json", timeout=10)
            if resp.status_code == 200 and resp.json():
                dados = resp.json()
                for key, val in dados.items():
                    if isinstance(val, dict) and (val.get("token") == token or key == token):
                        dados_prestador = val
                        requests.patch(f"{FIREBASE_URL}/{node}/{key}.json", json={"approved": 1}, timeout=10)
                        encontrou = True
                        
        if dados_prestador:
            dados_prestador["approved"] = 1
            requests.put(f"{FIREBASE_URL}/providers/{token}.json", json=dados_prestador, timeout=10)
            requests.put(f"{FIREBASE_URL}/prestadores/{token}.json", json=dados_prestador, timeout=10)
        else:
            requests.patch(f"{FIREBASE_URL}/providers/{token}.json", json={"approved": 1}, timeout=10)
            requests.patch(f"{FIREBASE_URL}/prestadores/{token}.json", json={"approved": 1}, timeout=10)
            
        return True
    except Exception as e:
        st.error(f"Erro ao aprovar prestador: {e}")
        return False

# --- GESTÃO DA FILA DO PRESTADOR ---
@st.fragment(run_every=1)
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
        if not tocando_agora and pedidos_ativos:
            primeiro_id = pedidos_ativos[0].get('id')
            atualizar_estado_pedido(provider_token, primeiro_id, 'aprovado')
            pedidos_ativos[0]["estado"] = "aprovado"
            tocando_agora = pedidos_ativos[0]

        col_esq, col_dir = st.columns([1.5, 1], gap="medium")
        
        with col_esq:
            st.markdown("### 📋 Estado da Fila e Controlo de Reprodução")

            if pedidos_ativos:
                for idx, p in enumerate(pedidos_ativos, start=1):
                    titulo_musica = limpar_nome_musica(p.get("musica", {}))
                    cliente_nome = p.get("cliente", "Convidado").upper()
                    
                    c_num, c_cli, c_tit, c_btn = st.columns([0.5, 2, 4, 0.8])
                    with c_num:
                        st.markdown(f"<div style='background:#000; color:#FFC107; border:1px solid #FFC107; padding:6px; text-align:center; font-family:monospace; font-weight:bold; border-radius:4px;'>{idx}</div>", unsafe_allow_html=True)
                    with c_cli:
                        st.markdown(f"<div style='background:#000; color:#FFC107; border:1px solid #FFC107; padding:6px; font-family:monospace; font-weight:bold; border-radius:4px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;'>{cliente_nome}</div>", unsafe_allow_html=True)
                    with c_tit:
                        st.markdown(f"<div style='background:#000; color:#FFC107; border:1px solid #FFC107; padding:6px; font-family:monospace; font-weight:bold; border-radius:4px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;'>{titulo_musica}</div>", unsafe_allow_html=True)
                    with c_btn:
                        if st.button("✕", key=f"del_fila_{p.get('id')}", use_container_width=True):
                            atualizar_estado_pedido(provider_token, p.get('id'), 'terminado')
                            st.rerun()
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="background-color: #000000; border: 2px solid #FFC107; border-radius: 6px; padding: 12px; color: #FFC107; font-family: monospace; font-size: 13px; margin-bottom: 15px; text-align: center; font-weight: bold;">
                        NENHUM PEDIDO NA LISTA NESTE MOMENTO.<br>À ESPERA DE NOVOS PEDIDOS...
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("### LEITOR KARAOKE")
            
            if tocando_agora:
                cantor_atual = tocando_agora.get("cliente", "CONVIDADO").upper()
                musica_atual = limpar_nome_musica(tocando_agora.get("musica", {}))
                
                st.markdown(f"""
                    <div style="background: #000000; border: 3px solid #FFC107; border-radius: 6px; padding: 20px; margin-bottom: 15px; text-align: center;">
                        <div style="color: #FFC107; font-family: monospace; font-size: 32px; font-weight: bold; text-transform: uppercase; margin-bottom: 8px; text-shadow: 2px 2px 6px rgba(0,0,0,0.9);">
                            {cantor_atual}
                        </div>
                        <div style="color: #ffffff; font-family: monospace; font-size: 15px; font-weight: bold;">
                            {musica_atual}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                c_t1, c_t2, c_t3 = st.columns(3)
                with c_t1:
                    if st.button("▶️ Tocar o Karaoke", key=f"btn_tocar_{tocando_agora.get('id')}", use_container_width=True):
                        terminar_todas_musicas_ativas(provider_token, pedidos)
                        atualizar_estado_pedido(provider_token, tocando_agora.get('id'), 'aprovado')
                        st.rerun()
                with c_t2:
                    if st.button("⏹️ Parar o Karaoke", key=f"btn_parar_{tocando_agora.get('id')}", use_container_width=True):
                        terminar_todas_musicas_ativas(provider_token, pedidos)
                        st.rerun()
                with c_t3:
                    if st.button("⏭️ Avançar Karaoke", key=f"btn_prox_{tocando_agora.get('id')}", use_container_width=True):
                        atualizar_estado_pedido(provider_token, tocando_agora.get('id'), 'terminado')
                        restantes = [x for x in pedidos_ativos if x.get('id') != tocando_agora.get('id')]
                        if restantes:
                            atualizar_estado_pedido(provider_token, restantes[0].get('id'), 'aprovado')
                        st.rerun()
            else:
                st.markdown("""
                    <div style="background: #000000; border: 3px solid #FFC107; border-radius: 6px; padding: 20px; text-align: center; font-family: monospace; color: #FFC107; font-weight: bold;">
                        NENHUMA MÚSICA EM REPRODUÇÃO - À ESPERA DA FILA DE ESPERA
                    </div>
                """, unsafe_allow_html=True)

        with col_dir:
            st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
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

            with st.form(key="form_video_fundo_pos"):
                st.markdown("<div style='font-family: monospace; color: #ffffff; font-size: 13px; font-weight: bold; margin-bottom: 5px;'>Pesquisar Vídeo Clipe</div>", unsafe_allow_html=True)
                escolha_video = st.selectbox("Pesquisar Vídeo Clipe", options=opcoes_labels, index=index_atual, label_visibility="collapsed")
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                btn_salvar_fundo = st.form_submit_button("🎬 TOCAR VIDEO CLIP", use_container_width=True)
                if btn_salvar_fundo:
                    valor_a_guardar = "" if escolha_video == "Nenhum (Ecrã Preto)" else mapa_url_por_label.get(escolha_video, "")
                    definir_video_fundo(provider_token, valor_a_guardar)
                    st.success("Vídeo clipe de fundo atualizado e em reprodução na tela!")
                    st.rerun()
          
    except Exception as e:
        st.error(f"Erro ao carregar os pedidos do Firebase: {e}")

# --- PAINEL PERSONALIZADO DO PRESTADOR ---
def show_provider_panel_custom(provider_token):
    url_logotipo = "https://cdn.phototourl.com/free/2026-08-03-8b13edf5-0257-491d-ab78-f0d5329ffc15.jpg"
    url_fundo_painel = "https://cdn.phototourl.com/free/2026-08-03-694a4a2e-9914-4da8-93b2-87538a4805ab.png"

    df_prov = get_all_providers()
    nome_prestador = "CARLOS MIGUEL"
    tempo_plano = "2 Horas - 12 Mil Kwanzas"
    data_registo_str = None
    
    if not df_prov.empty and 'token' in df_prov.columns:
        match = df_prov[df_prov['token'] == provider_token]
        if not match.empty:
            row = match.iloc[0]
            nome_prestador = row.get('nome_prestador', row.get('nome', 'CARLOS MIGUEL')).upper()
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
        except Exception:
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
    }}</style>
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
                    <h1 style="margin: 0; color: #FFC107; font-family: monospace; font-size: 20px; text-transform: uppercase; font-weight: bold;">PAINEL DO PRESTADOR: <span style="color: #FFC107;">{nome_prestador}</span></h1>
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
                        "referencia": referencia_comprovativo,
                        "tempo_plano": duracao_reforco,
                        "approved": 0,
                        "data_registo": str(datetime.now())
                    }
                    try:
                        ref_id = str(uuid.uuid4())[:8]
                        requests.put(f"{FIREBASE_URL}/reforcos_pendentes/{provider_token}/{ref_id}.json", json=dados_reforco, timeout=10)
                        st.success("Aguarde a confirmação do Administrador.")
                    except Exception as err:
                        st.error(f"Erro ao enviar reforço: {err}")

    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
    renderizar_gestao_fila_prestador(provider_token)

# --- PAINEL DE ADMINISTRAÇÃO ---
def show_admin_panel():
    st.markdown("""
    <style>
    .stApp {
        background: url('https://cdn.phototourl.com/free/2026-08-03-694a4a2e-9914-4da8-93b2-87538a4805ab.png') no-repeat center center fixed !important;
        background-size: cover !important;
        color: #ffffff !important;
        font-weight: bold !important;
    }
    .block-container {
        background-color: rgba(0, 0, 0, 0.75) !important;
        border: 4px solid #FFC107 !important;
        border-radius: 12px;
        padding: 3rem !important;
    }
    .link-box {
        background: rgba(17, 17, 17, 0.9);
        border: 1px solid #D4AF37;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        color: white !important;
    }
    .link-box b, .link-box a {
        color: #FFD700 !important;
    }
    .badge-pendente-global {
        background-color: #ff3333;
        color: #ffffff;
        padding: 9px 21px;
        border-radius: 50%;
        font-weight: 900;
        font-size: 24px;
        display: inline-block;
        box-shadow: 0px 0px 14px rgba(255, 51, 51, 0.7);
        text-align: center;
        min-width: 52px;
    }
    p, span, label, h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
    }
    </style>
    """, unsafe_allow_html=True)

    df_all = get_all_providers()
    
    pendentes_count = 0
    if not df_all.empty and 'approved' in df_all.columns:
        pendentes_count = len(df_all[df_all['approved'].astype(int) == 0])

    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.subheader("🛠️ Painel de Administração — FF Karaoke")
    with col_t2:
        if pendentes_count > 0:
            st.markdown(f"⏳ <span class='badge-pendente-global'>{pendentes_count}</span>", unsafe_allow_html=True)
        else:
            st.markdown("✅ Sem Pendentes", unsafe_allow_html=True)
            
    st.markdown("---")

    aba1, aba2, aba3, aba4 = st.tabs([
        "🔗 Link e QR Registo", 
        "⏳ Pedidos e Aprovação", 
        "📊 Gestão Total", 
        "📈 Relatórios e Estatísticas"
    ])

    with aba1:
        st.subheader("🔗 Portal de Auto-Registo de Prestadores")
        base_url = "https://appadm.streamlit.app/?page=register"
        col_l, col_q = st.columns([3, 1])
        with col_l:
            st.markdown(f"""
            <div class="link-box">
                <b>Link Direto de Registo:</b><br>
                <a href="{base_url}" target="_blank" style="color: #FFD700; font-size: 16px;">{base_url}</a>
            </div>
            """, unsafe_allow_html=True)
        with col_q:
            qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={base_url}"
            st.image(qr_api_url, width=140, caption="QR Code de Registo")

    with aba2:
        st.subheader("📋 Pedidos de Registo Pendentes")
        if df_all.empty:
            st.info("Nenhum prestador registado na base de dados.")
        else:
            pendentes = df_all[df_all['approved'].astype(int) == 0]
            if pendentes.empty:
                st.success("Não existem novos pedidos de registo pendentes.")
            else:
                for index, row in pendentes.iterrows():
                    nome = row.get('name', row.get('nome', 'Desconhecido'))
                    telefone = row.get('phone', 'N/A')
                    estabelecimento = row.get('estabelecimento', row.get('venue', 'N/A'))
                    payment_ref = row.get('payment_ref', 'N/A')
                    amount_paid = row.get('amount_paid', 'N/A')
                    expires_at = row.get('expires_at', 'N/A')
                    token = row.get('token', row.get('id', ''))
                    
                    col_info1, col_info2, col_info3 = st.columns([3, 2, 2])
                    with col_info1:
                        st.markdown(f"🎤 **{nome}**<br>📞 {telefone} | 🏠 {estabelecimento}", unsafe_allow_html=True)
                    with col_info2:
                        st.markdown(f"Ref: {payment_ref} ({amount_paid})", unsafe_allow_html=True)
                    with col_info3:
                        if st.button("✅ Aprovar", key=f"btn_aprov_{token}"):
                            if approve_provider(token):
                                st.success(f"Prestador {nome} aprovado!")
                                time.sleep(1)
                                st.rerun()
                    st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

    with aba3:
        st.subheader("📑 Gestão Total de Prestadores Ativos")
        df_active = get_active_providers()
        if df_active.empty:
            st.info("Nenhum prestador com sessão ativa no momento.")
        else:
            st.dataframe(df_active, use_container_width=True, hide_index=True)

    with aba4:
        st.subheader("📈 Relatórios Financeiros")
        total_recebido = get_total_revenue()
        st.metric(label="💳 Total Geral Faturado", value=f"{total_recebido:,.2f} Kz")

# --- FUNÇÃO PRINCIPAL ---
def main():
    try:
        query_params = st.query_params
        
        token = query_params.get("prestador") or query_params.get("token") or query_params.get("provider")
        
        if token:
            prestador_encontrado = None
            
            # Consulta direta ao Firebase para evitar atrasos de cache
            for node in ["providers", "prestadores", "prestadores_pendentes"]:
                resp = requests.get(f"{FIREBASE_URL}/{node}/{token}.json", timeout=5)
                if resp.status_code == 200 and resp.json():
                    prestador_encontrado = resp.json()
                    break
            
            if not prestador_encontrado:
                df = get_all_providers()
                if not df.empty and 'token' in df.columns:
                    match = df[df['token'] == token]
                    if not match.empty:
                        prestador_encontrado = match.iloc[0].to_dict()

            if prestador_encontrado:
                status_aprov = int(prestador_encontrado.get('approved', 0))
                if status_aprov == 1:
                    show_provider_panel_custom(token)
                    return
                elif status_aprov == -1:
                    st.error("❌ O seu registo foi recusado pelo Administrador.")
                    return
                else:
                    st.warning("⏳ O seu registo aguarda aprovação do Administrador. Esta página atualizará automaticamente assim que for aprovado.")
                    time.sleep(4)
                    st.rerun()
                    return
            else:
                st.warning("Token de prestador não encontrado na base de dados.")
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
            </style>
        """, unsafe_allow_html=True)

        if not st.session_state.get("admin_logged", False):
            st.title("🔒 FFKaraoke - (Administrador)")
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
            show_admin_panel()
                
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar a aplicação: {e}")

if __name__ == "__main__":
    main()
