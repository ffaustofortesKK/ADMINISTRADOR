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
        return pd.DataFrame(columns=['token', 'approved', 'data_registo'])

try:
    from modules.admin import show_admin_panel
except Exception:
    def show_admin_panel(): st.error("Módulo 'modules.admin' não encontrado.")

try:
    from modules.register import show_register_page
except Exception:
    def show_register_page(): st.error("Módulo 'modules.register' não encontrado.")

try:
    from modules.client import show_client_page
except Exception:
    def show_client_page(): st.error("Módulo 'modules.client' não encontrado.")

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
                <div style="background-color: #0b0b0b; border: 2px solid #FFC107; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
                    <div style="color: #4CAF50; font-family: monospace; font-size: 15px; font-weight: bold; margin-bottom: 5px;">Confirmação de Pedido</div>
                    <div style="color: #FFC107; font-family: monospace; font-size: 18px; font-weight: bold; margin-bottom: 10px;">QUER CANTAR</div>
            """, unsafe_allow_html=True)
            
            for p in pendentes:
                titulo_p = limpar_nome_musica(p.get("musica", {}))
                cliente_p = p.get("cliente", "Convidado")
                st.markdown(f"""
                    <div style="color: #ffffff; font-family: monospace; font-size: 15px; margin-bottom: 15px;">
                        <b>{titulo_p}</b> <span style="color: #aaa; font-size: 13px;">({cliente_p})</span>
                    </div>
                """, unsafe_allow_html=True)
                
                col_btn_sim, col_btn_nao = st.columns(2)
                with col_btn_sim:
                    if st.button("✅", key=f"conf_sim_{p.get('id')}", use_container_width=True):
                        terminar_todas_musicas_ativas(provider_token, pedidos)
                        atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                        st.success(f"Música '{titulo_p}' enviada para a tela!")
                        st.rerun()
                with col_btn_nao:
                    if st.button("❌", key=f"conf_nao_{p.get('id')}", use_container_width=True):
                        atualizar_estado_pedido(provider_token, p.get('id'), 'terminado')
                        st.warning("Pedido recusado/cancelado.")
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        col_fila, col_botoes = st.columns([3, 1])
        
        with col_fila:
            if pedidos_ativos:
                html_lista = '<div style="background-color: #050505; border: 2px solid #FFC107; padding: 15px; border-radius: 8px; color: #ffffff; width: 100%; font-family: monospace; font-size: 15px; margin-bottom: 20px;">'
                html_lista += '<div style="color: #FFC107; font-weight: bold; margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px;">ESTADO DA FILA:</div>'
                for idx, p in enumerate(pedidos_ativos, start=1):
                    titulo_musica = limpar_nome_musica(p.get("musica", {}))
                    cliente_nome = p.get("cliente", "Convidado")
                    estado_atual = p.get("estado")
                    badge = "🎵 [A Tocar]" if estado_atual == "aprovado" else "⏳ [Pendente]"
                    cor_badge = "#4CAF50" if estado_atual == "aprovado" else "#FFC107"
                    html_lista += f'<div style="padding: 6px 0; border-bottom: 1px solid #222;"><b>{idx}.</b> {titulo_musica} <span style="color:#aaa; font-size:13px;">({cliente_nome})</span> <span style="color:{cor_badge}; font-size:12px; float:right;">{badge}</span></div>'
                html_lista += '</div>'
                st.markdown(html_lista, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="background-color: #050505; border: 2px solid #FFC107; border-radius: 8px; padding: 15px; color: #FFC107; width: 100%; font-family: monospace; font-size: 14px; margin-top: 15px; margin-bottom: 20px;">
                        <div>NENHUM PEDIDO NA LISTA NESTE MOMENTO.<br>À ESPERA DE NOVOS PEDIDOS...</div>
                    </div>
                """, unsafe_allow_html=True)

        with col_botoes:
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            if tocando_agora:
                if st.button("⏹️ Terminar", key=f"term_top_{tocando_agora.get('id')}", use_container_width=True):
                    terminar_todas_musicas_ativas(provider_token, pedidos)
                    st.success("Música terminada!")
                    st.rerun()

        if tocando_agora:
            titulo_tocando = limpar_nome_musica(tocando_agora.get("musica", {}))
            st.success(f"🎵 A tocar agora: **{titulo_tocando}** (Cliente: {tocando_agora.get('cliente', 'Convidado')})")
            col_s1, col_s2 = st.columns([1, 1])
            with col_s1:
                if st.button("⏹️ Terminar Música Atual", key=f"term_{tocando_agora.get('id')}"):
                    terminar_todas_musicas_ativas(provider_token, pedidos)
                    st.success("Música terminada e tela limpa com sucesso!")
                    st.rerun()
            with col_s2:
                if st.button("🛑 Stop Geral", key=f"stop_{tocando_agora.get('id')}"):
                    terminar_todas_musicas_ativas(provider_token, pedidos)
                    definir_video_fundo(provider_token, "")
                    st.warning("Reprodução parada (Stop) com sucesso!")
                    st.rerun()

        st.markdown("---")
        st.markdown("### 🎬 Configuração de Vídeo Clipe de Fundo (Tela)")
        
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
                "SELECIONE O VÍDEO CLIPE DA PASTA 'CLIPES':", 
                options=opcoes_labels, 
                index=index_atual
            )

            btn_salvar_fundo = st.form_submit_button("PESQUISAR")
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
    st.markdown("""
    <style>
    .stApp {
        background-color: #0b0b0b;
        color: #ffffff;
    }
    .panel-header {
        display: flex;
        align-items: center;
        gap: 15px;
        border-bottom: 2px solid #FFC107;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .card-link {
        background: linear-gradient(90deg, #0d1b2a 0%, #1b263b 100%);
        border: 2px solid #FFC107;
        border-radius: 10px;
        padding: 18px 25px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(255, 193, 7, 0.15);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .card-tv {
        background: linear-gradient(90deg, #1f1a24 0%, #2e1a38 100%);
        border: 2px solid #9c27b0;
        border-radius: 10px;
        padding: 18px 25px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(156, 39, 176, 0.15);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .qr-box {
        background: #000;
        border: 2px solid #FFC107;
        border-radius: 8px;
        padding: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .link-title {
        font-family: monospace;
        color: #FFC107;
        font-size: 24px;
        font-weight: bold;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .link-text {
        font-family: monospace;
        color: #3a86ff;
        font-size: 15px;
        text-decoration: underline;
    }
    .link-text-tv {
        font-family: monospace;
        color: #b5179e;
        font-size: 15px;
        text-decoration: underline;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="panel-header">
            <span style="font-size: 32px;">🎤</span>
            <div>
                <h1 style="margin: 0; color: #FFC107; font-family: monospace; font-size: 26px; text-transform: uppercase;">PAINEL DO PRESTADOR — FF KARAOKE</h1>
                <p style="margin: 5px 0 0 0; color: #aaa; font-size: 13px; font-family: monospace;">TOKEN ATIVO: <code style="background: #222; color: #4CAF50; padding: 2px 6px; border-radius: 4px;">{provider_token}</code></p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    link_cliente_rel = f"/?page=client_register&prestador={provider_token}"
    link_tv_rel = f"/?page=client_screen&prestador={provider_token}"
    
    host_dominio = st.context.headers.get('Host', 'grupoffkaraoke.streamlit.app')
    link_cliente_absoluto = f"https://{host_dominio}{link_cliente_rel}"
    link_tv_absoluto = f"https://{host_dominio}{link_tv_rel}"
    
    qr_url_cliente = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={urllib.parse.quote(link_cliente_absoluto)}"

    col_qr1, col_card1 = st.columns([1, 5])
    with col_qr1:
        st.markdown(f"""
            <div class="qr-box">
                <img src="{qr_url_cliente}" width="100" style="border-radius: 4px;" />
            </div>
        """, unsafe_allow_html=True)
    with col_card1:
        st.markdown(f"""
            <div class="card-link">
                <div class="link-title">LINK DO CLIENTE</div>
                <a href="{link_cliente_rel}" target="_blank" class="link-text">{link_cliente_rel}</a>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    st.markdown(f"""
        <div class="card-tv">
            <div class="link-title" style="color: #b5179e;">LINK DA TV</div>
            <a href="{link_tv_rel}" target="_blank" class="link-text-tv">{link_tv_rel}</a>
        </div>
    """, unsafe_allow_html=True)

    renderizar_gestao_fila_prestador(provider_token)

@st.fragment(run_every=3)
def renderizar_ecra_tv(provider_token):
    try:
        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json?_t={time.time()}"
        response = requests.get(url_firebase, timeout=10)
        
        pedidos_ativos = []
        tocando_agora = None
        
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
            tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)
        
        frame_styles = """
            <style>
                @keyframes pulseSpeaker {
                    0% { transform: scale(1); filter: drop-shadow(0 0 2px #FFC107); }
                    50% { transform: scale(1.12); filter: drop-shadow(0 0 14px #FFC107); }
                    100% { transform: scale(1); filter: drop-shadow(0 0 2px #FFC107); }
                }
                @keyframes bounceIcon {
                    0%, 100% { transform: translateY(0) rotate(0deg); }
                    50% { transform: translateY(-5px) rotate(10deg); }
                }
                @keyframes marqueeFast {
                    0% { transform: translateX(0%); }
                    100% { transform: translateX(-50%); }
                }
                .speaker-box {
                    position: fixed;
                    z-index: 99998;
                    width: 90px;
                    height: 140px;
                    background: #111;
                    border: 3px solid #FFC107;
                    border-radius: 10px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: space-around;
                    padding: 8px 0;
                    box-shadow: 0 0 15px rgba(255, 193, 7, 0.4);
                    pointer-events: none;
                    animation: pulseSpeaker 0.55s infinite ease-in-out;
                }
                .woofer {
                    width: 55px;
                    height: 55px;
                    border: 3px solid #FFC107;
                    border-radius: 50%;
                    background: radial-gradient(circle, #333 30%, #000 90%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: inset 0 0 8px #FFC107;
                }
                .woofer-inner {
                    width: 22px;
                    height: 22px;
                    background: #FFC107;
                    border-radius: 50%;
                }
                
                .speaker-tl { top: 15px; left: 15px; }
                .speaker-tr { top: 15px; right: 15px; }
                .speaker-bl { bottom: 50px; left: 15px; }
                .speaker-br { bottom: 50px; right: 15px; }

                .marquee-footer {
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    width: 100vw;
                    height: 38px;
                    background: #111;
                    border-top: 2px solid #FFC107;
                    z-index: 99997;
                    overflow: hidden;
                    display: flex;
                    align-items: center;
                    white-space: nowrap;
                    pointer-events: none;
                }
                .marquee-track {
                    display: inline-block;
                    white-space: nowrap;
                    animation: marqueeFast 15s linear infinite;
                    font-family: monospace;
                    font-size: 16px;
                    color: #FFC107;
                    font-weight: bold;
                }
                .marquee-item {
                    display: inline-flex;
                    align-items: center;
                    gap: 12px;
                    margin-right: 40px;
                }
                .icon-anim {
                    display: inline-block;
                    animation: bounceIcon 0.8s infinite ease-in-out;
                }
            </style>

            <div class="speaker-box speaker-tl">
                <div class="woofer"><div class="woofer-inner"></div></div>
                <div class="woofer"><div class="woofer-inner"></div></div>
            </div>
            <div class="speaker-box speaker-tr">
                <div class="woofer"><div class="woofer-inner"></div></div>
                <div class="woofer"><div class="woofer-inner"></div></div>
            </div>
            <div class="speaker-box speaker-bl">
                <div class="woofer"><div class="woofer-inner"></div></div>
                <div class="woofer"><div class="woofer-inner"></div></div>
            </div>
            <div class="speaker-box speaker-br">
                <div class="woofer"><div class="woofer-inner"></div></div>
                <div class="woofer"><div class="woofer-inner"></div></div>
            </div>

            <div class="marquee-footer">
                <div class="marquee-track">
                    <span class="marquee-item"><span class="icon-anim">🎵</span> FF KARAOKE CLOUD <span class="icon-anim">🎤</span> CANTE COMIGO <span class="icon-anim">🎶</span> A SUA MÚSICA FAVORITA <span class="icon-anim">🎙️</span> DIVIRTA-SE AO MÁXIMO</span>
                    <span class="marquee-item"><span class="icon-anim">🎵</span> FF KARAOKE CLOUD <span class="icon-anim">🎤</span> CANTE COMIGO <span class="icon-anim">🎶</span> A SUA MÚSICA FAVORITA <span class="icon-anim">🎙️</span> DIVIRTA-SE AO MÁXIMO</span>
                </div>
            </div>
        """

        if tocando_agora:
            musica = tocando_agora.get("musica", {})
            if isinstance(musica, dict):
                titulo = musica.get("titulo", musica.get("nome", "Karaoke"))
                url_video = musica.get("url_cloudinary", "") or musica.get("url", "")
            else:
                titulo = str(musica)
                url_video = ""
            
            titulo_limpo = limpar_nome_musica(titulo)
            url_video = obter_url_video_cloudinary(musica, titulo_limpo)

            video_html = f"""
            <style>
                body, html {{
                    margin: 0;
                    padding: 0;
                    background: #000;
                    overflow: hidden;
                    width: 100vw;
                    height: 100vh;
                }}
                @keyframes zoomInNumber {{
                    0% {{ transform: scale(0.2); opacity: 0; }}
                    50% {{ transform: scale(1.2); opacity: 1; }}
                    100% {{ transform: scale(1); opacity: 1; }}
                }}
                .countdown-overlay {{
                    position: fixed;
                    top: 0; left: 0; width: 100vw; height: 100vh;
                    background: rgba(0,0,0,0.95);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 99999;
                    color: #FFC107;
                    font-family: monospace;
                    font-size: 15vw;
                    font-weight: bold;
                    animation: zoomInNumber 0.9s ease-in-out infinite;
                }}
            </style>

            <div id="countdown-screen" class="countdown-overlay">3</div>

            <div id="karaoke-container" style="display: none; width: 100vw; height: 100vh; background: black; position: fixed; top: 0; left: 0;">
                <video id="karaoke-player" width="100%" height="100%" autoplay playsinline controlslist="nodownload noremoteplayback" disablepictureinpicture style="object-fit: contain; background: black; width: 100%; height: 100%;">
                    <source src="{url_video}" type="video/mp4">
                    O seu navegador não suporta a reprodução deste vídeo.
                </video>
                <div id="audio-warning" style="display: none; position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); text-align: center; background: #222; border: 2px solid #FFC107; padding: 10px 20px; border-radius: 5px; z-index: 99999;">
                    <p style="color: #FFC107; margin: 0 0 8px 0; font-family: monospace; font-size: 14px;">⚠️ O navegador bloqueou o áudio automático.</p>
                    <button onclick="unmuteVideo()" style="background-color: #4CAF50; color: white; border: none; padding: 8px 16px; font-size: 15px; border-radius: 4px; cursor: pointer; font-weight: bold;">🔊 CLIQUE AQUI PARA ATIVAR O SOM</button>
                </div>
            </div>

            <script>
                var count = 3;
                var cdScreen = document.getElementById('countdown-screen');
                
                var timer = setInterval(function() {{
                    count--;
                    if (count > 0) {{
                        cdScreen.innerText = count;
                    }} else if (count === 0) {{
                        cdScreen.innerText = "🎤 CANTE!";
                    }} else {{
                        clearInterval(timer);
                        cdScreen.style.display = 'none';
                        document.getElementById('karaoke-container').style.display = 'block';
                        
                        var video = document.getElementById('karaoke-player');
                        video.muted = false; 
                        var playPromise = video.play();
                        
                        if (playPromise !== undefined) {{
                            playPromise.then(_ => {{}}).catch(error => {{
                                video.muted = true;
                                video.play();
                                document.getElementById('audio-warning').style.display = 'block';
                            }});
                        }}
                    }}
                }}, 1000);

                function unmuteVideo() {{
                    var video = document.getElementById('karaoke-player');
                    video.muted = false;
                    video.play();
                    document.getElementById('audio-warning').style.display = 'none';
                }}

                function stopKaraoke() {{
                    var pedidoId = "{tocando_agora.get('id')}";
                    var token = "{provider_token}";
                    var firebaseURL = "{FIREBASE_URL}/pedidos/" + token + "/" + pedidoId + "/estado.json";
                    
                    fetch(firebaseURL, {{
                        method: 'PUT',
                        body: JSON.stringify('terminado'),
                        headers: {{ 'Content-Type': 'application/json' }}
                    }}).then(response => {{
                        setTimeout(function() {{ window.location.reload(); }}, 300);
                    }}).catch(err => {{
                        window.location.reload();
                    }});
                }}

                var video = document.getElementById('karaoke-player');
                if (video) {{
                    video.onended = function() {{
                        stopKaraoke();
                    }};
                }}
            </script>
            """
            components.html(video_html, height=750, scrolling=False)
            
        else:
            url_clipe_fundo = obter_video_fundo(provider_token)
            proximo_cantor = pedidos_ativos[0] if pedidos_ativos else None

            st.markdown(frame_styles, unsafe_allow_html=True)

            col_esq, col_dir = st.columns([1, 1])
            
            with col_esq:
                if proximo_cantor:
                    c_prox = proximo_cantor.get("cliente", "Convidado")
                    st.markdown(f"""
                        <div style="border: 2px solid #FFC107; border-radius: 10px; padding: 15px; background: #111; margin-bottom: 15px; display: flex; align-items: center; gap: 15px;">
                            <span style="color: #FFC107; font-size: 20px; font-weight: bold; font-family: monospace;">Á SEGUIR</span>
                            <span style="color: #ffffff; font-size: 20px; font-weight: bold; font-family: monospace; text-transform: uppercase;">{c_prox}</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div style="border: 2px solid #FFC107; border-radius: 10px; padding: 15px; text-align: center; background: #111; margin-bottom: 15px;">
                            <h2 style="color: #FFC107; margin: 0; font-family: monospace;">🎤 FILA DE ESPERA VAZIA</h2>
                        </div>
                    """, unsafe_allow_html=True)
                
                html_caixas = '<div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 40px;">'
                demais_pedidos = pedidos_ativos[1:] if len(pedidos_ativos) > 1 else []
                
                for idx, p_item in enumerate(demais_pedidos, start=2):
                    c_item = p_item.get("cliente", "Convidado")
                    texto_caixa = f"<b>{idx}.</b> {c_item}"
                    html_caixas += f'<div style="background: #111; border: 2px solid #FFC107; border-radius: 8px; padding: 12px; color: #fff; font-family: monospace; font-size: 16px;">{texto_caixa}</div>'
                
                html_caixas += '</div>'
                st.markdown(html_caixas, unsafe_allow_html=True)

            with col_dir:
                if url_clipe_fundo:
                    video_fundo_html = f"""
                    <div style="display: flex; justify-content: center; background: black; border: 2px solid #FFC107; border-radius: 10px; padding: 5px; width: 100%; position: relative; margin-top: 5px; margin-bottom: 40px;">
                        <video id="fundo-player" width="100%" height="450px" controls autoplay loop playsinline controlslist="nodownload noremoteplayback" disablepictureinpicture style="object-fit: contain; background: black; border-radius: 8px;">
                            <source src="{url_clipe_fundo}" type="video/mp4">
                            O seu navegador não suporta vídeo.
                        </video>
                        <div id="fundo-audio-warning" style="display: none; position: absolute; bottom: 15px; right: 15px; background: rgba(0,0,0,0.8); border: 1px solid #FFC107; padding: 6px 10px; border-radius: 5px; cursor: pointer;" onclick="unmuteFundo()">
                            <span style="font-size: 18px;" title="Ativar Som">🔊</span>
                        </div>
                    </div>
                    <script>
                        var fundoVideo = document.getElementById('fundo-player');
                        fundoVideo.muted = false;
                        var fundoPromise = fundoVideo.play();
                        if (fundoPromise !== undefined) {{
                            fundoPromise.then(_ => {{}}).catch(error => {{
                                fundoVideo.muted = true;
                                fundoVideo.play();
                                document.getElementById('fundo-audio-warning').style.display = 'block';
                            }});
                        }}
                        function unmuteFundo() {{
                            fundoVideo.muted = false;
                            fundoVideo.play();
                            document.getElementById('fundo-audio-warning').style.display = 'none';
                        }}
                    </script>
                    """
                    components.html(video_fundo_html, height=480)
                else:
                    st.markdown("""
                        <div style="border: 2px solid #FFC107; border-radius: 10px; padding: 100px 20px; text-align: center; background: #000; color: #FFC107; font-family: monospace; margin-top: 5px; margin-bottom: 40px;">
                            <div style="font-size: 40px; margin-bottom: 10px;">📺</div>
                            <p style="color: #aaa; font-size: 16px; margin: 0;">Aguardando o prestador selecionar um vídeo clipe no painel de controle...</p>
                        </div>
                    """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro de sincronização na TV: {e}")

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
    show_provider_panel_custom(token)

def main():
    try:
        query_params = st.query_params
        
        if "page" in query_params and query_params["page"] == "register":
            show_register_page()
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
            
        if not st.session_state.get("admin_logged", False):
            st.title("🔒 FFKaraoke - Área Restrita")
            
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
