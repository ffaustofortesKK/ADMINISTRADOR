import requests

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

def get_musicas_cloudinary():
    """Busca o catálogo de músicas de forma universal e tolerante a qualquer formato no Firebase."""
    try:
        response = requests.get(f"{FIREBASE_URL}/catalogo.json")
        if response.status_code == 200 and response.json():
            data = response.json()
            
            musicas_formatadas = []
            
            # Caso 1: O Firebase devolve um dicionário (ex: {"id1": {...}, "id2": {...}})
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, dict):
                        titulo = v.get('titulo') or v.get('nome') or v.get('title') or v.get('musica') or k
                        url = v.get('url_cloudinary') or v.get('url') or v.get('link') or v.get('video') or ""
                        musicas_formatadas.append({"titulo": str(titulo), "url_cloudinary": str(url)})
                    elif isinstance(v, list):
                        for sub_v in v:
                            if isinstance(sub_v, dict):
                                titulo = sub_v.get('titulo') or sub_v.get('nome') or sub_v.get('title') or "Música"
                                url = sub_v.get('url_cloudinary') or sub_v.get('url') or sub_v.get('link') or ""
                                musicas_formatadas.append({"titulo": str(titulo), "url_cloudinary": str(url)})
                                
            # Caso 2: O Firebase devolve uma lista direta
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        titulo = item.get('titulo') or item.get('nome') or item.get('title') or item.get('musica') or "Música"
                        url = item.get('url_cloudinary') or item.get('url') or item.get('link') or item.get('video') or ""
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
