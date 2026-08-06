import streamlit as st
import streamlit.components.v1 as components
import requests
import time
import datetime
import uuid
import qrcode
import io
import base64

# --- CONFIGURAÇÕES GLOBAIS ---
FIREBASE_URL = "https://ffkaraoke-default-rtdb.firebaseio.com"

# Funções auxiliares fictícias/mock caso não estejam definidas no escopo externo
def get_all_providers():
    try:
        res = requests.get(f"{FIREBASE_URL}/prestadores.json", timeout=5)
        if res.status_code == 200 and res.json():
            import pandas as pd
            data = res.json()
            return pd.DataFrame([{"token": k, **v} for k, v in data.items()])
    except Exception:
        pass
    import pandas as pd
    return pd.DataFrame()

def obter_video_fundo(provider_token):
    return ""

def limpar_nome_musica(musica_obj):
    if isinstance(musica_obj, dict):
        return musica_obj.get("titulo", "Música Desconhecida")
    return str(musica_obj)

def obter_url_video_cloudinary(musica_obj, titulo_limpo):
    if isinstance(musica_obj, dict):
        return musica_obj.get("url", "")
    return ""

def renderizar_gestao_fila_prestador(provider_token):
    st.markdown("### 📋 Gestão da Fila de Pedidos", unsafe_allow_html=True)
    try:
        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        res = requests.get(url_firebase, timeout=5)
        if res.status_code == 200 and res.json():
            data = res.json()
            for k, v in data.items():
                st.write(f"- **{v.get('cliente')}**: {limpar_nome_musica(v.get('musica'))} [{v.get('estado')}]")
        else:
            st.info("Nenhum pedido na fila de momento.")
    except Exception as e:
        st.error(f"Erro ao carregar fila: {e}")

def show_client_page():
    st.markdown("### Página do Cliente")

def show_admin_panel():
    st.markdown("### Painel Administrativo")

def custom_show_register_page():
    st.markdown("### Registo de Prestadores")
    st.info("Preencha os dados para solicitar o seu registo no FF Karaoke Cloud.")
    with st.form("form_registo_prestador"):
        nome = st.text_input("Nome do Prestador / Estabelecimento")
        telefone = st.text_input("Número de Telemóvel")
        plano = st.selectbox("Plano Pretendido", ["2 Horas - 12 Mil Kwanzas", "3 Horas - 15 Mil Kwanzas", "4 Horas - 20 Mil Kwanzas"])
        btn_reg = st.form_submit_button("Submeter Registo")
        if btn_reg:
            if not nome or not telefone:
                st.error("Por favor, preencha todos os campos obrigatórios.")
            else:
                token_novo = str(uuid.uuid4())[:8]
                dados_reg = {
                    "nome": nome,
                    "telefone": telefone,
                    "plano": plano,
                    "token": token_novo,
                    "approved": 0,
                    "data_registo": str(datetime.datetime.now())
                }
                try:
                    requests.put(f"{FIREBASE_URL}/prestadores/{token_novo}.json", json=dados_reg, timeout=10)
                    st.success(f"Registo submetido com sucesso! O seu token temporário é: {token_novo}")
                except Exception as err:
                    st.error(f"Erro ao submeter registo: {err}")

