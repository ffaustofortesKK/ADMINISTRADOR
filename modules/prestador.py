import streamlit as st
import requests
import time
import urllib.parse
from datetime import datetime

# --- FUNÇÕES AUXILIARES ---

def limpar_nome_musica(musica_data):
    if isinstance(musica_data, dict):
        return musica_data.get("titulo", "Música Desconhecida")
    return str(musica_data)

def atualizar_estado_pedido(provider_token, pedido_id, novo_estado):
    url = f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}/estado.json"
    requests.put(url, json=novo_estado)

def terminar_todas_musicas_ativas(provider_token, pedidos):
    for p in pedidos:
        if p.get("estado") in ["aprovado"]:
            atualizar_estado_pedido(provider_token, p.get("id"), "terminado")

def definir_video_fundo(provider_token, url_video):
    url = f"{FIREBASE_URL}/configuracoes/{provider_token}/video_fundo.json"
    requests.put(url, json=url_video)

def obter_video_fundo(provider_token):
    url = f"{FIREBASE_URL}/configuracoes/{provider_token}/video_fundo.json"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else ""

def listar_videos_pasta_clipes():
    return []

# --- FRAGMENTO DE GESTÃO DA FILA ---

@st.fragment(run_every=3)
def renderizar_gestao_fila_prestador(provider_token):
    try:
        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json?_t={time.time()}"
        response = requests.get(url_firebase, timeout=10)
        
        pedidos = []
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            
        pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
        pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
        
        tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)
        pendentes = [p for p in pedidos_ativos if p.get("estado") == "pendente"]

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

        st.markdown("### Fila de cantores")

        if pedidos_ativos:
            for idx, p in enumerate(pedidos_ativos, start=1):
                titulo_musica = limpar_nome_musica(p.get("musica", {}))
                cliente_nome = p.get("cliente", "Convidado")
                estado_atual = p.get("estado")
                
                is_playing = (estado_atual == "aprovado")
                cor_borda = "#4CAF50" if is_playing else "#FFC107"
                
                col_info, col_acao = st.columns([3, 1])
                with col_info:
                    st.markdown(f"""
                        <div style="background: rgba(0,0,0,0.95); border: 4px solid {cor_borda}; border-radius: 8px; padding: 10px 15px; margin-bottom: 8px; font-family: monospace;">
                            <span style="color: #ffffff; font-size: 16px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">
                                {idx}º {cliente_nome} — {titulo_musica}
                            </span>
                        </div>
                    """, unsafe_allow_html=True)
                with col_acao:
                    if st.button("❌ Remover", key=f"rem_linha_{p.get('id')}", use_container_width=True):
                        atualizar_estado_pedido(provider_token, p.get('id'), 'terminado')
                        st.rerun()
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

        st.markdown("---")
        
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

            btn_salvar_fundo = st.form_submit_button("Selecionar Vídeo")
            if btn_salvar_fundo:
                valor_a_guardar = "" if escolha_video == "Nenhum (Ecrã Preto)" else mapa_url_por_label.get(escolha_video, "")
                definir_video_fundo(provider_token, valor_a_guardar)
                st.rerun()
            
    except Exception as e:
        st.error(f"Erro ao carregar os pedidos: {e}")

# --- PAINEL PRINCIPAL DO PRESTADOR ---

