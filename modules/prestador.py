import time
import requests
import streamlit as st

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

# --- Funções de Suporte e Integração com Firebase / Cloudinary ---

def limpar_nome_musica(musica_field):
    if isinstance(musica_field, dict):
        return (
            musica_field.get("titulo")
            or musica_field.get("nome")
            or musica_field.get("title")
            or "Música sem título"
        )
    return str(musica_field) if musica_field else "Música sem título"

def atualizar_estado_pedido(token, pedido_id, novo_estado):
    try:
        requests.patch(
            f"{FIREBASE_URL}/pedidos/{token}/{pedido_id}.json",
            json={"estado": novo_estado},
            timeout=10
        )
    except Exception as e:
        print(f"Erro ao atualizar estado do pedido: {e}")

def terminar_todas_musicas_ativas(token, pedidos):
    for p in pedidos:
        if p.get("estado") == "aprovado":
            atualizar_estado_pedido(token, p.get("id"), "terminado")

def obter_video_fundo(token):
    try:
        response = requests.get(f"{FIREBASE_URL}/config/{token}/video_fundo.json", timeout=10)
        if response.status_code == 200:
            return response.json() or ""
    except Exception:
        pass
    return ""

def definir_video_fundo(token, url):
    try:
        requests.put(f"{FIREBASE_URL}/config/{token}/video_fundo.json", json=url, timeout=10)
    except Exception as e:
        print(f"Erro ao definir vídeo de fundo: {e}")

def listar_videos_pasta_clipes():
    # Certifique-se de ligar aqui a sua integração ao Cloudinary se já a tiver configurada noutra parte
    # Exemplo de estrutura esperada: [{"nome": "Clipe 1", "url": "https://..."}, ...]
    return []
