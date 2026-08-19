import streamlit as st
import requests
import os
import uuid
import time
import cloudinary
import cloudinary.uploader
import cloudinary.api
import streamlit.components.v1 as components

# --- 1. CONFIGURAÇÃO DA PÁGINA E AMBIENTE ---
st.set_page_config(
    page_title="FF Karaoke Cloud",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

# --- 2. CONFIGURAÇÃO DO CLOUDINARY ---
cloudinary.config(
    cloud_name="dq72vpvur",
    api_key="324159822649641",
    api_secret="A_Seu_Api_Secret_Aqui", # Mantenha a sua chave secreta real se necessário
    secure=True
)

# --- 3. MODO PRODUÇÃO / KIOSK (BLOQUEIO VISUAL DO STREAMLIT) ---
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
    </style>
    <script>
        function annihilateManageButton() {
            const doc = window.parent.document;
            const customEls = doc.querySelectorAll('lib-app-badge, div[data-testid="stToolbar"], button[kind="header"]');
            customEls.forEach(el => el.remove());
        }
        setInterval(annihilateManageButton, 500);
    </script>
""", unsafe_allow_html=True)

# --- 4. FUNÇÕES AUXILIARES GLOBAIS ---
def obter_video_fundo(provider_token):
    try:
        url = f"{FIREBASE_URL}/config/{provider_token}/video_fundo.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

def definir_video_fundo(provider_token, url_clipe):
    try:
        url = f"{FIREBASE_URL}/config/{provider_token}/video_fundo.json"
        requests.put(url, json=url_clipe, timeout=10)
    except Exception:
        pass

@st.cache_data(ttl=60)
def listar_videos_pasta_clipes():
    try:
        resources = cloudinary.api.resources(
            type="upload",
            prefix="clipes/",
            max_results=100
        )
        return [item['secure_url'] for item in resources.get('resources', [])]
    except Exception:
        return []

def limpar_nome_musica(filename):
    nome_base = os.path.splitext(filename)[0]
    return nome_base.replace("_", " ").replace("-", " ").title()


# --- 5. MÓDULO DE REGISTO DE NOVO PRESTADOR ---
def custom_show_register_page():
    st.markdown("""
        <style>
            .stApp { background-color: #000 !important; color: #fff !important; }
            .reg-container { border: 3px solid #FFC107; padding: 25px; border-radius: 12px; background: rgba(0,0,0,0.9); }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='reg-container'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: #FFC107; text-align: center;'>📝 Registo de Novo Prestador - FF Karaoke Cloud</h2>", unsafe_allow_html=True)
    
    with st.form("form_registo_prestador"):
        nome_prestador = st.text_input("Nome do Estabelecimento / Artista / DJ")
        responsavel = st.text_input("Nome do Responsável")
        contacto = st.text_input("Contacto Telefónico / WhatsApp")
        tempo_plano = st.selectbox("Selecione o Plano Inicial", ["2 Horas", "3 Horas", "4 Horas"])
        referencia_pagamento = st.text_input("Referência ou Código de Comprovativo de Pagamento")
        
        submitted = st.form_submit_button("Submeter Registo para Aprovação")
        
        if submitted:
            if not nome_prestador or not contacto:
                st.error("Por favor, preencha os campos obrigatórios (Nome e Contacto).")
            else:
                token_gerado = str(uuid.uuid4())[:8]
                dados_registo = {
                    "token": token_gerado,
                    "nome_prestador": nome_prestador,
                    "responsavel": responsavel,
                    "contacto": contacto,
                    "tempo_plano": tempo_plano,
                    "referencia": referencia_pagamento,
                    "approved": 0,
                    "timestamp": time.time()
                }
                
                try:
                    url_fb = f"{FIREBASE_URL}/prestadores_registados/{token_gerado}.json"
                    requests.put(url_fb, json=dados_registo, timeout=10)
                    st.session_state["token_pendente"] = token_gerado
                    st.success("Registo efetuado com sucesso! Aguarde a aprovação do Administrador.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao comunicar com a base de dados: {e}")
                    
    st.markdown("</div>", unsafe_allow_html=True)


# --- 6. MÓDULO DE GESTÃO DE FILA (PAINEL DO PRESTADOR) ---
def gerir_fila_prestador(provider_token):
    st.markdown("""
        <style>
            .stApp { background-color: #000 !important; color: #fff !important; }
            .card-pedido { background: rgba(20,20,20,0.95); border: 2px solid #FFC107; padding: 15px; border-radius: 8px; margin-bottom: 12px; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h2 style='color: #FFC107;'>🎛️ Painel de Controlo - Gestão de Fila</h2>", unsafe_allow_html=True)
    
    url_tv = f"/?page=client_screen&prestador={provider_token}"
    st.markdown(f"""
        <div style="background: #111; border: 1px dashed #FFC107; padding: 10px; border-radius: 6px; margin-bottom: 20px; text-align: center;">
            <p style="margin: 0; font-size: 14px;">📺 <b>Link do Ecrã de TV (Projeção):</b> <a href="{url_tv}" target="_blank" style="color: #FFC107;">Abrir Ecrã de TV em Nova Aba</a></p>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        url_pedidos = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        res = requests.get(url_pedidos, timeout=10)
        pedidos = res.json() if res.status_code == 200 and res.json() else {}
        
        pendentes = []
        aprovados = []
        
        for pid, pdata in pedidos.items():
            if isinstance(pdata, dict):
                pdata['id'] = pid
                estado = pdata.get("estado", "pendente")
                if estado == "pendente":
                    pendentes.append(pdata)
                elif estado == "aprovado":
                    aprovados.append(pdata)
                    
        tab1, tab2, tab3 = st.tabs([f"📥 Pedidos Pendentes ({len(pendentes)})", f"🎵 Fila de Reprodução ({len(aprovados)})", "⚙️ Configurações"])
        
        with tab1:
            st.markdown("### Pedidos de Músicas Enviados pelos Clientes")
            if not pendentes:
                st.info("Não há pedidos pendentes no momento.")
            else:
                for p in pendentes:
                    p_id = p.get("id")
                    cliente = p.get("cliente", "Convidado")
                    musica = p.get("musica", "Música")
                    if isinstance(musica, dict):
                        musica = musica.get("titulo", musica.get("nome", ""))
                    
                    with st.container():
                        st.markdown(f"""
                            <div class="card-pedido">
                                <b>Cantor:</b> {cliente}<br>
                                <b>Música:</b> {musica}<br>
                                <b>Hora:</b> {time.strftime('%H:%M:%S', time.localtime(p.get('timestamp', time.time())))}
                            </div>
                        """, unsafe_allow_html=True)
                        
                        col_a, col_r = st.columns(2)
                        with col_a:
                            if st.button("✅ Aceitar na Fila", key=f"aceitar_{p_id}"):
                                requests.patch(f"{FIREBASE_URL}/pedidos/{provider_token}/{p_id}.json", json={"estado": "aprovado"})
                                st.success("Pedido aceite!")
                                st.rerun()
                        with col_r:
                            if st.button("❌ Recusar", key=f"recusar_{p_id}"):
                                requests.patch(f"{FIREBASE_URL}/pedidos/{provider_token}/{p_id}.json", json={"estado": "recusado"})
                                st.warning("Pedido recusado.")
                                st.rerun()
                                
        with tab2:
            st.markdown("### Ordem Atual de Execução")
            if not aprovados:
                st.info("A fila está vazia.")
            else:
                for idx, p in enumerate(aprovados, 1):
                    p_id = p.get("id")
                    cliente = p.get("cliente", "Convidado")
                    musica = p.get("musica", "")
                    if isinstance(musica, dict):
                        musica = musica.get("titulo", musica.get("nome", ""))
                        
                    st.markdown(f"""
                        <div class="card-pedido">
                            <b>#{idx} - {cliente}</b> : {musica}
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button("🗑️ Remover / Concluir", key=f"rem_{p_id}"):
                        requests.patch(f"{FIREBASE_URL}/pedidos/{provider_token}/{p_id}.json", json={"estado": "concluido"})
                        st.rerun()
                        
        with tab3:
            st.markdown("### Definições do Prestador")
            novo_video_fundo = st.text_input("URL do Vídeo de Fundo (Clube/Ambiente)")
            if st.button("Atualizar Vídeo de Fundo"):
                if novo_video_fundo:
                    definir_video_fundo(provider_token, novo_video_fundo)
                    st.success("Vídeo de fundo atualizado com sucesso!")
                    st.rerun()

    except Exception as e:
        st.error(f"Erro ao carregar os pedidos: {e}")


# --- 7. MÓDULO DO PORTAL DO CLIENTE (VIA QR CODE) ---
def renderizar_portal_cliente(provider_token):
    st.markdown("""
        <style>
            .stApp { background-color: #000 !important; color: #fff !important; }
            .client-box { background: rgba(15,15,15,0.95); border: 2px solid #FFC107; padding: 20px; border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='client-box'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: #FFC107; text-align: center;'>🎤 Pedido de Karaoke - FF Cloud</h2>", unsafe_allow_html=True)
    
    try:
        res = requests.get(f"{FIREBASE_URL}/prestadores_registados/{provider_token}.json", timeout=5)
        if res.status_code != 200 or not res.json():
            st.error("Estabelecimento ou sessão de karaoke inválida ou expirada.")
            st.markdown("</div>", unsafe_allow_html=True)
            return
        prestador_info = res.json()
        st.markdown(f"<p style='text-align: center; color: #aaa;'>Local: <b>{prestador_info.get('nome_prestador')}</b></p>", unsafe_allow_html=True)
    except Exception:
        pass

    with st.form("form_pedido_cliente"):
        nome_cliente = st.text_input("O seu Nome / alcunha")
        musica_escolhida = st.text_input("Nome da Música / Artista Pretendido")
        observacoes = st.text_area("Observações (Opcional)", placeholder="Ex: Tom mais baixo, dedicatória...")
        
        enviar_pedido = st.form_submit_button("Submeter Pedido à Fila")
        
        if enviar_pedido:
            if not nome_cliente or not musica_escolhida:
                st.error("Por favor, preencha o seu nome e a música pretendida.")
            else:
                novo_pedido = {
                    "cliente": nome_cliente,
                    "musica": musica_escolhida,
                    "obs": observacoes,
                    "estado": "pendente",
                    "timestamp": time.time()
                }
                try:
                    requests.post(f"{FIREBASE_URL}/pedidos/{provider_token}.json", json=novo_pedido, timeout=10)
                    st.success("Pedido enviado com sucesso! Aguarde a chamada no ecrã.")
                except Exception as e:
                    st.error(f"Erro ao enviar o pedido: {e}")
                    
    st.markdown("</div>", unsafe_allow_html=True)


# --- 8. MÓDULO DO ECRÃ DE TV (PROJEÇÃO) ---
def renderizar_ecra_tv(provider_token):
    frame_styles = """
    <style>
        .stApp { background-color: #000 !important; color: #fff !important; }
    </style>
    """
    script_sincronizacao_global = f"""
    <script>
        setTimeout(function() {{
            window.location.reload();
        }}, 15000);
    </script>
    """
    
    try:
        url_pedidos = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        res = requests.get(url_pedidos, timeout=10)
        pedidos_raw = res.json() if res.status_code == 200 and res.json() else {}
        
        pedidos_ativos = []
        tocando_agora = None
        
        for pid, pdata in pedidos_raw.items():
            if isinstance(pdata, dict):
                pdata['id'] = pid
                estado = pdata.get("estado", "pendente")
                if estado == "aprovado" and not tocando_agora:
                    tocando_agora = pdata
                elif estado in ["pendente", "aprovado"]:
                    pedidos_ativos.append(pdata)
                    
        if tocando_agora:
            c_nome = tocando_agora.get("cliente", "Convidado")
            m_nome = tocando_agora.get("musica", "Música")
            if isinstance(m_nome, dict):
                m_nome = m_nome.get("titulo", m_nome.get("nome", ""))
            url_video = tocando_agora.get("url_video", "")
            
            video_html = f"""
            <div id="countdown-screen" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: black; z-index: 99999; display: flex; flex-direction: column; justify-content: center; align-items: center; color: #FFC107; font-size: 80px; font-weight: bold; font-family: monospace;">
                3
            </div>
            <div id="karaoke-container" style="display:none; text-align: center; background: black; padding: 10px;">
                <div style="background: rgba(0,0,0,0.9); border: 3px solid #FFC107; padding: 10px; border-radius: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="color: #FFC107; font-family: monospace; font-size: 20px; text-transform: uppercase;">
                        🎤 A CANTAR: <b>{c_nome}</b> - {m_nome}
                    </div>
                    <button onclick="stopKaraoke()" style="background: #d9534f; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: bold;">⏹️ Terminar Música</button>
                </div>
                <div style="position: relative; width: 100%; max-width: 1100px; margin: auto;">
                    <video id="karaoke-player" width="100%" height="550px" autoplay playsinline controlslist="nodownload noremoteplayback" disablepictureinpicture style="object-fit: contain; background: black; border-radius: 8px;">
                        <source src="{url_video}" type="video/mp4">
                        O seu navegador não suporta vídeo.
                    </video>
                    <div id="audio-warning" style="display: none; position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.85); border: 2px solid #FFC107; padding: 12px 20px; border-radius: 6px; text-align: center;">
                        <p style="color: white; margin: 0 0 8px 0; font-size: 14px;">⚠️ O navegador bloqueou o áudio automático.</p>
                        <button onclick="unmuteVideo()" style="background-color: #4CAF50; color: white; border: none; padding: 8px 16px; font-size: 15px; border-radius: 4px; cursor: pointer; font-weight: bold;">🔊 CLIQUE AQUI PARA ATIVAR O SOM</button>
                    </div>
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
            {script_sincronizacao_global}
            """
            components.html(video_html, height=750, scrolling=False)
            
        else:
            proximo_cantor = pedidos_ativos[0] if pedidos_ativos else None

            st.markdown(frame_styles, unsafe_allow_html=True)
            st.markdown(script_sincronizacao_global, unsafe_allow_html=True)

            col_esq, col_dir = st.columns([1, 1])
            
            with col_esq:
                if proximo_cantor:
                    c_prox = proximo_cantor.get("cliente", "Convidado")
                    m_prox = proximo_cantor.get("musica", "Música")
                    if isinstance(m_prox, dict):
                        m_prox = m_prox.get("titulo", m_prox.get("nome", ""))
                    
                    st.markdown(f"""
                        <div style="border: 4px solid #FFC107; border-radius: 10px; padding: 15px; background: rgba(0,0,0,0.95); margin-bottom: 15px;">
                            <div style="color: #FFC107; font-size: 16px; font-weight: bold; font-family: monospace;">🎤 A SEGUIR:</div>
                            <div style="color: #ffffff; font-size: 20px; font-weight: bold; font-family: monospace; text-transform: uppercase;">{c_prox}</div>
                            <div style="color: #aaa; font-size: 14px; font-family: monospace;">🎵 {m_prox}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div style="border: 4px solid #FFC107; border-radius: 10px; padding: 15px; text-align: center; background: rgba(0,0,0,0.95); margin-bottom: 15px;">
                            <h2 style="color: #ffffff; margin: 0; font-family: monospace; font-weight: bold;">🎤 FILA DOS CANTORES</h2>
                        </div>
                    """, unsafe_allow_html=True)
                
                html_caixas = '<div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 40px;">'
                demais_pedidos = pedidos_ativos[1:] if len(pedidos_ativos) > 1 else []
                
                for idx, p_item in enumerate(demais_pedidos, start=2):
                    c_item = p_item.get("cliente", "Convidado")
                    m_item = p_item.get("musica", "")
                    if isinstance(m_item, dict):
                        m_item = m_item.get("titulo", m_item.get("nome", ""))
                    
                    texto_caixa = f"<b>{idx}.</b> {c_item} {('- ' + m_item) if m_item else ''}"
                    html_caixas += f'<div style="background: rgba(0,0,0,0.95); border: 4px solid #FFC107; border-radius: 8px; padding: 12px; color: #ffffff; font-family: monospace; font-size: 16px; font-weight: bold;">{texto_caixa}</div>'
                
                html_caixas += '</div>'
                st.markdown(html_caixas, unsafe_allow_html=True) 

            with col_dir:
                url_clipe_fundo = obter_video_fundo(provider_token)
                if url_clipe_fundo:
                    video_fundo_html = f"""
                    <div style="display: flex; justify-content: center; background: rgba(0,0,0,0.95); border: 4px solid #FFC107; border-radius: 10px; padding: 5px; width: 100%; position: relative; margin-top: 5px; margin-bottom: 40px;">
                        <video id="fundo-player" width="100%" height="450px" autoplay loop muted playsinline controlslist="nodownload noremoteplayback" disablepictureinpicture style="object-fit: contain; background: black; border-radius: 8px;">
                            <source src="{url_clipe_fundo}" type="video/mp4">
                            O seu navegador não suporta vídeo.   </video>
                    </div>
                    """
                    components.html(video_fundo_html, height=480)
                else:
                    st.markdown("""
                        <div style="border: 4px solid #FFC107; border-radius: 10px; padding: 100px 20px; text-align: center; background: rgba(0,0,0,0.95); color: #ffffff; font-family: monospace; margin-top: 5px; margin-bottom: 40px; font-weight: bold;">
                            <div style="font-size: 40px; margin-bottom: 10px;">📺</div>
                            <p style="color: #ffffff; font-size: 16px; margin: 0; font-weight: bold;">Aguardando Vídeo de Fundo...</p>
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
    st.markdown("""<style>.stApp { background-color: #000000; color: white; }</style>""", unsafe_allow_html=True)
    renderizar_ecra_tv(provider_token)


# --- 9. ROTEADOR E CONTROLADOR PRINCIPAL (`main`) ---
def main():
    try:
        query_params = st.query_params
        
        # 1. Rota Ecrã de TV
        if "page" in query_params and query_params["page"] == "client_screen":
            show_client_screen()
            return

        # 2. Rota Portal do Cliente (QR Code)
        token_cliente = query_params.get("pedido") or query_params.get("client")
        if token_cliente:
            renderizar_portal_cliente(token_cliente)
            return

        # 3. Rota Painel do Prestador
        token_prestador = query_params.get("prestador") or query_params.get("token") or query_params.get("provider")
        if token_prestador:
            try:
                res = requests.get(f"{FIREBASE_URL}/prestadores_registados/{token_prestador}.json", timeout=5)
                if res.status_code == 200 and res.json():
                    dados_p = res.json()
                    if dados_p.get("approved", 0) == 1:
                        gerir_fila_prestador(token_prestador)
                        return
                    else:
                        st.markdown("""<style>.stApp { background-color: #000; color: #fff; text-align: center; }</style>""", unsafe_allow_html=True)
                        st.warning("⚠️ O seu registo ainda se encontra pendente de aprovação pelo Administrador.")
                        st.info("Por favor, aguarde a validação do pagamento.")
                        return
                else:
                    st.error("Token de prestador inválido ou inexistente.")
                    return
            except Exception as e:
                st.error(f"Erro ao verificar o prestador: {e}")
                return

        # 4. Rota Registo de Novo Prestador
        if "register" in query_params and query_params["register"] == "true":
            custom_show_register_page()
            return

        # 5. Painel de Administração Principal
        st.markdown("""<style>
            .stApp { background-color: #000000 !important; color: #ffffff !important; }
            .block-container { background-color: #000000 !important; border: 4px solid #FFC107 !important; border-radius: 12px; padding: 3rem !important; }
            </style>
        """, unsafe_allow_html=True)

        if not st.session_state.get("admin_logged", False):
            st.title("🔒 FF Karaoke Cloud - Administração Geral")
            with st.form("form_admin_login"):
                senha = st.text_input("Palavra-passe de Administrador", type="password")
                submitted = st.form_submit_button("Entrar no Sistema")
                if submitted:
                    if senha == "ffkaraoke2026" or senha == "admin123":
                        st.session_state["admin_logged"] = True
                        st.success("Sessão iniciada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Palavra-passe incorreta.")
            
            st.markdown("---")
            st.markdown("### É um novo estabelecimento ou artista?")
            if st.button("📝 Registar Novo Prestador / Obter Acesso"):
                st.query_params["register"] = "true"
                st.rerun()

        if st.session_state.get("admin_logged", False):
            st.title("⚙️ Painel de Controlo Master - FF Karaoke Cloud")
            st.markdown("---")
            
            st.subheader("📋 Pedidos de Registo e Ativação de Parceiros")
            try:
                res_reg = requests.get(f"{FIREBASE_URL}/prestadores_registados.json", timeout=10)
                if res_reg.status_code == 200 and res_reg.json():
                    regs = res_reg.json()
                    tem_pendentes = False
                    for tok, r_data in regs.items():
                        if isinstance(r_data, dict) and r_data.get("approved", 0) == 0:
                            tem_pendentes = True
                            st.markdown(f"""
                            <div style="background: rgba(20,20,20,0.95); border: 2px solid #FFC107; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                                <b>Estabelecimento:</b> {r_data.get('nome_prestador')}<br>
                                <b>Responsável:</b> {r_data.get('responsavel')} | <b>Contacto:</b> {r_data.get('contacto')}<br>
                                <b>Plano Selecionado:</b> {r_data.get('tempo_plano')} | <b>Comprovativo/Ref:</b> {r_data.get('referencia')}<br>
                                <b>Token de Acesso:</b> <code>{tok}</code>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col_aprov, col_rec = st.columns(2)
                            with col_aprov:
                                if st.button(f"✅ Aprovar Parceiro", key=f"aprov_{tok}"):
                                    r_data["approved"] = 1
                                    requests.put(f"{FIREBASE_URL}/prestadores_registados/{tok}.json", json=r_data)
                                    st.success(f"Parceiro {r_data.get('nome_prestador')} aprovado!")
                                    st.rerun()
                            with col_rec:
                                if st.button(f"❌ Recusar/Apagar", key=f"rec_{tok}"):
                                    requests.delete(f"{FIREBASE_URL}/prestadores_registados/{tok}.json")
                                    st.warning("Registo removido.")
                                    st.rerun()
                    if not tem_pendentes:
                        st.info("Não existem registos de parceiros pendentes de aprovação.")
                else:
                    st.info("Nenhum registo encontrado na base de dados.")
            except Exception as e:
                st.warning(f"Erro ao carregar registos: {e}")

    except Exception as e:
        st.error(f"Erro crítico no arranque da aplicação: {e}")

if __name__ == "__main__":
    main()
