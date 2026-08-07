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
    return []


# --- Função Principal do Módulo (Painel Completo do Prestador) ---
@st.fragment(run_every=3)
def renderizar_gestao_fila_prestador(provider_token, nome_prestador="PRESTADOR", plano_info="02:00:00 (2 Horas - 12 Mil Kwanzas)"):
    try:
        # 1. CABEÇALHO PERSONALIZÁVEL DO PRESTADOR (Agora gerido totalmente aqui!)
        st.markdown(f"""
            <div style="background: rgba(0,0,0,0.85); border: 3px solid #FFC107; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-family: monospace;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <h2 style="color: #ffffff; margin: 0; font-size: 22px;">🎤 PAINEL DO PRESTADOR2: {nome_prestador}</h2>
                    <div style="background: #111; border: 2px solid #FFC107; padding: 8px 12px; border-radius: 6px; color: #fff; font-size: 14px;">
                        <b>TEMPO / PLANO ESCOLHIDO:</b><br>⏱️ {plano_info}
                    </div>
                </div>
                <div style="margin-top: 10px; color: #aaa; font-size: 13px;">
                    TOKEN: <code>{provider_token}</code>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Links úteis (Cliente e Tela de TV)
        base_url = "https://appadm.streamlit.app"
        link_cliente = f"{base_url}/?page=client_register&prestador={provider_token}"
        link_tela = f"{base_url}/?page=client_screen&prestador={provider_token}"

        col_links, col_qr = st.columns([2.5, 1])
        with col_links:
            st.markdown(f"""
                <div style="background: rgba(0,0,0,0.9); border: 2px solid #FFC107; padding: 10px; border-radius: 6px; margin-bottom: 10px; font-family: monospace;">
                    <span style="font-size: 12px; color: #FFC107;">🔗 LINK DO CLIENTE (REGISTO DE MÚSICA)</span><br>
                    <a href="{link_cliente}" target="_blank" style="color: #fff; font-size: 12px; word-break: break-all;">{link_cliente}</a>
                </div>
                <div style="background: rgba(0,0,0,0.9); border: 2px solid #9C27B0; padding: 10px; border-radius: 6px; font-family: monospace;">
                    <span style="font-size: 12px; color: #BA68C8;">📺 LINK DA TELA DE TV / REPRODUÇÃO</span><br>
                    <a href="{link_tela}" target="_blank" style="color: #fff; font-size: 12px; word-break: break-all;">{link_tela}</a>
                </div>
            """, unsafe_allow_html=True)
            
        with col_qr:
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={link_cliente}"
            st.markdown(f"""
                <div style="text-align: center; background: rgba(0,0,0,0.9); border: 2px solid #FFC107; padding: 5px; border-radius: 6px;">
                    <span style="font-size: 11px; color: #FFC107; font-family: monospace;">QR CODE CLIENTE</span><br>
                    <img src="{qr_url}" width="110" style="border-radius: 4px; margin-top: 4px;">
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # 2. LÓGICA DA FILA E PEDIDOS
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
                    <div style="color: #ffffff; font-family: monospace; font-size: 15px; font-weight: bold; margin-bottom: 5px;">Confirmação de Pedido</div>
                    <div style="color: #ffffff; font-family: monospace; font-size: 18px; font-weight: bold; margin-bottom: 10px;">QUER CANTAR</div>
            """, unsafe_allow_html=True)
            
            for p in pendentes:
                titulo_p = limpar_nome_musica(p.get("musica", {}))
                cliente_p = p.get("cliente", "Convidado")
                st.markdown(f"""
                    <div style="color: #ffffff; font-family: monospace; font-size: 15px; margin-bottom: 15px; font-weight: bold;">
                        <b>{titulo_p}</b> <span style="color: #aaa; font-size: 13px;">({cliente_p})</span>
                    </div>
                """, unsafe_allow_html=True)
                
                col_btn_dummy1, col_center_btn, col_btn_dummy2 = st.columns([1, 1.2, 1])
                with col_center_btn:
                    if st.button("✅ Sim", key=f"conf_sim_{p.get('id')}", use_container_width=True):
                        terminar_todas_musicas_ativas(provider_token, pedidos)
                        atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                        st.rerun()
                    if st.button("❌ Não", key=f"conf_nao_{p.get('id')}", use_container_width=True):
                        atualizar_estado_pedido(provider_token, p.get('id'), 'terminado')
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 📋 Estado da Fila e Controlo de Reprodução")

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
                                <span style="color: #ffffff; font-weight: bold; font-size: 14px;">{badge_texto}</span>
                                <span style="color: #ccc; font-size: 13px;">Cliente: <b>{cliente_nome}</b></span>
                            </div>
                            <div style="color: #ffffff; font-size: 16px; font-weight: bold;">
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
                                st.rerun()
                    with col_acao2:
                        if is_playing:
                            if st.button("⏹️ Terminar Atual", key=f"term_linha_{p.get('id')}", use_container_width=True):
                                terminar_todas_musicas_ativas(provider_token, pedidos)
                                st.rerun()
                    with col_acao3:
                        if st.button("❌ Remover", key=f"rem_linha_{p.get('id')}", use_container_width=True):
                            atualizar_estado_pedido(provider_token, p.get('id'), 'terminado')
                            st.rerun()
                    st.markdown("<hr style='margin: 5px 0 15px 0; border-color: #333;'>", unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background-color: rgba(0,0,0,0.95); border: 4px solid #FFC107; border-radius: 8px; padding: 15px; color: #ffffff; width: 100%; font-family: monospace; font-size: 14px; margin-bottom: 20px; text-align: center; font-weight: bold;">
                    NENHUM PEDIDO NA LISTA NESTE MOMENTO.<br>À ESPERA DE NOVOS PEDIDOS...
                </div>
            """, unsafe_allow_html=True)

        if tocando_agora:
            if st.button("🛑 Stop Geral (Limpar Tela)", key="stop_geral_btn", use_container_width=True):
                terminar_todas_musicas_ativas(provider_token, pedidos)
                definir_video_fundo(provider_token, "")
                st.rerun()
                
    except Exception as e:
        st.error(f"Erro ao carregar o painel: {e}")
