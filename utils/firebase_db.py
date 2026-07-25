import requests

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

def get_musicas_cloudinary():
    """Busca a lista de músicas guardadas no Firebase (associadas ao Cloudinary)."""
    try:
        response = requests.get(f"{FIREBASE_URL}/musicas.json")
        if response.status_code == 200 and response.json():
            data = response.json()
            # Se estiver guardado como dicionário ou lista
            if isinstance(data, dict):
                return list(data.values())
            elif isinstance(data, list):
                return [m for m in data if m is not None]
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
            "estado": "pendente", # pendente / aprovado / terminado
            "timestamp": requests.post(f"{FIREBASE_URL}/timestamp.json", json={".sv": "timestamp"}).json().get("name")
        }
        response = requests.post(url, json=dados_pedido)
        return response.status_code == 200
    except Exception:
        return False
