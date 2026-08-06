import streamlit as st
import streamlit.components.v1 as components
import requests
import time

def show_provider_panel_custom(provider_token, FIREBASE_URL):
    st.markdown("""
        <style>
            .provider-header {
                font-family: monospace;
                font-weight: bold;
                color: #FFC107;
                text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 class='provider-header'>🎛️ Painel de Controlo do Prestador</h2>", unsafe_allow_html=True)
    st.write(f"Token do Estabelecimento: `{provider_token}`")

    url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json?_t={time.time()}"
    try:
        response = requests.get(url_firebase, timeout=10)
        pedidos_ativos = []
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
    except Exception as e:
        st.error(f"Erro ao carregar dados do Firebase: {e}")
        pedidos_ativos = []

    # Abas organizadas: Pedidos, Vídeo de Fundo, Perfil e Customização Avançada
    tab1, tab2, tab3 = st.tabs(["🎵 Fila de Pedidos", "📺 Vídeo de Fundo", "⚙️ Perfil, Cores e Campos"])

    with tab1:
        st.subheader("Gerenciamento da Fila de Espera")
        if not pedidos_ativos:
            st.info("Não existem pedidos pendentes ou em reprodução no momento.")
        else:
            for idx, p in enumerate(pedidos_ativos):
                p_id = p.get("id")
                cliente = p.get("cliente", "Convidado")
                musica = p.get("musica", {})
                titulo = musica.get("titulo", musica.get("nome", "Karaoke")) if isinstance(musica, dict) else str(musica)
                estado = p.get("estado")

                cols = st.columns([3, 2, 1])
                with cols[0]:
                    st.markdown(f"**{idx+1}. Cliente:** {cliente} <br>🎵 *{titulo}*", unsafe_allow_html=True)
                with cols[1]:
                    st.markdown(f"Estado: `{estado}`")
                with cols[2]:
                    if estado == "pendente":
                        if st.button("Aprovar", key=f"apr_{p_id}"):
                            _atualizar_estado_pedido(provider_token, p_id, "aprovado", FIREBASE_URL)
                            st.rerun()
                    elif estado == "aprovado":
                        if st.button("Terminar", key=f"ter_{p_id}"):
                            _atualizar_estado_pedido(provider_token, p_id, "terminado", FIREBASE_URL)
                            st.rerun()

    with tab2:
        st.subheader("Seleção de Vídeo de Fundo (Descanso de Tela)")
        st.write("Escolha um clipe para ser reproduzido automaticamente na TV quando a fila de espera estiver vazia.")
        
        url_atual = _obter_video_fundo(provider_token, FIREBASE_URL)
        nova_url_fundo = st.text_input("URL do Vídeo de Fundo (MP4/Cloudinary):", value=url_atual or "")
        
        if st.button("Guardar Vídeo de Fundo"):
            _salvar_video_fundo(provider_token, nova_url_fundo, FIREBASE_URL)
            st.success("Vídeo de fundo atualizado com sucesso!")
            st.rerun()

    with tab3:
        st.subheader("👤 Perfil, Cores e Customização de Campos")
        st.write("Altere os dados institucionais, personalize letras, cores das caixas e campos exibidos na TV e no painel.")
        
        perfil_atual = _obter_perfil_prestador(provider_token, FIREBASE_URL)
        
        st.markdown("### 📋 Informações Básicas do Espaço")
        nome_estabelecimento = st.text_input("Nome do Estabelecimento / Espaço:", value=perfil_atual.get("nome", ""))
        responsavel = st.text_input("Nome do Responsável:", value=perfil_atual.get("responsavel", ""))
        contacto = st.text_input("Contacto Telefónico:", value=perfil_atual.get("contacto", ""))
        
        st.markdown("### 🎨 Personalização Visual e Textos do Ecrã")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            cor_texto_atual = perfil_atual.get("cor_texto", "#FFFFFF")
            cor_texto = st.color_picker("Cor das Letras / Textos:", value=cor_texto_atual)
        with col_c2:
            cor_borda_atual = perfil_atual.get("cor_borda", "#FFC107")
            cor_borda = st.color_picker("Cor dos Contornos / Bordas:", value=cor_borda_atual)

        fonte_escolhida = st.selectbox(
            "Estilo de Letra (Fonte):", 
            ["monospace", "Arial", "Courier New", "Verdana", "Georgia"],
            index=["monospace", "Arial", "Courier New", "Verdana", "Georgia"].index(perfil_atual.get("fonte", "monospace")) if perfil_atual.get("fonte") in ["monospace", "Arial", "Courier New", "Verdana", "Georgia"] else 0
        )

        mensagem_rodape = st.text_input(
            "Mensagem Personalizada do Letreiro (Rodapé da TV):", 
            value=perfil_atual.get("mensagem_rodape", "FF KARAOKE CLOUD 🎤 CANTE COMIGO 🎶 A SUA MÚSICA FAVORITA")
        )
        
        if st.button("💾 Guardar Todas as Alterações"):
            dados_atualizados = {
                "nome": nome_estabelecimento,
                "responsavel": responsavel,
                "contacto": contacto,
                "cor_texto": cor_texto,
                "cor_borda": cor_borda,
                "fonte": fonte_escolhida,
                "mensagem_rodape": mensagem_rodape
            }
            _salvar_perfil_prestador(provider_token, dados_atualizados, FIREBASE_URL)
            st.success("Perfil e customizações guardados com sucesso!")
            st.rerun()
            
        st.markdown("---")
        if st.button("🔄 Atualizar Painel Geral"):
            st.rerun()


@st.fragment(run_every=3)
def renderizar_ecra_tv(provider_token, FIREBASE_URL, limpar_nome_musica_func=None, obter_url_video_cloudinary_func=None):
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

        # Buscar definições customizadas do perfil do prestador
        perfil = _obter_perfil_prestador(provider_token, FIREBASE_URL)
        cor_txt = perfil.get("cor_texto", "#FFFFFF")
        cor_brd = perfil.get("cor_borda", "#FFC107")
        fonte_utilizada = perfil.get("fonte", "monospace")
        texto_rodape = perfil.get("mensagem_rodape", "FF KARAOKE CLOUD 🎤 CANTE COMIGO 🎶 A SUA MÚSICA FAVORITA")
        
        frame_styles = f"""
            <style>
                @keyframes pulseSpeaker {{
                    0% {{ transform: scale(1); filter: drop-shadow(0 0 2px {cor_brd}); }}
                    50% {{ transform: scale(1.12); filter: drop-shadow(0 0 14px {cor_brd}); }}
                    100% {{ transform: scale(1); filter: drop-shadow(0 0 2px {cor_brd}); }}
                }}
                @keyframes bounceIcon {{
                    0%, 100% {{ transform: translateY(0) rotate(0deg); }}
                    50% {{ transform: translateY(-5px) rotate(10deg); }}
                }}
                @keyframes marqueeFast {{
                    0% {{ transform: translateX(0%); }}
                    100% {{ transform: translateX(-50%); }}
                }}
                .speaker-box {{
                    position: fixed;
                    z-index: 99998;
                    width: 90px;
                    height: 140px;
                    background: #111;
                    border: 4px solid {cor_brd};
                    border-radius: 10px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: space-around;
                    padding: 8px 0;
                    box-shadow: 0 0 15px rgba(255, 193, 7, 0.4);
                    pointer-events: none;
                    animation: pulseSpeaker 0.55s infinite ease-in-out;
                }}
                .woofer {{
                    width: 55px;
                    height: 55px;
                    border: 3px solid {cor_brd};
                    border-radius: 50%;
                    background: radial-gradient(circle, #333 30%, #000 90%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: inset 0 0 8px {cor_brd};
                }}
                .woofer-inner {{
                    width: 22px;
                    height: 22px;
                    background: {cor_brd};
                    border-radius: 50%;
                }}
                .speaker-tl {{ top: 15px; left: 15px; }}
                .speaker-tr {{ top: 15px; right: 15px; }}
                .speaker-bl {{ bottom: 50px; left: 15px; }}
                .speaker-br {{ bottom: 50px; right: 15px; }}

                .marquee-footer {{
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    width: 100vw;
                    height: 38px;
                    background: #111;
                    border-top: 4px solid {cor_brd};
                    z-index: 99997;
                    overflow: hidden;
                    display: flex;
                    align-items: center;
                    white-space: nowrap;
                    pointer-events: none;
                }}
                .marquee-track {{
                    display: inline-block;
                    white-space: nowrap;
                    animation: marqueeFast 15s linear infinite;
                    font-family: {fonte_utilizada};
                    font-size: 16px;
                    color: {cor_txt};
                    font-weight: bold;
                    text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
                }}
                .marquee-item {{
                    display: inline-flex;
                    align-items: center;
                    gap: 12px;
                    margin-right: 40px;
                }}
                .icon-anim {{
                    display: inline-block;
                    animation: bounceIcon 0.8s infinite ease-in-out;
                }}
            </style>
            <div class="speaker-box speaker-tl"><div class="woofer"><div class="woofer-inner"></div></div><div class="woofer"><div class="woofer-inner"></div></div></div>
            <div class="speaker-box speaker-tr"><div class="woofer"><div class="woofer-inner"></div></div><div class="woofer"><div class="woofer-inner"></div></div></div>
            <div class="speaker-box speaker-bl"><div class="woofer"><div class="woofer-inner"></div></div><div class="woofer"><div class="woofer-inner"></div></div></div>
            <div class="speaker-box speaker-br"><div class="woofer"><div class="woofer-inner"></div></div><div class="woofer"><div class="woofer-inner"></div></div></div>

            <div class="marquee-footer">
                <div class="marquee-track">
                    <span class="marquee-item"><span class="icon-anim">🎵</span> {texto_rodape}</span>
                    <span class="marquee-item"><span class="icon-anim">🎵</span> {texto_rodape}</span>
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
            
            if limpar_nome_musica_func:
                titulo = limpar_nome_musica_func(titulo)
            if obter_url_video_cloudinary_func:
                url_video = obter_url_video_cloudinary_func(musica, titulo)
            
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
                    z-index: 99999; color: {cor_txt}; font-family: {fonte_utilizada}; font-size: 15vw; font-weight: bold;
                    text-shadow: 2px 2px 5px rgba(0,0,0,0.9); animation: zoomInNumber 0.9s ease-in-out infinite;
                }}
            </style>
            <div id="countdown-screen" class="countdown-overlay">3</div>
            <div id="karaoke-container" style="display: none; width: 100vw; height: 100vh; background: black; position: fixed; top: 0; left: 0;">
                <video id="karaoke-player" width="100%" height="100%" autoplay playsinline style="object-fit: contain; background: black; width: 100%; height: 100%;">
                    <source src="{url_video}" type="video/mp4">
                </video>
                <div id="audio-warning" style="display: none; position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); text-align: center; background: #222; border: 4px solid {cor_brd}; padding: 10px 20px; border-radius: 5px; z-index: 99999;">
                    <p style="color: {cor_txt}; margin: 0 0 8px 0; font-family: {fonte_utilizada}; font-size: 14px; font-weight: bold;">⚠️ O navegador bloqueou o áudio automático.</p>
                    <button onclick="unmuteVideo()" style="background-color: #4CAF50; color: white; border: none; padding: 8px 16px; font-size: 15px; border-radius: 4px; cursor: pointer; font-weight: bold;">🔊 CLIQUE AQUI PARA ATIVAR O SOM</button>
                </div>
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
                    }}).then(_ => {{ setTimeout(() => window.location.reload(), 300); }})
                      .catch(_ => {{ window.location.reload(); }});
                }}
                var video = document.getElementById('karaoke-player');
                if (video) {{ video.onended = function() {{ stopKaraoke(); }}; }}
            </script>
            """
            components.html(video_html, height=750, scrolling=False)
        else:
            url_clipe_fundo = _obter_video_fundo(provider_token, FIREBASE_URL)
            proximo_cantor = pedidos_ativos[0] if pedidos_ativos else None

            st.markdown(frame_styles, unsafe_allow_html=True)
            col_esq, col_dir = st.columns([1, 1])
            
            with col_esq:
                if proximo_cantor:
                    c_prox = proximo_cantor.get("cliente", "Convidado")
                    st.markdown(f"""
                        <div style="border: 4px solid {cor_brd}; border-radius: 10px; padding: 15px; background: rgba(0,0,0,0.95); margin-bottom: 15px; display: flex; align-items: center; gap: 15px;">
                            <span style="color: {cor_txt}; font-size: 20px; font-weight: bold; font-family: {fonte_utilizada};">Á SEGUIR</span>
                            <span style="color: {cor_txt}; font-size: 20px; font-weight: bold; font-family: {fonte_utilizada}; text-transform: uppercase;">{c_prox}</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style="border: 4px solid {cor_brd}; border-radius: 10px; padding: 15px; text-align: center; background: rgba(0,0,0,0.95); margin-bottom: 15px;">
                            <h2 style="color: {cor_txt}; margin: 0; font-family: {fonte_utilizada}; font-weight: bold;">🎤 FILA DE ESPERA VAZIA</h2>
                        </div>
                    """, unsafe_allow_html=True)
                
                html_caixas = '<div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 40px;">'
                demais_pedidos = pedidos_ativos[1:] if len(pedidos_ativos) > 1 else []
                for idx, p_item in enumerate(demais_pedidos, start=2):
                    c_item = p_item.get("cliente", "Convidado")
                    html_caixas += f'<div style="background: rgba(0,0,0,0.95); border: 4px solid {cor_brd}; border-radius: 8px; padding: 12px; color: {cor_txt}; font-family: {fonte_utilizada}; font-size: 16px; font-weight: bold;"><b>{idx}.</b> {c_item}</div>'
                html_caixas += '</div>'
                st.markdown(html_caixas, unsafe_allow_html=True)

            with col_dir:
                if url_clipe_fundo:
                    video_fundo_html = f"""
                    <div style="display: flex; justify-content: center; background: rgba(0,0,0,0.95); border: 4px solid {cor_brd}; border-radius: 10px; padding: 5px; width: 100%; position: relative; margin-top: 5px; margin-bottom: 40px;">
                        <video id="fundo-player" width="100%" height="450px" autoplay loop playsinline controlslist="nodownload noremoteplayback" disablepictureinpicture style="object-fit: contain; background: black; border-radius: 8px;">
                            <source src="{url_clipe_fundo}" type="video/mp4">
                        </video>
                        <div id="fundo-audio-warning" style="display: none; position: absolute; bottom: 15px; right: 15px; background: rgba(0,0,0,0.8); border: 2px solid {cor_brd}; padding: 6px 10px; border-radius: 5px; cursor: pointer;" onclick="unmuteFundo()">
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
                    st.markdown(f"""
                        <div style="border: 4px solid {cor_brd}; border-radius: 10px; padding: 100px 20px; text-align: center; background: rgba(0,0,0,0.95); color: {cor_txt}; font-family: {fonte_utilizada}; margin-top: 5px; margin-bottom: 40px; font-weight: bold;">
                            <div style="font-size: 40px; margin-bottom: 10px;">📺</div>
                            <p style="color: {cor_txt}; font-size: 16px; margin: 0; font-weight: bold;">Aguardando o prestador selecionar um vídeo clipe no painel de controle...</p>
                        </div>
                    """, unsafe_allow_html=True)  
    except Exception as e:
        st.error(f"Erro de sincronização na TV: {e}")


