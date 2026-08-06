import streamlit as st
import pandas as pd
import requests
import datetime
import time
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
        renderizar_gestao_fila_prestador(token)

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

def renderizar_gestao_fila_prestador(provider_token):
    FIREBASE_URL = "https://ffkaraoke-default-rtdb.firebaseio.com"
    try:
        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json?_t={time.time()}"
        response = requests.get(url_firebase, timeout=10)
        
        pedidos = []
        if response.status_code == 200 and response.json():
            data = response.json()
            if isinstance(data, dict):
                pedidos = [{"id": k, **v} for k, v in data.items()]
            elif isinstance(data, list):
                pedidos = [{"id": str(idx), **item} for idx, item in enumerate(data) if item is not None]
        
        pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
        pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
        
        tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)
        pendentes = [p for p in pedidos_ativos if p.get("estado") == "pendente"]

        def obter_titulo(musica_field):
            if isinstance(musica_field, dict):
                return musica_field.get("titulo") or musica_field.get("nome") or musica_field.get("title") or "Música sem título"
            return str(musica_field) if musica_field else "Música sem título"

        if pendentes:
            st.markdown("""
                <div style="background-color: rgba(0,0,0,0.95); border: 4px solid #FFC107; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
                    <div style="color: #ffffff; font-family: monospace; font-size: 15px; font-weight: bold; margin-bottom: 5px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Confirmação de Pedido</div>
                    <div style="color: #ffffff; font-family: monospace; font-size: 18px; font-weight: bold; margin-bottom: 10px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">QUER CANTAR</div>
            """, unsafe_allow_html=True)
            
            for p in pendentes:
                titulo_p = obter_titulo(p.get("musica", {}))
                cliente_p = p.get("cliente", "Convidado")
                st.markdown(f"""
                    <div style="color: #ffffff; font-family: monospace; font-size: 15px; margin-bottom: 15px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">
                        <b>{titulo_p}</b> <span style="color: #ffffff; font-size: 13px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">({cliente_p})</span>
                    </div>
                """, unsafe_allow_html=True)
                
                col_btn_dummy1, col_center_btn, col_btn_dummy2 = st.columns([1, 1.2, 1])
                with col_center_btn:
                    if st.button("✅ Sim", key=f"conf_sim_{p.get('id')}", use_container_width=True):
                        atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                        st.success(f"Música '{titulo_p}' enviada para a tela!")
                        st.rerun()
                    if st.button("❌ Não", key=f"conf_nao_{p.get('id')}", use_container_width=True):
                        atualizar_estado_pedido(provider_token, p.get('id'), 'terminado')
                        st.warning("Pedido recusado/cancelado.")
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 📋 Estado da Fila e Controlo de Reprodução")
        if pedidos_ativos:
            for idx, p in enumerate(pedidos_ativos, start=1):
                titulo_musica = obter_titulo(p.get("musica", {}))
                cliente_nome = p.get("cliente", "Convidado")
                estado_atual = p.get("estado")
                
                is_playing = (estado_atual == "aprovado")
                cor_borda = "#4CAF50" if is_playing else "#FFC107"
                badge_texto = "🎵 A TOCAR AGORA" if is_playing else f"⏳ Fila #{idx}"
                
                with st.container():
                    st.markdown(f"""
                        <div style="background: rgba(0,0,0,0.95); border: 4px solid {cor_borda}; border-radius: 8px; padding: 12px 15px; margin-bottom: 10px; font-family: monospace;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="color: #ffffff; font-weight: bold; font-size: 14px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">{badge_texto}</span>
                                <span style="color: #ffffff; font-size: 13px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Cliente: <b>{cliente_nome}</b></span>
                            </div>
                            <div style="color: #ffffff; font-size: 16px; font-weight: bold; margin-bottom: 8px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">
                                🎶 {titulo_musica}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col_acao1, col_acao2, col_acao3 = st.columns(3)
                    with col_acao1:
                        if not is_playing:
                            if st.button("▶️ Tocar Agora", key=f"play_linha_{p.get('id')}", use_container_width=True):
                                atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                                st.success(f"A avançar para: {titulo_musica}")
                                st.rerun()
                    with col_acao2:
                        if is_playing:
                            if st.button("⏹️ Terminar Atual", key=f"term_linha_{p.get('id')}", use_container_width=True):
                                atualizar_estado_pedido(provider_token, p.get('id'), 'terminado')
                                st.success("Música terminada!")
                                st.rerun()
                    with col_acao3:
                        if st.button("❌ Remover", key=f"rem_linha_{p.get('id')}", use_container_width=True):
                            atualizar_estado_pedido(provider_token, p.get('id'), 'terminado')
                            st.warning("Música removida da fila.")
                            st.rerun()
                    st.markdown("<hr style='margin: 5px 0 15px 0; border-color: #333;'>", unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background-color: rgba(0,0,0,0.95); border: 4px solid #FFC107; border-radius: 8px; padding: 15px; color: #ffffff; width: 100%; font-family: monospace; font-size: 14px; margin-bottom: 20px; text-align: center; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">
                    NENHUM PEDIDO NA LISTA NESTE MOMENTO.<br>À ESPERA DE NOVOS PEDIDOS...
                </div>
            """, unsafe_allow_html=True)

        if tocando_agora:
            if st.button("🛑 Stop Geral (Limpar Tela)", key="stop_geral_btn", use_container_width=True):
                atualizar_estado_pedido(provider_token, tocando_agora.get('id'), 'terminado')
                st.warning("Reprodução parada e tela limpa com sucesso!")
                st.rerun()

    except Exception as e:
        st.error(f"Erro ao carregar os pedidos do Firebase: {e}")

def atualizar_estado_pedido(provider_token, pedido_id, novo_estado):
    FIREBASE_URL = "https://ffkaraoke-default-rtdb.firebaseio.com"
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}.json"
        res = requests.get(url, timeout=10)
        if res.status_code == 200 and res.json():
            dados = res.json()
            dados["estado"] = novo_estado
            requests.put(url, json=dados)
    except Exception:
        pass

def renderizar_ecra_tv(token):
    """Renderiza o ecrã secundário da TV para visualização dos clientes."""
    st.title("📺 Ecrã de TV - FFKaraoke")
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
