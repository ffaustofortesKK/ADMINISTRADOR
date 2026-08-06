import streamlit as st
import requests
import time

def show_provider_panel_custom(provider_token, FIREBASE_URL):
    st.markdown("""
        <style>
            .provider-header {
                font-family: monospace;
                font-weight: bold;
                color: #FFC107;
                text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 class='provider-header'>🎛️ Painel de Controlo do Prestador2</h2>", unsafe_allow_html=True)
    st.write(f"Token do Estabelecimento: `{provider_token}`")

    # Obter dados do Firebase para o prestador
    url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json?_t={time.time()}"
    try:
        response = requests.get(url_firebase, timeout=10)
        pedidos_ativos = []
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
    except Exception as e:
        st.error(f"Erro ao carregar dados do Firebase: {e}")
        pedidos_ativos = []

    tab1, tab2, tab3 = st.tabs(["🎵 Fila de Pedidos", "📺 Vídeo de Fundo", "⚙️ Configurações"])

    with tab1:
        st.subheader("Gerenciamento da Fila de Espera")
        if not pedidos_ativos:
            st.info("Não existem pedidos pendentes ou em reprodução no momento.")
        else:
            for idx, p in enumerate(pedidos_ativos):
                p_id = p.get("id")
                cliente = p.get("cliente", "Convidado")
                musica = p.get("musica", {})
                titulo = musica.get("titulo", musica.get("nome", "Karaoke")) if isinstance(musica, dict) else str(musica)
                estado = p.get("estado")

                cols = st.columns([3, 2, 1])
                with cols[0]:
                    st.markdown(f"**{idx+1}. Cliente:** {cliente} <br>🎵 *{titulo}*", unsafe_allow_html=True)
                with cols[1]:
                    st.markdown(f"Estado: `{estado}`")
                with cols[2]:
                    if estado == "pendente":
                        if st.button("Aprovar", key=f"apr_{p_id}"):
                            _atualizar_estado_pedido(provider_token, p_id, "aprovado", FIREBASE_URL)
                            st.rerun()
                    elif estado == "aprovado":
                        if st.button("Terminar", key=f"ter_{p_id}"):
                            _atualizar_estado_pedido(provider_token, p_id, "terminado", FIREBASE_URL)
                            st.rerun()

    with tab2:
        st.subheader("Seleção de Vídeo de Fundo (Descanso de Tela)")
        st.write("Escolha um clipe para ser reproduzido automaticamente na TV quando a fila de espera estiver vazia.")
        
        url_atual = _obter_video_fundo(provider_token, FIREBASE_URL)
        nova_url_fundo = st.text_input("URL do Vídeo de Fundo (MP4/Cloudinary):", value=url_atual or "")
        
        if st.button("Guardar Vídeo de Fundo"):
            _salvar_video_fundo(provider_token, nova_url_fundo, FIREBASE_URL)
            st.success("Vídeo de fundo atualizado com sucesso!")
            st.rerun()

    with tab3:
        st.subheader("Informações e Utilitários")
        st.write("Utilize este painel para monitorizar a atividade em tempo real do seu espaço no **FF Karaoke Cloud**.")
        if st.button("🔄 Atualizar Painel"):
            st.rerun()


def _atualizar_estado_pedido(provider_token, pedido_id, novo_estado, FIREBASE_URL):
    url = f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}/estado.json"
    try:
        requests.put(url, json=novo_estado, timeout=5)
    except Exception as e:
        st.error(f"Erro ao atualizar estado: {e}")


def _obter_video_fundo(provider_token, FIREBASE_URL):
    url = f"{FIREBASE_URL}/configuracoes/{provider_token}/video_fundo.json"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return ""


def _salvar_video_fundo(provider_token, url_video, FIREBASE_URL):
    url = f"{FIREBASE_URL}/configuracoes/{provider_token}/video_fundo.json"
    try:
        requests.put(url, json=url_video, timeout=5)
    except Exception as e:
        st.error(f"Erro ao salvar vídeo de fundo: {e}")
