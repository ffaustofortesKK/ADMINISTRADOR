import requests

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

def get_musicas_cloudinary():
    """Busca o catálogo de músicas e depura a resposta."""
    try:
        response = requests.get(f"{FIREBASE_URL}/catalogo.json")
        print("STATUS CODE:", response.status_code)
        print("DADOS BRUTOS DO FIREBASE:", response.json())
        
        if response.status_code == 200 and response.json():
            data = response.json()
            
            itens = []
            if isinstance(data, dict):
                itens = [v for v in data.values() if isinstance(v, dict)]
            elif isinstance(data, list):
                itens = [m for m in data if m is not None and isinstance(m, dict)]
            
            musicas_formatadas = []
            for item in itens:
                titulo = (
                    item.get('titulo') or 
                    item.get('nome') or 
                    item.get('title') or 
                    item.get('musica') or 
                    "Música sem título"
                )
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
            
            print("MÚSICAS FORMATADAS:", musicas_formatadas)
            return musicas_formatadas
        return []
    except Exception as e:
        print("ERRO NA REQUISIÇÃO:", e)
        return []

def enviar_pedido_cliente(provider_token, nome_cliente, musica):
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
