import streamlit as st
import requests
import time
import urllib.parse
from datetime import datetime
import pandas as pd
import yt_dlp

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

# --- FUNÇÃO AUXILIAR: BUSCAR MÚLTIPLOS LINKS NO YOUTUBE ---
def buscar_multiplos_links_youtube(termo, max_resultados=6):
    ydl_opts = {'default_search': f'ytsearch{max_resultados}', 'format': 'best', 'extract_flat': False}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(termo, download=False)
            entries = info.get('entries', [])
            resultados = []
            for entry in entries:
                if entry:
                    titulo = entry.get('title', 'Vídeo do YouTube')
                    vid_id = entry.get('id', '')
                    if vid_id:
                        resultados.append({
                            "titulo": titulo,
                            "url": f"https://www.youtube.com/watch?v={vid_id}"
                        })
            return resultados
        except Exception:
            pass
    return []

def limpar_nome_musica(musica_obj):
    if isinstance(musica_obj, dict):
        return musica_obj.get("titulo", "Música Desconhecida")
    return str(musica_obj)

def atualizar_estado_pedido(provider_token, pedido_id, novo_estado):
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}.json"
        requests.patch(url, json={"estado": novo_estado}, timeout=5)
    except Exception:
        pass

def terminar_todas_musicas_ativas(provider_token, pedidos):
    for p in pedidos:
        if p.get("estado") == "aprovado":
            atualizar_estado_pedido(provider_token, p.get("id"), "terminado")

def obter_video_fundo(provider_token):
    try:
        url = f"{FIREBASE_URL}/video_fundo/{provider_token}.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            return res.json().get("url", "")
    except Exception:
        pass
    return ""

def definir_video_fundo(provider_token, url_video):
    try:
        url = f"{FIREBASE_URL}/video_fundo/{provider_token}.json"
        requests.put(url, json={"url": url_video}, timeout=5)
    except Exception:
        pass

def listar_videos_pasta_clipes():
    return []

def get_all_providers():
    try:
        url = f"{FIREBASE_URL}/providers.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            data = res.json()
            return pd.DataFrame([{"token": k, **v} for k, v in data.items()])
    except Exception:
        pass
    return pd.DataFrame(columns=['token', 'approved', 'data_registo', 'nome_prestador', 'tempo_plano'])


