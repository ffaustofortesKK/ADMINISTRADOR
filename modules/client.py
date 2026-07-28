import streamlit as st
import requests
import base64

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

# Credenciais da sua conta Cloudinary (fornecidas nos seus dados anteriores)
CLOUD_NAME = "yhwgjh7g"
# Opcional: se quiser usar autenticação da API Admin para listar vídeos de uma pasta específica
# API_KEY = "o_seu_api_key"
# API_SECRET = "o_seu_api_secret"

@st.cache_data(ttl=60) # Guarda em cache durante 60 segundos para otimizar a velocidade
def obter_catalogo_cloudinary():
    """
    Busca a lista de vídeos diretamente do Cloudinary usando a API pública/Search 
    ou retorna uma lista dinâmica baseada nos ficheiros conhecidos da nuvem.
    """
    catalogo_padrao = [
        {"titulo": "Há Mulheres e Mulheres", "artista": "Landrick", "url": f"https://res.cloudinary.com/{CLOUD_NAME}/video/upload/f_auto,q_auto/v1784592601/Karaoke_H%C3%81_MULHERES_E_MULHERES_-_Landrick_rnomfr.mp4"},
        {"titulo": "Nani Tá Quieto", "artista": "Kudurista", "url": f"https://res.cloudinary.com/{CLOUD_NAME}/video/upload/f_auto,q_auto/Nani_Ta_Quieto_f35hpj.mp4"}
    ]
    
    try:
        # Consulta à API de listagem pública do Cloudinary (se os recursos estiverem definidos como listáveis)
        url_api = f"https://res.cloudinary.com/{CLOUD_NAME}/video/list/karaoke.json"
        response = requests.get(url_api, timeout=3)
        if response.status_code == 200:
            data = response.json()
            recursos = data.get("resources", [])
            lista_dinamica = []
            for item in recursos:
                public_id = item.get("public_id", "")
                titulo_formatado = public_id.replace("_", " ").replace("-", " ").title()
                url_video = f"https://res.cloudinary.com/{CLOUD_NAME}/video/upload/f_auto,q_auto/{public_id}.mp4"
                lista_dinamica.append({
                    "titulo": titulo_formatado,
                    "artista": "Cloudinary Video",
                    "url": url_video
                })
            if lista_dinamica:
                return lista_dinamica
    except Exception:
        pass
        
    return catalogo_padrao

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
        print(f"Erro ao enviar pedido: {e}")
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
    st.markdown("Escolha a sua música diretamente da nuvem e envie para a fila!")
    st.markdown("---")

    cliente_nome = st.text_input("O seu Nome / alcunha:", placeholder="Ex: João da Silva")

    st.markdown("### 📚 Catálogo em Direto da Nuvem")

    pesquisa = st.text_input("🔍 Pesquisar música:", placeholder="Digite o nome...")

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
                        sucesso = enviar_pedido_firebase(provider_token, cliente_nome, musica)
                        if sucesso:
                            st.success(f"Pedido de '{musica['titulo']}' enviado com sucesso!")
                            st.balloons()
                        else:
                            st.error("Erro ao enviar o pedido.")
