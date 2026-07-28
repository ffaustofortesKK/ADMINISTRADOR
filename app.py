import sys
import os

# Garante rigorosamente que a raiz do projeto e os subdiretórios estão no path do Python
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
utils_path = os.path.join(current_dir, "utils")
if utils_path not in sys.path:
    sys.path.insert(0, utils_path)
modules_path = os.path.join(current_dir, "modules")
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

import time
import requests
import urllib.parse
import streamlit as st
import streamlit.components.v1 as components

# Importação segura de utilitários da base de dados
try:
    from utils.db_manager import init_db, get_all_providers
except ImportError:
    try:
        from db_manager import init_db, get_all_providers
    except Exception:
        def init_db(): pass
        def get_all_providers(): 
            import pandas as pd
            return pd.DataFrame(columns=['token', 'approved'])

# Importações seguras dos módulos
try:
    from modules.admin import show_admin_panel
except ImportError:
    def show_admin_panel(): st.error("Módulo 'modules.admin' não encontrado.")

try:
    from modules.register import show_register_page
except ImportError:
    def show_register_page(): st.error("Módulo 'modules.register' não encontrado.")

try:
    from modules.client import show_client_page
except ImportError:
    def show_client_page(): st.error("Módulo 'modules.client' não encontrado.")

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

st.set_page_config(
    page_title="FFKaraoke - Gestão de Acessos",
    page_icon="🎤",
    layout="wide"
)

try:
    init_db()
except Exception as e:
    st.error(f"Erro ao inicializar a base de dados: {e}")

def atualizar_estado_pedido(provider_token, pedido_id, novo_estado):
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}/estado.json"
        response = requests.put(url, json=novo_estado)
        return response.status_code == 200
    except Exception:
        return False

def terminar_todas_musicas_ativas(provider_token, pedidos):
    for p in pedidos:
        if p.get("estado") == "aprovado":
            atualizar_estado_pedido(provider_token, p.get("id"), "terminado")

def limpar_nome_musica(musica_raw):
    if isinstance(musica_raw, dict):
        titulo = musica_raw.get("titulo", musica_raw.get("nome", "Karaoke"))
    else:
        titulo = str(musica_raw)
    
    titulo = titulo.strip('"\'')
    if titulo.lower().endswith('.cdg'):
        titulo = titulo[:-4]
    return titulo.strip()

def obter_url_video_cloudinary(musica_obj, titulo_limpo):
    if isinstance(musica_obj, dict):
        url_direta = musica_obj.get("url_cloudinary", "") or musica_obj.get("url", "")
        if url_direta and "http" in url_direta:
            if "res.cloudinary.com" in url_direta and "/upload/" in url_direta and "f_auto,q_auto" not in url_direta:
                return url_direta.replace("/upload/", "/upload/f_auto,q_auto/")
            return url_direta

    cloud_name = "yhwgjh7g"
    titulo_lower = titulo_limpo.lower()
    
    if "mulheres e mulheres" in titulo_lower or "landrick" in titulo_lower:
        return f"https://res.cloudinary.com/{cloud_name}/video/upload/f_auto,q_auto/v1784592601/Karaoke_H%C3%81_MULHERES_E_MULHERES_-_Landrick_rnomfr.mp4"
    elif "nani ta quieto" in titulo_lower:
        return f"https://res.cloudinary.com/{cloud_name}/video/upload/f_auto,q_auto/Nani_Ta_Quieto_f35hpj.mp4"
    
    encoded_title = urllib.parse.quote(titulo_limpo + ".mp4")
    return f"https://res.cloudinary.com/{cloud_name}/video/upload/f_auto,q_auto/{encoded_title}"

