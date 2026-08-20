import streamlit as st
import requests
import time
import urllib.parse
from datetime import datetime
import pandas as pd

def show_provider_panel_custom(provider_token, FIREBASE_URL=None, get_all_providers=None, renderizar_gestao_fila_prestador=None):
    if not FIREBASE_URL:
        FIREBASE_URL = "https://grupo-ff-karaoke-default-rtdb.firebaseio.com"

    url_logotipo = "https://cdn.phototourl.com/free/2026-08-03-8b13edf5-0257-491d-ab78-f0d5329ffc15.jpg"
    url_fundo_painel = "https://cdn.phototourl.com/free/2026-08-03-694a4a2e-9914-4da8-93b2-87538a4805ab.png"

    df_prov = get_all_providers() if get_all_providers else st.session_state.get('df_prov', pd.DataFrame())
    
    nome_prestador = "PRESTADOR NÃO IDENTIFICADO"
    tempo_plano = "2 Horas - 12 Mil Kwanzas"
    data_registo_str = None
    
    if not df_prov.empty:
        col_token_candidates = ['token', 'provider_token', 'id']
        col_token_encontrada = next((c for c in col_token_candidates if c in df_prov.columns), None)
        
        if col_token_encontrada:
            match = df_prov[df_prov[col_token_encontrada].astype(str) == str(provider_token)]
            if not match.empty:
                row = match.iloc[0]
                
                for col_n in ['nome_prestador', 'nome', 'prestador', 'user']:
                    if col_n in df_prov.columns and pd.notna(row.get(col_n)):
                        nome_prestador = str(row.get(col_n))
                        break
                
                for col_p in ['tempo_plano', 'plano', 'duracao', 'tempo']:
                    if col_p in df_prov.columns and pd.notna(row.get(col_p)):
                        tempo_plano = str(row.get(col_p))
                        break
                        
                for col_d in ['data_registo', 'data', 'timestamp', 'created_at']:
                    if col_d in df_prov.columns and pd.notna(row.get(col_d)):
                        data_registo_str = str(row.get(col_d))
                        break

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
    elif "2 Horas" in tempo_plano:
        segundos_base = 7200

    segundos_totais = segundos_base + segundos_bónus
    segundos_restantes = segundos_totais
    
    if data_registo_str:
        try:
            dt_str_clean = data_registo_str.split('.')[0]
            try:
                dt_reg = datetime.strptime(dt_str_clean, "%Y-%m-%d %H:%M:%S")
            except Exception:
                dt_reg = datetime.fromisoformat(data_registo_str.replace('Z', '+00:00').split('+')[0])
                
            diff = (datetime.now() - dt_reg).total_seconds()
            segundos_restantes = max(0, int(segundos_totais - diff))
        except Exception:
            pass

    horas_restantes = segundos_restantes // 3600
    min_restantes = (segundos_restantes % 3600) // 60
    seg_restantes = segundos_restantes % 60
    tempo_formatado = f"{int(horas_restantes):02d}:{int(min_restantes):02d}:{int(seg_restantes):02d}"
    
    aviso_reforço_html = ""
    classe_piscar = ""
    if segundos_restantes <= 1800 and segundos_restantes > 0:
        classe_piscar = "animation: piscarRelogio 1s infinite;"
        aviso_reforço_html = """
        <div style="background: rgba(255,0,0,0.85); border: 3px solid #ffeb3b; padding: 10px; border-radius: 6px; margin-bottom: 15px; text-align: center; animation: pulseAviso 1s infinite;">
            <span style="color: #ffffff; font-size: 14px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">
                O SEU TEMPO ESTÁ TERMINANDO. PARA QUE NÃO PERCAS OS SEUS REGISTOS PEÇA REFORÇO DE TEMPO.
            </span>
            <div style="margin-top: 8px;">
                <a href="#reforco_seccao" style="background: #FFC107; color: #000; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 13px;">⚡ PEDIR REFORÇO AGORA</a>
            </div>
        </div>
        """

    st.markdown(f"""
    <style>
    .stApp {{
        background: url("{url_fundo_painel}") no-repeat center center fixed !important;
        background-size: cover !important;
    }}
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        background: rgba(0, 0, 0, 0.95) !important;
        border-radius: 12px;
        margin-top: 1rem;
        margin-bottom: 1rem;
        border: 4px solid #FFC107 !important;
        max-width: 1400px;
    }}
    @keyframes pulseAviso {{
        0% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.7; transform: scale(1.01); }}
        100% {{ opacity: 1; transform: scale(1); }}
    }}
    @keyframes piscarRelogio {{
        0% {{ opacity: 1; color: #FFC107; }}
        50% {{ opacity: 0.3; color: #ff5252; }}
        100% {{ opacity: 1; color: #FFC107; }}
    }}
    .card-link, .card-tv {{
        background: #000000 !important;
        border: 3px solid #FFC107 !important;
        border-radius: 8px;
        padding: 10px 14px;
        text-align: left;
        box-shadow: 0 4px 15px rgba(255, 193, 7, 0.25);
        margin-bottom: 12px;
        width: 100%;
    }}
    .card-tv {{
        border: 3px solid #9c27b0 !important;
        box-shadow: 0 4px 15px rgba(156, 39, 176, 0.25);
    }}
    .qr-box {{
        background: #000;
        border: 3px solid #FFC107 !important;
        border-radius: 8px;
        padding: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .link-title, .link-title-tv {{
        font-family: monospace;
        color: #ffffff !important;
        font-size: 13px;
        font-weight: bold !important;
        margin-bottom: 4px;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.9) !important;
    }}
    .link-text, .link-text-tv {{
        font-family: monospace;
        color: #ffffff !important;
        font-size: 11px;
        word-break: break-all;
        text-decoration: underline;
        font-weight: bold !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.9) !important;
    }}
    .top-logo {{
        width: 55px;
        height: 55px;
        border-radius: 50%;
        border: 3px solid #FFC107;
        object-fit: cover;
    }}
    h1, h2, h3, h4, h5, h6, p, label, span, div, .stMarkdown {{
        color: #ffffff !important;
        font-weight: bold !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.9) !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    col_topo_1, col_topo_2, col_topo_3 = st.columns([1.2, 3, 0.8])
    
    with col_topo_1:
        st.markdown(f"""
            <div style="background: #000000; border: 2px solid #FFC107; border-radius: 6px; padding: 8px; text-align: center;">
                <div style="font-family: monospace; color: #ffffff; font-size: 9px; text-transform: uppercase; letter-spacing: 1px;">TEMPO / PLANO ESCOLHIDO</div>
                <div style="font-family: monospace; color: #FFC107; font-size: 18px; font-weight: bold; {classe_piscar} margin: 2px 0;">⏱️ {tempo_formatado}</div>
                <div style="font-family: monospace; color: #fff; font-size: 10px;">({tempo_plano})</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_topo_2:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 12px; padding-top: 5px;">
                <span style="font-size: 28px;">🎤</span>
                <div>
                    <h1 style="margin: 0; color: #FFC107; font-family: monospace; font-size: 20px; text-transform: uppercase; font-weight: bold;">PAINEL DO PRESTADOR: <span style="color: #FFC107;">{nome_prestador}</span></h1>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_topo_3:
        st.markdown(f'<div style="text-align: right;"><img src="{url_logotipo}" class="top-logo" /></div>', unsafe_allow_html=True)

    st.markdown("<hr style='border-color: #FFC107; margin: 15px 0;'>", unsafe_allow_html=True)

    # --- ABAS DE NAVEGAÇÃO DO PAINEL ---
    aba_principal, aba_extras = st.tabs(["Painel de Controlo", "🎵 Pedidoss Extras"])

    with aba_extras:
        st.header("🎵 Gestão Automática de Pedidos Extras")
        st.info("Aqui pode ver os pedidos manuais enviados pelos clientes e aceder diretamente às sugestões geradas no YouTube.")
        
        try:
            extras_data = None
            res_extras = requests.get(f"{FIREBASE_URL}/pedidos_extras/{provider_token}.json", timeout=10)
            if res_extras.status_code == 200 and res_extras.json():
                extras_data = res_extras.json()
            else:
                res_all = requests.get(f"{FIREBASE_URL}/pedidos_extras.json", timeout=10)
                if res_all.status_code == 200 and res_all.json():
                    all_providers_extras = res_all.json()
                    if isinstance(all_providers_extras, dict):
                        for p_key, p_val in all_providers_extras.items():
                            if isinstance(p_val, dict) and len(p_val) > 0:
                                extras_data = p_val
                                break

            if extras_data and isinstance(extras_data, dict):
                for k, v in extras_data.items():
                    if not isinstance(v, dict):
                        continue
                    nome_musica = v.get('musica', '')
                    query_encoded = urllib.parse.quote(f"{nome_musica} karaoke")
                    url_sugestao_yt = f"https://www.youtube.com/results?search_query={query_encoded}"
                    
                    with st.expander(f"🎵 {nome_musica} (Cliente: {v.get('cliente', 'Anónimo')})"):
                        st.write(f"**Estado:** {v.get('estado', 'pendente')}")
                        timestamp_val = v.get('timestamp', time.time())
                        if timestamp_val > 10000000000:
                            timestamp_val = timestamp_val / 1000
                        st.write(f"**Enviado em:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp_val))}")
                        
                        st.markdown(f"""
                        <div style="background: #111; border: 2px solid #FFC107; padding: 12px; border-radius: 6px; margin: 10px 0;">
                            <p style="margin: 0 0 8px 0; color: #FFC107; font-weight: bold;">🔍 Pesquisa Automatizada no YouTube:</p>
                            <a href="{url_sugestao_yt}" target="_blank" style="color: #4CAF50; font-size: 14px; text-decoration: underline;">▶️ Procurar por "{nome_musica}" no YouTube</a>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("🗑️ Remover Pedido", key=f"del_extra_{k}"):
                            requests.delete(f"{FIREBASE_URL}/pedidos_extras/{provider_token}/{k}.json")
                            st.warning("Pedido removido.")
                            st.rerun()
            else:
                st.info("Nenhum pedido extra pendente no momento.")
        except Exception as e:
            st.error(f"Erro ao carregar pedidos extras: {e}")

    with aba_principal:
        st.markdown(aviso_reforço_html, unsafe_allow_html=True)
        link_cliente_rel = f"/?page=client_register&prestador={provider_token}"
        link_tv_rel = f"/?page=client_screen&prestador={provider_token}"
        
        host_dominio = st.context.headers.get('Host', 'grupoffkaraoke.streamlit.app')
        link_cliente_absoluto = f"https://{host_dominio}{link_cliente_rel}"
        link_tv_absoluto = f"https://{host_dominio}{link_tv_rel}"
        
        qr_url_cliente = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={urllib.parse.quote(link_cliente_absoluto)}"

        col_links, col_qr = st.columns([2.5, 1], gap="medium")
        with col_links:
            st.markdown(f"""
                <div class="card-link">
                    <div class="link-title">🔗 LINK DO CLIENTE (REGISTO DE MÚSICA)</div>
                    <a href="{link_cliente_rel}" target="_blank" class="link-text">{link_cliente_absoluto}</a>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
                <div class="card-tv">
                    <div class="link-title-tv">📺 LINK DA TELA DE TV / REPRODUÇÃO</div>
                    <a href="{link_tv_rel}" target="_blank" class="link-text-tv">{link_tv_absoluto}</a>
                </div>
            """, unsafe_allow_html=True)

        with col_qr:
            st.markdown("<div style='font-family: monospace; color: #ffffff; font-size: 11px; font-weight: bold; margin-bottom: 3px; text-align: center;'>QR CODE CLIENTE</div>", unsafe_allow_html=True)
            st.markdown(f"""
                <div class="qr-box">
                    <img src="{qr_url_cliente}" width="110" style="border-radius: 4px;" />
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color: #333; margin: 15px 0;'>", unsafe_allow_html=True)
        st.markdown("<div id='reforco_seccao'></div>", unsafe_allow_html=True)
        
        if segundos_restantes <= 1800:
            st.markdown("### ⚡ Solicitar Reforço de Tempo")
            with st.form("form_reforco_prestador"):
                referencia_comprovativo = st.text_input("Referência de Pagamento / Nº de Comprovativo")
                duracao_reforco = st.selectbox(
                    "Duração Pretendida", 
                    options=[
                        "2 Horas - 12 Mil Kwanzas", 
                        "3 Horas - 15 Mil Kwanzas", 
                        "4 Horas - 20 Mil Kwanzas"
                    ]
                )
                btn_sub_reforco = st.form_submit_button("Submeter Pedido de Reforço")
                if btn_sub_reforco:
                    if not referencia_comprovativo:
                        st.error("Por favor, preencha a Referência de Pagamento / Nº de Comprovativo.")
                    else:
                        dados_reforco = {
                            "token": provider_token,
                            "nome_prestador": nome_prestador,
                            "referencia": referencia_comprovativo,
                            "tempo_plano": duracao_reforco,
                            "approved": 0,
                            "data_registo": str(datetime.now())
                        }
                        try:
                            import uuid
                            ref_id = str(uuid.uuid4())[:8]
                            requests.put(f"{FIREBASE_URL}/reforcos_pendentes/{provider_token}/{ref_id}.json", json=dados_reforco, timeout=10)
                            st.success("Pedido de reforço submetido com sucesso! Aguarde a confirmação do Administrador.")
                        except Exception as err:
                            st.error(f"Erro ao enviar reforço: {err}")

        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        if renderizar_gestao_fila_prestador:
            renderizar_gestao_fila_prestador(provider_token)
