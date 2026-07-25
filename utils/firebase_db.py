import requests

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
