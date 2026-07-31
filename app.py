import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import json

# Configuração da página principal
st.set_page_config(
    page_title="FF Karaoke Cloud",
    page_icon="🎤",
    layout="wide"
)

# Funções utilitárias simuladas ou integradas na sua arquitetura
def get_all_providers():
    # Retorna o DataFrame com os provedores cadastrados
    try:
        # Exemplo de chamada padrão para obter base de dados
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def obter_video_fundo(token):
    # Retorna o link do clipe de fundo selecionado pelo prestador
    return ""

def show_register_page():
    st.title("Registo de Novo Prestador")
    # Lógica de registo de prestador

def show_client_page():
    st.markdown("""
        <style>
        .stApp { background-color: #000000; color: white; }
        /* Botão de registo do cliente com texto negrito e cor preta */
        .stButton>button {
            font-weight: bold !important;
            color: #000000 !important;
            background-color: #FFC107 !important;
            border-radius: 8px;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
        }
        .stButton>button:hover {
            background-color: #ffca28 !important;
            color: #000000 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🎤 Registo de Pedido de Karaoke")
    with st.form("form_cliente_registo"):
        nome_cliente = st.text_input("O seu Nome / Convidado")
        musica_escolhida = st.text_input("Nome da Música / Artista")
        
        # O botão abaixo assume agora automaticamente a formatação preta e negrito definida no CSS
        submitted = st.form_submit_button("ENTRAR")
        
        if submitted:
            if nome_cliente and musica_escolhida:
                st.success(f"Pedido registado com sucesso para {nome_cliente}!")
            else:
                st.warning("Por favor, preencha todos os campos.")

def show_provider_panel_custom(token):
    st.title(f"Painel de Controlo - Prestador: {token}")
    # Painel customizado do prestador

def show_admin_panel():
    st.title("Painel de Administração Global")
    # Painel de administração

def renderizar_ecra_tv(provider_token):
    try:
        FIREBASE_URL = "https://ffkaraokecloud-default-rtdb.firebaseio.com"
        
        # Simulação de pedidos ativos e tocando agora para manter a integridade do bloco fornecido
        pedidos_ativos = []
        tocando_agora = {"id": "123", "cliente": "Convidado"}
        
        frame_styles = """
        <style>
            .stApp { background-color: #000000; }
        </style>
        """

        url_clipe_fundo = obter_video_fundo(provider_token)
        proximo_cantor = pedidos_ativos[0] if pedidos_ativos else None

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

def show_provider_panel_center(token):
    show_provider_panel_custom(token)

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
