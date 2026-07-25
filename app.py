import streamlit as st
import requests
import time
from utils.db_manager import get_all_providers

def show_client_portal(provider_token):
    # Validar se o token do prestador existe e está ativo na base de dados local
    df_prov = get_all_providers()
    prestador = df_prov[df_prov['token'] == provider_token]
    
    if prestador.empty:
        st.error("❌ Link de prestador inválido ou inexistente.")
        return

    row_prov = prestador.iloc[0]
    if row_prov.get('approved', 0) != 1:
        st.warning("⏳ Este painel de prestador encontra-se temporariamente inativo ou expirado.")
        return

    # Usar o token como identificador único (slug) para as chaves do Firebase
    prestador_slug = provider_token

    if 'registado' not in st.session_state: st.session_state.registado = False
    if 'musica_pendente_confirmacao' not in st.session_state: st.session_state.musica_pendente_confirmacao = None
    if 'aviso_personalizado_ativo' not in st.session_state: st.session_state.aviso_personalizado_ativo = False
    if 'texto_pedido_anterior' not in st.session_state: st.session_state.texto_pedido_anterior = ""

    URL_STATUS = f"https://grupoffkaraoke-default-rtdb.firebaseio.com/status_{prestador_slug}.json"
    URL_PEDIDOS = f"https://grupoffkaraoke-default-rtdb.firebaseio.com/pedidos_{prestador_slug}.json"
    URL_CATALOGO = "https://grupoffkaraoke-default-rtdb.firebaseio.com/catalogo.json"

    @st.cache_data(ttl=300)
    def obter_catalogo():
        try:
            res = requests.get(URL_CATALOGO).json()
            return list(res.values()) if isinstance(res, dict) else (res or [])
        except: return []

    if not st.session_state.registado:
        st.title(f"🎤 FF Karaoke - {row_prov['name']}")
        nome = st.text_input("Como quer ser chamado?")
        if st.button("Entrar"):
            if nome: 
                st.session_state.nome = nome
                st.session_state.registado = True
                st.rerun()
    else:
        try:
            status = requests.get(f"{URL_STATUS}?nocache={time.time()}", timeout=2).json() or {}
            pedidos_json = requests.get(f"{URL_PEDIDOS}?nocache={time.time()}", timeout=2).json() or {}
        except: 
            status = {}
            pedidos_json = {}

        nome_firebase = str(status.get("cantor", "")).strip().lower()
        meu_nome = str(st.session_state.nome).strip().lower()
        
        fila = list(pedidos_json.items()) if pedidos_json else []
        posicao = next((i for i, (p_id, p) in enumerate(fila) if str(p.get('cantor')).strip().lower() == meu_nome), -1)

        tem_pedido_na_fila = posicao != -1
        esta_a_cantar_ou_chamado = (nome_firebase == meu_nome)
        comando_atual = status.get("comando")

        if esta_a_cantar_ou_chamado:
            if comando_atual == "aguardando_play":
                st.success("🎉 É a tua vez! Prepara-te, o vídeo vai começar a tocar na tela...")
            elif comando_atual == "play":
                st.info("🎵 A tua música está a passar na tela!")
        elif tem_pedido_na_fila:
            st.warning("⚠️ O seu pedido foi enviado. Aguarde a sua vez.")
            if posicao == 0:
                st.info("📢 Estás quase lá, aguarde o sinal para começar.")
            else:
                st.write(f"🔢 Existem **{posicao}** músicas à sua frente.")
        else:
            st.success("✅ Já podes enviar a tua próxima música!")

        st.divider()
        st.subheader("🔍 Pesquisa de Música")
        
        termo = st.text_input("Pesquisar música no catálogo:")
        resultados = [m for m in obter_catalogo() if termo.lower() in str(m).lower()] if termo else []
        
        if termo and resultados:
            musica_sel = st.selectbox("Escolha a música:", resultados, key="select_busca_musica")
            
            if st.button("➕ Enviar esta música para o DJ", use_container_width=True):
                st.session_state.musica_pendente_confirmacao = musica_sel
                st.rerun()

        # Bloco de Confirmação da Música Escolhida
        if st.session_state.musica_pendente_confirmacao:
            st.warning(f"⚠️ Tens a certeza que queres escolher a música: **{st.session_state.musica_pendente_confirmacao}**?")
            col_sim, col_nao = st.columns(2)
            with col_sim:
                if st.button("Sim, enviar!", use_container_width=True):
                    if tem_pedido_na_fila or esta_a_cantar_ou_chamado:
                        st.error("⛔ Só podes enviar outra música assim que a tua atuação atual terminar!")
                    else:
                        requests.post(URL_PEDIDOS, json={"cantor": st.session_state.nome, "musica": st.session_state.musica_pendente_confirmacao})
                        st.session_state.musica_pendente_confirmacao = None
                        st.rerun()
            with col_nao:
                if st.button("Não, quero escolher outra", use_container_width=True):
                    st.session_state.musica_pendente_confirmacao = None
                    st.rerun()

        st.divider()
        st.subheader("📝 Pedido Personalizado")
        
        if st.session_state.aviso_personalizado_ativo:
            st.info("ℹ️ Seu pedido foi enviado com sucesso, mas nem todas as músicas estão disponíveis em karaoke.")

        pedido_extra = st.text_input("Não encontrou? Escreva o seu pedido:", key="input_pedido_extra")
        
        if pedido_extra != st.session_state.texto_pedido_anterior:
            st.session_state.aviso_personalizado_ativo = False
            st.session_state.texto_pedido_anterior = pedido_extra

        if st.button("🚀 Enviar Pedido Personalizado", use_container_width=True):
            if tem_pedido_na_fila or esta_a_cantar_ou_chamado:
                st.error("⛔ Só podes enviar outra música assim que a tua atuação atual terminar!")
            elif not pedido_extra:
                st.warning("Escreva um pedido personalizado antes de enviar.")
            else:
                requests.post(URL_PEDIDOS, json={"cantor": st.session_state.nome, "musica": f"PEDIDO: {pedido_extra}"})
                st.session_state.aviso_personalizado_ativo = True
                st.rerun()

        st.divider()
        if st.button("Sair"): 
            st.session_state.registado = False
            st.session_state.musica_pendente_confirmacao = None
            st.session_state.aviso_personalizado_ativo = False
            st.rerun()
        
        time.sleep(1.5)
        st.rerun()
