import streamlit as st
import pandas as pd
import requests
import datetime
import qrcode
from io import BytesIO

def show_provider_panel_custom(token):
    """Renderiza o painel de controlo completo e personalizado do prestador."""
    st.markdown("""
        <style>
        .stApp {
            background-color: #000000 !important;
            color: #ffffff !important;
        }
        .block-container {
            background-color: #000000 !important;
            border: 4px solid #FFC107 !important;
            border-radius: 12px;
            padding: 2rem !important;
        }
        h1, h2, h3, h4, h5, h6, p, span, label, div {
            color: #ffffff !important;
            font-weight: bold !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🎛️ Painel do Prestador - FFKaraoke")
    
    # Navegação interna do prestador por abas
    aba_painel, aba_fila, aba_musicas, aba_config = st.tabs([
        "📺 Ecrã / TV", "📋 Gestão da Fila", "🎵 Repertório", "⚙️ Configurações"
    ])

    with aba_painel:
        st.subheader("Controlo do Ecrã de TV (Clientes)")
        st.markdown(f"**Link de Acesso para a TV do Estabelecimento:**")
        
        link_tv = f"/?page=client_screen&prestador={token}"
        st.info(link_tv)
        
        link_pedido_cliente = f"/?page=client_register&prestador={token}"
        st.markdown(f"**Link para os Clientes Pedirem Músicas:** `{link_pedido_cliente}`")
        
        try:
            img = qrcode.make(link_pedido_cliente)
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), caption="QR Code para Pedidos dos Clientes", width=200)
        except Exception:
            pass

    with aba_fila:
        st.subheader("Fila de Espera Ativa")
        st.write("Aqui pode gerir, avançar ou remover os pedidos dos cantores na fila.")
        try:
            res = requests.get(f"https://ffkaraoke-default-rtdb.firebaseio.com/pedidos/{token}.json", timeout=10)
            if res.status_code == 200 and res.json():
                pedidos = res.json()
                if isinstance(pedidos, dict):
                    for p_id, p_val in pedidos.items():
                        if isinstance(p_val, dict) and p_val.get("status") == "ativo":
                            col1, col2, col3 = st.columns([3, 2, 1])
                            with col1:
                                st.markdown(f"**Cliente:** {p_val.get('cliente')} | **Música:** {p_val.get('musica')}")
                            with col2:
                                st.markdown(f"Estado: `{p_val.get('status')}`")
                            with col3:
                                if st.button("Concluir", key=f"concluir_{p_id}"):
                                    p_val["status"] = "concluido"
                                    requests.put(f"https://ffkaraoke-default-rtdb.firebaseio.com/pedidos/{token}/{p_id}.json", json=p_val)
                                    st.success("Atualizado!")
                                    st.rerun()
                else:
                    st.info("Nenhum pedido ativo no momento.")
            else:
                st.info("A fila de espera está vazia.")
        except Exception as e:
            st.warning(f"Erro ao carregar fila: {e}")

    with aba_musicas:
        st.subheader("Catálogo de Músicas / Vídeos Disponíveis")
        st.write("Selecione os vídeos de fundo ou o catálogo de karaoke para exibição.")
        url_clipe = st.text_input("URL do Vídeo Clipe Atual para a TV (MP4 / YouTube / Stream)")
        if st.button("💾 Atualizar Vídeo na TV"):
            dados_extras = {"url_clipe_fundo": url_clipe}
            requests.patch(f"https://ffkaraoke-default-rtdb.firebaseio.com/config_prestadores/{token}.json", json=dados_extras)
            st.success("Vídeo de fundo atualizado com sucesso no ecrã da TV!")

    with aba_config:
        st.subheader("Definições da Conta e Dados do Estabelecimento")
        with st.form("form_config_prestador"):
            nome_espaco = st.text_input("Nome do Estabelecimento / Espaço")
            responsavel = st.text_input("Nome do Responsável")
            contacto = st.text_input("Contacto Telefónico")
            
            salvar_configs = st.form_submit_button("Guardar Alterações")
            if salvar_configs:
                novos_dados = {
                    "nome_espaco": nome_espaco,
                    "responsavel": responsavel,
                    "contacto": contacto
                }
                requests.patch(f"https://ffkaraoke-default-rtdb.firebaseio.com/prestadores_info/{token}.json", json=novos_dados)
                st.success("Dados do prestador atualizados com sucesso!")

def renderizar_ecra_tv(token):
    """Renderiza o ecrã secundário da TV para visualização dos clientes."""
    st.title("📺 Ecrã de TV - FFKaraoke")
    st.write(f"A carregar transmissão para o prestador: {token}")
    
    try:
        res = requests.get(f"https://ffkaraoke-default-rtdb.firebaseio.com/config_prestadores/{token}.json", timeout=10)
        if res.status_code == 200 and res.json():
            config_data = res.json()
            url_clipe = config_data.get("url_clipe_fundo")
            if url_clipe:
                st.video(url_clipe)
            else:
                st.info("Aguardando o prestador selecionar um vídeo clipe...")
        else:
            st.info("Aguardando o prestador selecionar um vídeo clipe...")
    except Exception as e:
        st.error(f"Erro ao carregar o ecrã da TV: {e}")
