import streamlit as st
import requests
import time

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

def obter_pedidos_cliente(provider_token):
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}.json?_t={time.time()}"
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

# Usamos um fragmento com atualização automática a cada 4 segundos para o telemóvel do cliente acompanhar a fila em tempo real
@st.fragment(run_every=4)
def relogio_fila_cliente(provider_token, cliente_nome):
    st.markdown("""
    <style>
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .spinning-mic {
        animation: spin 3s linear infinite;
        display: inline-block;
        font-size: 100px;
    }
    </style>
    """, unsafe_allow_html=True)

    pedidos = obter_pedidos_cliente(provider_token)
    
    # Filtrar apenas pedidos ativos (pendentes ou aprovados/a tocar)
    pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
    pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))

    # Verificar se o cliente tem pedido ativo
    meu_pedido = None
    minha_posicao = None
    tocando_agora = None

    for idx, p in enumerate(pedidos_ativos, start=1):
        if p.get("estado") == "aprovado" and not tocando_agora:
            tocando_agora = p
        if p.get("cliente", "").lower() == cliente_nome.lower():
            if not meu_pedido:
                meu_pedido = p
                minha_posicao = idx

    if not meu_pedido:
        st.info("ℹ️ Não tem nenhum pedido ativo na fila neste momento. Escolha uma música abaixo para cantar!")
        return

    # Calcular quantas músicas estão estritamente à frente na fila de espera pendente
    # (Exclui o que está a tocar agora da contagem de músicas à frente)
    pendentes_frente = [p for p in pedidos_ativos if p.get("estado") == "pendente" and p.get("timestamp", 0) < meu_pedido.get("timestamp", 0)]
    musicas_a_frente = len(pendentes_frente)

    if meu_pedido.get("estado") == "aprovado":
        # Chegou a vez!
        st.markdown("""
            <div style="text-align: center; padding: 30px; background: rgba(76, 175, 80, 0.15); border: 3px solid #4CAF50; border-radius: 15px; margin: 15px 0;">
                <div class="spinning-mic">🎤</div>
                <h1 style="color: #4CAF50; font-size: 32px; margin-top: 15px;">Chegou a sua vez de cantar !!!</h1>
                <p style="color: #fff; font-size: 18px; margin-top: 10px;">Dirija-se ao palco, o seu microfone está pronto!</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        # Ainda na fila, exibir alerta dinâmico de quantas músicas faltam
        titulo_musica = meu_pedido.get("musica", {}).get("titulo", "A sua música") if isinstance(meu_pedido.get("musica"), dict) else str(meu_pedido.get("musica"))
        
        if musicas_a_frente == 0:
            aviso_texto = "É o próximo a cantar! Prepare-se!"
            cor_alerta = "#4CAF50"
        elif musicas_a_frente == 1:
            aviso_texto = "Tem mais 1 música à sua frente."
            cor_alerta = "#FFC107"
        elif musicas_a_frente == 2:
            aviso_texto = "Tem mais 2 músicas à sua frente."
            cor_alerta = "#FF9800"
        else:
            aviso_texto = f"Tem mais {musicas_a_frente} músicas à sua frente na fila."
            cor_alerta = "#FF5722"

        st.markdown(f"""
            <div style="text-align: center; padding: 25px; background: #161a23; border: 2px solid {cor_alerta}; border-radius: 15px; margin: 15px 0;">
                <div class="spinning-mic">🎤</div>
                <h3 style="color: #FFC107; margin-top: 15px; font-size: 22px;">Pedido: {titulo_musica}</h3>
                <h2 style="color: {cor_alerta}; font-size: 26px; margin-top: 10px; font-weight: bold;">{aviso_texto}</h2>
                <p style="color: #aaa; font-size: 14px; margin-top: 8px;">Acompanhe o painel no telemóvel. O estado atualiza automaticamente.</p>
            </div>
        """, unsafe_allow_html=True)

def show_client_page():
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
    </style>
    """, unsafe_allow_html=True)

    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider", "1")

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

    # Registo inicial do nome do cliente
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
    st.markdown(f"<h1 style='color: #4CAF50; font-size: 26px; margin-bottom: 0;'>Benvindo, {cliente_nome}</h1>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top: 10px; margin-bottom: 15px;'>", unsafe_allow_html=True)

    # Executar o componente dinâmico de contagem regressiva da fila
    relogio_fila_cliente(provider_token, cliente_nome)

    # Se selecionou uma música, exibe a confirmação para envio
    if st.session_state.musica_selecionada:
        musica_atual = st.session_state.musica_selecionada
        titulo_m = musica_atual.get('titulo', 'Música')
        st.markdown(f"""
            <div style="background: #161a23; padding: 15px; border-radius: 12px; border: 2px solid #4CAF50; text-align: center; margin: 15px 0;">
                <h3 style="color: #4CAF50; margin-bottom: 8px; font-size: 18px;">Confirmação de Pedido</h3>
                <p style="font-size: 16px; font-weight: bold; margin-bottom: 10px;">Quer tocar <b>{titulo_m}</b>?</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("✅ Sim, Enviar", use_container_width=True, key="btn_sim_enviar"):
                pedidos_atuais = obter_pedidos_cliente(provider_token)
                tem_ativo = any(p.get("cliente", "").lower() == cliente_nome.lower() and p.get("estado") in ["pendente", "aprovado"] for p in pedidos_atuais)
                
                if tem_ativo:
                    st.error("❌ Já tem um pedido ativo na fila. Aguarde que seja concluído para pedir outra música.")
                else:
                    sucesso = enviar_pedido_firebase(provider_token, cliente_nome, musica_atual)
                    if sucesso:
                        st.success(f"Pedido enviado com sucesso!")
                        st.session_state.pesquisa_input = ""
                        st.session_state.musica_selecionada = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Erro ao enviar o pedido.")
        with col_c2:
            if st.button("❌ Cancelar", use_container_width=True, key="btn_nao_cancelar"):
                st.session_state.musica_selecionada = None
                st.rerun()
        st.markdown("---")

    # Caixa de pesquisa de músicas
    st.markdown("### 🔍 Pesquisar Música no Catálogo")
    pesquisa = st.text_input("Digite o nome da música ou artista:", value=st.session_state.pesquisa_input, placeholder="Ex: Landrick, Nani...")
    st.session_state.pesquisa_input = pesquisa

    # Catálogo simulado/carregado
    from modules.admin import obter_catalogo_cloudinary if 'obter_catalogo_cloudinary' in globals() else lambda: []
    # Fallback básico caso a função de catálogo esteja noutro ficheiro
    try:
        from app import obter_catalogo_cloudinary
        catalogo = obter_catalogo_cloudinary()
    except Exception:
        catalogo = []

    if pesquisa and catalogo:
        musicas_filtradas = [
            m for m in catalogo 
            if pesquisa.lower() in m["titulo"].lower() or pesquisa.lower() in m["artista"].lower()
        ]

        if musicas_filtradas:
            st.write(f"Encontradas {len(musicas_filtradas)} músicas:")
            container_lista = st.container(height=280)
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