def show_provider_panel_custom(provider_token):
    url_logotipo = "https://cdn.phototourl.com/free/2026-08-03-8b13edf5-0257-491d-ab78-f0d5329ffc15.jpg"
    url_fundo_painel = "https://cdn.phototourl.com/free/2026-08-03-694a4a2e-9914-4da8-93b2-87538a4805ab.png"

    df_prov = get_all_providers()
    nome_prestador = "PRESTADOR"
    tempo_plano = "2 Horas - 12 Mil Kwanzas"
    data_registo_str = None
    
    if not df_prov.empty and 'token' in df_prov.columns:
        match = df_prov[df_prov['token'] == provider_token]
        if not match.empty:
            row = match.iloc[0]
            nome_prestador = row.get('nome_prestador', row.get('nome', 'PRESTADOR'))
            tempo_plano = row.get('tempo_plano', row.get('tempo', '2 Horas - 12 Mil Kwanzas'))
            data_registo_str = row.get('data_registo', None)

    segundos_bónus = 0
    try:
        res_ref = requests.get(f"{FIREBASE_URL}/reforcos_aprovados/{provider_token}.json", timeout=5)
        if res_ref.status_code == 200 and res_ref.json():
            dados_ref = res_ref.json()
            if isinstance(dados_ref, dict):
                for r_id, r_info in dados_ref.items():
                    t_ref = r_info.get("tempo_plano", "")
                    if "3 Horas" in t_ref:
                        segundos_bónus += 10800
                    elif "4 Horas" in t_ref:
                        segundos_bónus += 14400
                    elif "2 Horas" in t_ref:
                        segundos_bónus += 7200
    except Exception:
        pass

    segundos_base = 7200
    if "3 Horas" in tempo_plano:
        segundos_base = 10800
    elif "4 Horas" in tempo_plano:
        segundos_base = 14400

    segundos_totais = segundos_base + segundos_bónus
    segundos_restantes = segundos_totais
    
    if data_registo_str:
        try:
            dt_str_clean = data_registo_str.split('.')[0]
            dt_reg = datetime.strptime(dt_str_clean, "%Y-%m-%d %H:%M:%S")
            diff = (datetime.now() - dt_reg).total_seconds()
            segundos_restantes = max(0, int(segundos_totais - diff))
        except Exception:
            pass

    horas_restantes = segundos_restantes // 3600
    min_restantes = (segundos_restantes % 3600) // 60
    seg_restantes = segundos_restantes % 60
    tempo_formatado = f"{int(horas_restantes):02d}:{int(min_restantes):02d}:{int(seg_restantes):02d}"

    st.markdown(f"""
    <style>
    .stApp {{
        background: url("{url_fundo_painel}") no-repeat center center fixed !important;
        background-size: cover !important;
    }}
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        background: rgba(0, 0, 0, 0.92) !important;
        border-radius: 12px;
        border: 4px solid #FFC107 !important;
    }}
    .card-link, .card-tv {{
        background: #000000 !important;
        border: 4px solid #FFC107 !important;
        border-radius: 8px;
        padding: 10px 15px;
        margin-bottom: 12px;
    }}
    .card-tv {{
        border: 4px solid #9c27b0 !important;
    }}
    .link-title {{
        font-family: monospace;
        color: #ffffff !important;
        font-size: 14px;
        font-weight: bold !important;
    }}
    .link-text {{
        font-family: monospace;
        color: #ffffff !important;
        font-size: 12px;
        word-break: break-all;
        text-decoration: underline;
    }}
    </style>
    """, unsafe_allow_html=True)

    # Layout superior ajustado: Título à esquerda, Relógio e QR Code à direita (lado a lado)
    col_topo_esq, col_topo_dir = st.columns([2.2, 1])

    with col_topo_esq:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                <span style="font-size: 28px;">🎤</span>
                <h1 style="margin: 0; color: #ffffff; font-family: monospace; font-size: 20px; font-weight: bold;">PAINEL DO PRESTADOR: {nome_prestador}</h1>
            </div>
            <p style="margin: 0 0 15px 0; color: #ffffff; font-family: monospace; font-size: 12px;">TOKEN: <code style="background: #222; color: #fff; padding: 2px 6px;">{provider_token}</code></p>
        """, unsafe_allow_html=True)

        link_cliente_rel = f"/?page=client_register&prestador={provider_token}"
        link_tv_rel = f"/?page=client_screen&prestador={provider_token}"
        host_dominio = st.context.headers.get('Host', 'grupoffkaraoke.streamlit.app')
        link_cliente_absoluto = f"https://{host_dominio}{link_cliente_rel}"
        link_tv_absoluto = f"https://{host_dominio}{link_tv_rel}"

        st.markdown(f"""
            <div class="card-link">
                <div class="link-title">🔗 LINK DO CLIENTE (REGISTO DE MÚSICA)</div>
                <a href="{link_cliente_rel}" target="_blank" class="link-text">{link_cliente_absoluto}</a>
            </div>
            <div class="card-tv">
                <div class="link-title" style="color:#e040fb !important;">📺 LINK DA TELA DE TV / REPRODUÇÃO</div>
                <a href="{link_tv_rel}" target="_blank" class="link-text">{link_tv_absoluto}</a>
            </div>
        """, unsafe_allow_html=True)

    with col_topo_dir:
        qr_url_cliente = f"https://api.qrserver.com/v1/create-qr-code/?size=130x130&data={urllib.parse.quote(link_cliente_absoluto)}"
        st.markdown(f"""
            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 8px;">
                <div style="background: rgba(255,193,7,0.15); border: 2px solid #FFC107; padding: 6px 10px; border-radius: 8px; text-align: center; width: 100%;">
                    <div style="font-family: monospace; color: #fff; font-size: 10px; font-weight: bold;">TEMPO / PLANO ESCOLHIDO</div>
                    <div style="font-family: monospace; color: #FFC107; font-size: 13px; font-weight: bold;">⏱️ {tempo_formatado} ({tempo_plano})</div>
                </div>
                <div style="text-align: center; width: 100%;">
                    <span style="font-family: monospace; color: #fff; font-size: 10px; font-weight: bold;">QR CODE CLIENTE</span>
                    <div style="background: #000; border: 3px solid #FFC107; border-radius: 6px; padding: 4px; display: inline-block;">
                        <img src="{qr_url_cliente}" width="100" style="border-radius: 4px;" />
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    renderizar_gestao_fila_prestador(provider_token)