@st.fragment(run_every=1)
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
        
        pedidos_extras = [p for p in pedidos if p.get("estado") == "pendente_ext"]

        tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)
        if not tocando_agora and pedidos_ativos:
            primeiro_id = pedidos_ativos[0].get('id')
            atualizar_estado_pedido(provider_token, primeiro_id, 'aprovado')
            pedidos_ativos[0]["estado"] = "aprovado"
            tocando_agora = pedidos_ativos[0]

        aba_fila, aba_extras = st.tabs([f"📋 Fila de Reprodução ({len(pedidos_ativos)})", f"🎵 Pedidos Extras ({len(pedidos_extras)})"])

        with aba_fila:
            col_esq, col_dir = st.columns([1.5, 1], gap="medium")
            
            with col_esq:
                st.markdown("### 📋 Estado da Fila e Controlo de Reprodução")

                if pedidos_ativos:
                    for idx, p in enumerate(pedidos_ativos, start=1):
                        titulo_musica = limpar_nome_musica(p.get("musica", {}))
                        cliente_nome = p.get("cliente", "Convidado").upper()
                        
                        c_num, c_cli, c_tit, c_btn = st.columns([0.5, 2, 4, 0.8])
                        with c_num:
                            st.markdown(f"<div style='background:#000; color:#FFC107; border:1px solid #FFC107; padding:6px; text-align:center; font-family:monospace; font-weight:bold; border-radius:4px;'>{idx}</div>", unsafe_allow_html=True)
                        with c_cli:
                            st.markdown(f"<div style='background:#000; color:#FFC107; border:1px solid #FFC107; padding:6px; font-family:monospace; font-weight:bold; border-radius:4px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;'>{cliente_nome}</div>", unsafe_allow_html=True)
                        with c_tit:
                            st.markdown(f"<div style='background:#000; color:#FFC107; border:1px solid #FFC107; padding:6px; font-family:monospace; font-weight:bold; border-radius:4px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;'>{titulo_musica}</div>", unsafe_allow_html=True)
                        with c_btn:
                            if st.button("✕", key=f"del_fila_{p.get('id')}", use_container_width=True):
                                atualizar_estado_pedido(provider_token, p.get('id'), 'terminado')
                                st.rerun()
                    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div style="background-color: #000000; border: 2px solid #FFC107; border-radius: 6px; padding: 12px; color: #FFC107; font-family: monospace; font-size: 13px; margin-bottom: 15px; text-align: center; font-weight: bold;">
                            NENHUM PEDIDO NA LISTA NESTE MOMENTO.<br>À ESPERA DE NOVOS PEDIDOS...</div>
                    """, unsafe_allow_html=True)

                st.markdown("### LEITOR KARAOKE")
                
                if tocando_agora:
                    cantor_atual = tocando_agora.get("cliente", "CONVIDADO").upper()
                    musica_atual = limpar_nome_musica(tocando_agora.get("musica", {}))
                    
                    st.markdown(f"""
                        <div style="background: #000000; border: 3px solid #FFC107; border-radius: 6px; padding: 20px; margin-bottom: 15px; text-align: center;">
                            <div style="color: #FFC107; font-family: monospace; font-size: 32px; font-weight: bold; text-transform: uppercase; margin-bottom: 8px; text-shadow: 2px 2px 6px rgba(0,0,0,0.9);">
                                {cantor_atual}
                            </div>
                            <div style="color: #ffffff; font-family: monospace; font-size: 15px; font-weight: bold;">
                                {musica_atual}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    c_t1, c_t2, c_t3 = st.columns(3)
                    with c_t1:
                        if st.button("▶️ Tocar o Karaoke", key=f"btn_tocar_{tocando_agora.get('id')}", use_container_width=True):
                            terminar_todas_musicas_ativas(provider_token, pedidos)
                            atualizar_estado_pedido(provider_token, tocando_agora.get('id'), 'aprovado')
                            st.rerun()
                    with c_t2:
                        if st.button("⏹️ Parar o Karaoke", key=f"btn_parar_{tocando_agora.get('id')}", use_container_width=True):
                            terminar_todas_musicas_ativas(provider_token, pedidos)
                            st.rerun()
                    with c_t3:
                        if st.button("⏭️ Avançar Karaoke", key=f"btn_prox_{tocando_agora.get('id')}", use_container_width=True):
                            atualizar_estado_pedido(provider_token, tocando_agora.get('id'), 'terminado')
                            restantes = [x for x in pedidos_ativos if x.get('id') != tocando_agora.get('id')]
                            if restantes:
                                atualizar_estado_pedido(provider_token, restantes[0].get('id'), 'aprovado')
                            st.rerun()
                else:
                    st.markdown("""
                        <div style="background: #000000; border: 3px solid #FFC107; border-radius: 6px; padding: 20px; text-align: center; font-family: monospace; color: #FFC107; font-weight: bold;">
                            NENHUMA MÚSICA EM REPRODUÇÃO - À ESPERA DA FILA DE ESPERA
                        </div>
                    """, unsafe_allow_html=True)

            with col_dir:
                st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
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

                with st.form(key="form_video_fundo_pos"):
                    st.markdown("<div style='font-family: monospace; color: #ffffff; font-size: 13px; font-weight: bold; margin-bottom: 5px;'>Pesquisar Vídeo Clipe</div>", unsafe_allow_html=True)
                    escolha_video = st.selectbox("Pesquisar Vídeo Clipe", options=opcoes_labels, index=index_atual, label_visibility="collapsed")
                    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                    
                    col_btn_play, col_btn_stop = st.columns(2)
                    with col_btn_play:
                        btn_play_fundo = st.form_submit_button("▶️ Play", use_container_width=True)
                    with col_btn_stop:
                        btn_stop_fundo = st.form_submit_button("⏹️ Stop", use_container_width=True)

                    if btn_play_fundo:
                        valor_a_guardar = "" if escolha_video == "Nenhum (Ecrã Preto)" else mapa_url_por_label.get(escolha_video, "")
                        definir_video_fundo(provider_token, valor_a_guardar)
                        st.success("Vídeo clipe de fundo colocado em reprodução na tela!")
                        st.rerun()
                    
                    if btn_stop_fundo:
                        definir_video_fundo(provider_token, "")
                        st.success("Vídeo clipe parado (Ecrã Preto ativado)!")
                        st.rerun()

        # --- ABA DE PEDIDOS EXTRAS ---
        with aba_extras:
            st.markdown("### 🕹️ CAIXA DE PEDIDOS NÃO ACHADOS (EXTERNOS)")
            if pedidos_extras:
                for p in pedidos_extras:
                    pedido_id = p.get("id")
                    cliente = p.get("cliente", "Desconhecido")
                    musica_nome = p.get("musica", "")
                    timestamp_pedido = p.get("timestamp_str", "Data não registada")
                    
                    opcoes_encontradas = p.get("opcoes_yt", [])
                    link_selecionado = p.get("link_yt", "")
                    
                    with st.container(border=True):
                        st.markdown(f"🎵 **{musica_nome}**")
                        st.caption(f"Pedido de cliente - {cliente} - {timestamp_pedido}")
                        
                        if link_selecionado:
                            st.markdown(f"🔗 [{link_selecionado}]({link_selecionado})")
                        
                        # Se já existirem opções guardadas, mostra os links diretamente
                        if opcoes_encontradas:
                            for opt in opcoes_encontradas:
                                st.markdown(f"▶️ [{opt['titulo']}]({opt['url']})")
                        
                        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
                        
                        col_b1, col_b2, col_b3 = st.columns([1.5, 1, 0.8])
                        with col_b1:
                            if st.button("🔍 Procurar karaoke no YouTube", key=f"procurar_ext_{pedido_id}"):
                                termo_busca = f"{musica_nome} karaoke"
                                resultados_busca = buscar_multiplos_links_youtube(termo_busca, max_resultados=6)
                                if resultados_busca:
                                    primeiro_link = resultados_busca[0]['url']
                                    # Grava de imediato no Firebase para atualizar o estado da página
                                    payload_atualizacao = {
                                        "opcoes_yt": resultados_busca,
                                        "link_yt": primeiro_link
                                    }
                                    requests.patch(f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}.json", json=payload_atualizacao)
                                    st.success(f"{len(resultados_busca)} opções encontradas!")
                                    time.sleep(0.3)
                                    st.rerun()
                                else:
                                    st.error("Nenhum vídeo correspondente encontrado.")
                        with col_b2:
                            if link_selecionado:
                                if st.button("Abrir no YouTube", key=f"abrir_yt_ext_{pedido_id}", use_container_width=True):
                                    st.markdown(f'<meta http-equiv="refresh" content="0;url={link_selecionado}">', unsafe_allow_html=True)
                            else:
                                st.button("Abrir no YouTube", key=f"abrir_yt_disabled_{pedido_id}", disabled=True, use_container_width=True)
                        with col_b3:
                            if st.button("Apagar", key=f"apagar_ext_{pedido_id}", type="primary", use_container_width=True):
                                requests.delete(f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}.json")
                                st.rerun()
            else:
                st.markdown("<div style='border: 2px solid #FFC107; padding: 15px; color: #FFC107; text-align: center; font-weight: bold;'>NENHUM PEDIDO EXTRA PENDENTE NO MOMENTO.</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro ao carregar os pedidos do Firebase: {e}")


def show_provider_panel_custom(provider_token):
    url_logotipo = "https://cdn.phototourl.com/free/2026-08-03-8b13edf5-0257-491d-ab78-f0d5329ffc15.jpg"
    url_fundo_painel = "https://cdn.phototourl.com/free/2026-08-03-694a4a2e-9914-4da8-93b2-87538a4805ab.png"

    df_prov = get_all_providers()
    
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
                        nome_prestador = str(row.get(col_n)).upper()
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
                O SEU TEMPO ESTA TERMINANDO. PARA QUE NÃO PERCAS OS SEUS REGISTOS PEÇA REFORÇO DE TEMPO.
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
                <div class="link-title">🔗 LINNK DO CLIENTE (REGISTO DE MÚSICA)</div>
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


def show_prestador_page(token, url):
    show_provider_panel_custom(token)
