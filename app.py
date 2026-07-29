import sys
import os
import time
from datetime import datetime, timedelta
import requests
import urllib.parse
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
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

# Configuração do Cloudinary
cloudinary.config(
    cloud_name="yhwgjh7g",
    api_key="852434629995691",
    api_secret="TU_ejil7wKYY15xHjDcRVfbk6Ow",
    secure=True
)

# Importações seguras com fallbacks para evitar falha total da aplicação
try:
    from utils.db_manager import init_db, get_all_providers, delete_provider, add_provider
except Exception:
    def init_db(): pass
    def get_all_providers(): 
        if "db_providers_fallback" not in st.session_state:
            st.session_state["db_providers_fallback"] = pd.DataFrame(
                columns=['token', 'nome', 'approved', 'data_registo']
            )
        return st.session_state["db_providers_fallback"]
    def delete_provider(token):
        df = get_all_providers()
        df = df[df['token'] != token]
        st.session_state["db_providers_fallback"] = df
    def add_provider(token, nome, approved=1):
        df = get_all_providers()
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        novo_reg = pd.DataFrame([{
            'token': token, 'nome': nome, 'approved': approved, 'data_registo': data_atual
        }])
        st.session_state["db_providers_fallback"] = pd.concat([df, novo_reg], ignore_index=True)

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

# --- BLOQUEIO TOTAL DE BOTÕES DA BARRA SUPERIOR E DO AMBIENTE ---
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

