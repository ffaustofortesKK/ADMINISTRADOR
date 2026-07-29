import sys
import os

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

import time
import requests
import urllib.parse
import streamlit as st
import streamlit.components.v1 as components
import cloudinary
import cloudinary.api
import cloudinary.uploader
import cloudinary.search

# Configuração do Cloudinary com as suas credenciais oficiais
cloudinary.config(
    cloud_name="yhwgjh7g",
    api_key="852434629995691",
    api_secret="TU_ejil7wKYY15xHjDcRVfbk6Ow",
    secure=True
)

# Importações seguras com fallbacks para evitar crash total da aplicação
try:
    from utils.db_manager import init_db, get_all_providers
except Exception:
    def init_db(): pass
    def get_all_providers(): 
        import pandas as pd
        return pd.DataFrame(columns=['token', 'approved'])

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
    """Lista todos os vídeos disponíveis na conta Cloudinary com estratégia tripla de resiliência."""
    videos_encontrados = []
    urls_vistas = set()
    
    # 1. Pesquisa por Search API
    try:
        resultado = cloudinary.search.Search()\
            .expression('resource_type:video')\
            .max_results(500)\
            .execute()
            
        for recurso in resultado.get("resources", []):
            url_secure = recurso.get("secure_url", "")
            public_id = recurso.get("public_id", "")
            if url_secure and url_secure not in urls_vistas:
                if "/upload/" in url_secure and "f_auto,q_auto" not in url_secure:
                    url_secure = url_secure.replace("/upload/", "/upload/f_auto,q_auto/")
                filename = recurso.get("filename", "")
                nome_amigavel = filename if filename else public_id.split("/")[-1]
                urls_vistas.add(url_secure)
                videos_encontrados.append({"nome": nome_amigavel, "url": url_secure, "public_id": public_id})
    except Exception:
        pass

    # 2. Pesquisa por Admin API (resources)
    try:
        resultado_alt = cloudinary.api.resources(
            resource_type="video",
            type="upload",
            max_results=500
        )
        for recurso in resultado_alt.get("resources", []):
            url_secure = recurso.get("secure_url", "")
            public_id = recurso.get("public_id", "")
            if url_secure and url_secure not in urls_vistas:
                if "/upload/" in url_secure and "f_auto,q_auto" not in url_secure:
                    url_secure = url_secure.replace("/upload/", "/upload/f_auto,q_auto/")
                nome_amigavel = public_id.split("/")[-1]
                urls_vistas.add(url_secure)
                videos_encontrados.append({"nome": nome_amigavel, "url": url_secure, "public_id": public_id})
    except Exception:
        pass

    # 3. Pesquisa por sub-pastas específicas (caso os ficheiros estejam organizados em pastas no Cloudinary)
    try:
        pastas = ["clip", "clips", "videos", "fundo"]
        for pasta in pastas:
            try:
                res_pasta = cloudinary.api.resources_by_prefix(
                    prefix=f"{pasta}/",
                    resource_type="video",
                    max_results=100
                )
                for recurso in res_pasta.get("resources", []):
                    url_secure = recurso.get("secure_url", "")
                    public_id = recurso.get("public_id", "")
                    if url_secure and url_secure not in urls_vistas:
                        if "/upload/" in url_secure and "f_auto,q_auto" not in url_secure:
                            url_secure = url_secure.replace("/upload/", "/upload/f_auto,q_auto/")
                        nome_amigavel = public_id.split("/")[-1]
                        urls_vistas.add(url_secure)
                        videos_encontrados.append({"nome": nome_amigavel, "url": url_secure, "public_id": public_id})
            except Exception:
                continue
    except Exception:
        pass
          
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
            "Selecione o Vídeo Clipe disponível no Cloudinary:", 
            options=opcoes_labels, 
            index=index_atual
        )

        btn_salvar_fundo = st.form_submit_button("💾 Atualizar Vídeo Clipe de Fundo")
        if btn_salvar_fundo:
            if escolha_video == "Nenhum (Ecrã Preto)":
                valor_a_guardar = ""
            else:
                valor_a_guardar = mapa_url_por_label.get(escolha_video, "")
                
            definir_video_fundo(provider_token, valor_a_guardar)
            st.success("Vídeo clipe de fundo atualizado com sucesso para a tela!")
            st.rerun()

    if not lista_clipes_cloudinary:
        st.warning("⚠️ Nenhum vídeo foi retornado pelo Cloudinary. Verifique se os vídeos foram carregados corretamente na sua conta do Cloudinary.")

    st.markdown("---")
    st.markdown("### 🎬 Fila de Pedidos Atual")

    try:
        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json?_t={time.time()}"
        response = requests.get(url_firebase, timeout=10)
        
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
            
            tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)
            pendentes = [p for p in pedidos_ativos if p.get("estado") == "pendente"]

            if pedidos_ativos:
                html_lista = '<div style="background-color: #111111; border: 2px solid #333333; padding: 15px; border-radius: 8px; color: #ffffff; max-width: 550px; font-family: monospace; font-size: 15px; margin-bottom: 20px;">'
                html_lista += '<div style="color: #4CAF50; font-weight: bold; margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px;">ESTADO DA FILA:</div>'
                for idx, p in enumerate(pedidos_ativos, start=1):
                    titulo_musica = limpar_nome_musica(p.get("musica", {}))
                    cliente_nome = p.get("cliente", "Convidado")
                    estado_atual = p.get("estado")
                    badge = "🎵 [A Tocar]" if estado_atual == "aprovado" else "⏳ [Pendente]"
                    cor_badge = "#4CAF50" if estado_atual == "aprovado" else "#FFC107"
                    html_lista += f'<div style="padding: 4px 0;"><b>{idx}.</b> {titulo_musica} <span style="color:#aaa; font-size:13px;">({cliente_nome})</span> <span style="color:{cor_badge}; font-size:12px; float:right;">{badge}</span></div>'
                html_lista += '</div>'
                st.markdown(html_lista, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="background-color: #111111; border: 2px solid #333333; padding: 15px; border-radius: 8px; color: #888; max-width: 550px; font-family: monospace; font-size: 15px; margin-bottom: 20px;">
                        <div>Nenhum pedido na lista neste momento. À espera de novos pedidos...</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 📋 Gestão de Fila e Controlo")

            if tocando_agora:
                titulo_tocando = limpar_nome_musica(tocando_agora.get("musica", {}))
                st.success(f"🎵 A tocar agora: **{titulo_tocando}** (Cliente: {tocando_agora.get('cliente', 'Convidado')})")
                if st.button("⏹️ Terminar Música Atual", key=f"term_{tocando_agora.get('id')}"):
                    terminar_todas_musicas_ativas(provider_token, pedidos)
                    st.success("Música terminada e tela limpa com sucesso!")
                    st.rerun()

            if not pendentes:
                st.write("Fila de pendentes vazia. Os pedidos feitos pelos clientes aparecerão aqui automaticamente.")
            else:
                st.write("### Pedidos Pendentes para Aprovar:")
                for idx, p in enumerate(pendentes, start=1):
                    titulo_musica = limpar_nome_musica(p.get("musica", {}))
                    cliente_nome = p.get("cliente", "Convidado")
                    
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.write(f"**Pedido** - {titulo_musica} *(Cliente: {cliente_nome})*")
                    with col_btn:
                        if st.button(f"▶️ Play", key=f"btn_play_{p.get('id')}"):
                            terminar_todas_musicas_ativas(provider_token, pedidos)
                            atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                            st.success(f"Música '{titulo_musica}' enviada para a tela!")
                            st.rerun()
        else:
            st.info("Nenhum pedido encontrado no Firebase para este prestador. Abra o link do cliente e envie uma música para testar.")
            
    except Exception as e:
        st.error(f"Erro ao carregar os pedidos do Firebase: {e}")

def show_provider_panel_custom(provider_token):
    st.markdown("### 🎤 Painel do Prestador — FF Karaoke")
    st.markdown(f"<p style='color: #888; font-size: 13px;'>Token Ativo: <code>{provider_token}</code></p>", unsafe_allow_html=True)
    st.markdown("---")
    
    link_cliente_rel = f"/?page=client_register&prestador={provider_token}"
    link_tv_rel = f"/?page=client_screen&prestador={provider_token}"
    
    host_dominio = st.context.headers.get('Host', 'grupoffkaraoke.streamlit.app')
    link_cliente_absoluto = f"https://{host_dominio}{link_cliente_rel}"
    qr_url_cliente = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={urllib.parse.quote(link_cliente_absoluto)}"

    col_link, col_qr = st.columns([3, 1])
    with col_link:
        st.markdown(f"""
            <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 15px;">
                <div style="background-color: #e8f0fe; border: 1px solid #d2e3fc; padding: 10px 15px; border-radius: 8px;">
                    <span style="font-size: 14px; color: #202124;">📎 <b>Link do Cliente:</b> <a href="{link_cliente_rel}" target="_blank" rel="noopener noreferrer" style="color: #1a73e8; text-decoration: none;">{link_cliente_rel}</a></span>
                </div>
                <div style="background-color: #e8f0fe; border: 1px solid #d2e3fc; padding: 10px 15px; border-radius: 8px;">
                    <span style="font-size: 14px; color: #202124;">📺 <b>Link da TV:</b> <a href="{link_tv_rel}" target="_blank" rel="noopener noreferrer" style="color: #1a73e8; text-decoration: none;">{link_tv_rel}</a></span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with col_qr:
        st.image(qr_url_cliente, width=130, caption="QR Code Cliente")

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
        
        if tocando_agora:
            musica = tocando_agora.get("musica", {})
            if isinstance(musica, dict):
                titulo = musica.get("titulo", musica.get("nome", "Karaoke"))
            else:
                titulo = str(musica)
            
            titulo_limpo = limpar_nome_musica(titulo)
            url_video = obter_url_video_cloudinary(musica, titulo_limpo)
            cantor_name = tocando_agora.get('cliente', 'Convidado')
            
            st.markdown(f"<h2 style='text-align:center; color: #FFC107;'>A tocar: {titulo_limpo} <span style='font-size:16px; color:#aaa;'>(Cantor: {cantor_name})</span></h2>", unsafe_allow_html=True)

            video_html = f"""
            <div style="display: flex; justify-content: center; background: black; padding: 0px; width: 100%;">
                <video id="karaoke-player" width="100%" height="560px" controls autoplay playsinline controlslist="nodownload noremoteplayback" disablepictureinpicture style="object-fit: contain; background: black;">
                    <source src="{url_video}" type="video/mp4">
                    O seu navegador não suporta a reprodução deste vídeo.
                </video>
            </div>
            <script>
                var video = document.getElementById('karaoke-player');
                video.muted = false;
                var playPromise = video.play();
                if (playPromise !== undefined) {{
                    playPromise.then(_ => {{}}).catch(error => {{
                        video.muted = true;
                        video.play();
                    }});
                }}

                video.onended = function() {{
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
                }};
            </script>
            """
            components.html(video_html, height=620)
            
        else:
            url_clipe_fundo = obter_video_fundo(provider_token)
            proximo_cantor = pedidos_ativos[0] if pedidos_ativos else None
            
            col_esq, col_dir = st.columns([1, 1])
            
            with col_esq:
                st.markdown("""
                    <div style="border: 2px solid #FFC107; border-radius: 10px; padding: 15px; text-align: center; background: #111; margin-bottom: 15px;">
                        <h2 style="color: #FFC107; margin: 0; font-family: monospace;">🎤 FILA DE ESPERA</h2>
                    </div>
                """, unsafe_allow_html=True)
                
                if proximo_cantor:
                    t_prox = limpar_nome_musica(proximo_cantor.get("musica", {}))
                    c_prox = proximo_cantor.get("cliente", "Convidado")
                    st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #2b1035, #111); border: 2px solid #9c27b0; border-radius: 12px; padding: 15px; margin-bottom: 15px; text-align: center;">
                            <span style="color: #FFC107; font-size: 14px; font-weight: bold;">1 — Á Seguir —</span>
                            <h3 style="color: #ffffff; margin: 5px 0 0 0; font-family: monospace;">{c_prox}</h3>
                            <p style="color: #4CAF50; font-size: 14px; margin: 5px 0 0 0;">🎵 {t_prox}</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                html_caixas = '<div style="display: flex; flex-direction: column; gap: 8px;">'
                for idx in range(2, 7):
                    p_item = pedidos_ativos[idx-1] if len(pedidos_ativos) >= idx else None
                    if p_item:
                        t_item = limpar_nome_musica(p_item.get("musica", {}))
                        c_item = p_item.get("cliente", "Convidado")
                        texto_caixa = f"<b>{idx}.</b> {c_item} — {t_item}"
                    else:
                        texto_caixa = f"<b>{idx}.</b>"
                    
                    html_caixas += f'<div style="background: #111; border: 2px solid #FFC107; border-radius: 8px; padding: 12px; color: #fff; font-family: monospace; font-size: 16px;">{texto_caixa}</div>'
                html_caixas += '</div>'
                st.markdown(html_caixas, unsafe_allow_html=True)

            with col_dir:
                st.markdown("""
                    <div style="border: 2px solid #FFC107; border-radius: 10px; padding: 15px; text-align: center; background: #111; margin-bottom: 15px;">
                        <h2 style="color: #FFC107; margin: 0; font-family: monospace;">📺 VÍDEO CLIPE (FUNDO)</h2>
                    </div>
                """, unsafe_allow_html=True)
                
                if url_clipe_fundo:
                    video_fundo_html = f"""
                    <div style="display: flex; justify-content: center; background: black; border: 2px solid #FFC107; border-radius: 10px; padding: 5px; width: 100%;">
                        <video id="fundo-player" width="100%" height="470px" autoplay loop muted playsinline style="object-fit: contain; background: black; border-radius: 8px;">
                            <source src="{url_clipe_fundo}" type="video/mp4">
                            O seu navegador não suporta vídeo.
                        </video>
                    </div>
                    """
                    components.html(video_fundo_html, height=500)
                else:
                    st.markdown("""
                        <div style="border: 2px solid #FFC107; border-radius: 10px; padding: 80px 20px; text-align: center; background: #000; color: #FFC107; font-family: monospace;">
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
    </style>
    """, unsafe_allow_html=True)

    renderizar_ecra_tv(provider_token)

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
                show_provider_panel_custom(token)
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
            
        st.sidebar.title("Panel Admin")
        senha = st.sidebar.text_input("Palavra-passe", type="password")
        
        if senha == "ffkaraoke2026" or senha == "admin123":
            st.sidebar.success("Sessão Iniciada")
            show_admin_panel()
        else:
            st.title("🔒 FFKaraoke - Área Restrita")
            st.write("Introduza a palavra-passe de administrador na barra lateral para gerir os acessos ou aceda através do link do seu painel de prestador.")
                
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar a aplicação: {e}")

if __name__ == "__main__":
    main()
