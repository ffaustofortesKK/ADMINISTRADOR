import streamlit as st
import requests
import cloudinary
import cloudinary.api

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

# Configuração com as suas credenciais exatas do Cloudinary
cloudinary.config(
    cloud_name="TU_ejil7wKYY15xHjDcRVfbk6Ow",
    api_key="852434629995691",
    api_secret="oWTTGfF8KRtd4ojFiS",
    secure=True
)

@st.cache_data(ttl=30)
def obter_catalogo_cloudinary():
    catalogo = []
    try:
        # Tenta listar os vídeos da nuvem (incluindo a pasta de vídeos se aplicável)
        result = cloudinary.api.resources(
            resource_type="video",
            max_results=100
        )
        
        for item in result.get("resources", []):
            public_id = item.get("public_id", "")
            titulo_limpo = public_id.split("/")[-1].replace("_", " ").replace("-", " ").title()
            url_video = item.get("secure_url", "")
            catalogo.append({
                "titulo": titulo_limpo,
                "artista": "FFKaraoke",
                "url": url_video
            })
    except Exception as e:
        print(f"Erro ao ligar ao Cloudinary SDK: {e}")

    # Fallback de segurança caso a ligação demore ou a nuvem esteja vazia
    if not catalogo:
        catalogo = [
            {
                "titulo": "Há Mulheres e Mulheres", 
                "artista": "Landrick", 
                "url": "https://res.cloudinary.com/TU_ejil7wKYY15xHjDcRVfbk6Ow/video/upload/f_auto,q_auto/v1784592601/Karaoke_H%C3%81_MULHERES_E_MULHERES_-_Landrick_rnomfr.mp4"
            },
            {
                "titulo": "Nani Tá Quieto", 
                "artista": "Kudurista", 
                "url": "https://res.cloudinary.com/TU_ejil7wKYY15xHjDcRVfbk6Ow/video/upload/f_auto,q_auto/Nani_Ta_Quieto_f35hpj.mp4"
            }
        ]
    return catalogo

def enviar_pedido_firebase(provider_token, cliente_nome, musica_escolhida):
    try:
        import time
        novo_pedido = {
            "cliente": cliente_nome if cliente_nome else "Convidado",
            "musica": musica_escolhida,
            "estado": "pendente",
            "timestamp": int(time.time() * 1000)
        }
        url = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        response = requests.post(url, json=novo_pedido)
        return response.status_code == 200
    except Exception:
        return False

def show_client_page():
    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider", None)

    if not provider_token:
        st.error("Link de pedido inválido. Falta o código do prestador.")
        return

    st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("## 🎤 FFKaraoke — Pedir Música")
    st.markdown("Pesquise e escolha a sua música diretamente da nuvem!")
    st.markdown("---")

    cliente_nome = st.text_input("O seu Nome / alcunha:", placeholder="Ex: João da Silva")
    pesquisa = st.text_input("🔍 Pesquisar música:", placeholder="Digite para filtrar os títulos...")

    catalogo = obter_catalogo_cloudinary()

    musicas_filtradas = [
        m for m in catalogo 
        if pesquisa.lower() in m["titulo"].lower() or pesquisa.lower() in m["artista"].lower()
    ] if pesquisa else catalogo

    if not musicas_filtradas:
        st.warning("Nenhuma música encontrada.")
    else:
        for idx, musica in enumerate(musicas_filtradas):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"🎵 **{musica['titulo']}** — *{musica['artista']}*")
            with col2:
                if st.button("📤 Pedir", key=f"btn_cloud_{idx}"):
                    if not cliente_nome.strip():
                        st.warning("Por favor, insira o seu nome.")
                    else:
                        if enviar_pedido_firebase(provider_token, cliente_nome, musica):
                            st.success(f"Pedido de '{musica['titulo']}' enviado com sucesso!")
                            st.balloons()
                        else:
                            st.error("Erro ao enviar o pedido.")