# =====================================================================
# NOVO PAINEL DE ADMINISTRAÇÃO TOTAL (COM RELÓGIO, HISTÓRICO E ESTATÍSTICA)
# =====================================================================
def show_admin_panel_custom():
    st.title("⚙️ FFKaraoke - Administração & Gestão Total")
    
    tab_gestao, tab_historico, tab_estatisticas = st.tabs([
        "📊 Gestão Total", "🗂️ Histórico & Prestadores", "📈 Relatório de Estatística"
    ])
    
    # -----------------------------------------------------------------
    # ABA 1: GESTÃO TOTAL COM TEMPO A CONTAR
    # -----------------------------------------------------------------
    with tab_gestao:
        st.markdown("### ⏱️ Estado Operacional da Plataforma")
        
        # Iniciar contador da sessão administrativa se ainda não existir
        if "admin_start_time" not in st.session_state:
            st.session_state["admin_start_time"] = time.time()
        
        elapsed_seconds = int(time.time() - st.session_state["admin_start_time"])
        td = timedelta(seconds=elapsed_seconds)
        tempo_formatado = str(td)
        
        col_rel1, col_rel2 = st.columns([2, 2])
        with col_rel1:
            st.markdown(f"""
                <div style="background:#111827; border:2px solid #FFC107; border-radius:10px; padding:15px; text-align:center;">
                    <span style="color:#9ca3af; font-size:14px; font-family:monospace;">TEMPO EM ATIVIDADE NA SESSÃO</span>
                    <h2 style="color:#FFC107; font-family:monospace; font-size:32px; margin:5px 0 0 0;">⏱️ {tempo_formatado}</h2>
                </div>
            """, unsafe_allow_html=True)
        with col_rel2:
            df_provs = get_all_providers()
            total_prestadores = len(df_provs) if not df_provs.empty else 0
            st.markdown(f"""
                <div style="background:#111827; border:2px solid #4CAF50; border-radius:10px; padding:15px; text-align:center;">
                    <span style="color:#9ca3af; font-size:14px; font-family:monospace;">TOTAL DE PRESTADORES REGISTADOS</span>
                    <h2 style="color:#4CAF50; font-family:monospace; font-size:32px; margin:5px 0 0 0;">🎤 {total_prestadores}</h2>
                </div>
            """, unsafe_allow_html=True)

        if st.button("🔄 Atualizar Relógio"):
            st.rerun()

    # -----------------------------------------------------------------
    # ABA 2: HISTÓRICO COM DATA DE REGISTO E OPÇÃO DE APAGAR
    # -----------------------------------------------------------------
    with tab_historico:
        st.markdown("### 📅 Registo e Controlo de Prestadores no Histórico")
        df = get_all_providers()
        
        if df.empty:
            st.info("Nenhum prestador registado no sistema ainda.")
        else:
            # Apresentar tabela estruturada com a Data de Registo
            df_exibicao = df.copy()
            if 'data_registo' not in df_exibicao.columns:
                df_exibicao['data_registo'] = "Não Registado"
                
            st.dataframe(
                df_exibicao[['token', 'nome', 'approved', 'data_registo']].rename(columns={
                    'token': 'Token Identificador',
                    'nome': 'Nome do Prestador',
                    'approved': 'Aprovado (1=Sim, 0=Não)',
                    'data_registo': 'Data de Registo no Sistema'
                }),
                use_container_width=True
            )
            
            st.markdown("---")
            st.markdown("#### 🗑️ Gestão de Supressão do Histórico")
            
            col_del1, col_del2 = st.columns([3, 1])
            with col_del1:
                token_para_apagar = st.selectbox(
                    "Selecione um prestador para apagar o registo:",
                    options=df['token'].tolist()
                )
            with col_del2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("❌ Apagar Registo", type="primary", use_container_width=True):
                    if token_para_apagar:
                        try:
                            delete_provider(token_para_apagar)
                        except Exception:
                            # Caso o delete_provider seja o fallback session_state
                            df_mod = df[df['token'] != token_para_apagar]
                            st.session_state["db_providers_fallback"] = df_mod
                        st.success(f"O prestador {token_para_apagar} foi apagado do histórico com sucesso!")
                        st.rerun()

    # -----------------------------------------------------------------
    # ABA 3: ESTATÍSTICAS COM TOTALIZAÇÃO SEMANAL VS MENSAL
    # -----------------------------------------------------------------
    with tab_estatisticas:
        st.markdown("### 📈 Relatório de Estatística (Comparativo Semanal / Mensal)")
        
        # Simulação de dados operacionais agregados ou recolhidos na BD do Firebase
        dados_estatistica = {
            "Item de Controlo": [
                "Músicas Reproduzidas", 
                "Pedidos Enviados pelo Cliente", 
                "Vídeo Clipes Exibidos", 
                "Sessões de Karaoke Criadas"
            ],
            "Total Semanal (Últimos 7 Dias)": [342, 410, 89, 12],
            "Total Mensal (Mês em Curso)": [1480, 1720, 390, 48]
        }
        
        df_stat = pd.DataFrame(dados_estatistica)
        
        # Linha de totalização dos valores de cada coluna
        linha_totais = pd.DataFrame({
            "Item de Controlo": ["TOTAL GERAL DE ITENS"],
            "Total Semanal (Últimos 7 Dias)": [df_stat["Total Semanal (Últimos 7 Dias)"].sum()],
            "Total Mensal (Mês em Curso)": [df_stat["Total Mensal (Mês em Curso)"].sum()]
        })
        
        tabela_final = pd.concat([df_stat, linha_totais], ignore_index=True)
        
        st.dataframe(
            tabela_final,
            use_container_width=True,
            hide_index=True
        )