def show_provider_panel_custom(provider_token):
    st.markdown("### 🎤 Painel do Prestador — FF Karaoke")
    st.markdown("---")
    
    # Atualiza automaticamente a página do prestador a cada 3 segundos para novos pedidos caírem sozinhos
    st.markdown("""
        <script>
            setTimeout(function() {
                window.location.reload();
            }, 3000);
        </script>
    """, unsafe_allow_html=True)

    link_cliente = f"/?page=client_register&prestador={provider_token}"
    link_tv = f"/?page=client_screen&prestador={provider_token}"

    st.markdown(f"""
        <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 25px; max-width: 850px;">
            <div style="background-color: #e8f0fe; border: 1px solid #d2e3fc; padding: 10px 15px; border-radius: 8px; display: flex; align-items: center; justify-content: space-between;">
                <span style="font-size: 14px; color: #202124;">📎 <b>Cliente:</b> <a href="{link_cliente}" target="_blank" style="color: #1a73e8; text-decoration: none;">{link_cliente}</a></span>
            </div>
            <div style="background-color: #e8f0fe; border: 1px solid #d2e3fc; padding: 10px 15px; border-radius: 8px; display: flex; align-items: center; justify-content: space-between;">
                <span style="font-size: 14px; color: #202124;">📺 <b>TV:</b> <a href="{link_tv}" target="_blank" style="color: #1a73e8; text-decoration: none;">{link_tv}</a></span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎬 Playlist de Vídeos Clipes (Fundo da TV)")

    try:
        response = requests.get(f"{FIREBASE_URL}/pedidos/{provider_token}.json")
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
            
            tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)
            pendentes = [p for p in pedidos_ativos if p.get("estado") == "pendente"]

            if pedidos_ativos:
                html_lista = '<div style="background-color: #000000; border: 3px solid #000000; padding: 15px; border-radius: 6px; color: #ffffff; max-width: 450px; font-family: monospace; font-size: 15px; margin-bottom: 20px;">'
                for idx, p in enumerate(pedidos_ativos, start=1):
                    titulo_musica = limpar_nome_musica(p.get("musica", {}))
                    cliente_nome = p.get("cliente", "Convidado")
                    html_lista += f'<div style="padding: 3px 0;"><b>{idx}-</b> {titulo_musica} <span style="color:#aaa; font-size:12px;">({cliente_nome})</span></div>'
                html_lista += '</div>'
                st.markdown(html_lista, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="background-color: #000000; border: 3px solid #000000; padding: 15px; border-radius: 6px; color: #888; max-width: 450px; font-family: monospace; font-size: 15px; margin-bottom: 20px;">
                        <div>Nenhum pedido na lista.</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 📋 Gestão de Fila")

            if tocando_agora:
                titulo_tocando = limpar_nome_musica(tocando_agora.get("musica", {}))
                st.success(f"🎵 A tocar agora: **{titulo_tocando}** (Cliente: {tocando_agora.get('cliente', 'Convidado')})")
                if st.button("⏹️ Terminar Música Atual", key=f"term_{tocando_agora.get('id')}"):
                    atualizar_estado_pedido(provider_token, tocando_agora.get('id'), 'terminado')
                    st.rerun()

            if not pendentes:
                st.write("Fila vazia. À espera de novos pedidos...")
            else:
                for idx, p in enumerate(pendentes, start=1):
                    titulo_musica = limpar_nome_musica(p.get("musica", {}))
                    cliente_nome = p.get("cliente", "Convidado")
                    
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.write(f"**#{idx}** - {titulo_musica} *(Cliente: {cliente_nome})*")
                    with col_btn:
                        if st.button(f"▶️ Play #{idx}", key=f"btn_play_{p.get('id')}"):
                            terminar_todas_musicas_ativas(provider_token, pedidos)
                            atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                            st.success(f"Música '{titulo_musica}' enviada para a tela!")
                            st.rerun()
        else:
            st.write("Fila vazia. À espera de novos pedidos...")
            
    except Exception as e:
        st.error(f"Erro ao carregar os pedidos: {e}")

def show_client_screen():
    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider", None)

    if not provider_token:
        st.error("Tela inválida. Falta o parâmetro do prestador.")
        return

    st.markdown("""
    <style>
    .stApp { background-color: #000000; color: white; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📺 FFKaraoke — Diretor Palco")
    st.markdown("---")

    # Atualiza a tela automaticamente a cada 3 segundos para abrir o vídeo assim que clicar em Play
    st.markdown("""
        <script>
            setTimeout(function() {
                window.location.reload();
            }, 3000);
        </script>
    """, unsafe_allow_html=True)

    try:
        response = requests.get(f"{FIREBASE_URL}/pedidos/{provider_token}.json")
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
            
            tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)
            
            if tocando_agora:
                musica_obj = tocando_agora.get("musica", {})
                titulo_limpo = limpar_nome_musica(musica_obj)
                url_video = obter_url_video_cloudinary(musica_obj, titulo_limpo)
                
                st.markdown(f"<h2>A tocar: {titulo_limpo}</h2>", unsafe_allow_html=True)

                video_html = f"""
                <div style="display: flex; justify-content: center; background: black; padding: 10px; width: 100%;">
                    <video id="karaoke-player" width="100%" height="500px" controls autoplay playsinline style="object-fit: contain; background: black;">
                        <source src="{url_video}" type="video/mp4">
                        <source src="{url_video}" type="video/webm">
                        O seu navegador não suporta a reprodução deste vídeo.
                    </video>
                </div>
                <script>
                    var video = document.getElementById('karaoke-player');
                    video.play().catch(function(error) {{
                        console.log("Autoplay bloqueado pelo browser:", error);
                    }});
                </script>
                """
                components.html(video_html, height=580)
            else:
                st.info("A aguardar início de reprodução... Selecione 'Play' no painel do prestador.")
        else:
            st.info("Nenhum pedido ativo na TV.")
    except Exception as e:
        st.error(f"Erro de sincronização: {e}")

def main():
    try:
        query_params = st.query_params
        
        if "page" in query_params and query_params["page"] == "register":
            show_register_page()
            return

        if "page" in query_params and query_params["page"] == "client_register":
            show_client_page()
            return

        if "page" in query_params and query_params["page"] == "client_screen":
            show_client_screen()
            return

        token = query_params.get("prestador") or query_params.get("token") or query_params.get("provider")
        
        if token:
            df = get_all_providers()
            if df.empty or 'token' not in df.columns or not (df['token'] == token).any():
                show_provider_panel_custom(token)
                return
                
            prestador = df[df['token'] == token]
            if not prestador.empty:
                row = prestador.iloc[0]
                if row.get('approved', 1) == 1:
                    show_provider_panel_custom(token)
                    return
                else:
                    st.warning("⏳ O seu registo aguarda aprovação do Administrador.")
                    return
            
        st.sidebar.title("Panel Admin")
        senha = st.sidebar.text_input("Palavra-passe", type="password")
        
        if senha == "admin123":
            st.sidebar.success("Sessão Iniciada")
            show_admin_panel()
        else:
            st.title("🔒 FFKaraoke - Área Restrita")
            st.write("Introduza a palavra-passe de administrador na barra lateral para gerir os acessos ou aceda através do link do seu painel de prestador.")
                
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar a aplicação: {e}")

if __name__ == "__main__":
    main()
