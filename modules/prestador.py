import time
import requests
import streamlit as st

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

# --- Funções Auxiliares de Suporte ---
def limpar_nome_musica(musica_field):
    if isinstance(musica_field, dict):
        return (
            musica_field.get("titulo")
            or musica_field.get("nome")
            or musica_field.get("title")
            or "Música sem título"
        )
    return str(musica_field) if musica_field else "Música sem título"

def atualizar_estado_pedido(token, pedido_id, novo_estado):
    try:
        requests.patch(
            f"{FIREBASE_URL}/pedidos/{token}/{pedido_id}.json",
            json={"estado": novo_estado},
            timeout=10
        )
    except Exception:
        pass

def terminar_todas_musicas_ativas(token, pedidos):
    for p in pedidos:
        if p.get("estado") == "aprovado":
            atualizar_estado_pedido(token, p.get("id"), "terminado")

def obter_video_fundo(token):
    try:
        response = requests.get(f"{FIREBASE_URL}/config/{token}/video_fundo.json", timeout=10)
        if response.status_code == 200:
            return response.json() or ""
    except Exception:
        pass
    return ""

def definir_video_fundo(token, url):
    try:
        requests.put(f"{FIREBASE_URL}/config/{token}/video_fundo.json", json=url, timeout=10)
    except Exception:
        pass

def listar_videos_pasta_clipes():
    # Pode integrar aqui a sua listagem do Cloudinary se necessário
    return []


# --- Função Principal do Módulo (Painel Completo do Prestador) ---
@st.fragment(run_every=3)
def renderizar_gestao_fila_prestador(provider_token):
    try:
        # Título principal do painel (pode alterar aqui o texto e as cores quando quiser!)
        st.markdown("## 🎛️ Painel do Prestador 2 — FF Karaoke Cloud")
        st.markdown("---")

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

        # Secção de Confirmação de Pedidos Pendentes
        if pendentes:
            st.markdown("""
                <div style="background-color: rgba(0,0,0,0.95); border: 4px solid #FFC107; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
                    <div style="color: #ffffff; font-family: monospace; font-size: 15px; font-weight: bold; margin-bottom: 5px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Confirmação de Pedido</div>
                    <div style="color: #ffffff; font-family: monospace; font-size: 18px; font-weight: bold; margin-bottom: 10px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">QUER CANTAR</div>
            """, unsafe_allow_html=True)
            
            for p in pendentes:
                titulo_p = limpar_nome_musica(p.get("musica", {}))
                cliente_p = p.get("cliente", "Convidado")
                st.markdown(f"""
                    <div style="color: #ffffff; font-family: monospace; font-size: 15px; margin-bottom: 15px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">
                        <b>{titulo_p}</b> <span style="color: #ffffff; font-size: 13px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">({cliente_p})</span>
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

        st.markdown("### 📋 Estado da Fila e Controlo de Reprodução")

        # Lista de Pedidos Ativos
        if pedidos_ativos:
            for idx, p in enumerate(pedidos_ativos, start=1):
                titulo_musica = limpar_nome_musica(p.get("musica", {}))
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
                <div style="background-color: rgba(0,0,0,0.95); border: 4px solid #FFC107; border-radius: 8px; padding: 15px; color: #ffffff; width: 100%; font-family: monospace; font-size: 14px; margin-bottom: 20px; text-align: center; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">
                    NENHUM PEDIDO NA LISTA NESTE MOMENTO.<br>À ESPERA DE NOVOS PEDIDOS...
                </div>
            """, unsafe_allow_html=True)

        if tocando_agora:
            if st.button("🛑 Stop Geral (Limpar Tela)", key="stop_geral_btn", use_container_width=True):
                terminar_todas_musicas_ativas(provider_token, pedidos)
                definir_video_fundo(provider_token, "")
                st.warning("Reprodução parada e tela limpa com sucesso!")
                st.rerun()
                
        st.markdown("---")
        
        # Gestão de Vídeos de Fundo (Cloudinary)
        video_fundo_atual = obter_video_fundo(provider_token)
        lista_clipes_cloudinary = listar_videos_pasta_clipes()
        
        opcoes_labels = ["Nenhum (Ecrã Preto)"]
        mapa_url_por_label = {}
        
        for clipe in lista_clipes_cloudinary:
            label = f"📁 {clipe['nome']}"
            opcoes_labels.append(label)
            mapa_url_por_label[label] = clipe['url']
            
        index_atual = 0
        for idx, label in enumerate(opcoes_labels):
            if label != "Nenhum (Ecrã Preto)":
                url_mapeada = mapa_url_por_label.get(label, "")
                if video_fundo_atual and (video_fundo_atual in url_mapeada or url_mapeada in video_fundo_atual):
                    index_atual = idx
                    break

        with st.form(key="form_video_fundo"):
            escolha_video = st.selectbox(
                "Pesquisar Vídeo Clipe", 
                options=opcoes_labels, 
                index=index_atual
            )

            st.markdown("""
                <style>
                div[data-testid="stFormSubmitButton"] button {
                    background-color: #4CAF50 !important;
                    color: white !important;
                    border: 2px solid #2E7D32 !important;
                }
                div[data-testid="stFormSubmitButton"] button:hover {
                    background-color: #43A047 !important;
                }
                </style>
            """, unsafe_allow_html=True)

            btn_salvar_fundo = st.form_submit_button("Pesquisar Vídeo Clipe")
            if btn_salvar_fundo:
                if escolha_video == "Nenhum (Ecrã Preto)":
                    valor_a_guardar = ""
                else:
                    valor_a_guardar = mapa_url_por_label.get(escolha_video, "")
                    
                definir_video_fundo(provider_token, valor_a_guardar)
                st.success("Vídeo clipe de fundo iniciado com sucesso na tela!")
                st.rerun()
            
    except Exception as e:
        st.error(f"Erro ao carregar os pedidos do Firebase: {e}")
