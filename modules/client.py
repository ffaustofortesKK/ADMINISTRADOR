import streamlit as st
import requests
import time
import cloudinary
import cloudinary.api
from utils.db_manager import get_all_providers

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

# Configuração do Cloudinary
cloudinary.config(
    cloud_name="ejil7wKYY15xHjDcRVfbk6Ow",
    api_key="766164269958181",
    api_secret="oWTTGfF8KRtd4ojFiS",
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
        for item in result.get("resources", []):
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

    df_prov = get_all_providers()
    prestador = df_prov[df_prov['token'] == provider_token]
    
    if prestador.empty:
        st.error("❌ Link de prestador inválido ou inexistente na base de dados.")
        return

    row_prov = prestador.iloc[0]
    if row_prov.get('approved', 0) != 1:
        st.warning("⏳ Este painel de prestador encontra-se temporariamente inativo ou expirado.")
        return

    st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"## 🎤 FFKaraoke — {row_prov['name']}")
    st.markdown("Pesquise e escolha a sua música diretamente da nuvem!")
    st.markdown("---")

    if 'cliente_nome_input' not in st.session_state:
        st.session_state.cliente_nome_input = ""

    cliente_nome = st.text_input("O seu Nome / alcunha:", value=st.session_state.cliente_nome_input, placeholder="Ex: João da Silva")
    st.session_state.cliente_nome_input = cliente_nome

    pesquisa = st.text_input("🔍 Pesquisar música:", placeholder="Digite o nome da música...")

    catalogo = obter_catalogo_cloudinary()

    if not pesquisa:
        st.info("💡 Digite algo na caixa de pesquisa acima para encontrar as músicas disponíveis.")
        musicas_filtradas = []
    else:
        musicas_filtradas = [
            m for m in catalogo 
            if pesquisa.lower() in m["titulo"].lower() or pesquisa.lower() in m["artista"].lower()
        ]

    if pesquisa and not musicas_filtradas:
        st.warning("Nenhuma música encontrada com esse termo.")
    elif musicas_filtradas:
        st.write(f"Encontradas {len(musicas_filtradas)} músicas:")
        for musica in musicas_filtradas[:30]:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"🎵 **{musica['titulo']}**")
            with col2:
                safe_key = f"btn_cloud_{musica['id']}"
                if st.button("📤 Pedir", key=safe_key):
                    if not cliente_nome.strip():
                        st.warning("⚠️ Por favor, insira o seu nome antes de pedir.")
                    else:
                        if enviar_pedido_firebase(provider_token, cliente_nome, musica):
                            st.success(f"Pedido de '{musica['titulo']}' enviado com sucesso!")
                            st.balloons()
                        else:
                            st.error("Erro ao enviar o pedido para o DJ.")
