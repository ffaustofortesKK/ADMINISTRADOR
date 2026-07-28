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

def verificar_pedido_ativo_cliente(provider_token, cliente_nome):
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()
            for k, v in data.items():
                if v.get("cliente", "").strip().lower() == cliente_nome.strip().lower():
                    if v.get("estado") in ["pendente", "aprovado"]:
                        return True, v.get("estado")
    except Exception:
        pass
    return False, None

def obter_posicao_fila(provider_token, cliente_nome):
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

    # Validação tolerante do prestador
    nome_prestador = "FFKaraoke"
    try:
        df_prov = get_all_providers()
        if not df_prov.empty and 'token' in df_prov.columns:
            prestador = df_prov[df_prov['token'] == provider_token]
            if not prestador.empty:
                nome_prestador = prestador.iloc[0].get('name', 'FFKaraoke')
    except Exception:
        pass

    st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"## 🎤 FFKaraoke — {nome_prestador}")
    st.markdown("---")

    # Inicializar session states
    if 'cliente_nome_input' not in st.session_state:
        st.session_state.cliente_nome_input = ""
    if 'pesquisa_musica' not in st.session_state:
        st.session_state.pesquisa_musica = ""
    if 'musica_selecionada_confirmar' not in st.session_state:
        st.session_state.musica_selecionada_confirmar = None

    # Registo / Identificação do Cliente
    if not st.session_state.cliente_nome_input.strip():
        st.markdown("### Identificação do Cantor")
        nome_temp = st.text_input("Insira o seu Nome ou Alcunha:", placeholder="Ex: João da Silva")
        if st.button("Registar Nome"):
            if nome_temp.strip():
                st.session_state.cliente_nome_input = nome_temp.strip()
                st.rerun()
            else:
                st.warning("⚠️ Por favor, insira um nome válido.")
        return

    # Se já estiver registado, mostra o nome em ponto grande
    cliente_nome = st.session_state.cliente_nome_input
    st.markdown(f"<h1 style='color: #4CAF50; text-align: center; margin-bottom: 20px;'>Bem-vindo, {cliente_nome}! 👋</h1>", unsafe_allow_html=True)

    # Verificar se o cliente já tem pedido ativo na fila
    tem_ativo, estado_atual = verificar_pedido_ativo_cliente(provider_token, cliente_nome)
    
    if tem_ativo:
        posicao, _ = obter_posicao_fila(provider_token, cliente_nome)
        st.warning(f"🚫 **Aviso:** Não pode enviar outro pedido enquanto o seu pedido anterior não for cantado.")
        if posicao:
            st.info(f"📊 O seu pedido encontra-se atualmente na **posição {posicao}** da fila do prestador.")
        else:
            st.info("⏳ O seu pedido está registado na fila. Aguarde a sua vez.")
        
        if st.button("🔄 Atualizar Estado"):
            st.rerun()
        return
    else:
        # Mensagem informativa de liberação caso tenha acabado de cantar
        st.success("✅ Já pode enviar o seu próximo pedido!")

    st.markdown("---")
    st.markdown("### 🔍 Pesquisar Música")

    # Campo de pesquisa reativo
    pesquisa = st.text_input("Digite o nome da música ou artista:", value=st.session_state.pesquisa_musica, placeholder="Ex: Landrick...")
    st.session_state.pesquisa_musica = pesquisa

    catalogo = obter_catalogo_cloudinary()

    if not catalogo:
        st.warning("⚠️ O catálogo do Cloudinary está vazio ou indisponível no momento.")
        return

    if not pesquisa.strip():
        st.info("💡 Digite algo acima para ver as músicas semelhantes disponíveis.")
        return

    # Filtrar músicas parecidas
    musicas_filtradas = [
        m for m in catalogo 
        if pesquisa.lower() in m["titulo"].lower() or pesquisa.lower() in m["artista"].lower()
    ]

    if not musicas_filtradas:
        st.warning("Nenhuma música encontrada com esse termo.")
    else:
        st.write(f"Encontradas {len(musicas_filtradas)} músicas:")
        for musica in musicas_filtradas[:20]:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"🎵 **{musica['titulo']}**")
            with col2:
                safe_key = f"btn_cloud_{musica['id']}"
                if st.button("📤 Pedir", key=safe_key):
                    st.session_state.musica_selecionada_confirmar = musica

    # Confirmação de Envio ("Tem a certeza ou quer tocar?")
    if st.session_state.musica_selecionada_confirmar:
        musica_escolhida = st.session_state.musica_selecionada_confirmar
        st.markdown("---")
        st.markdown(f"### ❓ Confirmação de Pedido")
        st.info(f"Tem a certeza de que deseja encomendar e tocar a música: **{musica_escolhida['titulo']}**?")
        
        col_sim, col_nao = st.columns(2)
        with col_sim:
            if st.button("✅ Sim, Enviar Pedido", use_container_width=True):
                # Dupla verificação de segurança antes de enviar
                ativo_check, _ = verificar_pedido_ativo_cliente(provider_token, cliente_nome)
                if ativo_check:
                    st.error("Não é possível enviar: já existe um pedido ativo na fila.")
                else:
                    if enviar_pedido_firebase(provider_token, cliente_nome, musica_escolhida):
                        st.success(f"Pedido de '{musica_escolhida['titulo']}' enviado com sucesso!")
                        # Limpar campos de pesquisa após envio
                        st.session_state.pesquisa_musica = ""
                        st.session_state.musica_selecionada_confirmar = None
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Erro ao enviar o pedido para o DJ.")
        with col_nao:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state.musica_selecionada_confirmar = None
                st.rerun()
