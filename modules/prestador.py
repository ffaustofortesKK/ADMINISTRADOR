import streamlit as st
import streamlit.components.v1 as components
import requests

# Configuração e variáveis globais do sistema FF Karaoke
FIREBASE_URL = "https://ffkaraoke-default-rtdb.firebaseio.com"

def get_all_providers():
    try:
        res = requests.get(f"{FIREBASE_URL}/prestadores.json", timeout=10)
        if res.status_code == 200 and res.json():
            import pandas as pd
            data = res.json()
            return pd.DataFrame.from_dict(data, orient='index')
    except Exception:
        pass
    import pandas as pd
    return pd.DataFrame()

def obter_video_fundo(token):
    try:
        res = requests.get(f"{FIREBASE_URL}/config_fundo/{token}.json", timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

def show_client_page():
    st.markdown('<h1 style="color: #FFC107;">Registo de Cliente / Fila</h1>', unsafe_allow_html=True)

def custom_show_register_page():
    st.markdown('<h1 style="color: #FFC107;">Registo de Prestador</h1>', unsafe_allow_html=True)

def show_admin_panel():
    st.markdown('<h3 style="color: #FFC107;">Painel Geral de Administração</h3>', unsafe_allow_html=True)

def show_provider_panel_custom(token):
    st.markdown(f'<h1 style="color: #FFC107;">Painel do Prestador - Token: {token}</h1>', unsafe_allow_html=True)

def renderizar_ecra_tv(provider_token):
    try:
        res_pedidos = requests.get(f"{FIREBASE_URL}/pedidos/{provider_token}.json", timeout=10)
        pedidos_ativos = []
        tocando_agora = None

        if res_pedidos.status_code == 200 and res_pedidos.json():
            dados = res_pedidos.json()
            if isinstance(dados, dict):
                for p_id, p_val in dados.items():
                    if isinstance(p_val, dict):
                        p_val['id'] = p_id
                        estado = p_val.get('estado', 'pendente')
                        if estado == 'tocando':
                            tocando_agora = p_val
                        elif estado == 'ativo' or estado == 'pendente':
                            pedidos_ativos.append(p_val)

        frame_styles = """
        <style>
            .stApp { background-color: #000000; color: #FFC107; }
        </style>
        """

        if tocando_agora:
            video_url = tocando_agora.get('video_url', '')
            cliente_nome = tocando_agora.get('cliente', 'Convidado')
            
            video_html = f"""
            <div id="countdown-screen" style="display: flex; justify-content: center; align-items: center; height: 700px; background: #000000; color: #FFC107; font-size: 100px; font-weight: bold; font-family: monospace; border: 4px solid #FFC107; border-radius: 12px;">
                3
            </div>
            
            <div id="karaoke-container" style="display: none; position: relative; width: 100%; text-align: center; background: #000000; border: 4px solid #FFC107; border-radius: 12px; padding: 10px;">
                <h3 style="color: #FFC107; font-family: monospace; margin-bottom: 10px;">🎤 A CANTAR AGORA: {cliente_nome.upper()}</h3>
                <video id="karaoke-player" width="100%" height="550px" playsinline controlslist="nodownload noremoteplayback" disablepictureinpicture style="object-fit: contain; background: black; border-radius: 8px;">
                    <source src="{video_url}" type="video/mp4">
                    O seu navegador não suporta vídeo.
                </video>
                <div id="audio-warning" style="display: none; position: absolute; bottom: 25px; right: 25px; background: rgba(0,0,0,0.9); border: 2px solid #FFC107; padding: 10px 15px; border-radius: 8px; cursor: pointer;" onclick="unmuteVideo()">
                    <span style="font-size: 22px; color: #FFC107;" title="Ativar Som">🔊 Ativar Som</span>
                </div>
                <button onclick="stopKaraoke()" style="margin-top: 15px; background: #FFC107; color: black; border: none; padding: 10px 20px; font-weight: bold; border-radius: 5px; cursor: pointer;">Terminar Música</button>
            </div>

            <script>
                var count = 3;
                var cdScreen = document.getElementById('countdown-screen');
                
                var timer = setInterval(function() {
                    count--;
                    if (count > 0) {
                        cdScreen.innerText = count;
                    } else if (count === 0) {
                        cdScreen.innerText = "🎤 CANTE!";
                    } else {
                        clearInterval(timer);
                        cdScreen.style.display = 'none';
                        document.getElementById('karaoke-container').style.display = 'block';
                        
                        var video = document.getElementById('karaoke-player');
                        video.muted = false; 
                        var playPromise = video.play();
                        
                        if (playPromise !== undefined) {
                            playPromise.then(_ => {}).catch(error => {
                                video.muted = true;
                                video.play();
                                document.getElementById('audio-warning').style.display = 'block';
                            });
                        }
                    }
                }, 1000);

                function unmuteVideo() {
                    var video = document.getElementById('karaoke-player');
                    video.muted = false;
                    video.play();
                    document.getElementById('audio-warning').style.display = 'none';
                }

                function stopKaraoke() {
                    var pedidoId = "{tocando_agora.get('id')}";
                    var token = "{provider_token}";
                    var firebaseURL = "{FIREBASE_URL}/pedidos/" + token + "/" + pedidoId + "/estado.json";
                    
                    fetch(firebaseURL, {
                        method: 'PUT',
                        body: JSON.stringify('terminado'),
                        headers: { 'Content-Type': 'application/json' }
                    }).then(response => {
                        setTimeout(function() { window.location.reload(); }, 300);
                    }).catch(err => {
                        window.location.reload();
                    });
                }

                var video = document.getElementById('karaoke-player');
                if (video) {
                    video.onended = function() {
                        stopKaraoke();
                    };
                }
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
                            <span style="color: #FFC107; font-size: 20px; font-weight: bold; font-family: monospace; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Á SEGUIR</span>
                            <span style="color: #FFC107; font-size: 20px; font-weight: bold; font-family: monospace; text-transform: uppercase; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">{c_prox}</span>
                        </div>
                    """, unsafe_allow_html=True)
                else: 
                    st.markdown("""
                        <div style="border: 4px solid #FFC107; border-radius: 10px; padding: 15px; text-align: center; background: rgba(0,0,0,0.95); margin-bottom: 15px;">
                            <h2 style="color: #FFC107; margin: 0; font-family: monospace; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">🎤 FILA DE ESPERA VAZIA</h2>
                        </div>
                    """, unsafe_allow_html=True)
                
                html_caixas = '<div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 40px;">'
                demais_pedidos = pedidos_ativos[1:] if len(pedidos_ativos) > 1 else []
                
                for idx, p_item in enumerate(demais_pedidos, start=2):
                    c_item = p_item.get("cliente", "Convidado")
                    texto_caixa = f"<b>{idx}.</b> {c_item}"
                    html_caixas += f'<div style="background: rgba(0,0,0,0.95); border: 4px solid #FFC107; border-radius: 8px; padding: 12px; color: #FFC107; font-family: monospace; font-size: 16px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">{texto_caixa}</div>'
                
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
                            <span style="font-size: 18px; color: #FFC107;" title="Ativar Som">🔊</span>
                        </div>
                    </div>
                    <script>
                        var fundoVideo = document.getElementById('fundo-player');
                        fundoVideo.muted = false;
                        var fundoPromise = fundoVideo.play();
                        if (fundoPromise !== undefined) {
                            fundoPromise.then(_ => {}).catch(error => {
                                fundoVideo.muted = true;
                                fundoVideo.play();
                                document.getElementById('fundo-audio-warning').style.display = 'block';
                            });
                        }
                        function unmuteFundo() {
                            fundoVideo.muted = false;
                            fundoVideo.play();
                            document.getElementById('fundo-audio-warning').style.display = 'none';
                        }
                    </script>
                    """
                    components.html(video_fundo_html, height=480)
                else:
                    st.markdown("""
                        <div style="border: 4px solid #FFC107; border-radius: 10px; padding: 100px 20px; text-align: center; background: rgba(0,0,0,0.95); color: #FFC107; font-family: monospace; margin-top: 5px; margin-bottom: 40px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">
                            <div style="font-size: 40px; margin-bottom: 10px;">📺</div>
                            <p style="color: #FFC107; font-size: 16px; margin: 0; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Aguardando o prestador selecionar um vídeo clipe no painel de controle...</p>
                        </div>
                    """, unsafe_allow_html=True)

    except Exception as e:
        st.markdown(f'<p style="color: #FFC107;">Erro de sincronização na TV: {e}</p>', unsafe_allow_html=True)

def show_client_screen():
    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider", None)

    if not provider_token:
        st.markdown('<p style="color: #FFC107;">Tela inválida. Falta o parâmetro do prestador.</p>', unsafe_allow_html=True)
        return

    st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFC107; }</style>""", unsafe_allow_html=True)

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
                    st.markdown('<p style="color: #FFC107;">⏳ O seu registo aguarda aprovação do Administrador.</p>', unsafe_allow_html=True)
                    return
            else:
                show_provider_panel_custom(token)
                return
            
        st.markdown("""
            <style>
            .stApp {
                background-color: #000000 !important;
                color: #FFC107 !important;
                font-weight: bold !important;
            }
            .block-container {
                background-color: #000000 !important;
                border: 4px solid #FFC107 !important;
                border-radius: 12px;
                padding: 3rem !important; }
            h1, h2, h3, h4, h5, h6, p, span, label, div, button, input {
                color: #FFC107 !important;
                font-weight: bold !important;
                text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
            }
            </style>
        """, unsafe_allow_html=True)

        if not st.session_state.get("admin_logged", False):
            st.markdown('<h1 style="color: #FFC107;">🔒 FFKaraoke - Área Restrita (Administrador)</h1>', unsafe_allow_html=True)
            
            with st.form("form_admin_login"):
                senha = st.text_input("Palavra-passe de Administrador", type="password")
                submitted = st.form_submit_button("Entrar")
                
                if submitted:
                    if senha == "ffkaraoke2026" or senha == "admin123":
                        st.session_state["admin_logged"] = True
                        st.markdown('<p style="color: #FFC107;">Sessão iniciada com sucesso!</p>', unsafe_allow_html=True)
                        st.rerun()
                    else:
                        st.markdown('<p style="color: #FFC107;">Palavra-passe incorreta.</p>', unsafe_allow_html=True)

        if st.session_state.get("admin_logged", False):
            st.markdown("---")
            st.markdown('<h3 style="color: #FFC107;">⚡ Gestão de Reforços de Tempo Pendentes</h3>', unsafe_allow_html=True)
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
                                    <div style="background: rgba(0,0,0,0.95); border: 2px solid #FFC107; color: #FFC107; padding: 12px; border-radius: 6px; margin-bottom: 10px;">
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
                                            st.markdown('<p style="color: #FFC107;">Reforço aprovado e acumulado com sucesso!</p>', unsafe_allow_html=True)
                                            st.rerun()
                                    with col_n:
                                        if st.button("❌ Recusar Reforço", key=f"rec_ref_{tok}_{r_id}"):
                                            requests.delete(f"{FIREBASE_URL}/reforcos_pendentes/{tok}/{r_id}.json")
                                            st.markdown('<p style="color: #FFC107;">Reforço recusado.</p>', unsafe_allow_html=True)
                                            st.rerun()
                    if not tem_reforcos:
                        st.markdown('<p style="color: #FFC107;">Nenhum pedido de reforço pendente neste momento.</p>', unsafe_allow_html=True)
                else:
                    st.markdown('<p style="color: #FFC107;">Nenhum pedido de reforço pendente neste momento.</p>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<p style="color: #FFC107;">Não foi possível carregar os reforços pendentes: {e}</p>', unsafe_allow_html=True)

            show_admin_panel()
                
    except Exception as e:
        st.markdown(f'<p style="color: #FFC107;">Ocorreu um erro ao carregar a aplicação: {e}</p>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
