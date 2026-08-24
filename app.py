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
import yt_dlp
import streamlit as st
import uuid

# --- 1. CONFIGURAR OS CAMINHOS UMA ÚNICA VEZ ---
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_path = os.path.join(current_dir, "utils")
modules_path = os.path.join(current_dir, "modules")

for path in [current_dir, utils_path, modules_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

# --- 2. IMPORTAR MÓDULOS DE FORMA SEGURA ---
from modules.admin import show_admin_panel
try:
    from modules.prestador import show_prestador_page
    importlib.reload(prestador)
except Exception:
    def show_prestador_page(token, url): 
        st.error("Módulo 'modules.prestador' não encontrado.")

# --- 3. CONFIGURAÇÃO DO CLOUDINARY ---
# (Dica: O ideal no futuro é usar st.secrets para esconder a api_secret)
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

# --- FUNÇÃO SEGURA PARA OBTER VÍDEO DE FUNDO ---
def obter_video_fundo(provider_token):
    """
    Vai buscar o vídeo de fundo primeiro ao Firebase. 
    Se não houver nenhum configurado, vai buscar automaticamente 
    um vídeo aleatório à pasta 'clipes' do Cloudinary.
    """
    try:
        # 1. Tenta verificar se o prestador definiu um vídeo específico no Firebase
        url_fb = f"{FIREBASE_URL}/video_fundo/{provider_token}.json"
        response = requests.get(url_fb, timeout=5)
        
        if response.status_code == 200 and response.json():
            dados = response.json()
            if isinstance(dados, str) and dados.startswith("http"):
                return dados
            elif isinstance(dados, dict) and dados.get("url"):
                return dados.get("url")

        # 2. Se o Firebase estiver vazio, vai buscar à pasta 'clipes' do Cloudinary (conforme a sua imagem)
        resultado_cloudinary = cloudinary.api.resources(
            type="upload",
            prefix="clipes/",  # Nome exato da pasta no Cloudinary
            resource_type="video",
            max_results=50
        )
        
        recursos = resultado_cloudinary.get("resources", [])
        if recursos:
            # Escolhe um clipe aleatório da pasta 'clipes' para servir de fundo
            clipe_escolhido = random.choice(recursos)
            return clipe_escolhido.get("secure_url")

    except Exception as e:
        print(f"Aviso: Não foi possível carregar o vídeo de fundo: {e}")
    
    return None
        
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
    st.markdown("<p>Preencha os seus dados.</p>", unsafe_allow_html=True)
    
    with st.form("form_registo_prestador_custom"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome")
        with col2:
            sobrenome = st.text_input("Sobrenome")
            
        telefone = st.text_input("Número de Telefone")
        duracao = st.selectbox(
            "Contrato Pretendido", 
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

# --- FUNÇÃO AUXILIAR: BUSCAR MÚLTIPLOS LINKS NO YOUTUBE ---
def buscar_multiplos_links_youtube(termo_busca, max_resultados=5):
    """
    Função robusta para pesquisar vídeos no YouTube sem falhar silenciosamente,
    retornando uma lista de dicionários com 'titulo' e 'url'.
    """
    resultados = []
    try:
        query_tratada = urllib.parse.quote(termo_busca)
        url = f"https://www.youtube.com/results?search_query={query_tratada}"
        
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )
        
        with urllib.request.urlopen(req, timeout=8) as response:
            html_content = response.read().decode('utf-8')
            
        match = re.search(r'ytInitialData\s*=\s*({.+?});</script>', html_content)
        if match:
            data_json = json.loads(match.group(1))
            try:
                contents = data_json['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
                for section in contents:
                    if 'itemSectionRenderer' in section:
                        for item in section['itemSectionRenderer']['contents']:
                            if 'videoRenderer' in item:
                                v_data = item['videoRenderer']
                                v_id = v_data.get('videoId')
                                if v_id:
                                    v_title_runs = v_data.get('title', {}).get('runs', [])
                                    v_title = "".join([run.get('text', '') for run in v_title_runs]) or "Vídeo Karaoke"
                                    
                                    resultados.append({
                                        "titulo": v_title,
                                        "url": f"https://www.youtube.com/watch?v={v_id}"
                                    })
                                    if len(resultados) >= max_resultados:
                                        break
            except Exception:
                pass
                
        if not resultados:
            video_ids = re.findall(r'\"videoId\":\"([a-zA-Z0-9_-]{11})\"', html_content)
            vistos = set()
            for v_id in video_ids:
                if v_id not in vistos:
                    vistos.add(v_id)
                    resultados.append({
                        "titulo": f"Karaoke - {termo_busca} ({len(resultados)+1})",
                        "url": f"https://www.youtube.com/watch?v={v_id}"
                    })
                    if len(resultados) >= max_resultados:
                        break
                        
    except Exception as e:
        print(f"Erro na pesquisa do YouTube: {e}")
        
    if not resultados:
        url_fallback = f"https://www.youtube.com/results?search_query={urllib.parse.quote(termo_busca)}"
        resultados.append({
            "titulo": f"🔍 Abrir pesquisa direta para: {termo_busca}",
            "url": url_fallback
        })
        
    return resultados

def limpar_nome_musica(musica_obj):
    if isinstance(musica_obj, dict):
        return musica_obj.get("titulo", "Música Desconhecida")
    return str(musica_obj)

def atualizar_estado_pedido(provider_token, pedido_id, novo_estado):
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}.json"
        requests.patch(url, json={"estado": novo_estado}, timeout=5)
    except Exception:
        pass

def terminar_todas_musicas_ativas(provider_token, pedidos):
    for p in pedidos:
        if p.get("estado") == "aprovado":
            atualizar_estado_pedido(provider_token, p.get("id"), "terminado")

def obter_video_fundo(provider_token):
    try:
        url = f"{FIREBASE_URL}/video_fundo/{provider_token}.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            return res.json().get("url", "")
    except Exception:
        pass
    return ""

def definir_video_fundo(provider_token, url_video):
    try:
        url = f"{FIREBASE_URL}/video_fundo/{provider_token}.json"
        requests.put(url, json={"url": url_video}, timeout=5)
    except Exception:
        pass

def listar_videos_pasta_clipes():
    return []

def get_all_providers():
    """Exemplo de função auxiliar para ir buscar os dados dos prestadores ao Firebase."""
    try:
        res = requests.get(f"{FIREBASE_URL}/prestadores.json", timeout=5)
        if res.status_code == 200 and res.json():
            data = res.json()
            if isinstance(data, dict):
                lista = []
                for k, v in data.items():
                    if isinstance(v, dict):
                        v['token'] = k
                        lista.append(v)
                return pd.DataFrame(lista)
    except Exception:
        pass
    return pd.DataFrame()

@st.fragment(run_every=1)
def renderizar_gestao_fila_prestador(provider_token):
    """Secção de gestão da fila e pedidos extras do prestador."""
    st.markdown("### 📋 Gestão de Pedidos e Fila")
    
    try:
        res = requests.get(f"{FIREBASE_URL}/pedidos/{provider_token}.json", timeout=5)
        pedidos_extras = []
        
        if res.status_code == 200 and res.json():
            dados_pedidos = res.json()
            if isinstance(dados_pedidos, dict):
                for p_id, p_val in dados_pedidos.items():
                    if isinstance(p_val, dict):
                        p_val['id'] = p_id
                        # Se for pedido externo / não achado
                        pedidos_extras.append(p_val)
                        
        with st.container():
            aba_extras, aba_fila = st.tabs(["🕹️ Pedidos Externos / Não Achados", "🎶 Fila Geral"])
            
            with aba_extras:
                st.markdown("### 🕹️ CAIXA DE PEDIDOS NÃO ACHADOS (EXTERNOS)")
                if pedidos_extras:
                    for p in pedidos_extras:
                        pedido_id = p.get("id")
                        cliente = p.get("cliente", "Desconhecido")
                        musica_nome = p.get("musica", "")
                        timestamp_pedido = p.get("timestamp_str", "Data não registada")
                        
                        opcoes_encontradas = p.get("opcoes_yt", [])
                        link_selecionado = p.get("link_yt", "")
                        
                        with st.container(border=True):
                            st.markdown(f"🎵 **{musica_nome}**")
                            st.caption(f"Pedido de cliente - {cliente} - {timestamp_pedido}")
                            
                            if link_selecionado:
                                st.markdown(f"<a href='{link_selecionado}' target='_blank' style='color: #FFC107; font-family: monospace; font-weight: bold; font-size: 13px; text-decoration: underline;'>{link_selecionado}</a>", unsafe_allow_html=True)
                            
                            if opcoes_encontradas:
                                for opt in opcoes_encontradas:
                                    t_opt = opt.get('titulo', 'Vídeo')
                                    u_opt = opt.get('url', '#')
                                    st.markdown(f"<div style='margin: 4px 0;'><a href='{u_opt}' target='_blank' style='color: #FFC107; font-family: monospace; font-size: 13px; text-decoration: none; font-weight: bold;'>▶️ {t_opt}</a></div>", unsafe_allow_html=True)
                            
                            st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
                            
                            col_b1, col_b2, col_b3 = st.columns([1.5, 1, 0.8])
                            
                            with col_b1:
                                if st.button("🔍 Procurar karaoke no YouTube", key=f"procurar_ext_{pedido_id}", type="secondary", use_container_width=True):
                                    termo_busca = f"{musica_nome} karaoke"
                                    with st.spinner("A pesquisar no YouTube..."):
                                        resultados_busca = buscar_multiplos_links_youtube(termo_busca, max_resultados=5)
                                    
                                    if resultados_busca:
                                        primeiro_link = resultados_busca[0]['url']
                                        payload_atualizacao = {
                                            "opcoes_yt": resultados_busca,
                                            "link_yt": primeiro_link
                                        }
                                        requests.patch(f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}.json", json=payload_atualizacao)
                                        st.success("Opções encontradas com sucesso!")
                                        time.sleep(0.3)
                                        st.rerun()
                                    else:
                                        st.error("Não foi possível obter links automáticos.")
                                        
                            with col_b2:
                                if link_selecionado:
                                    st.markdown(f"""
                                        <a href="{link_selecionado}" target="_blank" style="display: block; background-color: #000000; color: #ffffff; border: 1px solid #333; text-align: center; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-family: monospace; font-weight: bold; font-size: 14px;">
                                            Abrir no YouTube
                                        </a>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown("""
                                        <div style="background-color: #111; color: #666; border: 1px solid #222; text-align: center; padding: 6px 12px; border-radius: 4px; font-family: monospace; font-weight: bold; font-size: 14px; cursor: not-allowed;">
                                            Abrir no YouTube
                                        </div>
                                    """, unsafe_allow_html=True)
                                    
                            with col_b3:
                                if st.button("Apagar", key=f"apagar_ext_{pedido_id}", type="primary", use_container_width=True):
                                    requests.delete(f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}.json")
                                    st.rerun()
                else:
                    st.info("Nenhum pedido extra pendente no momento.")
                    
            with aba_fila:
                st.markdown("### Fila de músicas regular em andamento...")
                
    except Exception as e:
        st.error(f"Erro ao gerir a fila: {e}")
        
def show_provider_panel_custom(provider_token):
    url_logotipo = "https://cdn.phototourl.com/free/2026-08-03-8b13edf5-0257-491d-ab78-f0d5329ffc15.jpg"
    url_fundo_painel = "https://cdn.phototourl.com/free/2026-08-03-694a4a2e-9914-4da8-93b2-87538a4805ab.png"

    df_prov = get_all_providers()
    
    # Valores padrão caso não encontre
    nome_prestador = "PRESTADOR NÃO IDENTIFICADO"
    tempo_plano = "2 Horas - 12 Mil Kwanzas"
    data_registo_str = None
    
    if not df_prov.empty:
        # Tenta identificar qual coluna guarda o token
        col_token_candidates = ['token', 'provider_token', 'id']
        col_token_encontrada = next((c for c in col_token_candidates if c in df_prov.columns), None)
        
        if col_token_encontrada:
            match = df_prov[df_prov[col_token_encontrada].astype(str) == str(provider_token)]
            if not match.empty:
                row = match.iloc[0]
                
                # Procura dinamicamente pelas colunas de nome
                for col_n in ['nome_prestador', 'nome', 'prestador', 'user']:
                    if col_n in df_prov.columns and pd.notna(row.get(col_n)):
                        nome_prestador = str(row.get(col_n)).upper()
                        break
                
                # Procura dinamicamente pelas colunas de plano/tempo
                for col_p in ['tempo_plano', 'plano', 'duracao', 'tempo']:
                    if col_p in df_prov.columns and pd.notna(row.get(col_p)):
                        tempo_plano = str(row.get(col_p))
                        break
                        
                # Procura dinamicamente pela data de registo
                for col_d in ['data_registo', 'data', 'timestamp', 'created_at']:
                    if col_d in df_prov.columns and pd.notna(row.get(col_d)):
                        data_registo_str = str(row.get(col_d))
                        break

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

    # Define os segundos base com base estrita no plano escolhido pelo prestador
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
    }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(aviso_reforço_html, unsafe_allow_html=True)
    
    link_cliente_rel = f"/?page=client_register&prestador={provider_token}"
    link_tv_rel = f"/?page=client_screen&prestador={provider_token}"
    
    host_dominio = st.context.headers.get('Host', 'grupoffkaraoke.streamlit.app')
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
                        st.success("Pedido de reforço submetido com sucesso! Aguarde a confirmação do Administrador.")
                    except Exception as err:
                        st.error(f"Erro ao enviar reforço: {err}")

    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
    renderizar_gestao_fila_prestador(provider_token)
        
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

def obter_url_video_cloudinary(url_ou_nome):
    if not url_ou_nome:
        return ""
    # Se já for um link completo do Cloudinary, retorna diretamente
    if url_ou_nome.startswith("http"):
        return url_ou_nome
    
    # Caso contrário, tenta procurar na lista de clipes disponíveis
    try:
        lista = listar_videos_pasta_clipes()
        for clipe in lista:
            if clipe['nome'] == url_ou_nome or clipe['url'] == url_ou_nome:
                return clipe['url']
    except Exception:
        pass
        
    return url_ou_nome    

    renderizar_ecra_tv(provider_token)

def show_provider_panel_center(token):
    show_provider_panel_custom(token)

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
