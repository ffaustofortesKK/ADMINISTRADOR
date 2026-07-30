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

# Configuração do Cloudinary com as suas credenciais oficiais
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

        col_fila, col_botoes = st.columns([3, 1])
        
        with col_fila:
            if pedidos_ativos:
                html_lista = '<div style="background-color: #111111; border: 2px solid #FFC107; padding: 15px; border-radius: 8px; color: #ffffff; width: 100%; font-family: monospace; font-size: 15px; margin-bottom: 20px;">'
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
                    <div style="background-color: #111111; border: 2px solid #FFC107; border-radius: 8px; padding: 15px; color: #FFC107; width: 100%; font-family: monospace; font-size: 15px; margin-bottom: 20px;">
                        <div>NENHUM PEDIDO NA LISTA NESTE MOMENTO.<br>À ESPERA DE NOVOS PEDIDOS...</div>
                    </div>
                """, unsafe_allow_html=True)

        with col_botoes:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if tocando_agora:
                if st.button("⏹️ Terminar", key=f"term_top_{tocando_agora.get('id')}", use_container_width=True):
                    terminar_todas_musicas_ativas(provider_token, pedidos)
                    st.success("Música terminada!")
                    st.rerun()
            
            for p in pendentes:
                titulo_p = limpar_nome_musica(p.get("musica", {}))
                if st.button("▶️ Play", key=f"btn_play_side_{p.get('id')}", use_container_width=True):
                    terminar_todas_musicas_ativas(provider_token, pedidos)
                    atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                    st.success(f"Música '{titulo_p}' enviada para a tela!")
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

        # --- SECÇÃO DE PEDIDOS EXTRA DE MÚSICA PARA O PRESTADOR ---
        st.markdown("---")
        st.markdown("### 📥 Aba de Pedidos Extra de Música (Cliente não encontrou)")
        try:
            res_extras = requests.get(f"{FIREBASE_URL}/pedidos_extras/{provider_token}.json", timeout=10)
            if res_extras.status_code == 200 and res_extras.json():
                extras_data = res_extras.json()
                for extra_id, extra_val in extras_data.items():
                    if extra_val.get("estado") == "pendente":
                        c_nome = extra_val.get("cliente", "Cliente")
                        mus_pedida = extra_val.get("musica", "")
                        st.markdown(f"""
                            <div style="background: #111; border: 2px solid #FFC107; border-radius: 8px; padding: 12px; margin-bottom: 10px; font-family: monospace;">
                                <b>Cliente:</b> {c_nome} | <b>Música Extra Solicitada:</b> <span style="color: #4CAF50;">{mus_pedida}</span>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        col_bt1, col_bt2 = st.columns(2)
                        with col_bt1:
                            if st.button("🟩 Confirmar (Disponível/Outro local)", key=f"btn_verde_{extra_id}", use_container_width=True):
                                requests.put(f"{FIREBASE_URL}/pedidos_extras/{provider_token}/{extra_id}/estado.json", json="confirmado")
                                st.success("Pedido extra confirmado!")
                                st.rerun()
                        with col_bt2:
                            if st.button("🟥 Não temos (Aviso ao Cliente)", key=f"btn_vermelho_{extra_id}", use_container_width=True):
                                requests.put(f"{FIREBASE_URL}/pedidos_extras/{provider_token}/{extra_id}/estado.json", json="nao_temos")
                                st.success("Mensagem de indispobilidade enviada ao cliente com sucesso!")
                                st.rerun()
            else:
                st.info("Nenhum pedido extra pendente no momento.")
        except Exception as err:
            st.warning(f"Erro ao carregar pedidos extras: {err}")

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

            btn_salvar_fundo = st.form_submit_button("▶️ PLAY VÍDEO CLIPE DE FUNDO")
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
        border-radius: 12px;
        padding: 15px 20px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 15px rgba(255, 193, 7, 0.15);
    }
    .card-tv {
        background: linear-gradient(90deg, #1f1a24 0%, #2e1a38 100%);
        border: 2px solid #9c27b0;
        border-radius: 12px;
        padding: 15px 20px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 15px rgba(156, 39, 176, 0.15);
    }
    .link-text {
        font-family: monospace;
        color: #FFC107;
        font-size: 14px;
        text-decoration: none;
    }
    .link-text-tv {
        font-family: monospace;
        color: #e1bee7;
        font-size: 14px;
        text-decoration: none;
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
    qr_url_cliente = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={urllib.parse.quote(link_cliente_absoluto)}"

    col_links, col_qr = st.columns([3, 1])
    
    with col_links:
        st.markdown(f"""
            <div class="card-link">
                <div>
                    <div style="font-weight: bold; color: #fff; font-family: monospace; margin-bottom: 4px; font-size: 15px;">👥 LINK DO CLIENTE</div>
                    <a href="{link_cliente_rel}" target="_blank" class="link-text">{link_cliente_rel}</a>
                </div>
            </div>
            <div class="card-tv">
                <div>
                    <div style="font-weight: bold; color: #fff; font-family: monospace; margin-bottom: 4px; font-size: 15px;">📺 LINK DA TV</div>
                    <a href="{link_tv_rel}" target="_blank" class="link-text-tv">{link_tv_rel}</a>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_qr:
        st.markdown("""
            <div style="background: #111; border: 2px solid #FFC107; border-radius: 12px; padding: 10px; text-align: center; box-shadow: 0 4px 15px rgba(255, 193, 7, 0.2);">
        """, unsafe_allow_html=True)
        st.image(qr_url_cliente, width=135, caption="")
        st.markdown("<div style='color: #FFC107; font-family: monospace; font-size: 12px; font-weight: bold; margin-top: 5px;'>QR CODE CLIENTE</div></div>", unsafe_allow_html=True)

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
                    count -= 1;
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
            
            host_dominio = st.context.headers.get('Host', 'grupoffkaraoke.streamlit.app')
            link_cliente_absoluto = f"https://{host_dominio}/?page=client_register&prestador={provider_token}"
            qr_url_cliente = f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={urllib.parse.quote(link_cliente_absoluto)}"
            
            fila_nomes_html = ""
            for idx, p in enumerate(pedidos_ativos[:5], start=1):
                t_musica = limpar_nome_musica(p.get("musica", {}))
                c_nome = p.get("cliente", "Convidado")
                fila_nomes_html += f'<div style="padding: 8px 0; border-bottom: 1px solid rgba(255,193,7,0.2); font-size: 18px; color: #fff;"><b>{idx}.</b> {t_musica} <span style="color: #FFC107; font-size: 15px;">({c_nome})</span></div>'

            if not fila_nomes_html:
                fila_nomes_html = '<div style="color: #888; font-style: italic; padding: 10px 0; font-size: 16px;">A fila está vazia. Seja o primeiro a pedir!</div>'

            ecra_espera_html = f"""
            <style>
                body, html {{
                    margin: 0;
                    padding: 0;
                    background: #0b0b0b;
                    overflow: hidden;
                    width: 100vw;
                    height: 100vh;
                    font-family: monospace;
                }}
                .bg-video {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw;
                    height: 100vh;
                    object-fit: cover;
                    z-index: 1;
                    opacity: 0.45;
                }}
                .bg-overlay {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw;
                    height: 100vh;
                    background: radial-gradient(circle, rgba(11,11,11,0.4) 0%, rgba(11,11,11,0.85) 100%);
                    z-index: 2;
                }}
                .content-container {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw;
                    height: 100vh;
                    z-index: 3;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    padding: 30px 50px;
                    box-sizing: border-box;
                }}
                .header-tv {{
                    text-align: center;
                    border-bottom: 3px solid #FFC107;
                    padding-bottom: 15px;
                    background: rgba(17,17,17,0.75);
                    border-radius: 12px;
                    backdrop-filter: blur(5px);
                }}
                .main-grid {{
                    display: flex;
                    gap: 40px;
                    justify-content: space-between;
                    align-items: center;
                    flex: 1;
                    margin: 20px 0;
                }}
                .box-card {{
                    background: rgba(17, 17, 17, 0.85);
                    border: 3px solid #FFC107;
                    border-radius: 16px;
                    padding: 25px;
                    box-shadow: 0 8px 32px rgba(255, 193, 7, 0.25);
                    backdrop-filter: blur(8px);
                }}
            </style>

            {f'<video class="bg-video" autoplay muted loop playsinline><source src="{url_clipe_fundo}" type="video/mp4"></video>' if url_clipe_fundo else ''}
            <div class="bg-overlay"></div>

            <div class="content-container">
                <div class="header-tv">
                    <h1 style="color: #FFC107; margin: 0; font-size: 38px; text-transform: uppercase; letter-spacing: 2px;">🎤 FF KARAOKE CLOUD 🎶</h1>
                    <p style="color: #ccc; margin: 5px 0 0 0; font-size: 18px;">ESANCAE SEU QR CODE, ESCOLHA SUA MÚSICA E VENHA CANTAR!</p>
                </div>

                <div class="main-grid">
                    <div class="box-card" style="flex: 1.2; text-align: center;">
                        <h2 style="color: #FFC107; margin-top: 0; font-size: 26px; border-bottom: 2px solid #333; padding-bottom: 10px;">📱 ESCANEI PARA PEDIR</h2>
                        <img src="{qr_url_cliente}" style="width: 230px; height: 230px; border-radius: 10px; border: 4px solid #FFC107; padding: 5px; background: white; margin: 10px 0;" />
                        <p style="color: #fff; font-size: 15px; margin: 5px 0 0 0; word-break: break-all;"><b>{link_cliente_absoluto}</b></p>
                    </div>

                    <div class="box-card" style="flex: 1.8; height: 100%; display: flex; flex-direction: column; justify-content: flex-start;">
                        <h2 style="color: #FFC107; margin-top: 0; font-size: 26px; border-bottom: 2px solid #333; padding-bottom: 10px;">📋 PRÓXIMOS NA FILA</h2>
                        <div style="flex-direction: column; display: flex;">
                            {fila_nomes_html}
                        </div>
                    </div>
                </div>
            </div>

            {frame_styles}
            """
            components.html(ecra_espera_html, height=750, scrolling=False)

    except Exception as e:
        st.error(f"Erro no ecrã da TV: {e}")

# --- CONTROLO DE ROTAS DA APLICAÇÃO ---
query_params = st.query_params
pagina_atual = query_params.get("page", "home")
prestador_token_param = query_params.get("prestador", "")

if pagina_atual == "admin_login":
    show_admin_panel()
elif pagina_atual == "client_register":
    if prestador_token_param:
        show_register_page(prestador_token_param)
    else:
        st.error("Token do prestador não fornecido no link.")
elif pagina_atual == "client_screen":
    if prestador_token_param:
        renderizar_ecra_tv(prestador_token_param)
    else:
        st.error("Token do prestador não fornecido para a TV.")
else:
    # Página inicial / Painel do Prestador ou Login Rápido
    st.markdown("""
        <div style="text-align: center; padding: 40px 0;">
            <h1 style="color: #FFC107; font-family: monospace; font-size: 36px;">🎤 FF KARAOKE CLOUD</h1>
            <p style="color: #aaa; font-family: monospace; font-size: 16px;">Plataforma inteligente de gestão e pedidos de karaoke</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        token_input = st.text_input("INSIRA O SEU TOKEN DE PRESTADOR:", type="password")
        if st.button("ACEDER AO PAINEL", use_container_width=True):
            if token_input.strip():
                # Verificar se o token existe na base de dados ou redirecionar
                st.query_params["page"] = "provider_panel"
                st.query_params["prestador"] = token_input.strip()
                st.rerun()
            else:
                st.warning("Por favor, insira um token válido.")
                
        if prestador_token_param or pagina_atual == "provider_panel":
            token_ativo = prestador_token_param or token_input
            if token_ativo:
                show_provider_panel_custom(token_ativo)
