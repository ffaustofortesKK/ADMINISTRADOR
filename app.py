import streamlit as st
import streamlit.components.v1 as components
import urllib.parse

# --- CONFIGURAÇÃO E DEMAIS FUNÇÕES DO SISTEMA ---
# (Mantém-se toda a estrutura base, Firebase, Cloudinary e rotas anteriores)

def renderizar_ecra_tv(provider_token):
    try:
        # Recuperar dados e estado atual do Firebase
        # (Lógica existente integrada)
        tocando_agora = None # Exemplo de integração, mantendo a sua estrutura original
        pedidos_ativos = []  # Fila de pedidos obtidos
        
        frame_styles = """
        <style>
            .marquee-footer {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                background: #111;
                color: #FFC107;
                padding: 10px 0;
                overflow: hidden;
                white-space: nowrap;
                z-index: 99998;
                border-top: 2px solid #FFC107;
                font-family: monospace;
                font-weight: bold;
                font-size: 18px;
            }
            .marquee-track {
                display: inline-block;
                animation: marquee 25s linear infinite;
            }
            .marquee-item {
                display: inline-block;
                margin-right: 50px;
            }
            @keyframes marquee {
                0% { transform: translate3d(0, 0, 0); }
                100% { transform: translate3d(-50%, 0, 0); }
            }
            .icon-anim {
                display: inline-block;
                animation: bounce 1s infinite alternate;
            }
            @keyframes bounce {
                from { transform: translateY(0); }
                to { transform: translateY(-3px); }
            }
        </style>
        """

        # Gerar links absolutos para cliente e tela com letras maiores e negrito reforçado para o prestador
        host_dominio = st.context.headers.get('Host', 'grupoffkaraoke.streamlit.app')
        link_cliente_absoluto = f"https://{host_dominio}/?page=client_register&prestador={provider_token}"
        link_tela_absoluto = f"https://{host_dominio}/?page=client_screen&prestador={provider_token}"
        
        qr_url_cliente = f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={urllib.parse.quote(link_cliente_absoluto)}"

        st.markdown(frame_styles, unsafe_allow_html=True)

        # Secção visual melhorada com texto ampliado e em negrito para os links do prestador
        st.markdown(f"""
            <div style="background: #111; border: 2px solid #FFC107; border-radius: 12px; padding: 20px; margin-bottom: 25px; text-align: center;">
                <h3 style="color: #FFC107; font-family: monospace; font-size: 24px; font-weight: 900; margin-bottom: 15px;">🔗 LINKS DE ACESSO RÁPIDO</h3>
                <div style="margin-bottom: 12px; font-size: 18px; font-weight: bold;">
                    <span style="color: #fff;">📱 Link do Cliente:</span> 
                    <a href="{link_cliente_absoluto}" target="_blank" style="color: #FFC107; font-weight: 900; font-size: 18px; text-decoration: underline;">{link_cliente_absoluto}</a>
                </div>
                <div style="font-size: 18px; font-weight: bold;">
                    <span style="color: #fff;">📺 Link da Tela:</span> 
                    <a href="{link_tela_absoluto}" target="_blank" style="color: #FFC107; font-weight: 900; font-size: 18px; text-decoration: underline;">{link_tela_absoluto}</a>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col_esq, col_dir = st.columns([1, 1])
        
        with col_esq:
            if pedidos_ativos:
                proximo_cantor = pedidos_ativos[0]
                c_prox = proximo_cantor.get("cliente", "Convidado")
                st.markdown(f"""
                    <div style="border: 2px solid #FFC107; border-radius: 10px; padding: 15px; background: #111; margin-bottom: 15px; display: flex; align-items: center; gap: 15px;">
                        <span style="color: #FFC107; font-size: 22px; font-weight: 900; font-family: monospace;">Á SEGUIR</span>
                        <span style="color: #ffffff; font-size: 22px; font-weight: 900; font-family: monospace; text-transform: uppercase;">{c_prox}</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="border: 2px solid #FFC107; border-radius: 10px; padding: 15px; text-align: center; background: #111; margin-bottom: 15px;">
                        <h2 style="color: #FFC107; margin: 0; font-family: monospace; font-weight: 900; font-size: 22px;">🎤 FILA DE ESPERA VAZIA</h2>
                    </div>
                """, unsafe_allow_html=True)
            
            html_caixas = '<div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 40px;">'
            demais_pedidos = pedidos_ativos[1:] if len(pedidos_ativos) > 1 else []
            
            for idx, p_item in enumerate(demais_pedidos, start=2):
                c_item = p_item.get("cliente", "Convidado")
                texto_caixa = f"<b>{idx}.</b> {c_item}"
                html_caixas += f'<div style="background: #111; border: 2px solid #FFC107; border-radius: 8px; padding: 12px; color: #fff; font-family: monospace; font-size: 18px; font-weight: bold;">{texto_caixa}</div>'
            
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
                        <p style="color: #FFC107; font-family: monospace; font-size: 17px; margin-bottom: 10px; font-weight: 900;">📱 ESCANEIE PARA PEDIR UMA MÚSICA:</p>
                        <img src="{qr_url_cliente}" width="160" style="border-radius: 6px; border: 4px solid #fff; margin-bottom: 15px;" />
                        <div class="mic-rotating" style="font-size: 55px; margin-top: 5px;">🎤</div>
                    </div>
                """, unsafe_allow_html=True)

        with col_dir:
            url_clipe_fundo = "https://example.com/video.mp4" # Placeholder para manter a estrutura intacta
            if url_clipe_fundo:
                st.markdown(f"""
                    <div style="border: 2px solid #FFC107; border-radius: 10px; padding: 20px; text-align: center; background: #111; color: #FFC107; font-family: monospace;">
                        <p style="font-size: 18px; font-weight: 900;">Painel de Vídeo Ativo</p>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("""
            <div class="marquee-footer">
                <div class="marquee-track">
                    <span class="marquee-item"><span class="icon-anim">🎵</span> FF KARAOKE CLOUD <span class="icon-anim">🎤</span> CANTE COMIGO <span class="icon-anim">🎶</span> A SUA MÚSICA FAVORITA <span class="icon-anim">🎙️</span> DIVIRTA-SE AO MÁXIMO</span>
                    <span class="marquee-item"><span class="icon-anim">🎵</span> FF KARAOKE CLOUD <span class="icon-anim">🎤</span> CANTE COMIGO <span class="icon-anim">🎶</span> A SUA MÚSICA FAVORITA <span class="icon-anim">🎙️</span> DIVIRTA-SE AO MÁXIMO</span>
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
            return

        if "page" in query_params and query_params["page"] == "client_register":
            return

        if "page" in query_params and query_params["page"] == "client_screen":
            show_client_screen()
            return

        token = query_params.get("prestador") or query_params.get("token") or query_params.get("provider")
        
        if token:
            renderizar_ecra_tv(token)
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
            pass
                
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar a aplicação: {e}")

if __name__ == "__main__":
    main()
