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

def show_client_page():
    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider", None)

    if not provider_token:
        st.error("❌ Link de pedido inválido. Falta o código do prestador.")
        return

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
        font-size: 208px;
    }
    .stButton button {
        padding: 4px 12px !important;
        font-size: 14px !important;
        min-height: 35px !important;
    }
    .stTextInput label {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

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
        st.markdown(f"""
            <div style="text-align: center; padding: 20px 10px; margin: 10px auto; max-width: 700px;">
                """ + (f'<div style="color: white; font-weight: bold; font-size: 20px; margin-bottom: 12px;">Encontra-se na <b style="color: #FFC107;">{posicao_fila}º</b> posição</div>' if posicao_fila else '') + """
                <div class="spinning-mic">🎤</div>
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
                        st.error("Erro ao enviar o pedido para o DJ.")
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

    st.markdown("---")

    st.markdown("""
        <div style="background: linear-gradient(135deg, #1f1c2c, #928dab); padding: 25px; border-radius: 12px; text-align: center; color: white; margin-top: 30px;">
            <h3 style="margin-bottom: 10px; color: #FFC107;">Quer saber mais do serviço de Karaoke do Grupo FF, clica abaixo.</h3>
            <p style="font-size: 16px; margin: 8px 0;">📸 <b>Instagram:</b> <a href="https://instagram.com/ff.karaoke" target="_blank" style="color: #00d2ff; text-decoration: none;">ff.karaoke</a></p>
            <p style="font-size: 16px; margin: 8px 0;">📞 <b>Contacto para Eventos Privados:</b> 955099159</p>
            <p style="font-size: 16px; margin: 8px 0;">💬 <b>WhatsApp:</b> <a href="https://wa.me/244955099159" target="_blank" style="color: #25D366; text-decoration: none;">955099159</a></p>
        </div>
    """, unsafe_allow_html=True)
