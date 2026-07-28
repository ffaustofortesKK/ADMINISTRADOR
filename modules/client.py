import streamlit as st
import requests
import time
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
        result = cloudinary.api.resources(resource_type="video", max_results=200)
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

def obter_pedidos_firebase(provider_token):
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()
            return [{"id": k, **v} for k, v in data.items()]
    except Exception:
        pass
    return []

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

    # Estilos CSS gerais (incluindo o letreiro em rodapé estilo marquee)
    st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .marquee-container {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #1a1d24;
        color: #FFC107;
        padding: 10px 0;
        font-family: monospace;
        font-size: 15px;
        white-space: nowrap;
        overflow: hidden;
        z-index: 9999;
        border-top: 2px solid #333;
    }
    .marquee-text {
        display: inline-block;
        padding-left: 100%;
        animation: marquee 25s linear infinite;
    }
    @keyframes marquee {
        0%   { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); }
    }
    .banner-box {
        background: linear-gradient(135deg, #1f4068, #162447);
        border: 1px solid #e43f5a;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
    <div class="marquee-container">
        <div class="marquee-text">
            🎤✨ AGENDA DO GRUPO FF KARAOKE ✨🎤 &nbsp;&nbsp;|&nbsp;&nbsp; 🎵 QUARTA-FEIRA: Restaurante Cave da Samba (Apresentação: CEFAS DAVID) &nbsp;&nbsp;|&nbsp;&nbsp; 🎵 SEXTA-FEIRA: Restaurante O Kubico - Maculusso (Apresentação: CEFAS DAVID) &nbsp;&nbsp;|&nbsp;&nbsp; 🎵 SEXTA-FEIRA: Restaurante Dinugo - Rangel B7 (Apresentação: EDNA ANJINHA)
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## 🎤 FFKaraoke — Painel do Cliente")
    st.markdown("---")

    # Gestão do Nome / Alcunha do Cliente
    if 'cliente_nome_input' not in st.session_state:
        st.session_state.cliente_nome_input = ""

    cliente_nome = st.text_input("Insira o seu Nome ou Alcunha para começar:", value=st.session_state.cliente_nome_input, placeholder="Ex: João da Silva")
    
    if not cliente_nome.strip():
        st.info("💡 Por favor, insira o seu nome acima para desbloquear o sistema de pedidos.")
        return

    st.session_state.cliente_nome_input = cliente_nome.strip()
    
    # Mensagem de Boas-vindas em destaque
    st.markdown(f"<h1 style='color: #4CAF50; text-align: center;'>Bem-vindo, {st.session_state.cliente_nome_input}!</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Verificar se o cliente já tem um pedido ativo na fila (pendente ou aprovado/a tocar)
    pedidos_atuais = obter_pedidos_firebase(provider_token)
    meus_pedidos_ativos = [
        p for p in pedidos_atuais 
        if p.get("cliente", "").strip().lower() == st.session_state.cliente_nome_input.lower() 
        and p.get("estado") in ["pendente", "aprovado"]
    ]

    if meus_pedidos_ativos:
        # Descobrir a posição exata na playlist
        pedidos_ativos_geral = [p for p in pedidos_atuais if p.get("estado") in ["pendente", "aprovado"]]
        pedidos_ativos_geral.sort(key=lambda x: x.get("timestamp", 0))
        
        # Encontrar a posição do cliente
        posicao = next((idx for idx, p in enumerate(pedidos_ativos_geral, start=1) if p.get("cliente", "").strip().lower() == st.session_state.cliente_nome_input.lower()), 0)
        
        st.warning(f"🚫 **Atenção:** Você já tem um pedido ativo na fila! Encontra-se na **posição nº {posicao}** da playlist.")
        st.info("ℹ️ Só poderá enviar um novo pedido assim que a sua música atual passar na tela e terminar.")
    else:
        # Se cantou e terminou, exibe a mensagem de permissão
        if 'ja_cantou_notificado' in st.session_state and st.session_state.ja_cantou_notificado:
            st.success("🎉 A sua música anterior já passou! Já poderá enviar o seu próximo pedido.")

        pesquisa = st.text_input("🔍 Pesquisar música:", placeholder="Digite o nome da música ou artista...")

        catalogo = obter_catalogo_cloudinary()

        if pesquisa:
            musicas_filtradas = [
                m for m in catalogo 
                if pesquisa.lower() in m["titulo"].lower() or pesquisa.lower() in m["artista"].lower()
            ]

            if not musicas_filtradas:
                st.warning("Nenhuma música encontrada com esse termo.")
            else:
                st.write(f"Encontradas {len(musicas_filtradas)} músicas semelhantes:")
                for musica in musicas_filtradas[:20]:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"🎵 **{musica['titulo']}**")
                    with col2:
                        safe_key = f"btn_cloud_{musica['id']}"
                        if st.button("📤 Pedir", key=safe_key):
                            st.session_state['musica_selecionada_pendente'] = musica

        # Confirmação antes de enviar o pedido
        if 'musica_selecionada_pendente' in st.session_state and st.session_state['musica_selecionada_pendente']:
            musica_escolhida = st.session_state['musica_selecionada_pendente']
            st.info(q:=f"Tem a certeza que deseja enviar o pedido de **{musica_escolhida['titulo']}**?")
            
            c_sim, c_nao = st.columns(2)
            with c_sim:
                if st.button("✅ Sim, Enviar Pedido"):
                    if enviar_pedido_firebase(provider_token, st.session_state.cliente_nome_input, musica_escolhida):
                        st.success(f"Pedido de '{musica_escolhida['titulo']}' enviado com sucesso!")
                        st.session_state['musica_selecionada_pendente'] = None
                        st.session_state['ja_cantou_notificado'] = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Erro ao enviar o pedido para o DJ.")
            with c_nao:
                if st.button("❌ Cancelar"):
                    st.session_state['musica_selecionada_pendente'] = None
                    st.rerun()

    st.markdown("---")
    
    # Bloco Chamativo de Redes Sociais e Eventos
    st.markdown("""
        <div class="banner-box">
            <h3>Quer saber mais do serviço de Karaoke do Grupo FF, clica abaixo.</h3>
            <p style="font-size: 16px; margin: 10px 0;">📸 <b>Instagram:</b> <a href="https://instagram.com/ff.karaoke" target="_blank" style="color: #ff6584; text-decoration: none;">@ff.karaoke</a></p>
            <p style="font-size: 16px; margin: 5px 0;">📞 <b>Contacto para Eventos Privados:</b> 955099159</p>
            <p style="font-size: 16px; margin: 5px 0;">💬 <b>WhatsApp:</b> <a href="https://wa.me/244955099159" target="_blank" style="color: #4CAF50; text-decoration: none;">955099159</a></p>
        </div>
    """, unsafe_allow_html=True)
