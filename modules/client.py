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

    # Estilos CSS gerais, cores e animação do rodapé (agenda em marquee)
    st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .welcome-banner {
        background: linear-gradient(135deg, #1f4068, #162447);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        border: 2px solid #e43f5a;
        margin-bottom: 20px;
    }
    .marquee-container {
        overflow: hidden;
        white-space: nowrap;
        background: #111;
        border-top: 2px solid #e43f5a;
        border-bottom: 2px solid #e43f5a;
        padding: 10px 0;
        margin-top: 30px;
        color: #00ffcc;
        font-family: monospace;
        font-size: 16px;
    }
    .marquee-content {
        display: inline-block;
        animation: marquee 35s linear infinite;
    }
    @keyframes marquee {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    .promo-box {
        background-color: #1a1a2e;
        border: 1px solid #162447;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-top: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Gestão de Estados da Sessão do Cliente
    if 'cliente_nome' not in st.session_state:
        st.session_state.cliente_nome = ""
    if 'confirmar_musica' not in st.session_state:
        st.session_state.confirmar_musica = None
    if 'pesquisa_input' not in st.session_state:
        st.session_state.pesquisa_input = ""

    st.markdown("## 🎤 FFKaraoke — Registo de Pedidos")
    st.markdown("---")

    # Passo 1: Registo do Nome
    if not st.session_state.cliente_nome:
        with st.form("form_nome"):
            nome_temp = st.text_input("Insira o seu Nome ou Alcunha para começar:", placeholder="Ex: João da Silva")
            submitted = st.form_submit_button("Entrar no Karaoke 🚀")
            if submitted:
                if nome_temp.strip():
                    st.session_state.cliente_nome = nome_temp.strip()
                    st.rerun()
                else:
                    st.warning("⚠️ Por favor, insira um nome válido.")
        return

    # Se já estiver registado, mostra o banner de boas-vindas personalizado
    st.markdown(f"""
        <div class="welcome-banner">
            <h1 style="color: #ffffff; margin: 0; font-size: 28px;">🎉 Bem-vindo, {st.session_state.cliente_nome}!</h1>
            <p style="color: #e43f5a; font-size: 16px; margin-top: 5px;">Prepare a sua voz e escolha o seu sucesso!</p>
        </div>
    """, unsafe_allow_html=True)

    # Verificar se o cliente já tem algum pedido ativo (pendente ou aprovado) na fila do prestador
    pedidos_atuais = obter_pedidos_firebase(provider_token)
    pedido_ativo_cliente = next(
        (p for p in pedidos_atuais if p.get("cliente", "").lower() == st.session_state.cliente_nome.lower() and p.get("estado") in ["pendente", "aprovado"]), 
        None
    )

    if pedido_ativo_cliente:
        estado_atual = pedido_ativo_cliente.get("estado")
        musica_nome = pedido_ativo_cliente.get("musica", {}).get("titulo", "Música") if isinstance(pedido_ativo_cliente.get("musica"), dict) else str(pedido_ativo_cliente.get("musica"))
        
        # Calcular posição na fila se estiver pendente
        if estado_atual == "pendente":
            pendentes_ordenados = [p for p in pedidos_atuais if p.get("estado") == "pendente"]
            pendentes_ordenados.sort(key=lambda x: x.get("timestamp", 0))
            posicao = next((i for i, p in enumerate(pendentes_ordenados, start=1) if p.get("id") == pedido_ativo_cliente.get("id")), 1)
            st.warning(f"⏳ **Atenção:** Já tem um pedido pendente na fila (**{musica_nome}**). Encontra-se na **posição {posicao}** da playlist. Só poderá enviar um novo pedido assim que a sua música passar na tela e terminar!")
        else:
            st.info(f"🎵 A sua música **'{musica_nome}'** está a tocar atualmente ou foi aprovada na tela! Assim que terminar, já poderá enviar um novo pedido.")

        if st.button("🔄 Alterar Nome / Sair da Sessão"):
            st.session_state.cliente_nome = ""
            st.session_state.confirmar_musica = None
            st.rerun()
            
    else:
        # Se não tiver pedidos ativos, permite pesquisar e solicitar músicas livremente
        st.markdown("### 🔍 Pesquisar Música")
        
        def limpar_pesquisa():
            st.session_state.pesquisa_input = ""

        pesquisa = st.text_input("Digite o título ou artista:", value=st.session_state.pesquisa_input, key="pesquisa_input", placeholder="Ex: Landrick, Kizomba...")

        catalogo = obter_catalogo_cloudinary()

        if pesquisa:
            musicas_filtradas = [
                m for m in catalogo 
                if pesquisa.lower() in m["titulo"].lower() or pesquisa.lower() in m["artista"].lower()
            ]

            if musicas_filtradas:
                st.write(result_msg := f"Encontradas {len(musicas_filtradas)} músicas semelhantes:")
                for musica in musicas_filtradas[:15]:
                    col_info, col_btn = st.columns([4, 1])
                    with col_info:
                        st.markdown(f"🎵 **{musica['titulo']}**")
                    with col_btn:
                        if st.button("📤 Pedir", key=f"sel_{musica['id']}"):
                            st.session_state.confirmar_musica = musica
                            st.rerun()
            else:
                st.warning("Nenhuma música encontrada com esse termo.")
        else:
            st.info("💡 Digite um termo na caixa acima para ver a lista de músicas disponíveis.")

        # Janela de Confirmação do Pedido ("Tem a certeza ou quer tocar?")
        if st.session_state.confirmar_musica:
            m_escolhida = st.session_state.confirmar_musica
            st.markdown("---")
            st.markdown(f"### 🤔 Confirmação de Pedido")
            st.markdown(f"Vai solicitar a música: **{m_escolhida['titulo']}**")
            
            c_sim, c_nao = st.columns(2)
            with c_sim:
                if st.button("✅ Tenho a certeza, Enviar Pedido!"):
                    if enviar_pedido_firebase(provider_token, st.session_state.cliente_nome, m_escolhida):
                        st.success("Pedido enviado com sucesso para o prestador!")
                        st.session_state.confirmar_musica = None
                        st.session_state.pesquisa_input = ""  # Limpa campos de pesquisa
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Erro ao enviar o pedido. Tente novamente.")
            with c_nao:
                if st.button("❌ Quero escolher outra"):
                    st.session_state.confirmar_musica = None
                    st.rerun()

    # Secção Promocional e Redes Sociais
    st.markdown("---")
    st.markdown("""
        <div class="promo-box">
            <h3 style="color: #00ffcc; margin-bottom: 10px;">Quer saber mais do serviço de Karaoke do Grupo FF, clica abaixo!</h3>
            <p style="font-size: 16px; margin: 5px 0;">📸 Instagram: <a href="https://instagram.com/ff.karaoke" target="_blank" style="color: #e43f5a; text-decoration: none;"><b>@ff.karaoke</b></a></p>
            <p style="font-size: 16px; margin: 5px 0;">📞 Contacto para Eventos Privados: <b>955099159</b></p>
            <p style="font-size: 16px; margin: 5px 0;">💬 WhatsApp: <b>955099159</b></p>
        </div>
    """, unsafe_allow_html=True)

    # Rodapé Animado (Marquee) com a Agenda Completa do Grupo FF Karaoke
    agenda_texto = (
        "🎤✨ AGENDA DO GRUPO FF KARAOKE ✨🎤  |  "
        "🗓️ Nossa Agenda da Semana  |  "
        "🎵 QUARTA-FEIRA ➔ 📍 Restaurante Cave da Samba | 🎤 Apresentação: CEFAS DAVID | 🕖 Hora: 19H  |  "
        "🎵 SEXTA-FEIRA ➔ 📍 Restaurante O Kubico | 🎤 Apresentação: CEFAS DAVID | 📌 Local: Maculusso | 🕖 Hora: 19H  |  "
        "🎵 SEXTA-FEIRA ➔ 📍 Restaurante Universidade | 🎤 Apresentação: EDNA ANJINHA | 📌 Local: Nova Vida – Rua 40  |  "
        "🎵 DOMINGO ➔ 📍 Restaurante TASCA | 🎤 Apresentação: EDNA ANJINHA | 📌 Local: Bairro Prenda – Frente ao Posto 15 | 🕖 Hora: 19H  |  "
        "🎶 LINHA DA FRENTE: Venha cantar, dançar e se divertir conosco! Entrada Gratuita! 🎶"
    )

    st.markdown(f"""
        <div class="marquee-container">
            <div class="marquee-content">{agenda_texto}</div>
        </div>
    """, unsafe_allow_html=True)
