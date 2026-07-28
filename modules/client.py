import streamlit as st
import requests

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

CLOUD_NAME = "yhwgjh7g"
API_KEY = "852581666546867"
API_SECRET = "oWTTGfF8KRtd4ojFiS"

@st.cache_data(ttl=30)
def obter_catalogo_cloudinary():
    catalogo = []
    if API_KEY and API_SECRET:
        try:
            # Se os vídeos estão numa pasta chamada "video", usamos o prefixo para pesquisar lá dentro
            url = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/resources/video?prefix=video/&max_results=100"
            response = requests.get(url, auth=(API_KEY, API_SECRET), timeout=5)
            
            # Se não encontrar nada com o prefixo, tenta listar a raiz geral
            if response.status_code == 200 and not response.json().get("resources"):
                url = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/resources/video?max_results=100"
                response = requests.get(url, auth=(API_KEY, API_SECRET), timeout=5)

            if response.status_code == 200:
                data = response.json()
                for item in data.get("resources", []):
                    public_id = item.get("public_id", "")
                    titulo_limpo = public_id.split("/")[-1].replace("_", " ").replace("-", " ").title()
                    url_video = item.get("secure_url", "")
                    catalogo.append({
                        "titulo": titulo_limpo,
                        "artista": "Cloudinary",
                        "url": url_video
                    })
        except Exception:
            pass

    if not catalogo:
        catalogo = [
            {
                "titulo": "Há Mulheres e Mulheres", 
                "artista": "Landrick", 
                "url": f"https://res.cloudinary.com/{CLOUD_NAME}/video/upload/f_auto,q_auto/v1784592601/Karaoke_H%C3%81_MULHERES_E_MULHERES_-_Landrick_rnomfr.mp4"
            },
            {
                "titulo": "Nani Tá Quieto", 
                "artista": "Kudurista", 
                "url": f"https://res.cloudinary.com/{CLOUD_NAME}/video/upload/f_auto,q_auto/Nani_Ta_Quieto_f35hpj.mp4"
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
    except Exception as e:
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
    st.markdown("Pesquise e escolha a sua música diretamente da pasta de vídeos!")
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
