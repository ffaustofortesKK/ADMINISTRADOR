import streamlit as st
import streamlit.components.v1 as components

def renderizar_ecra_tv(provider_token):
    try:
        # Recupera os dados e variáveis necessárias do ambiente global/sessão do seu projeto original
        pedidos_ativos = globals().get('pedidos_ativos', st.session_state.get('pedidos_ativos', []))
        proximo_cantor = pedidos_ativos[0] if pedidos_ativos else None
        qr_url_cliente = globals().get('qr_url_cliente', st.session_state.get('qr_url_cliente', ''))
        url_clipe_fundo = globals().get('url_clipe_fundo', st.session_state.get('url_clipe_fundo', ''))
        
        frame_styles = globals().get('frame_styles', '')
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
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: black; border: 2px solid #FFC107; border-radius: 10px; padding: 5px; width: 100%; position: relative; margin-top: 5px; margin-bottom: 40px;">
                    <div id="thriller-countdown" style="display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 99; display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 8px;">
                        <div id="countdown-number" style="color: #FFC107; font-size: 120px; font-weight: bold; font-family: monospace; text-shadow: 0 0 20px #FFC107;">3</div>
                        <div id="countdown-text" style="color: #fff; font-size: 30px; font-weight: bold; font-family: monospace; margin-top: 15px; text-transform: uppercase;">Atenção...</div>
                    </div>
                    <video id="fundo-player" width="100%" height="450px" controls autoplay loop playsinline controlslist="nodownload noremoteplayback" disablepictureinpicture style="object-fit: contain; background: black; border-radius: 8px;">
                        <source src="{url_clipe_fundo}" type="video/mp4">
                        O seu navegador não suporta vídeo.
                    </video>
                    <div id="fundo-audio-warning" style="display: none; position: absolute; bottom: 15px; right: 15px; background: rgba(0,0,0,0.8); border: 1px solid #FFC107; padding: 6px 10px; border-radius: 5px; cursor: pointer; z-index: 100;" onclick="unmuteFundo()">
                        <span style="font-size: 18px;" title="Ativar Som">🔊</span>
                    </div>
                </div>
                <script>
                    var fundoVideo = document.getElementById('fundo-player');
                    var countdownOverlay = document.getElementById('thriller-countdown');
                    var countdownNum = document.getElementById('countdown-number');
                    var countdownText = document.getElementById('countdown-text');
                    
                    countdownOverlay.style.display = 'none';

                    function playThrillerVoice(text, callback) {{
                        if ('speechSynthesis' in window) {{
                            window.speechSynthesis.cancel();
                            var utterance = new SpeechSynthesisUtterance(text);
                            utterance.lang = 'pt-PT';
                            utterance.rate = 0.85;
                            utterance.pitch = 0.4;
                            utterance.volume = 1.0;
                            
                            var voices = window.speechSynthesis.getVoices();
                            var selectedVoice = voices.find(v => v.lang.includes('pt') || v.lang.includes('en'));
                            if (selectedVoice) {{
                                utterance.voice = selectedVoice;
                            }}
                            
                            if (callback) {{
                                utterance.onend = callback;
                            }}
                            window.speechSynthesis.speak(utterance);
                        }} else if (callback) {{
                            callback();
                        }}
                    }}

                    function playLaughSound() {{
                        if ('speechSynthesis' in window) {{
                            var laughUtterance = new SpeechSynthesisUtterance("Ha ha ha ha ha ha!");
                            laughUtterance.lang = 'en-US';
                            laughUtterance.rate = 0.6;
                            laughUtterance.pitch = 0.2;
                            laughUtterance.volume = 1.0;
                            window.speechSynthesis.speak(laughUtterance);
                        }}
                    }}

                    function startThrillerCountdownSequence() {{
                        countdownOverlay.style.display = 'flex';
                        countdownNum.innerText = "3";
                        countdownText.innerText = "Atenção...";
                        
                        playThrillerVoice("Atenção em 3", function() {{
                            countdownNum.innerText = "2";
                            playThrillerVoice("2", function() {{
                                countdownNum.innerText = "1";
                                playThrillerVoice("1", function() {{
                                    countdownNum.innerText = "🎤";
                                    countdownText.innerText = "Solta a Voz!";
                                    playThrillerVoice("Solta a Voz!", function() {{
                                        playLaughSound();
                                        setTimeout(function() {{
                                            countdownOverlay.style.display = 'none';
                                            fundoVideo.muted = false;
                                            fundoVideo.play().catch(err => {{
                                                fundoVideo.muted = true;
                                                fundoVideo.play();
                                                document.getElementById('fundo-audio-warning').style.display = 'block';
                                            }});
                                        }}, 1000);
                                    }});
                                }});
                            }});
                        }});
                    }}

                    fundoVideo.muted = true;
                    var fundoPromise = fundoVideo.play();
                    if (fundoPromise !== undefined) {{
                        fundoPromise.then(_ => {{
                            fundoVideo.pause();
                            fundoVideo.currentTime = 0;
                            startThrillerCountdownSequence();
                        }}).catch(error => {{
                            fundoVideo.muted = true;
                            fundoVideo.play().catch(e => {{}});
                            document.getElementById('fundo-audio-warning').style.display = 'block';
                            startThrillerCountdownSequence();
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
            if 'show_register_page' in globals():
                show_register_page()
            return

        if "page" in query_params and query_params["page"] == "client_register":
            if 'show_client_page' in globals():
                show_client_page()
            return

        if "page" in query_params and query_params["page"] == "client_screen":
            show_client_screen()
            return

        token = query_params.get("prestador") or query_params.get("token") or query_params.get("provider")
        
        if token:
            get_providers_func = globals().get('get_all_providers')
            df = get_providers_func() if get_providers_func else st.DataFrame()
            if df.empty or 'token' not in df.columns or not (df['token'] == token).any():
                if 'show_provider_panel_center' in globals():
                    show_provider_panel_center(token) # type: ignore
                return
                
            prior_prestador = df[df['token'] == token]
            if not prior_prestador.empty:
                row = prior_prestador.iloc[0]
                if row.get('approved', 1) == 1:
                    if 'show_provider_panel_custom' in globals():
                        show_provider_panel_custom(token)
                    return
                else:
                    st.warning("⏳ O seu registo aguarda aprovação do Administrador.")
                    return
            else:
                if 'show_provider_panel_custom' in globals():
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
            if 'show_admin_panel' in globals():
                show_admin_panel()
                
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar a aplicação: {e}")

if __name__ == "__main__":
    main()
