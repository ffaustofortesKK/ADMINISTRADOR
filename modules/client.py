import streamlit as st
import requests
import time
import cloudinary
import cloudinary.api
from utils.db_manager import get_all_providers

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

# Configuração correta do Cloudinary
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
        print(f"Erro ao ligar ao Cloudinary: {e}")
    return catalogo

def verificar_estado_cliente(provider_token, cliente_nome):
    """Verifica se o cliente já tem um pedido pendente ou aprovado na fila."""
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()
            for k, v in data.items():
                if v.get("cliente", "").strip().lower() == cliente_nome.strip().lower():
                    estado = v.get("estado")
                    if estado in ["pendente", "aprovado"]:
                        # Calcular posição na fila
                        pedidos = [{"id": key, **val} for key, val in data.items() if val.get("estado") in ["pendente", "aprovado"]]
                        pedidos.sort(key=lambda x: x.get("timestamp", 0))
                        posicao = next((i for i, p in enumerate(pedidos, 1) if p["id"] == k), 1)
                        return True, posicao, estado
        return False, 0, None
    except Exception:
        return False, 0, None

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

def show_client_page():
    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider", None)

    if not provider_token:
        st.error("❌ Link de pedido inválido. Falta o código do prestador.")
        return

    # Estilos CSS gerais, marquee superior e microfone a girar
    st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    
    /* Marquee / Rodapé Superior */
    .marquee-container {
        width: 100%;
        overflow: hidden;
        white-space: nowrap;
        background: #1a1a1a;
        padding: 8px 0;
        border-bottom: 2px solid #FFC107;
        margin-bottom: 15px;
    }
    .marquee-text {
        display: inline-block;
        padding-left: 100%;
        animation: marquee 25s linear infinite;
        color: #FFC107;
        font-weight: bold;
        font-size: 14px;
        font-family: monospace;
    }
    @keyframes marquee {
        0%   { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); }
    }

    /* Microfone a girar */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .spinning-mic {
        display: inline-block;
        animation: spin 3s linear infinite;
        font-size: 40px;
    }
    
    /* Lista de músicas com scroll */
    .scroll-box {
        max-height: 250px;
        overflow-y: auto;
        padding-right: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Letreiro em rodapé na parte superior (marquee) com a agenda
    agenda_texto = (
        "🎤✨ AGENDA DO GRUPO FF KARAOKE ✨🎤  |  "
        "🎵 QUARTA-FEIRA 📍 Restaurante Cave da Samba 🎤 Apresentação: CEFAS DAVID  |  "
        "🎵 SEXTA-FEIRA 📍 Restaurante O Kubico 🎤 Apresentação: CEFAS DAVID 📌 Local: Maculusso  |  "
        "🎵 SEXTA-FEIRA 📍 Restaurante Dinugo 🎤 Apresentação: EDNA ANJINHA 📌 Local: Rangel B7"
    )
    st.markdown(f'<div class="marquee-container"><div class="marquee-text">{agenda_texto}</div></div>', unsafe_allow_html=True)

    # Gestão de Sessão do Nome do Cliente
    if 'cliente_nome' not in st.session_state:
        st.session_state.cliente_nome = ""
    if 'confirmar_musica' not in st.session_state:
        st.session_state.confirmar_musica = None

    # Ecrã de introdução de Nome / Boas-vindas compacta
    if not st.session_state.cliente_nome:
        st.markdown("### 🎤 Bem-vindo ao FFKaraoke")
        nome_input = st.text_input("Insira o seu Nome ou Alcunha:", placeholder="Ex: João da Silva")
        if st.button("Entrar"):
            if nome_input.strip():
                st.session_state.cliente_nome = nome_input.strip()
                st.rerun()
            else:
                st.warning("Por favor, insira um nome válido.")
        return

    # Cliente já registado: Apresentar saudação compacta
    st.markdown(f"<h3 style='color: #4CAF50; margin-bottom: 0px;'>Bem-vindo, {st.session_state.cliente_nome}! 🎤</h3>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    # Verificar se o cliente já tem pedido ativo na fila
    tem_pedido, posicao, estado = verificar_estado_cliente(provider_token, st.session_state.cliente_nome)

    if tem_pedido:
        # Bloco de espera com microfone a girar
        col_anim, col_msg = st.columns([1, 4])
        with col_anim:
            st.markdown('<div style="text-align: center;"><span class="spinning-mic">🎤</span></div>', unsafe_allow_html=True)
        with col_msg:
            st.warning(f"⚠️ **Não pode enviar outro pedido!** O seu pedido anterior está na posição **nº {posicao}** da playlist.")
            st.markdown("<p style='font-size: 13px; color: #aaa;'>Aguarde pela sua vez. Assim que a sua música cantar, poderá fazer um novo pedido.</p>", unsafe_allow_html=True)
        
        # Botão para atualizar estado da fila
        if st.button("🔄 Atualizar Estado"):
            st.rerun()
    else:
        # Permitir pesquisa e novo pedido
        st.markdown("🔍 **Pesquisar e Escolher Música:**")
        pesquisa = st.text_input("", placeholder="Digite o nome da música ou artista...", label_visibility="collapsed")

        catalogo = obter_catalogo_cloudinary()

        if not catalogo:
            st.warning("⚠️ O catálogo de músicas está temporariamente vazio.")
        elif pesquisa:
            musicas_filtradas = [
                m for m in catalogo 
                if pesquisa.lower() in m["titulo"].lower() or pesquisa.lower() in m["artista"].lower()
            ]

            if not musicas_filtradas:
                st.info("Nenhuma música encontrada com esse termo.")
            else:
                st.write(f"Encontradas {len(musicas_filtradas)} músicas:")
                
                # Caixa com scroll para a lista de resultados
                st.markdown('<div class="scroll-box">', unsafe_allow_html=True)
                for musica in musicas_filtradas:
                    col_t, col_b = st.columns([4, 1])
                    with col_t:
                        st.markdown(f"🎵 **{musica['titulo']}**")
                    with col_b:
                        if st.button("📤 Pedir", key=f"btn_{musica['id']}"):
                            st.session_state.confirmar_musica = musica
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        # Janela / Secção de Confirmação de Pedido
        if st.session_state.confirmar_musica:
            m_conf = st.session_state.confirmar_musica
            st.markdown("---")
            st.info(f"❓ **Tem a certeza que quer tocar:** *{m_conf['titulo']}*?")
            col_sim, col_nao = st.columns(2)
            with col_sim:
                if st.button("✅ Sim, Enviar Pedido"):
                    if enviar_pedido_firebase(provider_token, st.session_state.cliente_nome, m_conf):
                        st.success("Pedido enviado com sucesso!")
                        st.session_state.confirmar_musica = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Erro ao enviar o pedido.")
            with col_nao:
                if st.button("❌ Cancelar"):
                    st.session_state.confirmar_musica = None
                    st.rerun()

    st.markdown("---")

    # Secção de Redes Sociais e Eventos Privados
    st.markdown("""
    <div style="background-color: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; text-align: center; margin-top: 20px;">
        <p style="font-size: 15px; font-weight: bold; color: #58a6ff; margin-bottom: 8px;">
            Quer saber mais do serviço de Karaoke do Grupo FF, clica abaixo.
        </p>
        <p style="font-size: 14px; margin: 5px 0;">
            📸 Instagram: <a href="https://instagram.com/ff.karaoke" target="_blank" style="color: #ff79c6; text-decoration: none;">@ff.karaoke</a>
        </p>
        <p style="font-size: 14px; margin: 5px 0;">
            📞 Contacto para Eventos Privados / WhatsApp: <b>955099159</b>
        </p>
    </div>
    """, unsafe_allow_html=True)
