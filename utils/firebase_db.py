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
        dados_pedido = {
            "cliente": nome_cliente,
            "musica": musica,
            "estado": "pendente",
            "timestamp": requests.post(f"{FIREBASE_URL}/timestamp.json", json={".sv": "timestamp"}).json().get("name")
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
    """Painel completo do prestador com atualização automática na tela."""
    st.subheader("📺 Painel do Prestador — Fila de Reprodução")
    
    placeholder = st.empty()
    auto_refresh = st.toggle("Ativar atualização automática na tela", value=True)
    
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
                    st.success(f"🎵 **A Tocar Agora:** {tocando_agora.get('musica')} (Pedida por: {tocando_agora.get('cliente')})")
                    if st.button("Marcar como Terminado", key=f"term_{tocando_agora.get('id')}"):
                        atualizar_estado_pedido(provider_token, tocando_agora.get('id'), 'terminado')
                        st.rerun()
                
                st.write("---")
                st.write("**Próximos na Fila:**")
                for p in pedidos_ativos:
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.text(f"{p.get('musica')} ({p.get('cliente')})")
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
