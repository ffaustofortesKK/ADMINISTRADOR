import time
import requests
import streamlit as st

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

def get_musicas_cloudinary():
    """Busca a lista de títulos guardados diretamente no catálogo do Firebase."""
    try:
        response = requests.get(f"{FIREBASE_URL}/catalogo.json")
        if response.status_code == 200 and response.json():
            data = response.json()
            musicas_formatadas = []
            
            # Se vier em formato de dicionário (chaves numéricas ou IDs)
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, str):
                        musicas_formatadas.append({"titulo": v, "url_cloudinary": v})
                    elif isinstance(v, dict):
                        titulo = v.get('titulo') or v.get('nome') or v.get('title') or str(k)
                        url = v.get('url_cloudinary') or v.get('url') or v.get('link') or titulo
                        musicas_formatadas.append({"titulo": str(titulo), "url_cloudinary": str(url)})
            
            # Se vier em formato de lista pura
            elif isinstance(data, list):
                for item in data:
                    if item is not None:
                        if isinstance(item, str):
                            musicas_formatadas.append({"titulo": item, "url_cloudinary": item})
                        elif isinstance(item, dict):
                            titulo = item.get('titulo') or item.get('nome') or item.get('title') or "Música"
                            url = item.get('url_cloudinary') or item.get('url') or item.get('link') or titulo
                            musicas_formatadas.append({"titulo": str(titulo), "url_cloudinary": str(url)})
                            
            return musicas_formatadas
        return []
    except Exception:
        return []

def enviar_pedido_cliente(provider_token, nome_cliente, musica):
    """Envia o pedido do cliente para a base de dados do prestador correspondente."""
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        
        # Obter timestamp de forma segura
        try:
            ts_resp = requests.post(f"{FIREBASE_URL}/timestamp.json", json={".sv": "timestamp"})
            ts_val = ts_resp.json().get("name") if ts_resp.status_code == 200 else int(time.time() * 1000)
        except Exception:
            ts_val = int(time.time() * 1000)

        dados_pedido = {
            "cliente": nome_cliente,
            "musica": musica,
            "estado": "pendente",
            "timestamp": ts_val
        }
        response = requests.post(url, json=dados_pedido)
        return response.status_code == 200
    except Exception:
        return False

def buscar_pedidos_prestador(provider_token):
    """Busca os pedidos pendentes ou enviados para o prestador específico."""
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        response = requests.get(url)
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos_formatados = []
            if isinstance(data, dict):
                for pedido_id, info in data.items():
                    if isinstance(info, dict):
                        info['id'] = pedido_id
                        pedidos_formatados.append(info)
            return pedidos_formatados
        return []
    except Exception:
        return []

def atualizar_estado_pedido(provider_token, pedido_id, novo_estado):
    """Atualiza o estado do pedido (ex: pendente -> aprovado -> terminado)."""
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}/estado.json"
        response = requests.put(url, json=novo_estado)
        return response.status_code == 200
    except Exception:
        return False

def painel_prestador(provider_token):
    """Painel completo do prestador com atualização automática."""
    st.markdown("<style>*{color: #ffeb3b !important;}</style>", unsafe_allow_html=True)
    st.subheader("📺 Painel do Prestador — Fila de Reprodução")
    
    placeholder = st.empty()
    auto_refresh = st.toggle("Ativar atualização automática", value=True)
    
    while True:
        with placeholder.container():
            pedidos = buscar_pedidos_prestador(provider_token)
            pedidos_ativos = [p for p in pedidos if p.get('estado') in ['pendente', 'aprovado']]
            
            if not pedidos_ativos:
                st.info("A aguardar novos pedidos de músicas...")
            else:
                st.write(f"### Fila Atual ({len(pedidos_ativos)} pedidos)")
                
                tocando_agora = next((p for p in pedidos_ativos if p.get('estado') == 'aprovado'), None)
                
                if tocando_agora:
                    musica_obj = tocando_agora.get('musica', {})
                    titulo_musica = musica_obj.get('titulo', 'Karaoke') if isinstance(musica_obj, dict) else str(musica_obj)
                    st.success(f"🎵 **A Tocar Agora:** {titulo_musica} (Pedida por: {tocando_agora.get('cliente')})")
                    if st.button("Marcar como Terminado", key=f"term_{tocando_agora.get('id')}"):
                        atualizar_estado_pedido(provider_token, tocando_agora.get('id'), 'terminado')
                        st.rerun()
                
                st.write("---")
                st.write("**Próximos na Fila:**")
                for p in pedidos_ativos:
                    musica_obj = p.get('musica', {})
                    titulo_musica = musica_obj.get('titulo', 'Karaoke') if isinstance(musica_obj, dict) else str(musica_obj)
                    
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.text(f"{titulo_musica} ({p.get('cliente')})")
                    with col2:
                        estado_atual = p.get('estado')
                        st.text(f"Estado: {estado_atual}")
                    with col3:
                        if estado_atual == 'pendente':
                            if st.button("Aprovar", key=f"apr_{p.get('id')}"):
                                atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                                st.rerun()
                                
        if not auto_refresh:
            break
            
        time.sleep(4)
        st.rerun()

