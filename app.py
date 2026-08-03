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

# URL do Firebase (Definida globalmente para evitar erros)
FIREBASE_URL = "https://ffkaraoke-default-rtdb.firebaseio.com"

# --- FUNÇÕES AUXILIARES DE SUPORTE ---

def limpar_nome_musica(nome):
    if not nome:
        return ""
    return str(nome).replace(".mp4", "").replace(".avi", "").replace(".mkv", "").strip()

def obter_url_video_cloudinary(musica, titulo_limpo):
    if isinstance(musica, dict):
        url = musica.get("url_cloudinary", "") or musica.get("url", "")
        if url:
            return url
    return ""

def obter_video_fundo(provider_token):
    try:
        url = f"{FIREBASE_URL}/config_fundo/{provider_token}.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            data = res.json()
            if isinstance(data, dict):
                return data.get("url_clipe", "")
    except Exception:
        pass
    return ""

def get_all_providers():
    try:
        url = f"{FIREBASE_URL}/prestadores.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            data = res.json()
            prestadores_lista = [{"token": k, **v} for k, v in data.items()]
            return pd.DataFrame(prestadores_lista)
    except Exception:
        pass
    return pd.DataFrame()


# --- GESTÃO DA FILA DO PRESTADOR ---

def renderizar_gestao_fila_prestador(provider_token):
    st.markdown("### 🎛️ Gestão da Fila de Espera", unsafe_allow_html=True)
    
    try:
        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        response = requests.get(url_firebase, timeout=10)
        
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            pedidos.sort(key=lambda x: x.get("timestamp", 0))
            
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            
            if not pedidos_ativos:
                st.info("A fila de reprodução está vazia no momento.")
            else:
                for p in pedidos_ativos:
                    p_id = p.get("id")
                    cliente = p.get("cliente", "Desconhecido")
                    musica = p.get("musica", {})
                    titulo = musica.get("titulo", "Música") if isinstance(musica, dict) else str(musica)
                    estado = p.get("estado")
                    
                    cols = st.columns([3, 1, 1])
                    with cols[0]:
                        st.markdown(f"**Cliente:** {cliente} | **Música:** {titulo} | *Estado:* `{estado}`")
                    with cols[1]:
                        if estado == "pendente":
                            if st.button("Aprovar", key=f"aprov_{p_id}"):
                                requests.put(f"{FIREBASE_URL}/pedidos/{provider_token}/{p_id}/estado.json", json="aprovado", timeout=5)
                                st.rerun()
                    with cols[2]:
                        if st.button("Remover/Terminar", key=f"term_{p_id}"):
                            requests.put(f"{FIREBASE_URL}/pedidos/{provider_token}/{p_id}/estado.json", json="terminado", timeout=5)
                            st.rerun()
        else:
            st.info("Nenhum pedido registado.")
    except Exception as e:
        st.error(f"Erro ao carregar a fila: {e}")

    # Configuração de Vídeo Clipe de Fundo (Tela) com botão Verde
    st.markdown("---")
    st.markdown("### 📺 Configuração de Vídeo Clipe de Fundo (Tela)")
    
    url_atual_fundo = obter_video_fundo(provider_token)
    novo_clipe_fundo = st.text_input("URL do Vídeo Clipe de Fundo (MP4)", value=url_atual_fundo)
    
    # Inserção de estilos para colorir o botão de Pesquisar Vídeo Clipe de Verde
    st.markdown("""
        <style>
        div.stButton > button:first-child {
            background-color: #28a745 !important;
            color: white !important;
            border-color: #28a745 !important;
            font-weight: bold !important;
        }
        div.stButton > button:first-child:hover {
            background-color: #218838 !important;
            border-color: #1e7e34 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if st.button("Pesquisar Vídeo Clipe"):
        try:
            payload = {"url_clipe": novo_clipe_fundo}
            requests.put(f"{FIREBASE_URL}/config_fundo/{provider_token}.json", json=payload, timeout=5)
            st.success("Vídeo clipe de fundo atualizado com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar fundo: {e}")


# --- PAINEL DO CLIENTE (REGISTO) ---

def show_client_page():
    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider")

    if not provider_token:
        st.error("Link de registo inválido. Falta o token do prestador.")
        return

    st.markdown("""
        <style>
        .stApp { background-color: #000000; color: white; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🎤 Registo de Música - FF Karaoke")
    
    with st.form("form_registo_musica"):
        nome_cliente = st.text_input("O seu Nome / alcunha")
        titulo_musica = st.text_input("Título da Música ou Artista")
        submit_musica = st.form_submit_button("Submeter Pedido de Música")

        if submit_musica:
            if not nome_cliente or not titulo_musica:
                st.error("Por favor, preencha todos os campos.")
            else:
                novo_pedido = {
                    "cliente": nome_cliente,
                    "musica": {"titulo": titulo_musica},
                    "estado": "pendente",
                    "timestamp": int(time.time() * 1000)
                }
                try:
                    res = requests.post(f"{FIREBASE_URL}/pedidos/{provider_token}.json", json=novo_pedido, timeout=10)
                    if res.status_code == 200:
                        st.success("Música enviada para a fila com sucesso! Aguarde a reprodução.")
                    else:
                        st.error("Erro ao enviar a música.")
                except Exception as e:
                    st.error(f"Erro de conexão: {e}")


# --- TELA DE TV / REPRODUÇÃO ---

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

            <div class="speaker-box speaker-tl"><div class="woofer"><div class="woofer-inner"></div></div><div class="woofer"><div class="woofer-inner"></div></div></div>
            <div class="speaker-box speaker-tr"><div class="woofer"><div class="woofer-inner"></div></div><div class="woofer"><div class="woofer-inner"></div></div></div>
            <div class="speaker-box speaker-bl"><div class="woofer"><div class="woofer-inner"></div></div><div class="woofer"><div class="woofer-inner"></div></div></div>
            <div class="speaker-box speaker-br"><div class="woofer"><div class="woofer-inner"></div></div><div class="woofer"><div class="woofer-inner"></div></div></div>

            <div class="marquee-footer">
                <div class="marquee-track">
                    <span class="marquee-item"><span class="icon-anim">🎵</span> FF KARAOKE CLOUD <span class="icon-anim">🎤</span> CANTE COMIGO <span class="icon-anim">🎶</span> A SUA MÚSICA FAVORITA <span class="icon-anim">🎙️</span> DIVIRTA-SE AO MÁXIMO</span>
                    <span class="marquee-item"><span class="icon-anim">🎵</span> FF KARAOKE CLOUD <span class="icon-anim">🎤</span> CANTE COMIGO <span class="icon-anim">🎶</span> A SUA MÚSICA FAVORITA <span class="icon-anim">🎙️</span> DIVIRTA-SE AO MÁXIMO</span>
                </div>
            </div>
        """

        if tocando_agora:
            musica = tocando_agora.get("musica", {})
            titulo = musica.get("titulo", "Karaoke") if isinstance(musica, dict) else str(musica)
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
                        z-index: 99999; color: #ffffff; font-family: monospace; font-size: 15vw; font-weight: bold;
                        text-shadow: 2px 2px 5px rgba(0,0,0,0.9); animation: zoomInNumber 0.9s ease-in-out infinite;
                    }}
                </style>
                <div id="countdown-screen" class="countdown-overlay">3</div>
                <div id="karaoke-container" style="display: none; width: 100vw; height: 100vh; background: black; position: fixed; top: 0; left: 0;">
                    <video id="karaoke-player" width="100%" height="100%" autoplay playsinline style="object-fit: contain; background: black; width: 100%; height: 100%;">
                        <source src="{url_video}" type="video/mp4">
                    </video>
                </div>
                <script>
                    var count = 3;
                    var cdScreen = document.getElementById('countdown-screen');
                    var timer = setInterval(function() {{
                        count--;
                        if (count > 0) {{ cdScreen.innerText = count; }}
                        else if (count === 0) {{ cdScreen.innerText = "🎤 CANTE!"; }}
                        else {{
                            clearInterval(timer);
                            cdScreen.style.display = 'none';
                            document.getElementById('karaoke-container').style.display = 'block';
                            var video = document.getElementById('karaoke-player');
                            video.muted = false;
                            video.play().catch(e => {{ video.muted = true; video.play(); }});
                        }}
                    }}, 1000);
                </script>
            """
            components.html(video_html, height=750, scrolling=False)
        else:
            url_clipe_fundo = obter_video_fundo(provider_token)
            st.markdown(frame_styles, unsafe_allow_html=True)
            col_esq, col_dir = st.columns([1, 1])
            with col_esq:
                st.markdown('<div style="border: 4px solid #FFC107; border-radius: 10px; padding: 15px; background: rgba(0,0,0,0.95); color: white;"><b>FILA DE ESPERA DE MÚSICAS</b></div>', unsafe_allow_html=True)
            with col_dir:
                if url_clipe_fundo:
                    st.video(url_clipe_fundo, autoplay=True, loop=True, muted=True)
                else:
                    st.markdown("Aguardando clipe de fundo...")
    except Exception as e:
        st.error(f"Erro na TV: {e}")

def show_client_screen():
    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider")
    if provider_token:
        renderizar_ecra_tv(provider_token)
    else:
        st.error("Token em falta.")


# --- PAINEL DO PRESTADOR CUSTOMIZADO ---

def show_provider_panel_custom(provider_token):
    # Buscar dados do prestador
    df = get_all_providers()
    nome_prestador = "Prestador"
    tempo_plano = "2 Horas - 12 Mil Kwanzas"
    segundos_restantes = 7200 # Padrão
    
    if not df.empty and 'token' in df.columns:
        row = df[df['token'] == provider_token]
        if not row.empty:
            r = row.iloc[0]
            nome_prestador = r.get('nome_prestador', 'Prestador')
            tempo_plano = r.get('tempo_plano', '2 Horas - 12 Mil Kwanzas')
            
            # Cálculo do tempo estimado (simulado por tempo de registo ou dados)
            # Caso haja um tempo armazenado, podemos calcular:
            data_reg = r.get('data_registo', str(datetime.now()))
            try:
                dt_reg = datetime.strptime(data_reg.split('.')[0], "%Y-%m-%d %H:%M:%S")
                # Definir horas com base no plano escolhido
                horas_totais = 2
                if "3 Horas" in tempo_plano: horas_totais = 3
                elif "4 Horas" in tempo_plano: horas_totais = 4
                
                exp_time = dt_reg + timedelta(hours=horas_totais)
                segundos_restantes = int((exp_time - datetime.now()).total_seconds())
                if segundos_restantes < 0: segundos_restantes = 0
            except Exception:
                segundos_restantes = 3600

    # Formatar o tempo restante em formato decrescente (ex: 02:00:00)
    horas_dec = segundos_restantes // 3600
    mins_dec = (segundos_restantes % 3600) // 60
    secs_dec = segundos_restantes % 60
    tempo_formatado = f"{horas_dec:02d}:{mins_dec:02d}:{secs_dec:02d}"

    # Verificação de alerta de 30 minutos (1800 segundos)
    aviso_reforço_html = ""
    piscar_classe = ""
    if segundos_restantes <= 1800:
        piscar_classe = "animation: blinkWarning 1s infinite;"
        aviso_reforço_html = """
        <div style="background: #dc3545; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; font-family: monospace; margin-bottom: 15px; font-size: 15px; border: 2px solid #ffc107;">
            ⚠️ O SEU TEMPO ESTA TERMINANDO. PARA QUE NÃO PERCAS OS SEUS REGISTOS PEÇA REFORÇO DE TEMPO.
        </div>
        """

    st.markdown(f"""
        <style>
            @keyframes blinkWarning {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.4; }}
                100% {{ opacity: 1; }}
            }}
            .panel-header {{
                background: #111;
                border: 4px solid #FFC107;
                border-radius: 10px;
                padding: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }}
            .cronometro-box {{
                {piscar_classe}
            }}
        </style>
        <div class="panel-header">
            <div>
                <h1 style="margin: 0; color: #ffffff; font-family: monospace; font-size: 24px; text-transform: uppercase;">🎤 PAINEL DO PRESTADOR: {nome_prestador}</h1>
                <p style="margin: 3px 0 0 0; color: #ffffff; font-size: 13px; font-family: monospace;">TOKEN: <code>{provider_token}</code></p>
            </div>
            <div class="cronometro-box" style="background: rgba(255,193,7,0.15); border: 2px solid #FFC107; padding: 6px 12px; border-radius: 8px; text-align: right;">
                <div style="font-family: monospace; color: #ffffff; font-size: 11px;">TEMPO / PLANO ESCOLHIDO</div>
                <div style="font-family: monospace; color: #ffffff; font-size: 18px; font-weight: bold;">⏱️ {tempo_formatado} ({tempo_plano})</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(aviso_reforço_html, unsafe_allow_html=True)

    # Links e QR Code
    link_cliente_rel = f"/?page=client_register&prestador={provider_token}"
    link_tv_rel = f"/?page=client_screen&prestador={provider_token}"
    host_dominio = st.context.headers.get('Host', 'grupoffkaraoke.streamlit.app')
    link_cliente_absoluto = f"https://{host_dominio}{link_cliente_rel}"
    link_tv_absoluto = f"https://{host_dominio}{link_tv_rel}"
    qr_url_cliente = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={urllib.parse.quote(link_cliente_absoluto)}"

    col_links, col_qr = st.columns([3, 1])
    with col_links:
        st.markdown(f"**Link do Cliente:** [{link_cliente_absoluto}]({link_cliente_rel})")
        st.markdown(f"**Link da Tela de TV:** [{link_tv_absoluto}]({link_tv_rel})")
    with col_qr:
        st.image(qr_url_cliente, width=110)

    # Secção de pedido de reforço rápido se faltar pouco tempo ou pedido manual
    if segundos_restantes <= 1800:
        st.markdown("### ⚡ Solicitar Reforço de Tempo")
        with st.form("form_reforco_prestador"):
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
                dados_reforco = {
                    "token": provider_token,
                    "nome_prestador": nome_prestador,
                    "tempo_plano": duracao_reforco,
                    "approved": 0,
                    "data_registo": str(datetime.now())
                }
                try:
                    requests.put(f"{FIREBASE_URL}/reforcos_pendentes/{provider_token}.json", json=dados_reforco, timeout=10)
                    st.success("Pedido de reforço submetido com sucesso! Aguarde a confirmação do Administrador.")
                except Exception as err:
                    st.error(f"Erro ao enviar reforço: {err}")

    st.markdown("---")
    renderizar_gestao_fila_prestador(provider_token)


# --- PAINEL DE ADMINISTRADOR ---

def show_admin_panel():
    st.title("🛠️ Painel de Administração - Gestão Total")
    
    tab1, tab2 = st.tabs(["Prestadores Registados", "Pedidos de Reforço de Tempo"])
    
    with tab1:
        st.subheader("Aprovação e Controlo de Prestadores")
        df_p = get_all_providers()
        if not df_p.empty:
            for idx, row in df_p.iterrows():
                token = row.get("token")
                nome = row.get("nome_prestador", "N/A")
                aprovado = row.get("approved", 1)
                
                cols = st.columns([3, 1, 1])
                with cols[0]:
                    st.write(f"**{nome}** (Token: `{token}`) - Plano: {row.get('tempo_plano', 'N/A')}")
                with cols[1]:
                    if aprovado == 0 or aprovado == "0":
                        if st.button("Aprovar Prestador", key=f"apr_p_{token}"):
                            requests.patch(f"{FIREBASE_URL}/prestadores/{token}.json", json={"approved": 1}, timeout=5)
                            st.rerun()
                    else:
                        st.success("Aprovado")
                with cols[2]:
                    if st.button("Remover", key=f"del_p_{token}"):
                        requests.delete(f"{FIREBASE_URL}/prestadores/{token}.json", timeout=5)
                        st.rerun()
        else:
            st.info("Nenhum prestador encontrado.")

    with tab2:
        st.subheader("Gestão de Reforços de Tempo Solicitados")
        try:
            res_ref = requests.get(f"{FIREBASE_URL}/reforcos_pendentes.json", timeout=5)
            if res_ref.status_code == 200 and res_ref.json():
                reforcos = res_ref.json()
                for token, info in reforcos.items():
                    if isinstance(info, dict) and info.get("approved", 0) == 0:
                        st.markdown(f"**Prestador:** {info.get('nome_prestador')} | **Plano Solicitado:** {info.get('tempo_plano')}")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Sim (Aprovar Reforço)", key=f"sim_ref_{token}"):
                                # Aprova e atualiza o tempo acumulando no prestador principal
                                requests.patch(f"{FIREBASE_URL}/reforcos_pendentes/{token}.json", json={"approved": 1}, timeout=5)
                                requests.patch(f"{FIREBASE_URL}/prestadores/{token}.json", json={"tempo_plano": info.get('tempo_plano'), "data_registo": str(datetime.now())}, timeout=5)
                                st.success("Reforço aprovado com sucesso!")
                                st.rerun()
                        with c2:
                            if st.button("Não (Rejeitar)", key=f"nao_ref_{token}"):
                                requests.delete(f"{FIREBASE_URL}/reforcos_pendentes/{token}.json", timeout=5)
                                st.rerun()
            else:
                st.info("Nenhum pedido de reforço pendente.")
        except Exception as e:
            st.error(f"Erro ao carregar reforços: {e}")

    # Registo manual de novo prestador com opções fixas atualizadas
    st.markdown("---")
    st.subheader("➕ Registar Novo Prestador (Administrador)")
    with st.form("form_novo_prestador"):
        novo_nome = st.text_input("Nome do Prestador")
        novo_token = st.text_input("Token Único (ex: carlos123)")
        nova_duracao = st.selectbox(
            "Duração / Plano Escolhido", 
            options=[
                "2 Horas - 12 Mil Kwanzas", 
                "3 Horas - 15 Mil Kwanzas", 
                "4 Horas - 20 Mil Kwanzas"
            ]
        )
        btn_criar = st.form_submit_button("Criar Prestador")
        if btn_criar:
            if novo_nome and novo_token:
                dados_novo = {
                    "nome_prestador": novo_nome,
                    "token": novo_token,
                    "tempo_plano": nova_duracao,
                    "approved": 1,
                    "data_registo": str(datetime.now())
                }
                requests.put(f"{FIREBASE_URL}/prestadores/{novo_token}.json", json=dados_novo, timeout=5)
                st.success("Prestador criado com sucesso!")
                st.rerun()
            else:
                st.error("Preencha todos os campos obrigatórios.")


# --- ROTEAMENTO PRINCIPAL ---

def main():
    try:
        query_params = st.query_params
        
        if "page" in query_params and query_params["page"] == "client_register":
            show_client_page()
            return

        if "page" in query_params and query_params["page"] == "client_screen":
            show_client_screen()
            return

        token = query_params.get("prestador") or query_params.get("token") or query_params.get("provider")
        
        if token:
            df = get_all_providers()
            if not df.empty and 'token' in df.columns and (df['token'] == token).any():
                row = df[df['token'] == token].iloc[0]
                if row.get('approved', 1) == 1:
                    show_provider_panel_custom(token)
                    return
                else:
                    st.warning("⏳ O seu registo aguarda aprovação do Administrador.")
                    return
            else:
                show_provider_panel_custom(token)
                return

        # Login de Administrador padrão
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
