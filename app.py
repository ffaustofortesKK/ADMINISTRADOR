import streamlit as st
import requests
import time
import cloudinary
import cloudinary.api
from utils.db_manager import get_all_providers

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

# Configuração do Cloudinary para corresponder ao resto do sistema
cloudinary.config(
    cloud_name="ejil7wKYY15xHjDcRVfbk6Ow",
    api_key="766164269958181",
    api_secret="oWTTGfF8KRtd4ojFiS",
    secure=True
)

@st.cache_data(ttl=30)
def obter_catalogo_cloudinary():
    catalogo = []
    try:
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
    return catalogo

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

    if 'registado' not in st.session_state: st.session_state.registado = False
    if 'musica_pendente_confirmacao' not in st.session_state: st.session_state.musica_pendente_confirmacao = None
    if 'aviso_personalizado_ativo' not in st.session_state: st.session_state.aviso_personalizado_ativo = False
    if 'texto_pedido_anterior' not in st.session_state: st.session_state.texto_pedido_anterior = ""

    # URLs alinhadas exatamente com a estrutura do app.py
    URL_PEDIDOS = f"{FIREBASE_URL}/pedidos/{provider_token}.json"

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
            response_pedidos = requests.get(f"{URL_PEDIDOS}?nocache={time.time()}", timeout=5)
            pedidos_data = response_pedidos.json() if response_pedidos.status_code == 200 else {}
        except: 
            pedidos_data = {}

        # Converter dados do Firebase para lista manipulável idêntica ao app.py
        pedidos = [{"id": k, **v} for k, v in pedidos_data.items()] if pedidos_data else []
        pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
        pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))

        meu_nome = str(st.session_state.nome).strip().lower()
        
        # Verificar posição do cliente na fila
        meu_pedido_na_fila = next((p for p in pedidos_ativos if str(p.get('cliente', '')).strip().lower() == meu_nome), None)
        posicao = pedidos_ativos.index(meu_pedido_na_fila) if meu_pedido_na_fila else -1

        tem_pedido_na_fila = posicao != -1
        esta_a_cantar = meu_pedido_na_fila and meu_pedido_na_fila.get("estado") == "aprovado"

        if esta_a_cantar:
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
        catalogo = obter_catalogo_cloudinary()
        
        resultados = [
            m for m in catalogo 
            if termo.lower() in m["titulo"].lower() or termo.lower() in m["artista"].lower()
        ] if termo else []

        if termo:
            if resultados:
                # Mostrar selecção limpa por título e artista
                opcoes_map = {f"{m['titulo']} — {m['artista']}": m for m in resultados}
                escolha_txt = st.selectbox("Escolha a música:", list(opcoes_map.keys()), key="select_busca_musica")
                musica_sel = opcoes_map[escolha_txt]
                
                if st.button("➕ Enviar esta música para o DJ", use_container_width=True):
                    st.session_state.musica_pendente_confirmacao = musica_sel
                    st.rerun()
            else:
                st.warning("Nenhuma música encontrada com esse termo.")

        # Bloco de Confirmação da Música Escolhida
        if st.session_state.musica_pendente_confirmacao:
            m_obj = st.session_state.musica_pendente_confirmacao
            st.warning(f"⚠️ Tens a certeza que queres escolher a música: **{m_obj['titulo']}**?")
            col_sim, col_nao = st.columns(2)
            with col_sim:
                if st.button("Sim, enviar!", use_container_width=True):
                    if tem_pedido_na_fila or esta_a_cantar:
                        st.error("⛔ Só podes enviar outra música assim que a tua atuação atual terminar!")
                    else:
                        novo_pedido = {
                            "cliente": st.session_state.nome,
                            "musica": m_obj,
                            "estado": "pendente",
                            "timestamp": int(time.time() * 1000)
                        }
                        requests.post(URL_PEDIDOS, json=novo_pedido, timeout=5)
                        st.session_state.musica_pendente_confirmacao = None
                        st.rerun()
            with col_nao:
                if st.button("Não, quero escolher outra", use_container_width=True):
                    st.session_state.musica_pendente_confirmacao = None
                    st.rerun()

        st.divider()
        st.subheader("📝 Pedido Personalizado")
        
        if st.session_state.aviso_personalizado_ativo:
            st.info("ℹ️ Seu pedido personalizado foi enviado com sucesso!")

        pedido_extra = st.text_input("Não encontrou? Escreva o seu pedido:", key="input_pedido_extra")
        
        if pedido_extra != st.session_state.texto_pedido_anterior:
            st.session_state.aviso_personalizado_ativo = False
            st.session_state.texto_pedido_anterior = pedido_extra

        if st.button("🚀 Enviar Pedido Personalizado", use_container_width=True):
            if tem_pedido_na_fila or esta_a_cantar:
                st.error("⛔ Só podes enviar outra música assim que a tua atuação atual terminar!")
            elif not pedido_extra:
                st.warning("Escreva um pedido personalizado antes de enviar.")
            else:
                musica_custom_obj = {
                    "titulo": f"PEDIDO: {pedido_extra}",
                    "artista": "Personalizado",
                    "url": ""
                }
                novo_pedido = {
                    "cliente": st.session_state.nome,
                    "musica": musica_custom_obj,
                    "estado": "pendente",
                    "timestamp": int(time.time() * 1000)
                }
                requests.post(URL_PEDIDOS, json=novo_pedido, timeout=5)
                st.session_state.aviso_personalizado_ativo = True
                st.rerun()

        st.divider()
        if st.button("Sair"): 
            st.session_state.registado = False
            st.session_state.musica_pendente_confirmacao = None
            st.session_state.aviso_personalizado_ativo = False
            st.rerun()
        
        time.sleep(3)
        st.rerun()
