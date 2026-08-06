import streamlit as st
import requests
import time

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

def get_pedidos_prestador(token):
    try:
        response = requests.get(f"{FIREBASE_URL}/pedidos/{token}.json")
        if response.status_code == 200 and response.json():
            data = response.json()
            if isinstance(data, dict):
                return [{"id": k, **v} for k, v in data.items()]
            elif isinstance(data, list):
                return [{"id": str(idx), **item} for idx, item in enumerate(data) if item is not None]
        return []
    except Exception:
        return []

def atualizar_estado_pedido(token, pedido_id, novo_estado):
    try:
        url = f"{FIREBASE_URL}/pedidos/{token}/{pedido_id}.json"
        response = requests.patch(url, json={"estado": novo_estado}, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

def terminar_todas_musicas_ativas(token, pedidos):
    """Termina ou pausa todas as músicas que estejam marcadas como 'aprovado'."""
    try:
        for p in pedidos:
            if p.get("estado") == "aprovado":
                atualizar_estado_pedido(token, p.get("id"), "terminado")
    except Exception:
        pass

def obter_video_fundo(token):
    try:
        res = requests.get(f"{FIREBASE_URL}/config_prestador/{token}/video_fundo.json", timeout=5)
        if res.status_code == 200 and res.json():
            return res.json()
    except Exception:
        pass
    return ""

def definir_video_fundo(token, url_video):
    try:
        requests.put(f"{FIREBASE_URL}/config_prestador/{token}/video_fundo.json", json=url_video, timeout=5)
    except Exception:
        pass

def listar_videos_pasta_clipes():
    """Retorna lista de clipes de exemplo ou integração com Cloudinary se configurado."""
    return []

def obter_titulo_seguro(musica_field):
    if isinstance(musica_field, dict):
        return musica_field.get("titulo") or musica_field.get("nome") or musica_field.get("title") or "Música sem título"
    return str(musica_field) if musica_field else "Música sem título"

def renderizar_gestao_fila_prestador(provider_token):
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

        if pendentes:
            st.markdown("""
                <div style="background-color: rgba(0,0,0,0.95); border: 4px solid #FFC107; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
                    <div style="color: #ffeb3b; font-family: monospace; font-size: 15px; font-weight: bold; margin-bottom: 5px;">Confirmação de Pedido</div>
                    <div style="color: #ffeb3b; font-family: monospace; font-size: 18px; font-weight: bold; margin-bottom: 10px;">QUER CANTAR</div>
            """, unsafe_allow_html=True)
            
            for p in pendentes:
                titulo_p = obter_titulo_seguro(p.get("musica", {}))
                cliente_p = p.get("cliente", "Convidado")
                st.markdown(f"""
                    <div style="color: #ffeb3b; font-family: monospace; font-size: 15px; margin-bottom: 15px; font-weight: bold;">
                        <b>{titulo_p}</b> <span style="font-size: 13px;">({cliente_p})</span>
                    </div>
                """, unsafe_allow_html=True)
                
                col_btn_dummy1, col_center_btn, col_btn_dummy2 = st.columns([1, 1.2, 1])
                with col_center_btn:
                    if st.button("✅ Sim", key=f"conf_sim_{p.get('id')}", use_container_width=True):
                        terminar_todas_musicas_ativas(provider_token, pedidos)
                        atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                        st.success(f"Música '{titulo_p}' enviada para a tela!")
                        st.rerun()
                    if st.button("❌ Não", key=f"conf_nao_{p.get('id')}", use_container_width=True):
                        atualizar_estado_pedido(provider_token, p.get('id'), 'terminado')
                        st.warning("Pedido recusado/cancelado.")
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### <span style='color: #ffeb3b;'>📋 Estado da Fila e Controlo de Reprodução</span>", unsafe_allow_html=True)

        if pedidos_ativos:
            for idx, p in enumerate(pedidos_ativos, start=1):
                titulo_musica = obter_titulo_seguro(p.get("musica", {}))
                cliente_nome = p.get("cliente", "Convidado")
                estado_atual = p.get("estado")
                
                is_playing = (estado_atual == "aprovado")
                cor_borda = "#4CAF50" if is_playing else "#FFC107"
                badge_texto = "🎵 A TOCAR AGORA" if is_playing else f"⏳ Fila #{idx}"
                
                with st.container():
                    st.markdown(f"""
                        <div style="background: rgba(0,0,0,0.95); border: 4px solid {cor_borda}; border-radius: 8px; padding: 12px 15px; margin-bottom: 10px; font-family: monospace;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="color: #ffeb3b; font-weight: bold; font-size: 14px;">{badge_texto}</span>
                                <span style="color: #ffeb3b; font-size: 13px;">Cliente: <b>{cliente_nome}</b></span>
                            </div>
                            <div style="color: #ffeb3b; font-size: 16px; font-weight: bold; margin-bottom: 8px;">
                                🎶 {titulo_musica}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col_acao1, col_acao2, col_acao3 = st.columns(3)
                    with col_acao1:
                        if not is_playing:
                            if st.button("▶️ Tocar Agora", key=f"play_linha_{p.get('id')}", use_container_width=True):
                                terminar_todas_musicas_ativas(provider_token, pedidos)
                                atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                                st.success(f"A avançar para: {titulo_musica}")
                                st.rerun()
                    with col_acao2:
                        if is_playing:
                            if st.button("⏹️ Terminar Atual", key=f"term_linha_{p.get('id')}", use_container_width=True):
                                terminar_todas_musicas_ativas(provider_token, pedidos)
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
                <div style="background-color: rgba(0,0,0,0.95); border: 4px solid #FFC107; border-radius: 8px; padding: 15px; color: #ffeb3b; width: 100%; font-family: monospace; font-size: 14px; margin-bottom: 20px; text-align: center; font-weight: bold;">
                    NENHUM PEDIDO NA LISTA NESTE MOMENTO.<br>À ESPERA DE NOVOS PEDIDOS...
                </div>
            """, unsafe_allow_html=True)

        if tocando_agora:
            if st.button("🛑 Stop Geral (Limpar Tela)", key="stop_geral_btn", use_container_width=True):
                terminar_todas_musicas_ativas(provider_token, pedidos)
                definir_video_fundo(provider_token, "")
                st.warning("Reprodução parada e tela limpa com sucesso!")
                st.rerun()
          
    except Exception as e:
        st.error(f"Erro ao carregar os pedidos do Firebase: {e}")

def show_provider_panel_custom(token):
    if not token:
        st.error("Acesso não autorizado. Por favor, aceda através do link válido fornecido na sua aprovação.")
        return

    st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffeb3b !important; }
    * { color: #ffeb3b !important; }
    .link-row {
        background: linear-gradient(180deg, #111, #050505);
        border: 1px solid #ffeb3b;
        border-radius: 8px;
        padding: 12px 18px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0px 0px 10px rgba(255,235,59,0.1);
        max-width: 600px;
    }
    .link-title {
        color: #ffeb3b !important;
        font-weight: bold;
        font-size: 15px;
    }
    .btn-link {
        background-color: #1a1a1a;
        color: #ffeb3b !important;
        border: 1px solid #ffeb3b;
        border-radius: 6px;
        padding: 6px 20px;
        text-decoration: none;
        font-weight: bold;
        font-size: 14px;
        transition: all 0.3s ease;
    }
    .btn-link:hover {
        background-color: #ffeb3b;
        color: #000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Título com a cor amarela garantida explicitamente
    st.markdown("<h2 style='color: #ffeb3b;'>🎤 <span style='color: #ffeb3b;'>PAINEL DO PRESTADOR</span> — FF Karaoke</h2>", unsafe_allow_html=True)
    st.markdown("---")

    base_domain = "https://appadm.streamlit.app"
    link_registo_cliente = f"{base_domain}/?page=client_register&provider={token}"
    link_tela_cliente = f"{base_domain}/?page=client_screen&provider={token}"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="link-row">
            <div class="link-title">📝 Registo do Cliente</div>
            <div><a href="{link_registo_cliente}" target="_blank" class="btn-link">link</a></div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="link-row">
            <div class="link-title">📺 Tela de Vídeos</div>
            <div><a href="{link_tela_cliente}" target="_blank" class="btn-link">link</a></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Chama a gestão avançada da fila integrada no painel
    renderizar_gestao_fila_prestador(token)

def renderizar_ecra_tv(token):
    """Função de compatibilidade para a tela de TV/Vídeos do prestador."""
    if not token:
        st.error("Token de prestador inválido para o ecrã de TV.")
        return
    
    st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffeb3b !important; }
    * { color: #ffeb3b !important; }
    </style>
    """, unsafe_allow_html=True)
    
    st.subheader("📺 Ecrã de Reprodução — FF Karaoke")
    st.markdown(f"A carregar o fluxo de vídeos para o token: `{token}`")
