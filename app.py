import streamlit as st
import requests
import time
import cloudinary
import cloudinary.api

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

# Configuração do Cloudinary
cloudinary.config(
    cloud_name="yhwgjh7g",
    api_key="852434629995691",
    api_secret="TU_ejil7wKYY15xHjDcRVfbk6Ow",
    secure=True
)

@st.cache_data(ttl=60)
def obter_catalogo_cloudinary():
    catalogo = []
    try:
        result = cloudinary.api.resources(
            resource_type="video",
            max_results=200
        )
        resources = result.get("resources", [])
        for item in resources:
            public_id = item.get("public_id", "")
            titulo_limpo = public_id.split("/")[-1].replace("_", " ").replace("-", " ").title()
            url_video = item.get("secure_url", "")
            catalogo.append({
                "id": public_id,
                "titulo": titulo_limpo,
                "artista": "FFKaraoke",
                "url": url_video
            })
    except Exception as e:
        print(f"Erro ao ligar ao Cloudinary SDK: {e}")
    return catalogo

def enviar_pedido_firebase(provider_token, cliente_nome, musica_escolhida):
    try:
        novo_pedido = {
            "cliente": cliente_nome,
            "musica": musica_escolhida,
            "estado": "pendente",
            "timestamp": int(time.time() * 1000)
        }
        url = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        response = requests.post(url, json=novo_pedido, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

def obter_pedidos_cliente(provider_token):
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()
            return [{"id": k, **v} for k, v in data.items()]
    except Exception:
        pass
    return []

def atualizar_estado_pedido(provider_token, pedido_id, novo_estado):
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}/estado.json"
        response = requests.put(url, json=novo_estado, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

def apagar_pedido_firebase(provider_token, pedido_id):
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}.json"
        response = requests.delete(url, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

# ==================== PAINEL DE ADMINISTRADOR (ADM) ====================
def show_admin_page():
    if "admin_autenticado" not in st.session_state:
        st.session_state.admin_autenticado = False

    PALAVRA_PASSE_MESTRE = "ffkaraoke2026"

    if not st.session_state.admin_autenticado:
        st.markdown("<h2 style='color: #FFC107;'>🔒 Painel ADM - FF Karaoke</h2>", unsafe_allow_html=True)
        senha_adm = st.text_input("Palavra-passe do Administrador:", type="password", key="senha_adm_input")
        if st.button("Entrar no ADM", key="btn_login_adm"):
            if senha_adm == PALAVRA_PASSE_MESTRE:
                st.session_state.admin_autenticado = True
                st.rerun()
            else:
                st.error("❌ Palavra-passe incorreta!")
        return

    st.markdown("<h1>🎛️ Painel de Controlo do Prestador / ADM</h1>", unsafe_allow_html=True)
    st.markdown("Gerencie os pedidos de karaoke recebidos em tempo real.")

    # Definir o token do prestador gerido no ADM (ex: "1" ou o ID padrão)
    provider_token = st.text_input("Código do Prestador (Token):", value="1", key="input_token_adm")

    if st.button("🔄 Atualizar Pedidos", key="btn_refresh_adm"):
        st.rerun()

    pedidos = obter_pedidos_cliente(provider_token)
    
    if not pedidos:
        st.info("ℹ️ Nenhum pedido registado para este prestador no momento.")
        return

    st.markdown("### 📋 Lista de Pedidos")
    for p in pedidos:
        p_id = p.get("id")
        cliente = p.get("cliente", "Desconhecido")
        musica_dict = p.get("musica", {})
        titulo_musica = musica_dict.get("titulo", "Música desconhecida") if isinstance(musica_dict, dict) else str(musica_dict)
        estado = p.get("estado", "pendente")

        cor_estado = "#FFC107" if estado == "pendente" else "#4CAF50" if estado == "aprovado" else "#f44336"
        
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
            with col1:
                st.markdown(f"👤 **{cliente}**")
            with col2:
                st.markdown(f"🎵 {titulo_musica}")
            with col3:
                st.markdown(f"<span style='color: {cor_estado}; font-weight: bold;'>{estado.upper()}</span>", unsafe_allow_html=True)
            with col4:
                if estado == "pendente":
                    if st.button("✅ Aprovar", key=f"aprov_{p_id}"):
                        atualizar_estado_pedido(provider_token, p_id, "aprovado")
                        st.rerun()
                if st.button("🗑️ Apagar", key=f"del_{p_id}"):
                    apagar_pedido_firebase(provider_token, p_id)
                    st.rerun()
            st.markdown("---")

# ==================== PÁGINA DO CLIENTE ====================
def show_client_page():
    st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .marquee-container {
        width: 100%;
        overflow: hidden;
        white-space: nowrap;
        background: #1a1a1a;
        border-bottom: 2px solid #FFC107;
        border-top: 2px solid #FFC107;
        padding: 8px 0;
        margin-bottom: 20px;
    }
    .marquee-text {
        display: inline-block;
        padding-left: 100%;
        animation: marquee 25s linear infinite;
        color: #FFC107;
        font-weight: bold;
        font-size: 15px;
        font-family: monospace;
    }
    @keyframes marquee {
        0% { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); }
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .spinning-mic {
        animation: spin 3s linear infinite;
        display: inline-block;
        font-size: 160px;
    }
    </style>
    """, unsafe_allow_html=True)

    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider", "1")

    agenda_texto = (
        "🎤✨ AGENDA DO GRUPO FF KARAOKE ✨🎤  |  "
        "🎵 QUARTA-FEIRA 📍 Restaurante Cave da Samba 🎤 Apresentação: CEFAS DAVID  |  "
        "🎵 SEXTA-FEIRA 📍 Restaurante O Kubico 🎤 Apresentação: CEFAS DAVID 📌 Local: Maculusso  |  "
        "🎵 SEXTA-FEIRA 📍 Restaurante Dinugo 🎤 Apresentação: EDNA ANJINHA 📌 Local: Rangel B7"
    )
    st.markdown(f"""
        <div class="marquee-container">
            <div class="marquee-text">{agenda_texto}</div>
        </div>
    """, unsafe_allow_html=True)

    if 'cliente_registado' not in st.session_state:
        st.session_state.cliente_registado = ""
    if 'pesquisa_input' not in st.session_state:
        st.session_state.pesquisa_input = ""
    if 'musica_selecionada' not in st.session_state:
        st.session_state.musica_selecionada = None

    if not st.session_state.cliente_registado:
        st.markdown("## 🎤 Bem-vindo ao FF Karaoke")
        st.markdown("Insira o seu nome ou alcunha para começar:")
        with st.form("form_registo"):
            nome_input = st.text_input("O seu Nome / alcunha:", placeholder="Ex: João da Silva")
            submitted = st.form_submit_button("Entrar")
            if submitted:
                if nome_input.strip():
                    st.session_state.cliente_registado = nome_input.strip()
                    st.rerun()
                else:
                    st.warning("⚠️ Por favor, insira um nome válido.")
        return

    cliente_nome = st.session_state.cliente_registado
    st.markdown(f"<h1 style='color: #4CAF50; font-size: 28px; margin-bottom: 0;'>Benvindo {cliente_nome}</h1>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

    pedidos = obter_pedidos_cliente(provider_token)
    pedidos_cliente = [p for p in pedidos if p.get("cliente", "").lower() == cliente_nome.lower() and p.get("estado") in ["pendente", "aprovado"]]
    
    tem_pedido_ativo = len(pedidos_cliente) > 0
    posicao_fila = None
    if tem_pedido_ativo:
        pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
        pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
        for idx, p in enumerate(pedidos_ativos, start=1):
            if p.get("cliente", "").lower() == cliente_nome.lower():
                posicao_fila = idx
                break

    if tem_pedido_ativo:
        st.markdown("""
            <div style="text-align: center; padding: 40px 10px; margin: 20px auto; max-width: 700px;">
                <div class="spinning-mic">🎤</div>
                <h2 style="color: #FFC107; margin-top: 20px; font-size: 28px;">Aguarde pela sua vez</h2>
                <p style="color: #ddd; font-size: 16px; margin-top: 10px;">Fica dentro da agenda de karaoke do grupo FF. O seu pedido já está registado na fila.</p>
                """ + (f"<p style='color: #4CAF50; font-weight: bold; font-size: 18px; margin-top: 15px;'>📍 Encontra-se na posição <b>{posicao_fila}º</b> da fila.</p>" if posicao_fila else "") + """
            </div>
        """, unsafe_allow_html=True)
    else:
        st.success("✅ Já poderá enviar o seu pedido!")

    if st.session_state.musica_selecionada:
        musica_atual = st.session_state.musica_selecionada
        st.markdown(f"""
            <div style="background: #161a23; padding: 20px; border-radius: 12px; border: 2px solid #4CAF50; text-align: center; margin: 10px 0 15px 0;">
                <h3 style="color: #4CAF50; margin-bottom: 10px; font-size: 20px;">Confirmação de Pedido</h3>
                <p style="font-size: 18px; font-weight: bold; margin-bottom: 15px;">Quer tocar <b>{musica_atual['titulo']}</b>?</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_espaco1, col_c1, col_c2, col_espaco2 = st.columns([2, 2, 2, 2])
        with col_c1:
            if st.button("✅ Sim", use_container_width=True, key="btn_sim_enviar"):
                if tem_pedido_ativo:
                    st.error("❌ Não pode enviar outro pedido enquanto o pedido anterior não for cantado.")
                else:
                    sucesso = enviar_pedido_firebase(provider_token, cliente_nome, musica_atual)
                    if sucesso:
                        st.success(f"Pedido de '{musica_atual['titulo']}' enviado com sucesso!")
                        st.session_state.pesquisa_input = ""
                        st.session_state.musica_selecionada = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Erro ao enviar o pedido.")
        with col_c2:
            if st.button("❌ Não", use_container_width=True, key="btn_nao_cancelar"):
                st.session_state.musica_selecionada = None
                st.rerun()
        st.markdown("---")

    st.markdown("### 🔍 Pesquisar Música")
    pesquisa = st.text_input("Digite o nome da música ou artista:", value=st.session_state.pesquisa_input, placeholder="Ex: Landrick, Nani...")
    st.session_state.pesquisa_input = pesquisa

    catalogo = obter_catalogo_cloudinary()

    if pesquisa:
        musicas_filtradas = [
            m for m in catalogo 
            if pesquisa.lower() in m["titulo"].lower() or pesquisa.lower() in m["artista"].lower()
        ]

        if musicas_filtradas:
            st.write(f"Encontradas {len(musicas_filtradas)} músicas:")
            container_lista = st.container(height=300)
            with container_lista:
                for musica in musicas_filtradas:
                    cols = st.columns([4, 1])
                    with cols[0]:
                        st.markdown(f"🎵 **{musica['titulo']}**")
                    with cols[1]:
                        if st.button("Selecionar", key=f"sel_{musica['id']}"):
                            st.session_state.musica_selecionada = musica
                            st.rerun()
        else:
            st.warning("Nenhuma música encontrada com esse termo.")

# ==================== NAVEGAÇÃO PRINCIPAL ====================
def main():
    st.sidebar.title("🎛️ Menu FF Karaoke")
    pagina = st.sidebar.radio("Escolha a Vista:", ["🎤 Página do Cliente", "🛠️ Painel Administrador (ADM)"])

    if pagina == "🎤 Página do Cliente":
        show_client_page()
    else:
        show_admin_page()

if __name__ == "__main__":
    main()