def _atualizar_estado_pedido(provider_token, pedido_id, novo_estado, FIREBASE_URL):
    url = f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}/estado.json"
    try:
        requests.put(url, json=novo_estado, timeout=5)
    except Exception as e:
        st.error(f"Erro ao atualizar estado: {e}")


def _obter_video_fundo(provider_token, FIREBASE_URL):
    url = f"{FIREBASE_URL}/configuracoes/{provider_token}/video_fundo.json"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return ""


def _salvar_video_fundo(provider_token, url_video, FIREBASE_URL):
    url = f"{FIREBASE_URL}/configuracoes/{provider_token}/video_fundo.json"
    try:
        requests.put(url, json=url_video, timeout=5)
    except Exception as e:
        st.error(f"Erro ao salvar vídeo de fundo: {e}")


def _obter_perfil_prestador(provider_token, FIREBASE_URL):
    url = f"{FIREBASE_URL}/configuracoes/{provider_token}/perfil.json"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            return res.json()
    except:
        pass
    return {}


def _salvar_perfil_prestador(provider_token, dados_perfil, FIREBASE_URL):
    url = f"{FIREBASE_URL}/configuracoes/{provider_token}/perfil.json"
    try:
        requests.put(url, json=dados_perfil, timeout=5)
    except Exception as e:
        st.error(f"Erro ao salvar perfil: {e}")
