import streamlit as st
import streamlit.components.v1 as components
import urllib.parse

# [MANTIDO EXATAMENTE COMO O SEU FICHEIRO ORIGINAL ANTERIOR]
# (Nota: Funções auxiliares, Firebase, Cloudinary, etc., permanecem inalteradas na base)

    st.markdown("""
    <style>
    .stApp { background-color: #000000; color: white; }
    </style>""", unsafe_allow_html=True)

    renderizar_ecra_tv(provider_token)

# SECÇÃO DO PERFIL DO PRESTADOR / LINKS (COM LETRAS MAIORES E NEGRITO)
def show_provider_panel_custom(provider_token):
    host_dominio = st.context.headers.get('Host', 'grupoffkaraoke.streamlit.app')
    link_cliente_absoluto = f"https://{host_dominio}/?page=client_register&prestador={provider_token}"
    link_tela_absoluto = f"https://{host_dominio}/?page=client_screen&prestador={provider_token}"

    st.markdown("""
        <style>
        .link-box-container {
            background-color: #111111;
            border: 2px solid #FFC107;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            font-family: monospace;
        }
        .link-title {
            color: #FFC107;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .link-url {
            font-size: 18px;
            font-weight: bold;
            color: #ffffff;
            word-break: break-all;
            background: #222222;
            padding: 10px;
            border-radius: 6px;
            border: 1px dashed #FFC107;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="link-box-container">
            <div class="link-title">📱 LINK PARA OS CLIENTES PEDIREM MÚSICAS:</div>
            <div class="link-url">{link_cliente_absoluto}</div>
        </div>
        
        <div class="link-box-container">
            <div class="link-title">📺 LINK DA TELA DE TV (EXIBIÇÃO):</div>
            <div class="link-url">{link_tela_absoluto}</div>
        </div>
    """, unsafe_allow_html=True)


def renderizar_ecra_tv(provider_token):
    try:
        frame_styles = """
            <style>
                .marquee-footer {
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    width: 100vw;
                    background: #111;
                    color: #FFC107;
                    font-family: monospace;
                    font-size: 22px;
                    font-weight: bold;
                    overflow: hidden;
                    white-space: nowrap;
                    border-top: 2px solid #FFC107;
                    z-index: 99998;
                    padding: 8px 0;
                }
                .marquee-track {
                    display: inline-block;
                    animation: marquee 25s linear infinite;
                }
                .marquee-item {
                    display: inline-block;
                    padding-right: 50px;
                }
                @keyframes marquee {
                    0% { transform: translateX(0%); }
                    100% { transform: translateX(-50%); }
                }
                .icon-anim {
                    display: inline-block;
                }
            </style>
            <div class="marquee-footer">
                <div class="marquee-track">
                    <span class="marquee-item"><span class="icon-anim">🎵</span> FF KARAOKE CLOUD <span class="icon-anim">🎤</span> CANTE COMIGO <span class="icon-anim">🎶</span> A SUA MÚSICA FAVORITA <span class="icon-anim">🎙️</span> DIVIRTA-SE AO MÁXIMO</span>
                    <span class="marquee-item"><span class="icon-anim">🎵</span> FF KARAOKE CLOUD <span class="icon-anim">🎤</span> CANTE COMIGO <span class="icon-anim">🎶</span> A SUA MÚSICA FAVORITA <span class="icon-anim">🎙️</span> DIVIRTA-SE AO MÁXIMO</span>
                </div>
            </div>
        """

        tocando_agora = obter_tocando_agora(provider_token)
        pedidos_ativos = obter_pedidos_ativos(provider_token)

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
            
            host_dominio = st.context.headers.get('Host', 'grupoffkaraoke.streamlit.app')
            link_cliente_absoluto = f"https://{host_dominio}/?page=client_register&prestador={provider_token}"
            qr_url_cliente = f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={urllib.parse.quote(link_cliente_absoluto)}"

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

                if not pedidos_ativos:
                    st.markdown(f"""
                        <style>
                            @keyframes spinMic {{
                                0% {{ transform: rotate(0deg); }}
                                100% {{ transform: rotate(360deg); }}
                            }}
                            .mic-rotating {{
                                display: inline-block;
                                animation: spinMic 4s linear infinite;
                            }}
                        </style>
                        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: #111; border: 2px solid #FFC107; border-radius: 10px; padding: 20px; margin-top: 15px; margin-bottom: 40px; text-align: center;">
                            <p style="color: #FFC107; font-family: monospace; font-size: 15px; margin-bottom: 10px; font-weight: bold;">📱 ESCANEIE PARA PEDIR UMA MÚSICA:</p>
                            <img src="{qr_url_cliente}" width="160" style="border-radius: 6px; border: 4px solid #fff; margin-bottom: 15px;" />
                            <div class="mic-rotating" style="font-size: 55px; margin-top: 5px;">🎤</div>
                        </div>
                    """, unsafe_allow_html=True)

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
                show_provider_panel_center(token) # type: ignore
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
            
        # ÁREA RESTRITA CENTRALIZADA
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
