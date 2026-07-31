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

def obter_pedidos_adm(provider_token):
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

def show_admin_page():
    st.markdown("""
    <style>
    /* Fundo geral da página ADM em cor Lilás */
    .stApp { 
        background-color: #9370DB !important; 
        color: white !important; 
    }

    /* Imagem de fundo personalizada no painel de perfil */
    .adm-profile-bg {
        background-image: url('https://res.cloudinary.com/yhwgjh7g/image/upload/v1748000000/image_5b2977.jpg');
        background-size: cover;
        background-position: center;
        border-radius: 15px;
        padding: 30px;
        margin-bottom: 20px;
        border: 2px solid #FFC107;
    }

    .stButton button {
        padding: 6px 16px !important;
        font-size: 16px !important;
        min-height: 40px !important;
    }
    
    .stTextInput label, .stSelectbox label {
        color: #FFC107 !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="adm-profile-bg">
            <h1 style='color: #FFC107; text-align: center; margin-bottom: 0;'>Painel de Administração - FF Karaoke</h1>
        </div>
    """, unsafe_allow_html=True)

    # Identificação do prestador / DJ
    provider_token = st.text_input("🔑 Insira o seu Token / Código de Prestador:", placeholder="Ex: meu_token_dj")

    if not provider_token:
        st.warning("⚠️ Insira o token de prestador para ver e gerir os pedidos.")
        return

    st.markdown("---")
    st.subheader("📋 Gestão de Pedidos na Fila")

    if st.button("🔄 Atualizar Pedidos"):
        st.rerun()

    pedidos = obter_pedidos_adm(provider_token)

    if not pedidos:
        st.info("📭 Nenhum pedido encontrado para este prestador.")
        return

    # Organizar por timestamp
    pedidos.sort(key=lambda x: x.get("timestamp", 0))

    for p in pedidos:
        p_id = p.get("id")
        cliente = p.get("cliente", "Desconhecido")
        musica = p.get("musica", {})
        titulo_musica = musica.get("titulo", "Música desconhecida") if isinstance(musica, dict) else str(musica)
        estado = p.get("estado", "pendente")

        cor_estado = "#FFC107" if estado == "pendente" else "#4CAF50" if estado == "aprovado" else "#FF4B4B"

        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.markdown(f"👤 **Cliente:** {cliente}")
                st.markdown(f"🎵 **Música:** {titulo_musica}")
            with col2:
                st.markdown(f"Estado: <span style='color: {cor_estado}; font-weight: bold;'>{estado.upper()}</span>", unsafe_allow_html=True)
            with col3:
                if estado == "pendente":
                    if st.button("✅ Aprovar", key=f"aprov_{p_id}"):
                        if atualizar_estado_pedido(provider_token, p_id, "aprovado"):
                            st.success("Pedido aprovado!")
                            st.rerun()
                if estado in ["pendente", "aprovado"]:
                    if st.button("❌ Concluir/Remover", key=f"canc_{p_id}"):
                        if atualizar_estado_pedido(provider_token, p_id, "concluido"):
                            st.success("Pedido concluído!")
                            st.rerun()
            st.markdown("---")
