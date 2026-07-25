import requests

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

def get_musicas_cloudinary():
    """Busca o catálogo de músicas de forma flexível para detetar qualquer nome de campo."""
    try:
        response = requests.get(f"{FIREBASE_URL}/catalogo.json")
        if response.status_code == 200 and response.json():
            data = response.json()
            
            # Converter dados para uma lista de dicionários utilizáveis
            itens = []
            if isinstance(data, dict):
                itens = [v for v in data.values() if isinstance(v, dict)]
            elif isinstance(data, list):
                itens = [m for m in data if m is not None and isinstance(m, dict)]
            
            musicas_formatadas = []
            for item in itens:
                # Tenta encontrar automaticamente o título em qualquer campo possível
                titulo = (
                    item.get('titulo') or 
                    item.get('nome') or 
                    item.get('title') or 
                    item.get('musica') or 
                    list(item.values())[0] if item else "Música sem título"
                )
                
                # Tenta encontrar o link do Cloudinary em qualquer campo possível
                url = (
                    item.get('url_cloudinary') or 
                    item.get('url') or 
                    item.get('link') or 
                    item.get('video') or 
                    ""
                )
                
                musicas_formatadas.append({
                    "titulo": str(titulo),
                    "url_cloudinary": str(url)
                })
                
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
            "estado": "pendente", # pendente / aprovado / terminado
            "timestamp": requests.post(f"{FIREBASE_URL}/timestamp.json", json={".sv": "timestamp"}).json().get("name")
        }
        response = requests.post(url, json=dados_pedido)
        return response.status_code == 200
    except Exception:
        return False
