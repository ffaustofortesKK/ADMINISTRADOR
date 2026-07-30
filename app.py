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

        # --- SECÇÃO DE PEDIDOS EXTRA DE MÚSICA PARA O PRESTADOR E ADM ---
        st.markdown("---")
        st.markdown("### 📥 Caixa de Pedidos Extra (Músicas Não Encontradas)")
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
                                <b>Cliente:</b> {c_nome} | <b>Música Extra Solicitada:</b> <span style="color: #4CAF50;">{mus_pedida}</span><br>
                                <span style="color: #aaa; font-size: 12px;">🔄 [AUTOMAÇÃO ADM]: A verificar disponibilidade no YouTube / Web...</span>
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
                                st.success("Mensagem enviada: 'Infelizmente não temos essa música, pode solicitar outra.'")
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
    .stApp { background-color: #0b0b0b; color: #ffffff; }
    .panel-header { display: flex; align-items: center; gap: 15px; border-bottom: 2px solid #FFC107; padding-bottom: 10px; margin-bottom: 20px; }
    .card-link { background: linear-gradient(90deg, #0d1b2a 0%, #1b263b 100%); border: 2px solid #FFC107; border-radius: 12px; padding: 15px 20px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; }
    .card-tv { background: linear-gradient(90deg, #1f1a24 0%, #2e1a38 100%); border: 2px solid #9c27b0; border-radius: 12px; padding: 15px 20px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; }
    .link-text { font-family: monospace; color: #FFC107; font-size: 14px; text-decoration: none; }
    .link-text-tv { font-family: monospace; color: #e1bee7; font-size: 14px; text-decoration: none; }
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
        st.markdown("""<div style="background: #111; border: 2px solid #FFC107; border-radius: 12px; padding: 10px; text-align: center;">""", unsafe_allow_html=True)
        st.image(qr_url_cliente, width=135, caption="")
        st.markdown("<div style='color: #FFC107; font-family: monospace; font-size: 12px; font-weight: bold; margin-top: 5px;'>QR CODE CLIENTE</div></div>", unsafe_allow_html=True)

    renderizar_gestao_fila_prestador(provider_token)

# --- SECÇÃO CUSTOMIZADA DA PÁGINA DO CLIENTE COM A CAIXA DE PEDIDO EXTRA ---
def show_client_page_custom(provider_token):
    st.markdown("""
    <style>
    .stApp { background-color: #0b0b0b; color: white; font-family: monospace; }
    .client-header { border-bottom: 2px solid #FFC107; padding-bottom: 10px; margin-bottom: 20px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="client-header">
            <h1 style="color: #FFC107; font-size: 24px; margin: 0;">🎤 FF KARAOKE - PAINEL DO CLIENTE</h1>
            <p style="color: #aaa; font-size: 13px; margin: 5px 0 0 0;">Faça o seu pedido de música ou solicite um pedido extra caso não encontre!</p>
        </div>
    """, unsafe_allow_html=True)

    nome_cliente = st.text_input("O seu Nome / Convidado:", placeholder="Digite o seu nome aqui...")
    
    st.markdown("### 🔍 Caixa de Pedido Extra (Música não encontrada)")
    st.info("Caso não encontre a música pretendida nas opções disponíveis, escreva abaixo o nome da música e o cantor:")

    with st.form("form_pedido_extra_cliente"):
        musica_extra_input = st.text_input("Nome da Música e Cantor (Extra):", placeholder="Ex: Cefas David - Fica")
        enviar_extra = st.form_submit_button("📤 Enviar Pedido Extra")

        if enviar_extra:
            if not nome_cliente.strip():
                st.error("Por favor, preencha o seu nome antes de enviar o pedido.")
            elif not musica_extra_input.strip():
                st.error("Por favor, escreva o nome da música pretendida.")
            else:
                novo_pedido_extra = {
                    "cliente": nome_cliente.strip(),
                    "musica": musica_extra_input.strip(),
                    "estado": "pendente",
                    "timestamp": time.time()
                }
                try:
                    res = requests.post(f"{FIREBASE_URL}/pedidos_extras/{provider_token}.json", json=novo_pedido_extra, timeout=10)
                    if res.status_code == 200:
                        st.success("O seu pedido foi enviado, nem todas as musicas estao disponiveis em karaoke.")
                    else:
                        st.error("Erro ao enviar o pedido extra. Tente novamente.")
                except Exception as e:
                    st.error(f"Erro de ligação: {e}")

    # Verificar se há resposta do prestador para o cliente nesta sessão
    try:
        res_check = requests.get(f"{FIREBASE_URL}/pedidos_extras/{provider_token}.json", timeout=10)
        if res_check.status_code == 200 and res_check.json():
            dados_ex = res_check.json()
            for k_ex, v_ex in dados_ex.items():
                if v_ex.get("cliente") == nome_cliente and nome_cliente.strip() != "":
                    estado_resp = v_ex.get("estado")
                    if estado_resp == "nao_temos":
                        st.warning(f"⚠️ Resposta sobre '{v_ex.get('musica')}': Infelizmente não temos essa musica, pode solicitar outra.")
                    elif estado_resp == "confirmado":
                        st.success(f"✅ O seu pedido de música '{v_ex.get('musica')}' foi confirmado e encaminhado!")
    except Exception:
        pass

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
            titulo = limpar_nome_musica(musica)
            url_video = obter_url_video_cloudinary(musica, titulo)

            video_html = f"""
            <style>
                body, html {{ margin: 0; padding: 0; background: #000; overflow: hidden; width: 100vw; height: 100vh; }}
            </style>
            <div style="width: 100vw; height: 100vh; background: black; position: fixed; top: 0; left: 0;">
                <video width="100%" height="100%" autoplay playsinline controls style="object-fit: contain; background: black; width: 100%; height: 100%;">
                    <source src="{url_video}" type="video/mp4">
                </video>
            </div>
            """
            components.html(video_html, height=750, scrolling=False)
        else:
            st.markdown("""
                <div style="border: 2px solid #FFC107; border-radius: 10px; padding: 100px 20px; text-align: center; background: #000; color: #FFC107; font-family: monospace;">
                    <div style="font-size: 40px; margin-bottom: 10px;">📺</div>
                    <p style="color: #aaa; font-size: 16px; margin: 0;">Aguardando reprodução...</p>
                </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro na TV: {e}")

def show_client_screen():
    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider", None)
    if not provider_token:
        st.error("Tela inválida.")
        return
    renderizar_ecra_tv(provider_token)

def main():
    try:
        query_params = st.query_params
        
        if "page" in query_params and query_params["page"] == "register":
            show_register_page()
            return

        if "page" in query_params and query_params["page"] == "client_register":
            token_p = query_params.get("prestador") or query_params.get("provider", "")
            show_client_page_custom(token_p)
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
                    st.warning("⏳ O seu registo aguarda aprovação.")
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
                        st.success("Sessão iniciada!")
                        st.rerun()
                    else:
                        st.error("Palavra-passe incorreta.")

        if st.session_state.get("admin_logged", False):
            show_admin_panel()
                
    except Exception as e:
        st.error(f"Erro ao carregar a aplicação: {e}")

if __name__ == "__main__":
    main()