def show_provider_panel_custom(provider_token):
    url_fundo_painel = "https://cdn.phototourl.com/free/2026-08-03-694a4a2e-9914-4da8-93b2-87538a4805ab.png"
    url_logotipo = "https://cdn.phototourl.com/free/2026-08-03-8b13edf5-0257-491d-ab78-f0d5329ffc15.jpg"
    
    # Obter dados do prestador
    nome_prestador = "Prestador"
    segundos_restantes = 3600
    tempo_formatado = "01:00:00"
    classe_piscar = ""
    aviso_reforço_html = ""

    try:
        res = requests.get(f"{FIREBASE_URL}/prestadores/{provider_token}.json", timeout=5)
        if res.status_code == 200 and res.json():
            dados_p = res.json()
            nome_prestador = dados_p.get("nome", "Prestador")
    except Exception:
        pass

    st.markdown(f"""
    <style>
    .stApp {{
        background: url("{url_fundo_painel}") no-repeat center center fixed !important;
        background-size: cover !important;
    }}
    .block-container {{
        padding: 2rem !important;
        background: rgba(0, 0, 0, 0.90) !important;
        border: 4px solid #FFC107 !important;
        border-radius: 12px;
    }}
    .panel-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(20, 20, 20, 0.9);
        padding: 15px;
        border-radius: 8px;
        border: 2px solid #FFC107;
        margin-bottom: 20px;
    }}
    .card-link {{
        background: rgba(30, 30, 30, 0.9);
        border: 2px solid #FFC107;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }}
    .card-tv {{
        background: rgba(30, 30, 30, 0.9);
        border: 2px solid #9c27b0;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }}
    .link-title {{
        font-family: monospace;
        color: #FFC107;
        font-size: 14px;
        font-weight: bold;
        margin-bottom: 5px;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
    }}
    .link-url {{
        font-family: monospace;
        color: #FFC107 !important;
        font-size: 13px;
        font-weight: bold !important;
        word-break: break-all;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
    }}
    </style>

    <div class="panel-header">
        <div style="display: flex; align-items: center;">
            <img src="{url_logotipo}" style="width: 55px; height: 55px; border-radius: 50%; border: 2px solid #FFC107; object-fit: cover; margin-right: 15px;" />
            <div>
                <h2 style="margin: 0; color: #FFC107; font-family: monospace; font-size: 22px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">PAINEL DO PRESTADOR</h2>
                <p style="margin: 0; color: #ffffff; font-family: monospace; font-size: 14px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Prestador: <b>{nome_prestador.upper()}</b></p>
            </div>
        </div>
        <div style="text-align: right; font-family: monospace;">
            <div style="font-size: 12px; color: #ffffff; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">TEMPO RESTANTE</div>
            <div style="font-size: 22px; font-weight: bold; color: #FFC107; {classe_piscar} text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">⏳ {tempo_formatado}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if aviso_reforço_html:
        st.markdown(aviso_reforço_html, unsafe_allow_html=True)

    if segundos_restantes <= 0:
        st.markdown("""
            <div style="background: rgba(255,0,0,0.95); border: 4px solid #FFC107; padding: 30px; border-radius: 8px; text-align: center; font-family: monospace; margin-top: 30px;">
                <h1 style="color: #ffffff; font-size: 32px; font-weight: bold; margin-bottom: 15px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">O SEU TEMPO EXPIROU!</h1>
                <p style="color: #ffffff; font-size: 18px; font-weight: bold; margin-bottom: 20px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">O acesso ao painel foi temporariamente bloqueado. Efectue o pagamento do reforço ou contacte o administrador (Tel: 921204050).</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div id='reforco_seccao'></div>", unsafe_allow_html=True)
        st.markdown("### ⚡ Pedir Reforço de Tempo", unsafe_allow_html=True)
        with st.form("form_reforco_expinado"):
            duracao_reforco = st.selectbox(
                "Escolha o Plano de Reforço",
                options=[
                    "2 Horas - 12 Mil Kwanzas",
                    "3 Horas - 15 Mil Kwanzas",
                    "4 Horas - 20 Mil Kwanzas"
                ],
                key="sel_reforco_exp"
            )
            tel_reforco = st.text_input("Número de Telefone de Confirmação", key="tel_ref_exp")
            btn_sub_ref = st.form_submit_button("Submeter Pedido de Reforço")
            if btn_sub_ref:
                if not tel_reforco:
                    st.error("Por favor, insira o seu número de telefone.")
                else:
                    ref_id = str(uuid.uuid4())[:8]
                    dados_ref = {
                        "token_prestador": provider_token,
                        "nome_prestador": nome_prestador,
                        "telefone": tel_reforco,
                        "tempo_plano": duracao_reforco,
                        "approved": 0,
                        "data_registo": str(datetime.datetime.now())
                    }
                    try:
                        requests.put(f"{FIREBASE_URL}/reforcos_pendentes/{ref_id}.json", json=dados_ref, timeout=10)
                        st.success("Pedido de reforço submetido com sucesso! Aguarde aprovação do administrador.")
                        time.sleep(2)
                        st.rerun()
                    except Exception as err:
                        st.error(f"Erro ao submeter reforço: {err}")
        return

    base_url_app = "https://grupoffkaraoke.streamlit.app"
    link_cliente = f"{base_url_app}/?cliente={provider_token}"
    link_tv = f"{base_url_app}/?tv={provider_token}"

    def gerar_qr_code_base64(url_texto):
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(url_texto)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()
        except Exception:
            return ""

    qr_cliente_b64 = gerar_qr_code_base64(link_cliente)
    qr_tv_b64 = gerar_qr_code_base64(link_tv)

    col_links_1, col_links_2 = st.columns(2)
    with col_links_1:
        st.markdown(f"""
            <div class="card-link">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="flex-grow: 1; padding-right: 10px;">
                        <div class="link-title">📱 LINK DO CLIENTE (PEDIDOS)</div>
                        <div class="link-url">{link_cliente}</div>
                    </div>
                    <div style="min-width: 70px; text-align: center;">
                        <img src="data:image/png;base64,{qr_cliente_b64}" style="width: 65px; height: 65px; border-radius: 4px; border: 2px solid #FFC107;" />
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_links_2:
        st.markdown(f"""
            <div class="card-tv">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="flex-grow: 1; padding-right: 10px;">
                        <div class="link-title" style="color: #ffffff !important;">📺 LINK DA TELA DE TV / PROJETOR</div>
                        <div class="link-url" style="color: #e040fb !important;">{link_tv}</div>
                    </div>
                    <div style="min-width: 70px; text-align: center;">
                        <img src="data:image/png;base64,{qr_tv_b64}" style="width: 65px; height: 65px; border-radius: 4px; border: 2px solid #9c27b0;" />
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    renderizar_gestao_fila_prestador(provider_token)

    st.markdown("<div id='reforco_seccao'></div>", unsafe_allow_html=True)
    with st.expander("⚡ Solicitar Reforço de Tempo (Menu de Extensão)"):
        with st.form("form_reforco_painel"):
            duracao_ref_painel = st.selectbox(
                "Duração Adicional Pretendida",
                options=[
                    "2 Horas - 12 Mil Kwanzas",
                    "3 Horas - 15 Mil Kwanzas",
                    "4 Horas - 20 Mil Kwanzas"
                ]
            )
            telefone_ref_painel = st.text_input("Número de Telefone para Confirmação")
            btn_sub_ref_painel = st.form_submit_button("Submeter Pedido de Reforço")
            if btn_sub_ref_painel:
                if not telefone_ref_painel:
                    st.error("Por favor, preencha o número de telefone.")
                else:
                    ref_id = str(uuid.uuid4())[:8]
                    dados_ref = {
                        "token_prestador": provider_token,
                        "nome_prestador": nome_prestador,
                        "telefone": telefone_ref_painel,
                        "tempo_plano": duracao_ref_painel,
                        "approved": 0,
                        "data_registo": str(datetime.datetime.now())
                    }
                    try:
                        requests.put(f"{FIREBASE_URL}/reforcos_pendentes/{ref_id}.json", json=dados_ref, timeout=10)
                        st.success("Pedido de reforço submetido com sucesso! Aguarde a aprovação do Administrador.")
                    except Exception as err:
                        st.error(f"Erro ao submeter reforço: {err}")

def renderizar_ecra_tv(provider_token):
    url_fundo_painel = "https://cdn.phototourl.com/free/2026-08-03-694a4a2e-9914-4da8-93b2-87538a4805ab.png"
    url_logotipo = "https://cdn.phototourl.com/free/2026-08-03-8b13edf5-0257-491d-ab78-f0d5329ffc15.jpg"
    
    st.markdown(f"""
    <style>
    .stApp {{
        background: url("{url_fundo_painel}") no-repeat center center fixed !important;
        background-size: cover !important;
    }}
    .block-container {{
        padding: 1rem !important;
        max-width: 100% !important;
        background: rgba(0, 0, 0, 0.95) !important;
        border: 4px solid #FFC107 !important;
        border-radius: 12px;
    }}
    </style>
    """, unsafe_allow_html=True)

    try:
        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json?_t={time.time()}"
        res = requests.get(url_firebase, timeout=5)
        pedidos = []
        if res.status_code == 200 and res.json():
            data = res.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            
        tocando_agora = next((p for p in pedidos if p.get("estado") == "aprovado"), None)
        video_fundo = obter_video_fundo(provider_token)

        if tocando_agora:
            musica_obj = tocando_agora.get("musica", {})
            titulo_limpo = limpar_nome_musica(musica_obj)
            url_video = obter_url_video_cloudinary(musica_obj, titulo_limpo)
            cliente_nome = tocando_agora.get("cliente", "Convidado")

            st.markdown(f"""
                <div style="text-align: center; margin-bottom: 10px; font-family: monospace;">
                    <h2 style="color: #FFC107; font-size: 26px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9); margin: 0;">🎶 A CANTAR AGORA: {titulo_limpo.upper()}</h2>
                    <p style="color: #ffffff; font-size: 16px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9); margin: 5px 0 0 0;">Cantor(a): <b>{cliente_nome}</b></p>
                </div>
            """, unsafe_allow_html=True)

            if url_video:
                components.html(f"""
                    <div style="width: 100%; height: 75vh; background: #000; display: flex; align-items: center; justify-content: center; overflow: hidden; border-radius: 8px; border: 3px solid #FFC107;">
                        <video id="tvVideo" src="{url_video}" autoplay controls style="width: 100%; height: 100%; object-fit: contain;"></video>
                    </div>
                    <script>
                        const v = document.getElementById('tvVideo');
                        v.play().catch(e => console.log("Autoplay bloqueado:", e));
                        v.onended = () => {{
                            setTimeout(() => window.location.reload(), 1000);
                        }};
                    </script>
                """, height=550)
            else:
                st.error("URL do vídeo da música não encontrada.")
        else:
            if video_fundo:
                components.html(f"""
                    <div style="width: 100%; height: 82vh; background: #000; display: flex; align-items: center; justify-content: center; overflow: hidden; border-radius: 8px; border: 3px solid #FFC107;">
                        <video src="{video_fundo}" autoplay loop muted style="width: 100%; height: 100%; object-fit: cover;"></video>
                    </div>
                """, height=580)
            else:
                st.markdown(f"""
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 75vh; text-align: center; font-family: monospace;">
                        <img src="{url_logotipo}" style="width: 150px; height: 150px; border-radius: 50%; border: 4px solid #FFC107; object-fit: cover; margin-bottom: 25px; box-shadow: 0 0 30px rgba(255,193,7,0.5);" />
                        <h1 style="color: #FFC107; font-size: 38px; font-weight: bold; margin-bottom: 10px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">FF KARAOKE CLOUD</h1>
                        <p style="color: #ffffff; font-size: 20px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">À ESPERA DE SUA PRÓXIMA MÚSICA...</p>
                        <p style="color: #FFC107; font-size: 16px; font-weight: bold; margin-top: 15px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Faça o seu pedido através do telemóvel escaneando o QR Code do prestador.</p>
                    </div>
                """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro no ecrã de TV: {e}")

    time.sleep(3)
    st.rerun()

# --- ROTEAMENTO PRINCIPAL DA APLICAÇÃO ---
def main():
    query_params = st.query_params
    
    if "tv" in query_params:
        provider_token = query_params["tv"]
        renderizar_ecra_tv(provider_token)
        return

    if "prestador" in query_params:
        provider_token = query_params["prestador"]
        show_provider_panel_custom(provider_token)
        return

    if "cliente" in query_params:
        provider_token = query_params["cliente"]
        if show_client_page:
            try:
                show_client_page()
                return
            except Exception:
                pass

    if "admin" in query_params or query_params.get("mode") == "admin":
        if show_admin_panel:
            try:
                show_admin_panel()
                return
            except Exception:
                pass

    if "token_pendente_prestador" in st.session_state:
        custom_show_register_page()
        return

    # Página Inicial / Seletor de Acessos
    url_fundo_painel = "https://cdn.phototourl.com/free/2026-08-03-694a4a2e-9914-4da8-93b2-87538a4805ab.png"
    url_logotipo = "https://cdn.phototourl.com/free/2026-08-03-8b13edf5-0257-491d-ab78-f0d5329ffc15.jpg"

    st.markdown(f"""
    <style>
    .stApp {{
        background: url("{url_fundo_painel}") no-repeat center center fixed !important;
        background-size: cover !important;
    }}
    .block-container {{
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
        padding-left: 4rem !important;
        padding-right: 4rem !important;
        background: rgba(0, 0, 0, 0.90) !important;
        border-radius: 12px;
        margin-top: 2rem;
        margin-bottom: 2rem;
        border: 4px solid #FFC107 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        st.image(url_logotipo, width=110)
    with col_titulo:
        st.markdown("<h1 style='color: #FFC107; font-family: monospace; font-size: 32px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9); margin-top: 15px;'>GRUPO FF KARAOKE CLOUD</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #ffffff; font-family: monospace; font-size: 16px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);'>Sistema Profissional de Gestão de Acessos e Entretenimento</p>", unsafe_allow_html=True)

    st.markdown("---")

    aba1, aba2, aba3 = st.tabs(["🎤 Painel do Prestador", "📝 Solicitar Registo", "⚙️ Área Administrativa"])

    with aba1:
        st.markdown("<h3 style='color: #FFC107; font-family: monospace; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);'>Aceder com o Token do Prestador</h3>", unsafe_allow_html=True)
        token_input = st.text_input("Introduza o seu Token de Acesso", type="password")
        if st.button("🚀 Entrar no Painel", use_container_width=True):
            if not token_input:
                st.error("Por favor, introduza o token.")
            else:
                aprovado = False
                try:
                    df_prov = get_all_providers()
                    if not df_prov.empty and 'token' in df_prov.columns:
                        match = df_prov[df_prov['token'] == token_input]
                        if not match.empty:
                            if int(match.iloc[0].get('approved', 0)) == 1:
                                aprovado = True
                except Exception:
                    pass

                if aprovado:
                    st.query_params["prestador"] = token_input
                    st.rerun()
                else:
                    st.error("Token inválido ou registo ainda não aprovado pelo Administrador.")

    with aba2:
        custom_show_register_page()

    with aba3:
        st.markdown("<h3 style='color: #FFC107; font-family: monospace; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);'>Acesso Restrito ao Administrador</h3>", unsafe_allow_html=True)
        senha_admin = st.text_input("Senha de Administrador", type="password")
        if st.button("🔑 Entrar como Admin", use_container_width=True):
            if senha_admin == "admin123" or senha_admin == "ffkaraoke2026":
                st.query_params["admin"] = "true"
                st.rerun()
            else:
                st.error("Senha de administrador incorreta.")

if __name__ == "__main__":
    main()
