# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import time
import urllib.parse
from datetime import datetime, timedelta
import pandas as pd

# Configuração da página Streamlit
st.set_page_config(
    page_title="FF Karaoke Cloud",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configuração da URL do Firebase (Base de Dados)
FIREBASE_URL = "https://ffkaraokecloud-default-rtdb.firebaseio.com"

# --- FUNÇÕES AUXILIARES ---

def limpar_nome_musica(nome):
    if not nome:
        return ""
    return str(nome).replace(".mp4", "").replace(".mkv", "").replace("_", " ").strip()

def obter_url_video_cloudinary(musica, titulo_limpo):
    if isinstance(musica, dict):
        url = musica.get("url_cloudinary", "") or musica.get("url", "")
        if url:
            return url
    return ""

def get_all_providers():
    try:
        response = requests.get(f"{FIREBASE_URL}/prestadores.json", timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()
            prestadores = [{"id": k, **v} for k, v in data.items()]
            return pd.DataFrame(prestadores)
    except Exception:
        pass
    return pd.DataFrame(columns=['token', 'nome_prestador', 'tempo_plano', 'approved', 'data_registo', 'segundos_restantes'])

def obter_video_fundo(provider_token):
    try:
        res = requests.get(f"{FIREBASE_URL}/video_fundo/{provider_token}.json", timeout=5)
        if res.status_code == 200 and res.json():
            return res.json().get("url", "")
    except Exception:
        pass
    return ""

# --- TELA DO CLIENTE (REGISTO DE MÚSICA) ---
def show_client_page():
    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider", None)

    if not provider_token:
        st.error("Link inválido. Falta o parâmetro do prestador.")
        return

    st.markdown("""
        <style>
        .stApp { background-color: #000000; color: white; }
        .block-container { background-color: #000000; border: 4px solid #FFC107; border-radius: 12px; padding: 2rem; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #ffffff; font-family: monospace;'>🎤 FF KARAOKE - REGISTO DE MÚSICA</h1>", unsafe_allow_html=True)
    
    # Obter lista de músicas disponíveis
    try:
        res = requests.get(f"{FIREBASE_URL}/catalogo_musicas.json", timeout=10)
        catalogo = []
        if res.status_code == 200 and res.json():
            data = res.json()
            catalogo = [v for v in data.values()]
    except Exception:
        catalogo = []

    with st.form("form_registo_musica"):
        nome_cliente = st.text_input("O seu Nome / alcunha")
        
        if catalogo:
            opcoes_musicas = [m.get("titulo", "Música") for m in catalogo]
            escolha_musica = st.selectbox("Escolha a Música", options=opcoes_musicas)
        else:
            escolha_musica = st.text_input("Nome da Música pretendida")
            
        submitted = st.form_submit_button("Submeter Pedido de Música")
        
        if submitted:
            if not nome_cliente or not escolha_musica:
                st.error("Por favor, preencha o seu nome e escolha uma música.")
            else:
                novo_pedido = {
                    "cliente": nome_cliente,
                    "musica": {"titulo": escolha_musica},
                    "estado": "pendente",
                    "timestamp": int(time.time() * 1000)
                }
                try:
                    requests.post(f"{FIREBASE_URL}/pedidos/{provider_token}.json", json=novo_pedido, timeout=10)
                    st.success("Música registada com sucesso na fila! Aguarde a sua vez.")
                except Exception as err:
                    st.error(f"Erro ao enviar pedido: {err}")

# --- TELA DA TV / REPRODUÇÃO ---
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
                    border: 4px solid #FFC107;
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
                    border-top: 4px solid #FFC107;
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
                    color: #ffffff;
                    font-weight: bold;
                    text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
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
                    color: #ffffff;
                    font-family: monospace;
                    font-size: 15vw;
                    font-weight: bold;
                    text-shadow: 2px 2px 5px rgba(0,0,0,0.9);
                    animation: zoomInNumber 0.9s ease-in-out infinite;
                }}
            </style>

            <div id="countdown-screen" class="countdown-overlay">3</div>

            <div id="karaoke-container" style="display: none; width: 100vw; height: 100vh; background: black; position: fixed; top: 0; left: 0;">
                <video id="karaoke-player" width="100%" height="100%" autoplay playsinline style="object-fit: contain; background: black; width: 100%; height: 100%;">
                    <source src="{url_video}" type="video/mp4">
                    O seu navegador não suporta a reprodução deste vídeo.
                </video>
                <div id="audio-warning" style="display: none; position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); text-align: center; background: #222; border: 4px solid #FFC107; padding: 10px 20px; border-radius: 5px; z-index: 99999;">
                    <p style="color: #ffffff; margin: 0 0 8px 0; font-family: monospace; font-size: 14px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">⚠️ O navegador bloqueou o áudio automático.</p>
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
                        <div style="border: 4px solid #FFC107; border-radius: 10px; padding: 15px; background: rgba(0,0,0,0.95); margin-bottom: 15px; display: flex; align-items: center; gap: 15px;">
                            <span style="color: #ffffff; font-size: 20px; font-weight: bold; font-family: monospace; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Á SEGUIR</span>
                            <span style="color: #ffffff; font-size: 20px; font-weight: bold; font-family: monospace; text-transform: uppercase; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">{c_prox}</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div style="border: 4px solid #FFC107; border-radius: 10px; padding: 15px; text-align: center; background: rgba(0,0,0,0.95); margin-bottom: 15px;">
                            <h2 style="color: #ffffff; margin: 0; font-family: monospace; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">🎤 FILA DE ESPERA VAZIA</h2>
                        </div>
                    """, unsafe_allow_html=True)
                
                html_caixas = '<div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 40px;">'
                demais_pedidos = pedidos_ativos[1:] if len(pedidos_ativos) > 1 else []
                
                for idx, p_item in enumerate(demais_pedidos, start=2):
                    c_item = p_item.get("cliente", "Convidado")
                    texto_caixa = f"<b>{idx}.</b> {c_item}"
                    html_caixas += f'<div style="background: rgba(0,0,0,0.95); border: 4px solid #FFC107; border-radius: 8px; padding: 12px; color: #ffffff; font-family: monospace; font-size: 16px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">{texto_caixa}</div>'
                
                html_caixas += '</div>'
                st.markdown(html_caixas, unsafe_allow_html=True)

            with col_dir:
                if url_clipe_fundo:
                    video_fundo_html = f"""
                    <div style="display: flex; justify-content: center; background: rgba(0,0,0,0.95); border: 4px solid #FFC107; border-radius: 10px; padding: 5px; width: 100%; position: relative; margin-top: 5px; margin-bottom: 40px;">
                        <video id="fundo-player" width="100%" height="450px" autoplay loop playsinline controlslist="nodownload noremoteplayback" disablepictureinpicture style="object-fit: contain; background: black; border-radius: 8px;">
                            <source src="{url_clipe_fundo}" type="video/mp4">
                            O seu navegador não suporta vídeo.
                        </video>
                        <div id="fundo-audio-warning" style="display: none; position: absolute; bottom: 15px; right: 15px; background: rgba(0,0,0,0.8); border: 2px solid #FFC107; padding: 6px 10px; border-radius: 5px; cursor: pointer;" onclick="unmuteFundo()">
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
                        <div style="border: 4px solid #FFC107; border-radius: 10px; padding: 100px 20px; text-align: center; background: rgba(0,0,0,0.95); color: #ffffff; font-family: monospace; margin-top: 5px; margin-bottom: 40px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">
                            <div style="font-size: 40px; margin-bottom: 10px;">📺</div>
                            <p style="color: #ffffff; font-size: 16px; margin: 0; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Aguardando o prestador selecionar um vídeo clipe no painel de controle...</p>
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

# --- GESTÃO DA FILA PELO PRESTADOR ---
def renderizar_gestao_fila_prestador(provider_token):
    st.markdown("### 📋 Gestão de Fila e Pedidos")
    try:
        res = requests.get(f"{FIREBASE_URL}/pedidos/{provider_token}.json", timeout=10)
        if res.status_code == 200 and res.json():
            data = res.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            
            for p in pedidos:
                p_id = p.get("id")
                cliente = p.get("cliente", "Desconhecido")
                musica = p.get("musica", {})
                titulo = musica.get("titulo", "Música") if isinstance(musica, dict) else str(musica)
                estado = p.get("estado", "pendente")
                
                cols = st.columns([3, 2, 1])
                with cols[0]:
                    st.write(f"**Cliente:** {cliente} | **Música:** {titulo}")
                with cols[1]:
                    st.write(f"**Estado:** {estado}")
                with cols[2]:
                    if estado == "pendente":
                        if st.button("Aprovar / Tocar", key=f"apr_{p_id}"):
                            requests.put(f"{FIREBASE_URL}/pedidos/{provider_token}/{p_id}/estado.json", json="aprovado", timeout=5)
                            st.rerun()
                    elif estado == "aprovado":
                        if st.button("Terminar", key=f"term_{p_id}"):
                            requests.put(f"{FIREBASE_URL}/pedidos/{provider_token}/{p_id}/estado.json", json="terminado", timeout=5)
                            st.rerun()
        else:
            st.info("Nenhum pedido na fila de momento.")
    except Exception as e:
        st.error(f"Erro ao carregar fila: {e}")

    # Configuração de Vídeo Clipe de Fundo (Tela)
    st.markdown("---")
    st.markdown("### 📺 Configuração de Vídeo Clipe de Fundo (Tela)")
    try:
        res_cat = requests.get(f"{FIREBASE_URL}/catalogo_musicas.json", timeout=10)
        catalogo = []
        if res_cat.status_code == 200 and res_cat.json():
            catalogo = [v for v in res_cat.json().values()]
        
        if catalogo:
            opcoes_cli = {m.get("titulo", "Clipe"): (m.get("url_cloudinary", "") or m.get("url", "")) for m in catalogo}
            escolha_clipe = st.selectbox("Selecione o Vídeo Clipe", options=list(opcoes_cli.keys()))
            
            if st.button("Pesquisar Vídeo Clipe", type="primary"):
                url_escolhida = opcoes_cli.get(escolha_clipe, "")
                if url_escolhida:
                    requests.put(f"{FIREBASE_URL}/video_fundo/{provider_token}.json", json={"url": url_escolhida}, timeout=5)
                    st.success("Vídeo de fundo atualizado com sucesso!")
                    st.rerun()
                else:
                    st.error("URL do vídeo inválida.")
        else:
            st.info("Nenhum clipe disponível no catálogo.")
    except Exception as e:
        st.error(f"Erro ao configurar clipe: {e}")

# --- PAINEL DO PRESTADOR ---
def show_provider_panel_custom(provider_token):
    st.markdown("""
        <style>
        .stApp { background-color: #000000 !important; color: #ffffff !important; }
        .block-container { background-color: #000000 !important; border: 4px solid #FFC107 !important; border-radius: 12px; padding: 2rem !important; }
        .panel-header { display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.95); border: 3px solid #FFC107; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
        .card-link { background: #111; border: 2px solid #FFC107; padding: 12px; border-radius: 8px; margin-bottom: 10px; }
        .card-tv { background: #111; border: 2px solid #4CAF50; padding: 12px; border-radius: 8px; margin-bottom: 10px; }
        .link-title { color: #FFC107; font-family: monospace; font-weight: bold; font-size: 14px; margin-bottom: 5px; }
        .link-title-tv { color: #4CAF50; font-family: monospace; font-weight: bold; font-size: 14px; margin-bottom: 5px; }
        .link-text { color: #fff; font-family: monospace; text-decoration: none; word-break: break-all; }
        .link-text-tv { color: #fff; font-family: monospace; text-decoration: none; word-break: break-all; }
        .qr-box { background: #fff; padding: 10px; border-radius: 8px; display: inline-block; }
        @keyframes piscarAviso {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(1.02); }
            100% { opacity: 1; transform: scale(1); }
        }
        .aviso-reforco-faixa {
            background: #d9534f;
            color: white;
            padding: 12px;
            text-align: center;
            font-family: monospace;
            font-weight: bold;
            font-size: 16px;
            border-radius: 8px;
            border: 2px solid #fff;
            margin-bottom: 20px;
            animation: piscarAviso 0.8s infinite ease-in-out;
        }
        </style>
    """, unsafe_allow_html=True)

    # Obter dados do prestador
    df = get_all_providers()
    nome_prestador = "Prestador"
    tempo_plano = "2 Horas - 12 Mil Kwanzas"
    segundos_restantes = 7200 # Valor padrão simulado (2h)
    
    if not df.empty and 'token' in df.columns:
        p_row = df[df['token'] == provider_token]
        if not p_row.empty:
            nome_prestador = p_row.iloc[0].get('nome_prestador', 'Prestador')
            tempo_plano = p_row.iloc[0].get('tempo_plano', '2 Horas - 12 Mil Kwanzas')

    # Calcular formato do cronómetro (ex: 02:00:00)
    horas = segundos_restantes // 3600
    minutos = (segundos_restantes % 3600) // 60
    segundos = segundos_restantes % 60
    tempo_formatado = f"{horas:02d}:{minutos:02d}:{segundos:02d}"

    # Aviso de reforço caso faltem 30 minutos (1800 segundos) ou menos
    aviso_reforço_html = ""
    if segundos_restantes <= 1800:
        aviso_reforço_html = """
        <div class="aviso-reforco-faixa">
            ⚠️ O SEU TEMPO ESTA TERMINANDO. PARA QUE NÃO PERCAS OS SEUS REGISTOS PEÇA REFORÇO DE TEMPO.
        </div>
        """

    url_logotipo = "https://api.iconify.design/fluent-emoji-flat:microphone.svg"

    st.markdown(f"""
        <img src="{url_logotipo}" class="top-logo" />
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="panel-header">
            <div style="display: flex; align-items: center; gap: 15px;">
                <span style="font-size: 32px;">🎤</span>
                <div>
                    <h1 style="margin: 0; color: #ffffff; font-family: monospace; font-size: 24px; text-transform: uppercase; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">PAINEL DO PRESTADOR: {nome_prestador}</h1>
                    <p style="margin: 3px 0 0 0; color: #ffffff; font-size: 13px; font-family: monospace; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">TOKEN: <code style="background: #222; color: #ffffff; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{provider_token}</code></p>
                </div>
            </div>
            <div style="background: rgba(255,193,7,0.15); border: 2px solid #FFC107; padding: 6px 12px; border-radius: 8px; text-align: right; margin-right: 80px;">
                <div style="font-family: monospace; color: #ffffff; font-size: 11px; text-transform: uppercase; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">TEMPO / PLANO ESCOLHIDO</div>
                <div style="font-family: monospace; color: #ffffff; font-size: 15px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">⏱️ {tempo_formatado} ({tempo_plano})</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(aviso_reforço_html, unsafe_allow_html=True)
    
    link_cliente_rel = f"/?page=client_register&prestador={provider_token}"
    link_tv_rel = f"/?page=client_screen&prestador={provider_token}"
    
    host_dominio = st.context.headers.get('Host', 'grupoffkaraoke.streamlit.app')
    link_cliente_absoluto = f"https://{host_dominio}{link_cliente_rel}"
    link_tv_absoluto = f"https://{host_dominio}{link_tv_rel}"
    
    qr_url_cliente = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={urllib.parse.quote(link_cliente_absoluto)}"

    col_links, col_qr = st.columns([3, 1])
    
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
        st.markdown("<div style='font-family: monospace; color: #ffffff; font-size: 11px; font-weight: bold; margin-bottom: 2px; text-align: center; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);'>QR CODE CLIENTE</div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class="qr-box">
                <img src="{qr_url_cliente}" width="110" style="border-radius: 4px;" />
            </div>
        """, unsafe_allow_html=True)

    # Seção de pedido de reforço rápido
    st.markdown("<div id='reforco_seccao'></div>", unsafe_allow_html=True)
    if segundos_restantes <= 1800:
        st.markdown("### ⚡ Solicitar Reforço de Tempo")
        with st.form("form_reforco_prestador"):
            ref_pagamento = st.text_input("Referência de Pagamento / Nº de Comprovativo")
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
                if not ref_pagamento:
                    st.error("Por favor, insira a referência de pagamento ou comprovativo.")
                else:
                    dados_reforco = {
                        "token": provider_token,
                        "nome_prestador": nome_prestador,
                        "referencia": ref_pagamento,
                        "tempo_plano": duracao_reforco,
                        "approved": 0,
                        "data_registo": str(datetime.now())
                    }
                    try:
                        requests.put(f"{FIREBASE_URL}/reforcos_pendentes/{provider_token}.json", json=dados_reforco, timeout=10)
                        st.success("Pedido de reforço submetido com sucesso! Aguarde a confirmação do Administrador.")
                    except Exception as err:
                        st.error(f"Erro ao enviar reforço: {err}")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    renderizar_gestao_fila_prestador(provider_token)

def show_provider_panel_center(token):
    show_provider_panel_custom(token)

# --- PAINEL DO ADMINISTRADOR ---
def show_admin_panel():
    st.title("🛠️ Painel de Administração - FF Karaoke")
    
    tab1, tab2, tab3 = st.tabs(["Gestão de Prestadores", "Gestão de Reforços", "Catálogo de Músicas"])
    
    with tab1:
        st.subheader("Prestadores Registados")
        try:
            res = requests.get(f"{FIREBASE_URL}/prestadores.json", timeout=10)
            if res.status_code == 200 and res.json():
                data = res.json()
                for k, v in data.items():
                    st.write(f"**Nome:** {v.get('nome_prestador')} | **Plano:** {v.get('tempo_plano')} | **Aprovado:** {v.get('approved')}")
                    if v.get('approved') == 0:
                        if st.button(f"Aprovar {v.get('nome_prestador')}", key=f"app_{k}"):
                            requests.patch(f"{FIREBASE_URL}/prestadores/{k}.json", json={"approved": 1}, timeout=5)
                            st.success("Aprovado com sucesso!")
                            st.rerun()
            else:
                st.info("Nenhum prestador encontrado.")
        except Exception as e:
            st.error(f"Erro: {e}")
            
    with tab2:
        st.subheader("Gestão de Reforços Pendentes")
        try:
            res = requests.get(f"{FIREBASE_URL}/reforcos_pendentes.json", timeout=10)
            if res.status_code == 200 and res.json():
                data = res.json()
                for k, v in data.items():
                    if v.get('approved') == 0:
                        st.markdown(f"""
                        - **Prestador:** {v.get('nome_prestador')}
                        - **Plano Solicitado:** {v.get('tempo_plano')}
                        - **Comprovativo/Ref:** {v.get('referencia')}
                        - **Data:** {v.get('data_registo')}
                        """)
                        col_sim, col_nao = st.columns(2)
                        with col_sim:
                            if st.button("Sim (Aprovar Reforço)", key=f"sim_ref_{k}"):
                                requests.patch(f"{FIREBASE_URL}/reforcos_pendentes/{k}.json", json={"approved": 1}, timeout=5)
                                st.success("Reforço aprovado!")
                                st.rerun()
                        with col_nao:
                            if st.button("Não (Rejeitar)", key=f"nao_ref_{k}"):
                                requests.delete(f"{FIREBASE_URL}/reforcos_pendentes/{k}.json", timeout=5)
                                st.info("Reforço rejeitado/removido.")
                                st.rerun()
            else:
                st.info("Nenhum pedido de reforço pendente.")
        except Exception as e:
            st.error(f"Erro: {e}")

    with tab3:
        st.subheader("Adicionar Música ao Catálogo")
        with st.form("form_add_musica"):
            tit_m = st.text_input("Título da Música")
            url_m = st.text_input("URL Cloudinary do Vídeo")
            sub_m = st.form_submit_button("Adicionar Música")
            if sub_m:
                if tit_m and url_m:
                    nova_mus = {"titulo": tit_m, "url_cloudinary": url_m}
                    requests.post(f"{FIREBASE_URL}/catalogo_musicas.json", json=nova_mus, timeout=5)
                    st.success("Música adicionada ao catálogo!")
                else:
                    st.error("Preencha todos os campos.")

# --- FORMULÁRIO DE REGISTO INICIAL DO PRESTADOR ---
def custom_show_register_page():
    st.markdown("""
        <style>
        .stApp { background-color: #000000 !important; color: #ffffff !important; }
        .block-container { background-color: #000000 !important; border: 4px solid #FFC107 !important; border-radius: 12px; padding: 3rem !important; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🎤 FF Karaoke Cloud - Registo de Prestador")
    
    with st.form("form_registo_prestador"):
        nome_prestador = st.text_input("Nome do Prestador / Estabelecimento")
        tempo_plano = st.selectbox(
            "Duração Pretendida", 
            options=[
                "2 Horas - 12 Mil Kwanzas", 
                "3 Horas - 15 Mil Kwanzas", 
                "4 Horas - 20 Mil Kwanzas"
            ]
        )
        submitted = st.form_submit_button("Registar Prestador")
        
        if submitted:
            if not nome_prestador:
                st.error("Por favor, insira o nome do prestador.")
            else:
                import uuid
                token = str(uuid.uuid4())[:8]
                dados_prestador = {
                    "token": token,
                    "nome_prestador": nome_prestador,
                    "tempo_plano": tempo_plano,
                    "approved": 0,
                    "data_registo": str(datetime.now())
                }
                try:
                    requests.put(f"{FIREBASE_URL}/prestadores/{token}.json", json=dados_prestador, timeout=10)
                    st.success(f"Registo efetuado com sucesso! O seu Token é: {token}. Aguarde aprovação do Administrador.")
                except Exception as err:
                    st.error(f"Erro ao registar: {err}")

# --- ROTEAMENTO PRINCIPAL ---
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
            show_admin_panel()
                
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar a aplicação: {e}")

if __name__ == "__main__":
    main()
