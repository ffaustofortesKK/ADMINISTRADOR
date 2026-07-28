import streamlit as st
import requests
import time
import cloudinary
import cloudinary.api
from utils.db_manager import get_all_providers

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

# Configuração do Cloudinary
cloudinary.config(
    cloud_name="ejil7wKYY15xHjDcRVfbk6Ow",
    api_key="766164269958181",
    api_secret="oWTTGfF8KRtd4ojFiS",
    secure=True
)

st.set_page_config(page_title="FF Karaoke Manager", layout="wide")

def obter_pedidos(provider_token):
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200 and response.json():
            data = response.json()
            return [{"id": k, **v} for k, v in data.items()]
    except Exception:
        pass
    return []

def atualizar_estado_pedido(provider_token, pedido_id, novo_estado):
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}/estado.json"
        requests.put(url, json=novo_estado, timeout=5)
    except Exception:
        pass

def apagar_pedido(provider_token, pedido_id):
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}.json"
        requests.delete(url, timeout=5)
    except Exception:
        pass

def show_screen_view(provider_token):
    """Ecrã de Projecção / Tela para mostrar o vídeo a tocar aos clientes no estabelecimento"""
    st.markdown("""
        <style>
        .stApp { background-color: #000000; color: white; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🖥️ FF Karaoke — Tela de Projecção")
    
    pedidos = obter_pedidos(provider_token)
    pedidos_aprovados = [p for p in pedidos if p.get("estado") == "aprovado"]

    if not pedidos_aprovados:
        st.info("Aguardando o próximo cantor...")
    else:
        # Pega o primeiro aprovado para reprodução na tela
        ator_atual = pedidos_aprovados[0]
        musica = ator_atual.get("musica", {})
        
        titulo = musica.get("titulo", "Música") if isinstance(musica, dict) else str(musica)
        artista = musica.get("artista", "FFKaraoke") if isinstance(musica, dict) else ""
        url_video = musica.get("url", "") if isinstance(musica, dict) else ""
        cantor = ator_atual.get("cliente", "Convidado")

        st.markdown(f"## 🎤 A Cantar Agora: **{cantor}**")
        st.markdown(f"### 🎵 {titulo} — *{artista}*")

        if url_video:
            st.video(url_video, autoplay=True)
        else:
            st.warning("⚠️ Este pedido é personalizado (não possui vídeo automático na nuvem). Aguarde orientações do DJ.")

    # Atualiza automaticamente a tela a cada 4 segundos
    time.sleep(4)
    st.rerun()

def main():
    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider", None)
    modo_tela = query_params.get("tela") or query_params.get("screen", None)

    if not provider_token:
        st.warning("⚠️ Selecione ou aceda através de um link de prestador válido.")
        df_prov = get_all_providers()
        if not df_prov.empty:
            names = df_prov['name'].tolist()
            escolha = st.selectbox("Ou escolha um prestador da base de dados:", names)
            if escolha:
                provider_token = df_prov[df_prov['name'] == escolha]['token'].values[0]
        else:
            st.error("Nenhum prestador encontrado na base de dados.")
            return

    # Validar prestador
    df_prov = get_all_providers()
    prestador = df_prov[df_prov['token'] == provider_token]
    if prestador.empty:
        st.error("❌ Prestador não encontrado.")
        return

    row_prov = prestador.iloc[0]

    # Se o parâmetro 'tela' ou 'screen' estiver presente no link, abre a Tela de Projecção e não o Painel de Gestão/Cliente
    if modo_tela:
        show_screen_view(provider_token)
        return

    # Painel Normal de Gestão do DJ
    st.title(f"🎤 FF Karaoke — Painel de Gestão ({row_prov['name']})")
    st.sidebar.markdown(f"### Prestador: **{row_prov['name']}**")
    st.sidebar.markdown("---")

    pedidos = obter_pedidos(provider_token)
    pedidos_pendentes = [p for p in pedidos if p.get("estado") == "pendente"]
    pedidos_aprovados = [p for p in pedidos if p.get("estado") == "aprovado"]

    st.subheader("📋 Fila de Pedidos")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Pendentes")
        if not pedidos_pendentes:
            st.info("Nenhum pedido pendente.")
        else:
            for p in pedidos_pendentes:
                musica = p.get("musica", {})
                titulo = musica.get("titulo", str(musica)) if isinstance(musica, dict) else str(musica)
                st.write(f"🎵 **{titulo}** — *{p.get('cliente')}*")
                if st.button("Aprovar", key=f"aprov_{p['id']}"):
                    atualizar_estado_pedido(provider_token, p['id'], "aprovado")
                    st.rerun()

    with col2:
        st.markdown("### A Cantar / Aprovados")
        if not pedidos_aprovados:
            st.info("Nenhum cantor em atuação.")
        else:
            for p in pedidos_aprovados:
                musica = p.get("musica", {})
                titulo = musica.get("titulo", str(musica)) if isinstance(musica, dict) else str(musica)
                st.write(f"🎤 **{titulo}** — *{p.get('cliente')}*")
                if st.button("Concluir / Apagar", key=f"del_{p['id']}"):
                    apagar_pedido(provider_token, p['id'])
                    st.rerun()

if __name__ == "__main__":
    main()
