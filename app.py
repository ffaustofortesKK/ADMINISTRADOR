import streamlit as st
import streamlit.components.v1 as components
import requests
import time
import urllib.parse
from datetime import datetime, timedelta
import pandas as pd

# Configuração da página do Streamlit
st.set_page_config(
    page_title="FF Karaoke Cloud",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# URL do Firebase (Base de dados compartilhada)
FIREBASE_URL = "https://ffkaraoke-cloud-default-rtdb.firebaseio.com"

# ---------------------------------------------------------
# FUNÇÕES AUXILIARES E DE DADOS
# ---------------------------------------------------------

def get_all_providers():
    try:
        response = requests.get(f"{FIREBASE_URL}/prestadores.json", timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()
            prestadores = [{"token": k, **v} for k, v in data.items()]
            return pd.DataFrame(prestadores)
    except Exception:
        pass
    return pd.DataFrame(columns=['token', 'nome', 'approved', 'tempo_plano', 'data_inicio'])

def limpar_nome_musica(nome):
    if not nome:
        return ""
    import re
    nome_limpo = re.sub(r'\s*\(.*?\)', '', nome)
    nome_limpo = re.sub(r'\s*\[.*?\]', '', nome_limpo)
    return nome_limpo.strip()

def obter_url_video_cloudinary(musica, titulo_limpo):
    if isinstance(musica, dict):
        url = musica.get("url_cloudinary", "") or musica.get("url", "")
        if url:
            return url
    return ""

def obter_video_fundo(provider_token):
    try:
        resp = requests.get(f"{FIREBASE_URL}/video_fundo/{provider_token}.json", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict):
                return data.get("url", "")
    except Exception:
        pass
    return ""

# ---------------------------------------------------------
# TELA DO CLIENTE (REGISTO DE MÚSICA)
# ---------------------------------------------------------
def show_client_page():
    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider", None)

    if not provider_token:
        st.error("Link inválido. Falta o identificador do prestador.")
        return

    st.markdown("""
        <style>
        .stApp { background-color: #000000 !important; color: #ffffff !important; }
        .block-container { background-color: #000000 !important; border: 4px solid #FFC107 !important; border-radius: 12px; padding: 2rem !important; }
        h1, h2, h3, h4, h5, h6, p, span, label, div { font-weight: bold !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.9); }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #ffffff; font-family: monospace;'>🎤 FF KARAOKE - REGISTO DE MÚSICA</h1>", unsafe_allow_html=True)

    with st.form("form_registo_musica"):
        cliente_nome = st.text_input("O seu Nome / Convidado")
        musica_titulo = st.text_input("Título da Música / Artista")
        
        btn_submeter = st.form_submit_button("Submeter Pedido 🎵")
        
        if btn_submeter:
            if not cliente_nome or not musica_titulo:
                st.error("Por favor, preencha todos os campos.")
            else:
                novo_pedido = {
                    "cliente": cliente_nome,
                    "musica": {"titulo": musica_titulo},
                    "estado": "pendente",
                    "timestamp": int(time.time() * 1000)
                }
                try:
                    requests.post(f"{FIREBASE_URL}/pedidos/{provider_token}.json", json=novo_pedido, timeout=10)
                    st.success("Música registada com sucesso! Acompanhe na tela de TV.")
                except Exception as e:
                    st.error(f"Erro ao submeter pedido: {e}")

# ---------------------------------------------------------
# TELA DE TV / REPRODUÇÃO
# ---------------------------------------------------------
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
                }
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

# ---------------------------------------------------------
# GESTÃO DA FILA DO PRESTADOR E PAINEL PERSONALIZADO
# ---------------------------------------------------------
def renderizar_gestao_fila_prestador(provider_token):
    st.markdown("### 📋 Gestão da Fila de Pedidos")
    
    try:
        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        response = requests.get(url_firebase, timeout=10)
        
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            pedidos.sort(key=lambda x: x.get("timestamp", 0))
            
            for p in pedidos:
                p_id = p.get("id")
                cliente = p.get("cliente", "Desconhecido")
                musica = p.get("musica", {})
                titulo = musica.get("titulo", "Música") if isinstance(musica, dict) else str(musica)
                estado = p.get("estado", "pendente")
                
                col_p1, col_p2, col_p3 = st.columns([3, 2, 2])
                with col_p1:
                    st.markdown(f"**{cliente}** - 🎶 {titulo} `({estado})`")
                with col_p2:
                    if estado == "pendente":
                        if st.button("Aprovar / Tocar", key=f"aprov_{p_id}"):
                            requests.put(f"{FIREBASE_URL}/pedidos/{provider_token}/{p_id}/estado.json", json="aprovado", timeout=10)
                            st.rerun()
                    elif estado == "aprovado":
                        if st.button("Terminar", key=f"term_{p_id}"):
                            requests.put(f"{FIREBASE_URL}/pedidos/{provider_token}/{p_id}/estado.json", json="terminado", timeout=10)
                            st.rerun()
                with col_p3:
                    if st.button("Remover", key=f"rem_{p_id}"):
                        requests.delete(f"{FIREBASE_URL}/pedidos/{provider_token}/{p_id}.json", timeout=10)
                        st.rerun()
        else:
            st.info("Nenhum pedido na fila de momento.")
    except Exception as e:
        st.error(f"Erro ao carregar fila: {e}")

    st.markdown("---")
    st.markdown("### 🎬 Pesquisar Vídeo Clipe")
    
    # Campo de pesquisa e lista de clipes de fundo disponíveis
    termo_pesquisa = st.text_input("Pesquisar por nome do artista ou música", key="pesquisa_clipe")
    
    # Simulação de clipes disponíveis ou busca no firebase
    try:
        resp_clips = requests.get(f"{FIREBASE_URL}/biblioteca_videos.json", timeout=10)
        clips = []
        if resp_clips.status_code == 200 and resp_clips.json():
            data_clips = resp_clips.json()
            clips = [{"id": k, **v} for k, v in data_clips.items()]
        
        if termo_pesquisa:
            clips = [c for c in clips if termo_pesquisa.lower() in c.get("titulo", "").lower()]
            
        if clips:
            for clip in clips:
                c_titulo = clip.get("titulo", "Vídeo")
                c_url = clip.get("url", "")
                col_c1, col_c2 = st.columns([4, 1])
                with col_c1:
                    st.markdown(f"📹 {c_titulo}")
                with col_c2:
                    if st.button("Definir Fundo", key=f"clip_{clip.get('id')}"):
                        requests.put(f"{FIREBASE_URL}/video_fundo/{provider_token}.json", json={"url": c_url, "titulo": c_titulo}, timeout=10)
                        st.success("Vídeo clipe de fundo atualizado!")
                        st.rerun()
        else:
            st.info("Nenhum vídeo clipe encontrado na biblioteca.")
    except Exception:
        st.info("Biblioteca de vídeos em atualização.")

def show_provider_panel_custom(provider_token):
    df = get_all_providers()
    nome_prestador = "Prestador"
    tempo_plano = "2 Horas - 12 Mil Kwanzas"
    data_inicio = str(datetime.now())
    
    if not df.empty and 'token' in df.columns:
        prestador_row = df[df['token'] == provider_token]
        if not prestador_row.empty:
            row = prestador_row.iloc[0]
            nome_prestador = row.get('nome', 'Prestador')
            tempo_plano = row.get('tempo_plano', '2 Horas - 12 Mil Kwanzas')
            data_inicio = row.get('data_inicio', str(datetime.now()))

    # Calcular tempo restante com base no plano escolhido
    horas_plano = 2
    if "3 Horas" in tempo_plano:
        horas_plano = 3
    elif "4 Horas" in tempo_plano:
        horas_plano = 4

    try:
        dt_inicio = datetime.strptime(data_inicio.split('.')[0], "%Y-%m-%d %H:%M:%S")
    except Exception:
        dt_inicio = datetime.now()
        
    dt_fim = dt_inicio + timedelta(hours=horas_plano)
    delta_restante = dt_fim - datetime.now()
    segundos_restantes = int(delta_restante.total_seconds())
    if segundos_restantes < 0:
        segundos_restantes = 0

    horas_Restantes = segundos_restantes // 3600
     minutos_Restantes = (segundos_restantes % 3600) // 60
     segundos_restantes_mod = segundos_restantes % 60
     tempo_formatado = f"{horas_Restantes:02d}:{minutos_Restantes:02d}:{segundos_restantes_mod:02d}"

    aviso_reforço_html = ""
    if segundos_restantes <= 1800:
        aviso_reforço_html = """
            <div style="background: rgba(255, 0, 0, 0.25); border: 2px solid #FF0000; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 15px; animation: pulse 1s infinite;">
                <span style="color: #ffffff; font-family: monospace; font-size: 14px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">
                    ⚠️ O SEU TEMPO ESTA TERMINANDO. PARA QUE NÃO PERCAS OS SEUS REGISTOS PEÇA REFORÇO DE TEMPO.
                </span>
            </div>
        """

    st.markdown("""
        <style>
        .stApp { background-color: #000000 !important; color: #ffffff !important; }
        .block-container { background-color: #000000 !important; border: 4px solid #FFC107 !important; border-radius: 12px; padding: 2rem !important; }
        h1, h2, h3, h4, h5, h6, p, span, label, div { font-weight: bold !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.9); }
        .panel-header { display: flex; justify-content: space-between; align-items: center; background: #111; border: 3px solid #FFC107; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
        .card-link { background: #111; border: 3px solid #FFC107; padding: 15px; border-radius: 10px; margin-bottom: 15px; }
        .card-tv { background: #111; border: 3px solid #4CAF50; padding: 15px; border-radius: 10px; margin-bottom: 15px; }
        .link-title { color: #FFC107; font-family: monospace; font-size: 14px; margin-bottom: 5px; }
        .link-title-tv { color: #4CAF50; font-family: monospace; font-size: 14px; margin-bottom: 5px; }
        .link-text { color: #ffffff; font-family: monospace; font-size: 12px; word-break: break-all; }
        .link-text-tv { color: #ffffff; font-family: monospace; font-size: 12px; word-break: break-all; }
        .qr-box { background: #fff; padding: 10px; border-radius: 8px; display: inline-block; }
        </style>
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

# ---------------------------------------------------------
# PAINEL DO ADMINISTRADOR
# ---------------------------------------------------------
def show_admin_panel():
    st.title("⚙️ Painel de Administração - FF Karaoke")
    
    tab1, tab2, tab3 = st.tabs(["Prestadores", "Gestão Total & Reforços", "Biblioteca de Vídeos"])
    
    with tab1:
        st.subheader("Prestadores Registados")
        df_p = get_all_providers()
        if not df_p.empty:
            for idx, row in df_p.iterrows():
                t_token = row.get('token')
                p_nome = row.get('nome', 'Sem Nome')
                p_aprov = row.get('approved', 1)
                p_plano = row.get('tempo_plano', 'N/A')
                
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.markdown(f"**{p_nome}** (`{t_token}`) - Plano: {p_plano}")
                with col2:
                    if p_aprov == 0:
                        if st.button("Aprovar Prestador", key=f"aprov_p_{t_token}"):
                            requests.patch(f"{FIREBASE_URL}/prestadores/{t_token}.json", json={"approved": 1}, timeout=10)
                            st.rerun()
                    else:
                        st.markdown("✅ Aprovado")
                with col3:
                    if st.button("Remover Prestador", key=f"rem_p_{t_token}"):
                        requests.delete(f"{FIREBASE_URL}/prestadores/{t_token}.json", timeout=10)
                        st.rerun()
        else:
            st.info("Nenhum prestador registado.")

        st.markdown("---")
        st.subheader("Registar Novo Prestador (Administrador)")
        with st.form("form_reg_admin_prestador"):
            novo_nome = st.text_input("Nome do Prestador")
            novo_plano = st.selectbox(
                "Duração Pretendida", 
                options=[
                    "2 Horas - 12 Mil Kwanzas", 
                    "3 Horas - 15 Mil Kwanzas", 
                    "4 Horas - 20 Mil Kwanzas"
                ]
            )
            sub_prest = st.form_submit_button("Gerar Prestador")
            if sub_prest:
                if novo_nome:
                    import uuid
                    novo_token = str(uuid.uuid4())[:8]
                    novo_dados = {
                        "nome": novo_nome,
                        "tempo_plano": novo_plano,
                        "data_inicio": str(datetime.now()),
                        "approved": 1,
                        "token": novo_token
                    }
                    try:
                        requests.put(f"{FIREBASE_URL}/prestadores/{novo_token}.json", json=novo_dados, timeout=10)
                        st.success(f"Prestador criado com sucesso! Token: {novo_token}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao criar prestador: {e}")
                else:
                    st.error("Insira o nome do prestador.")

    with tab2:
        st.subheader("Pedidos de Reforço Pendentes")
        try:
            resp_ref = requests.get(f"{FIREBASE_URL}/reforcos_pendentes.json", timeout=10)
            if resp_ref.status_code == 200 and resp_ref.json():
                reforcos_data = resp_ref.json()
                for t_tok, r_val in reforcos_data.items():
                    if isinstance(r_val, dict) and r_val.get("approved", 0) == 0:
                        r_nome = r_val.get("nome_prestador", "Prestador")
                        r_ref = r_val.get("referencia", "N/A")
                        r_plano = r_val.get("tempo_plano", "2 Horas - 12 Mil Kwanzas")
                        
                        col_r1, col_r2, col_r3 = st.columns([3, 2, 2])
                        with col_r1:
                            st.markdown(f"**{r_nome}** - Ref: `{r_ref}` - Pedido: {r_plano}")
                        with col_r2:
                            if st.button("Sim (Aprovar Reforço)", key=f"sim_ref_{t_tok}"):
                                # Atualizar data de início ou somar tempo no prestador
                                resp_prest = requests.get(f"{FIREBASE_URL}/prestadores/{t_tok}.json", timeout=10)
                                if resp_prest.status_code == 200 and resp_prest.json():
                                    p_data = resp_prest.json()
                                    dt_ini_atual = datetime.strptime(str(p_data.get("data_inicio", datetime.now())).split('.')[0], "%Y-%m-%d %H:%M:%S")
                                    
                                    # Adicionar horas do reforço
                                    horas_adicionais = 2
                                    if "3 Horas" in r_plano:
                                        horas_adicionais = 3
                                    elif "4 Horas" in r_plano:
                                        horas_adicionais = 4
                                    
                                    novo_inicio = dt_ini_atual + timedelta(hours=horas_adicionais)
                                    requests.patch(f"{FIREBASE_URL}/prestadores/{t_tok}.json", json={"data_inicio": str(novo_inicio), "tempo_plano": r_plano}, timeout=10)
                                    requests.delete(f"{FIREBASE_URL}/reforcos_pendentes/{t_tok}.json", timeout=10)
                                    st.success("Reforço aprovado com sucesso!")
                                    st.rerun()
                        with col_r3:
                            if st.button("Não (Rejeitar)", key=f"nao_ref_{t_tok}"):
                                requests.delete(f"{FIREBASE_URL}/reforcos_pendentes/{t_tok}.json", timeout=10)
                                st.rerun()
            else:
                st.info("Nenhum pedido de reforço pendente.")
        except Exception as e:
            st.error(f"Erro ao carregar reforços: {e}")

    with tab3:
        st.subheader("Gerir Biblioteca de Vídeos de Fundo")
        with st.form("form_add_video"):
            v_titulo = st.text_input("Título do Vídeo Clipe")
            v_url = st.text_input("URL do Vídeo (Cloudinary ou Direto)")
            sub_vid = st.form_submit_button("Adicionar Vídeo")
            if sub_vid:
                if v_titulo and v_url:
                    novo_video = {"titulo": v_titulo, "url": v_url}
                    try:
                        requests.post(f"{FIREBASE_URL}/biblioteca_videos.json", json=novo_video, timeout=10)
                        st.success("Vídeo adicionado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao adicionar vídeo: {e}")
                else:
                    st.error("Preencha todos os campos.")

# ---------------------------------------------------------
# FUNÇÃO PRINCIPAL DE Roteamento
# ---------------------------------------------------------
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
