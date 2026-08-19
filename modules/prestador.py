import streamlit as st
import cloudinary
import cloudinary.search
import requests

def show_prestador_page(provider_token, FIREBASE_URL):
    """
    Painel do Prestador para gerir a reprodução e selecionar os vídeos de fundo da Cloudinary.
    """
    st.markdown("""
        <div style="background: rgba(0,0,0,0.85); border: 2px solid #FFC107; padding: 12px 18px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style='color: #FFC107; margin: 0; font-family: monospace; font-size: 18px;'>🎬 GESTÃO DE VÍDEO DE FUNDO (ECCRÃ DE TV)</h2>
            <p style='color: #fff; margin: 5px 0 0 0; font-size: 12px;'>Selecione um clipe de fundo dinâmico para ser reproduzido na tela principal do karaoke.</p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Função para ir buscar os vídeos à Cloudinary de forma segura
    def obter_clipes_cloudinary():
        try:
            result = cloudinary.search.Search().expression("resource_type:video").max_results(50).execute()
            return result.get("resources", [])
        except Exception as e:
            print(f"Erro ao comunicar com a Cloudinary: {e}")
            return []

    # 2. Obter vídeo de fundo atual guardado no Firebase
    def obter_video_fundo_atual(token):
        try:
            url = f"{FIREBASE_URL}/video_fundo/{token}.json"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                res_json = response.json()
                return res_json if isinstance(res_json, str) else ""
        except Exception:
            pass
        return ""

    # 3. Definir vídeo de fundo no Firebase
    def definir_video_fundo(token, url_video):
        try:
            url = f"{FIREBASE_URL}/video_fundo/{token}.json"
            requests.put(url, json=url_video, timeout=5)
        except Exception as e:
            print(f"Erro ao atualizar vídeo de fundo: {e}")

    # Carregar lista atual da Cloudinary
    lista_clipes_cloudinary = obter_clipes_cloudinary()

    # --- PROTEÇÃO DE CACHE (Evita que os vídeos desapareçam se a rede falhar) ---
    if not lista_clipes_cloudinary and "cache_clipes_fundo" in st.session_state:
        lista_clipes_cloudinary = st.session_state["cache_clipes_fundo"]
    elif lista_clipes_cloudinary:
        st.session_state["cache_clipes_fundo"] = lista_clipes_cloudinary
    # --------------------------------------------------------------------------

    video_fundo_atual = obter_video_fundo_atual(provider_token)

    opcoes_labels = ["Nenhum (Ecrã Preto)"]
    mapa_url_por_label = {}
    
    if lista_clipes_cloudinary:
        for clipe in lista_clipes_cloudinary:
            nome_clipe = clipe.get('public_id', 'Vídeo sem nome')
            url_clipe = clipe.get('secure_url', '')
            
            if url_clipe:
                label = f"📁 {nome_clipe}"
                opcoes_labels.append(label)
                mapa_url_por_label[label] = url_clipe
            
    index_atual = 0
    for idx, label in enumerate(opcoes_labels):
        if label != "Nenhum (Ecrã Preto)":
            url_mapeada = mapa_url_por_label.get(label, "")
            if video_fundo_atual and (video_fundo_atual in url_mapeada or url_mapeada in video_fundo_atual):
                index_atual = idx
                break

    # Layout em colunas para organizar a seleção e pré-visualização
    col_form, col_preview = st.columns([1.5, 1], gap="medium")

    with col_form:
        with st.form(key="form_video_fundo_pos"):
            st.markdown("<div style='font-family: monospace; color: #FFC107; font-size: 13px; font-weight: bold; margin-bottom: 5px;'>🔍 Selecionar Vídeo Clipe</div>", unsafe_allow_html=True)
            escolha_video = st.selectbox("Selecionar Vídeo Clipe", options=opcoes_labels, index=index_atual, label_visibility="collapsed")
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            
            col_btn_play, col_btn_stop = st.columns(2)
            with col_btn_play:
                btn_play_fundo = st.form_submit_button("▶️ Play / Aplicar", use_container_width=True)
            with col_btn_stop:
                btn_stop_fundo = st.form_submit_button("⏹️ Parar (Ecrã Preto)", use_container_width=True)

            if btn_play_fundo:
                valor_a_guardar = "" if escolha_video == "Nenhum (Ecrã Preto)" else mapa_url_por_label.get(escolha_video, "")
                definir_video_fundo(provider_token, valor_a_guardar)
                st.success("Vídeo clipe de fundo colocado em reprodução na tela!")
                st.rerun()
            
            if btn_stop_fundo:
                definir_video_fundo(provider_token, "")
                st.warning("Vídeo clipe parado com sucesso (Ecrã Preto ativado)!")
                st.rerun()

    with col_preview:
        st.markdown("<div style='font-family: monospace; color: #FFC107; font-size: 13px; font-weight: bold; margin-bottom: 5px;'>📺 Estado Atual na TV</div>", unsafe_allow_html=True)
        if video_fundo_atual:
            st.markdown("""
                <div style="background: #000; border: 2px solid #4CAF50; padding: 10px; border-radius: 6px; text-align: center;">
                    <span style="color: #4CAF50; font-size: 12px; font-weight: bold;">● VÍDEO ATIVO A REPRODUZIR</span>
                </div>
            """, unsafe_allow_html=True)
            st.video(video_fundo_atual)
        else:
            st.markdown("""
                <div style="background: #000; border: 2px solid #ff5252; padding: 15px; border-radius: 6px; text-align: center;">
                    <span style="color: #ff5252; font-size: 12px; font-weight: bold;">■ ECRÃ PRETO / SEM VÍDEO DE FUNDO</span>
                </div>
            """, unsafe_allow_html=True)
