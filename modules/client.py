import streamlit as st
import requests
import time
import urllib.parse
import cloudinary
import cloudinary.api
from utils.db_manager import get_all_providers

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
        print(f"Erro detalhado ao ligar ao Cloudinary SDK: {e}")
    return catalogo

def verificar_estado_cliente_firebase(provider_token, cliente_nome):
    """Verifica se o cliente já tem um pedido pendente ou a tocar na fila."""
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()
            for k, v in data.items():
                if v.get("cliente", "").strip().lower() == cliente_nome.strip().lower():
                    estado = v.get("estado")
                    if estado in ["pendente", "aprovado"]:
                        return True, estado
    except Exception:
        pass
    return False, None

def obterposicao_fila(provider_token, cliente_nome):
    """Calcula a posição do cliente na fila de espera."""
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
            
            for idx, p in enumerate(pedidos_ativos, start=1):
                if p.get("cliente", "").strip().lower() == cliente_nome.strip().lower():
                    return idx, p.get("estado")
    except Exception:
        pass
    return None, None

def enviar_pedido_firebase(provider_token, cliente_nome, musica_escolhida):
    try:
        novo_pedido = {
            "cliente": cliente_nome if cliente_nome else "Convidado",
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

    # Estilos CSS gerais e do Letreiro Deslizante (Marquee) para a Agenda
    st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    
    /* Estilo do Letreiro da Agenda */
    .marquee-container {
        width: 100%;
        overflow: hidden;
        white-space: nowrap;
        background: linear-gradient(90deg, #1f1c2c, #928DAB);
        padding: 10px 0;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .marquee-text {
        display: inline-block;
        padding-left: 100%;
        animation: marquee 30s linear infinite;
        font-family: monospace;
        font-size: 15px;
        color: #ffffff;
        font-weight: bold;
    }
    @keyframes marquee {
        0%   { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); }
    }
    
    .welcome-box {
        background: linear-gradient(135deg, #1f4037, #99f2c8);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        color: #000;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .social-box {
        background-color: #1a1a1a;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 10px;
        margin-top: 30px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # Letreiro / Rodapé Superior da Agenda
    agenda_html = """
    <div class="marquee-container">
        <div class="marquee-text">
            🎤✨ AGENDA DO GRUPO FF KARAOKE ✨🎤 &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; 
            🎵 QUARTA-FEIRA — 📍 Restaurante Cave da Samba — 🎤 Apresentação: CEFAS DAVID &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; 
            🎵 SEXTA-FEIRA — 📍 Restaurante O Kubico (Maculusso) — 🎤 Apresentação: CEFAS DAVID &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; 
            🎵 SEXTA-FEIRA — 📍 Restaurante Dinugo (Rangel B7) — 🎤 Apresentação: EDNA ANJINHA
        </div>
    </div>
    """
    st.markdown(agenda_html, unsafe_allow_html=True)

    st.markdown("## 🎤 FFKaraoke — Painel do Cliente")
    st.markdown("---")

    # Gestão do Estado do Nome do Cliente
    if 'cliente_nome_input' not in st.session_state:
        st.session_state.cliente_nome_input = ""
    if 'confirmar_envio_musica' not in st.session_state:
        st.session_state.confirmar_envio_musica = None

    cliente_nome = st.text_input("Insira o seu Nome ou Alcunha para começar:", value=st.session_state.cliente_nome_input, placeholder="Ex: João da Silva")
    st.session_state.cliente_nome_input = cliente_nome

    if not cliente_nome.strip():
        st.info("💡 Por favor, insira o seu nome/alcunha acima para desbloquear o sistema de pedidos.")
        return

    # Mensagem de Boas-Vindas em Ponto Grande
    st.markdown(f"""
        <div class="welcome-box">
            <h1>🎉 Bem-vindo, {cliente_nome}!</h1>
            <p>Escolha a sua música favorita e divirta-se no palco do Grupo FF.</p>
        </div>
    """, unsafe_allow_html=True)

    # Verificar se o cliente já tem pedido ativo na fila
    tem_pedido, estado_atual = verificar_estado_cliente_firebase(provider_token, cliente_nome)
    posicao, _ = obterposicao_fila(provider_token, cliente_nome)

    if tem_pedido:
        if estado_atual == "aprovado":
            st.warning(f"🚨 A sua música está a tocar ou foi aprovada! Aguarde que termine para poder submeter um novo pedido.")
        else:
            st.info(f"⏳ Já tem um pedido pendente na fila! Encontra-se na **posição nº {posicao}**. Só poderá enviar outro pedido assim que a sua música passar e terminar.")
    else:
        if posicao is not None:
            st.success("✅ A sua música anterior já passou! Já pode enviar um novo pedido.")

        # Barra de Pesquisa de Músicas
        if 'termo_pesquisa' not in st.session_state:
            st.session_state.termo_pesquisa = ""

        pesquisa = st.text_input("🔍 Pesquisar música:", value=st.session_state.termo_pesquisa, placeholder="Digite o nome da música ou artista...")
        st.session_state.termo_pesquisa = pesquisa

        catalogo = obter_catalogo_cloudinary()

        if not catalogo:
            st.warning("⚠️ O catálogo de músicas ainda está vazio ou a carregar.")
        elif pesquisa:
            musicas_filtradas = [
                m for m in catalogo 
                if pesquisa.lower() in m["titulo"].lower() or pesquisa.lower() in m["artista"].lower()
            ]

            if not musicas_filtradas:
                st.warning("Nenhuma música encontrada com esse termo.")
            else:
                st.write(f"Encontradas {len(musicas_filtradas)} músicas semelhantes:")
                for musica in musicas_filtradas[:15]:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"🎵 **{musica['titulo']}**")
                    with col2:
                        safe_key = f"btn_cloud_{musica['id']}"
                        if st.button("📤 Pedir", key=safe_key):
                            st.session_state.confirmar_envio_musica = musica

        # Caixa de Confirmação de Envio ("Tem a certeza...")
        if st.session_state.confirmar_envio_musica:
            musica_alvo = st.session_state.confirmar_envio_musica
            st.markdown("---")
            st.warning(f"⚠️ **Confirmação de Pedido**\n\nTem a certeza de que deseja enviar o pedido da música **'{musica_alvo['titulo']}'**?")
            
            col_sim, col_nao = st.columns(2)
            with col_sim:
                if st.button("✅ Sim, tenho a certeza", use_container_width=True):
                    # Dupla checagem de segurança antes de enviar
                    checa_ativo, _ = verificar_estado_cliente_firebase(provider_token, cliente_nome)
                    if checa_ativo:
                        st.error("❌ Não pode enviar outro pedido enquanto o seu pedido anterior não for cantado e terminado.")
                    else:
                        if enviar_pedido_firebase(provider_token, cliente_nome, musica_alvo):
                            st.success(f"Pedido de '{musica_alvo['titulo']}' enviado com sucesso!")
                            st.balloons()
                            # Limpar campos após envio
                            st.session_state.termo_pesquisa = ""
                            st.session_state.confirmar_envio_musica = None
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Erro ao enviar o pedido para o DJ.")
            with col_nao:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.confirmar_envio_musica = None
                    st.rerun()

    # Secção de Redes Sociais e Contactos com texto chamativo pedido
    st.markdown("""
        <div class="social-box">
            <h3>Quer saber mais do serviço de Karaoke do Grupo FF, clica abaixo.</h3>
            <p style="margin: 15px 0; font-size: 16px;">
                📸 <b>Instagram:</b> <a href="https://instagram.com/ff.karaoke" target="_blank" style="color: #ff4b4b; text-decoration: none;">ff.karaoke</a>
            </p>
            <p style="margin: 10px 0; font-size: 16px;">
                📞 <b>Contacto para Eventos Privados:</b> 955099159
            </p>
            <p style="margin: 10px 0; font-size: 16px;">
                💬 <b>WhatsApp:</b> <a href="https://wa.me/244955099159" target="_blank" style="color: #25D366; text-decoration: none;">955099159</a>
            </p>
        </div>
    """, unsafe_allow_html=True)