def show_client_screen():
    """Tela de Apresentação Principal (Palco) com Contagem Decrescente e Vídeo em Grande."""
    query_params = st.query_params
    provider_token = query_params.get("provider", None)

    if not provider_token:
        st.error("Tela inválida. Falta o parâmetro do prestador.")
        return

    st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffeb3b !important; }
    * { color: #ffeb3b !important; }
    .box-header {
        background: linear-gradient(90deg, #1a1a1a, #2c2c2c);
        border: 2px solid #ffeb3b;
        padding: 10px;
        text-align: center;
        border-radius: 8px;
        color: #ffeb3b !important;
        font-weight: bold;
        font-size: 18px;
        letter-spacing: 2px;
        margin-bottom: 15px;
    }
    .card-next {
        background: linear-gradient(135deg, #2b103a, #14081c);
        border: 2px solid #ffeb3b;
        padding: 15px;
        border-radius: 10px;
        color: #ffeb3b !important;
        text-align: center;
        margin-bottom: 15px;
    }
    .card-fila {
        background-color: #121212;
        border: 1px solid #ffeb3b;
        padding: 10px;
        border-radius: 8px;
        color: #ffeb3b !important;
        margin-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("📺 FFKaraoke — Palco Principal")
    st.markdown("---")

    try:
        pedidos = buscar_pedidos_prestador(provider_token)
        pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
        
        tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)
        pendentes = [p for p in pedidos_ativos if p.get("estado") == "pendente"]

        col_esquerda, col_direita = st.columns([1.1, 0.9])

        with col_esquerda:
            st.markdown('<div class="box-header">🎙️ FILA DE ESPERA</div>', unsafe_allow_html=True)
            
            if tocando_agora:
                cliente = tocando_agora.get("cliente", "Convidado")
                musica = tocando_agora.get("musica", {})
                titulo = musica.get("titulo", "Karaoke") if isinstance(musica, dict) else str(musica)
                
                st.markdown(f"""
                    <div class="card-next">
                        <div style="font-size: 14px; color: #ffeb3b; margin-bottom: 5px;">— A Seguir —</div>
                        <div style="font-size: 22px; font-weight: bold; color: #ffeb3b;">{str(titulo).upper()}</div>
                        <div style="font-size: 12px; color: #ffeb3b; margin-top: 5px;">Cliente: {cliente}</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div class="card-next">
                        <div style="font-size: 16px; color: #ffeb3b;">Nenhuma música de karaoke a tocar no momento.</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("**Próximos Pedidos na Fila:**")
            
            if not pendentes:
                st.info("A fila de karaoke está vazia.")
            else:
                for idx, p in enumerate(pendentes, start=1):
                    cliente_p = p.get("cliente", "Convidado")
                    musica_p = p.get("musica", {})
                    titulo_p = musica_p.get("titulo", "Música") if isinstance(musica_p, dict) else str(musica_p)
                    
                    st.markdown(f"""
                        <div class="card-fila">
                            <b>{idx}.</b> {titulo_p} <span style="font-size:11px; color:#ffeb3b;">({cliente_p})</span>
                        </div>
                    """, unsafe_allow_html=True)

        with col_direita:
            st.markdown('<div class="box-header">📺 TELA DE REPRODUÇÃO</div>', unsafe_allow_html=True)
            
            if tocando_agora:
                musica = tocando_agora.get("musica", {})
                url_cloudinary = musica.get("url_cloudinary") if isinstance(musica, dict) else None
                
                if url_cloudinary and str(url_cloudinary).startswith("http"):
                    # Efeito de contagem decrescente visual antes de abrir o vídeo
                    placeholder_contagem = st.empty()
                    for i in [3, 2, 1]:
                        placeholder_contagem.markdown(f"""
                            <div style="border: 2px solid #ffeb3b; border-radius: 10px; padding: 40px; text-align: center; background-color: #0d0d0d; min-height: 300px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                                <h2 style="color: #ffeb3b; margin-bottom: 10px;">A PREPARAR PALCO...</h2>
                                <h1 style="color: #ffeb3b; font-size: 80px; margin: 0;">{i}</h1>
                            </div>
                        """, unsafe_allow_html=True)
                        time.sleep(1)
                    placeholder_contagem.empty()

                    # Exibição do vídeo em tamanho grande ocupando a secção
                    st.markdown("<h3 style='text-align: center; color: #ffeb3b;'>🎤 A CANTAR AGORA</h3>", unsafe_allow_html=True)
                    st.video(url_cloudinary, autoplay=True)
                else:
                    st.warning("O link do vídeo do Cloudinary não foi encontrado para esta música.")
            else:
                st.markdown("""
                    <div style="border: 2px solid #ffeb3b; border-radius: 10px; padding: 40px; text-align: center; background-color: #0d0d0d; min-height: 300px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                        <div style="color: #ffeb3b; font-size: 45px; margin-bottom: 10px;">📺</div>
                        <span style='color: #ffeb3b; font-size: 16px;'>Aguardando o prestador selecionar um pedido na fila...</span>
                    </div>
                """, unsafe_allow_html=True)
        
        time.sleep(4)
        st.rerun()

    except Exception:
        st.error("Erro ao sincronizar com a base de dados em tempo real.")

    time.sleep(5)
    st.rerun()
