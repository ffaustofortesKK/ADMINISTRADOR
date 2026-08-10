import streamlit as st
import requests
import time
import urllib.parse
from datetime import datetime
from config import FIREBASE_URL
from utils import limpar_nome_musica, obter_url_video_cloudinary, obter_video_fundo, get_all_providers

def renderizar_gestao_fila_prestador(provider_token):
    try:
        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json?_t={time.time()}"
        response = requests.get(url_firebase, timeout=10)
        
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
            
            st.markdown("### 📋 Gestão da Fila de Espera")
            
            if not pedidos_ativos:
                st.info("A fila de espera está vazia.")
                return
                
            for idx, p in enumerate(pedidos_ativos):
                pid = p.get("id")
                cliente = p.get("cliente", "Convidado")
                musica_info = p.get("musica", {})
                
                if isinstance(musica_info, dict):
                    titulo_musica = musica_info.get("titulo", musica_info.get("nome", "Karaoke"))
                else:
                    titulo_musica = str(musica_info)
                    
                estado = p.get("estado")
                
                col_info, col_btn1, col_btn2 = st.columns([3, 1, 1])
                with col_info:
                    st.markdown(f"**{idx+1}. Cliente:** {cliente} | **Música:** {titulo_musica} *({estado})*")
                    
                with col_btn1:
                    if estado == "pendente":
                        if st.button("▶️ Aprovar", key=f"aprov_{pid}"):
                            requests.put(f"{FIREBASE_URL}/pedidos/{provider_token}/{pid}/estado.json", json="aprovado")
                            st.rerun()
                    elif estado == "aprovado":
                        if st.button("⏹️ Terminar", key=f"term_{pid}"):
                            requests.put(f"{FIREBASE_URL}/pedidos/{provider_token}/{pid}/estado.json", json="terminado")
                            st.rerun()
                            
                with col_btn2:
                    if st.button("🗑️ Remover", key=f"rem_{pid}"):
                        requests.delete(f"{FIREBASE_URL}/pedidos/{provider_token}/{pid}.json")
                        st.rerun()
        else:
            st.info("Nenhum pedido registado na fila.")
    except Exception as e:
        st.error(f"Erro ao carregar fila: {e}")

def show_provider_panel_custom(provider_token):
    try:
        df_prov = get_all_providers()
        prestador_row = df_prov[df_prov['token'] == provider_token] if not df_prov.empty else pd.DataFrame()
        
        if not prestador_row.empty:
            row = prestador_row.iloc[0]
            nome_prestador = row.get('nome', 'Prestador')
            tempo_plano = row.get('tempo_plano', '2 Horas')
            url_logotipo = row.get('url_logotipo', 'https://via.placeholder.com/150')
            url_fundo_painel = row.get('url_fundo_painel', 'https://via.placeholder.com/1920x1080')
            segundos_restantes = int(row.get('segundos_restantes', 7200))
        else:
            nome_prestador = "Prestador FF"
            tempo_plano = "2 Horas"
            url_logotipo = "https://via.placeholder.com/150"
            url_fundo_painel = "https://via.placeholder.com/1920x1080"
            segundos_restantes = 7200

        horas = segundos_restantes // 3600
        minutos = (segundos_restantes % 3600) // 60
        segundos = segundos_restantes % 60
        tempo_formatado = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        
        classe_piscar = "animation: piscarRelogio 1s infinite;" if segundos_restantes <= 1800 else ""
        aviso_reforço_html = f"""
            <div style="background: rgba(255, 193, 7, 0.1); border: 2px dashed #FFC107; padding: 10px; border-radius: 6px; margin-bottom: 15px; text-align: center;">
                <span style="color: #FFC107; font-family: monospace; font-size: 13px;">⚠️ O seu tempo está a esgotar-se! Solicite um reforço abaixo para continuar a usar o sistema sem interrupções.</span>
            </div>
        """ if segundos_restantes <= 1800 else ""

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
        if segundos_restantes <= 1800:
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
        renderizar_gestao_fila_prestador(provider_token)

    except Exception as e:
        st.error(f"Erro ao carregar o painel do prestador: {e}")