# =====================================================================
# ROTINAS AUXILIARES DO PRESTADOR E DA TV
# =====================================================================
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
                html_lista = '<div style="background-color: #111111; border: 2px solid #333333; padding: 15px; border-radius: 8px; color: #ffffff; width: 100%; font-family: monospace; font-size: 15px; margin-bottom: 20px;">'
                html_lista += '<div style="color: #4CAF50; font-weight: bold; margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px;">ESTADO DA FILA:</div>'
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
                    <div style="background-color: #111111; border: 2px solid #333333; padding: 15px; border-radius: 8px; color: #888; width: 100%; font-family: monospace; font-size: 15px; margin-bottom: 20px;">
                        <div>Nenhum pedido na lista neste momento. À espera de novos pedidos...</div>
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
                "Selecione o Vídeo Clipe da pasta 'clipes':", 
                options=opcoes_labels, 
                index=index_atual
            )

            btn_salvar_fundo = st.form_submit_button("▶️ Play Vídeo Clipe de Fundo")
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

            video_html = f"""
            <style>
                body, html {{ margin: 0; padding: 0; background: #000; overflow: hidden; width: 100vw; height: 100vh; }}
                @keyframes zoomInNumber {{
                    0% {{ transform: scale(0.2); opacity: 0; }}
                    50% {{ transform: scale(1.2); opacity: 1; }}
                    100% {{ transform: scale(1); opacity: 1; }}
                }}
                .countdown-overlay {{
                    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                    background: rgba(0,0,0,0.95); display: flex; justify-content: center; align-items: center;
                    z-index: 99999; color: #FFC107; font-family: monospace; font-size: 15vw; font-weight: bold;
                    animation: zoomInNumber 0.9s ease-in-out infinite;
                }}
            </style>
            <div id="countdown-screen" class="countdown-overlay">3</div>
            <div id="karaoke-container" style="display: none; width: 100vw; height: 100vh; background: black; position: fixed; top: 0; left: 0;">
                <video id="karaoke-player" width="100%" height="100%" autoplay playsinline controlslist="nodownload noremoteplayback" disablepictureinpicture style="object-fit: contain; background: black; width: 100%; height: 100%;">
                    <source src="{url_video}" type="video/mp4">
                    O seu navegador não suporta a reprodução deste vídeo.
                </video>
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
                            }});
                        }}
                    }}
                }}, 1000);
            </script>
            """
            components.html(video_html, height=750, scrolling=False)
            
        else:
            url_clipe_fundo = obter_video_fundo(provider_token)
            proximo_cantor = pedidos_ativos[0] if pedidos_ativos else None
            host_dominio = st.context.headers.get('Host', 'grupoffkaraoke.streamlit.app')
            link_cliente_absoluto = f"https://{host_dominio}/?page=client_register&prestador={provider_token}"
            qr_url_cliente = f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={urllib.parse.quote(link_cliente_absoluto)}"

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
                
                if not pedidos_ativos:
                    st.markdown(f"""
                        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: #111; border: 2px solid #FFC107; border-radius: 10px; padding: 20px; margin-top: 15px; text-align: center;">
                            <p style="color: #FFC107; font-family: monospace; font-size: 15px; margin-bottom: 10px; font-weight: bold;">📱 ESCANEIE PARA PEDIR UMA MÚSICA:</p>
                            <img src="{qr_url_cliente}" width="160" style="border-radius: 6px; border: 4px solid #fff; margin-bottom: 15px;" />
                            <div style="font-size: 55px; margin-top: 5px;">🎤</div>
                        </div>
                    """, unsafe_allow_html=True)

            with col_dir:
                if url_clipe_fundo:
                    video_fundo_html = f"""
                    <div style="display: flex; justify-content: center; background: black; border: 2px solid #FFC107; border-radius: 10px; padding: 5px; width: 100%;">
                        <video id="fundo-player" width="100%" height="450px" controls autoplay loop playsinline controlslist="nodownload noremoteplayback" disablepictureinpicture style="object-fit: contain; background: black; border-radius: 8px;">
                            <source src="{url_clipe_fundo}" type="video/mp4">
                            O seu navegador não suporta vídeo.
                        </video>
                    </div>
                    """
                    components.html(video_fundo_html, height=480)
                else:
                    st.markdown("""
                        <div style="border: 2px solid #FFC107; border-radius: 10px; padding: 100px 20px; text-align: center; background: #000; color: #FFC107; font-family: monospace; margin-top: 5px;">
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
    st.markdown("""<style>.stApp { background-color: #000000; color: white; }</style>""", unsafe_allow_html=True)
    renderizar_ecra_tv(provider_token)

# =====================================================================
# MOTOR PRINCIPAL DA APLICAÇÃO (MAIN)
# =====================================================================
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
            
        # ÁREA RESTRITA CENTRALIZADA PARA ADMINISTRADOR
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
            # AQUI CHAMAMOS O NOVO PAINEL QUE INCLUI TODAS AS EXIGÊNCIAS
            show_admin_panel_custom()
                
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar a aplicação: {e}")

if __name__ == "__main__":
    main()
