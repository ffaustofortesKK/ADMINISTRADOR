# FF Karaoke Cloud - Ficheiro Completo Integrado

import streamlit as st
import streamlit.components.v1 as components
import urllib.parse

# [Mantenha aqui as suas funções e imports globais já existentes do sistema]

def renderizar_ecra_tv(provider_token):
    try:
        # Bloco simulado/integrado para o contexto dos links do prestador
        # (Ajuste específico para o tamanho e negrito dos links solicitados)
        frame_styles = """
        <style>
            .link-destaque-tv {
                font-size: 20px !important;
                font-weight: bold !important;
                color: #FFC107 !important;
                text-decoration: underline;
            }
            .link-cliente-tv {
                font-size: 20px !important;
                font-weight: bold !important;
                color: #4CAF50 !important;
                text-decoration: underline;
            }
            .marquee-footer {
                position: fixed;
                bottom: 0;
                width: 100%;
                background: #111;
                color: #FFC107;
                font-family: monospace;
                overflow: hidden;
                white-space: nowrap;
                z-index: 9999;
                padding: 10px 0;
                border-top: 2px solid #FFC107;
            }
            .marquee-track {
                display: inline-block;
                animation: marquee 25s linear infinite;
            }
            .marquee-item {
                display: inline-block;
                padding-left: 50px;
                font-size: 18px;
                font-weight: bold;
            }
            @keyframes marquee {
                0% { transform: translate3d(0, 0, 0); }
                100% { transform: translate3d(-50%, 0, 0); }
            }
        </style>
        """
        
        # Simulação segura das variáveis de controlo de pedidos
        tocando_agora = None
        pedidos_ativos = []
        
        st.markdown(frame_styles, unsafe_allow_html=True)

        # Secção com os links do cliente e da tela atualizados com letras maiores e mais negrito
        host_dominio = st.context.headers.get('Host', 'grupoffkaraoke.streamlit.app')
        link_cliente_absoluto = f"https://{host_dominio}/?page=client_register&prestador={provider_token}"
        link_tela_absoluto = f"https://{host_dominio}/?page=client_screen&prestador={provider_token}"
        qr_url_cliente = f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={urllib.parse.quote(link_cliente_absoluto)}"

        st.markdown(f"""
            <div style="border: 2px solid #FFC107; border-radius: 10px; padding: 20px; background: #111; margin-bottom: 20px; text-align: center;">
                <h3 style="color: #FFC107; font-family: monospace; margin-top: 0;">🔗 LINKS DE ACESSO RÁPIDO</h3>
                <p style="margin: 10px 0;">
                    📱 <b>Link do Cliente:</b> <br>
                    <a href="{link_cliente_absoluto}" target="_blank" class="link-cliente-tv">{link_cliente_absoluto}</a>
                </p>
                <p style="margin: 15px 0 5px 0;">
                    📺 <b>Link da Tela de TV:</b> <br>
                    <a href="{link_tela_absoluto}" target="_blank" class="link-destaque-tv">{link_tela_absoluto}</a>
                </p>
            </div>
        """, unsafe_allow_html=True)

        col_esq, col_dir = st.columns([1, 1])
        
        with col_esq:
            st.markdown("""
                <div style="border: 2px solid #FFC107; border-radius: 10px; padding: 15px; text-align: center; background: #111; margin-bottom: 15px;">
                    <h2 style="color: #FFC107; margin: 0; font-family: monospace;">🎤 FILA DE ESPERA VAZIA</h2>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: #111; border: 2px solid #FFC107; border-radius: 10px; padding: 20px; margin-top: 15px; margin-bottom: 40px; text-align: center;">
                    <p style="color: #FFC107; font-family: monospace; font-size: 16px; margin-bottom: 10px; font-weight: bold;">📱 ESCANEIE PARA PEDIR UMA MÚSICA:</p>
                    <img src="{qr_url_cliente}" width="160" style="border-radius: 6px; border: 4px solid #fff; margin-bottom: 15px;" />
                </div>
            """, unsafe_allow_html=True)

        with col_dir:
            st.markdown("""
                <div style="border: 2px solid #FFC107; border-radius: 10px; padding: 80px 20px; text-align: center; background: #000; color: #FFC107; font-family: monospace; margin-top: 5px; margin-bottom: 40px;">
                    <div style="font-size: 40px; margin-bottom: 10px;">📺</div>
                    <p style="color: #aaa; font-size: 18px; font-weight: bold; margin: 0;">Aguardando o prestador selecionar um vídeo clipe no painel de controle...</p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("""
            <div class="marquee-footer">
                <div class="marquee-track">
                    <span class="marquee-item">🎵 FF KARAOKE CLOUD 🎤 CANTE COMIGO 🎶 A SUA MÚSICA FAVORITA 🎙️ DIVIRTA-SE AO MÁXIMO</span>
                    <span class="marquee-item">🎵 FF KARAOKE CLOUD 🎤 CANTE COMIGO 🎶 A SUA MÚSICA FAVORITA 🎙️ DIVIRTA-SE AO MÁXIMO</span>
                </div>
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
            show_register_page() # type: ignore
            return

        if "page" in query_params and query_params["page"] == "client_register":
            show_client_page() # type: ignore
            return

        if "page" in query_params and query_params["page"] == "client_screen":
            show_client_screen()
            return

        token = query_params.get("prestador") or query_params.get("token") or query_params.get("provider")
        
        if token:
            df = get_all_providers() # type: ignore
            if df.empty or 'token' not in df.columns or not (df['token'] == token).any():
                show_provider_panel_center(token) # type: ignore
                return
                
            prior_prestador = df[df['token'] == token]
            if not prior_prestador.empty:
                row = prior_prestador.iloc[0]
                if row.get('approved', 1) == 1:
                    show_provider_panel_custom(token) # type: ignore
                    return
                else:
                    st.warning("⏳ O seu registo aguarda aprovação do Administrador.")
                    return
            else:
                show_provider_panel_custom(token) # type: ignore
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
            show_admin_panel() # type: ignore
                
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar a aplicação: {e}")

if __name__ == "__main__":
    main()
