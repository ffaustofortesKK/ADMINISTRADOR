import sys
import os

# Configuração estrita do caminho absoluto para evitar erros de importação
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

# Importações seguras com fallbacks para evitar crash total da aplicação
try:
    from utils.db_manager import init_db, get_all_providers
except Exception:
    def init_db(): pass
    def get_all_providers(): 
        import pandas as pd
        return pd.DataFrame(columns=['token', 'approved'])

try:
    from modules.admin import show_admin_panel
except Exception:
    def show_admin_panel(): st.error("Módulo 'modules.admin' não encontrado.")

try:
    from modules.register import show_register_page
except Exception:
    def show_register_page(): st.error("Módulo 'modules.register' não encontrado.")

try:
    from modules.client import show_client_page
except Exception:
    def show_client_page(): st.error("Módulo 'modules.client' não encontrado.")

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

st.set_page_config(
    page_title="FFKaraoke - Gestão de Acessos",
    page_icon="🎤",
    layout="wide"
)

try:
    init_db()
except Exception:
    pass

def atualizar_estado_pedido(provider_token, pedido_id, novo_estado):
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}/estado.json"
        response = requests.put(url, json=novo_estado, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

def terminar_todas_musicas_ativas(provider_token, pedidos):
    for p in pedidos:
        if p.get("estado") in ["aprovado", "pendente"]:
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
    st.markdown(f"<p style='color: #888; font-size: 13px;'>Token Ativo: <code>{provider_token}</code></p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Auto-refresh a cada 3 segundos para capturar novos pedidos instantaneamente
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
                <span style="font-size: 14px; color: #202124;">📎 <b>Link do Cliente:</b> <a href="{link_cliente}" target="_blank" rel="noopener noreferrer" style="color: #1a73e8; text-decoration: none;">{link_cliente}</a></span>
            </div>
            <div style="background-color: #e8f0fe; border: 1px solid #d2e3fc; padding: 10px 15px; border-radius: 8px; display: flex; align-items: center; justify-content: space-between;">
                <span style="font-size: 14px; color: #202124;">📺 <b>Link da TV:</b> <a href="{link_tv}" target="_blank" rel="noopener noreferrer" style="color: #1a73e8; text-decoration: none;">{link_tv}</a></span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎬 Fila de Pedidos Atual")

    try:
        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json?_t={time.time()}"
        response = requests.get(url_firebase, timeout=10)
        
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
            
            tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)
            pendentes = [p for p in pedidos_ativos if p.get("estado") == "pendente"]

            if pedidos_ativos:
                html_lista = '<div style="background-color: #111111; border: 2px solid #333333; padding: 15px; border-radius: 8px; color: #ffffff; max-width: 550px; font-family: monospace; font-size: 15px; margin-bottom: 20px;">'
                html_lista += '<div style="color: #4CAF50; font-weight: bold; margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px;">ESTADO DA FILA:</div>'
                for idx, p in enumerate(pedidos_ativos, start=1):
                    titulo_musica = limpar_nome_musica(p.get("musica", {}))
                    cliente_nome = p.get("cliente", "Convidado")
                    estado_atual = p.get("estado")
                    badge = "🎵 [A Tocar]" if estado_atual == "aprovado" else "⏳ [Pendente]"
                    cor_badge = "#4CAF50" if estado_atual == "aprovado" else "#FFC107"
                    html_lista += f'<div style="padding: 4px 0;"><b>{idx}.</b> {titulo_musica} <span style="color:#aaa; font-size:13px;">({cliente_nome})</span> <span style="color:{cor_badge}; font-size:12px; float:right;">{badge}</span></div>'
                html_lista += '</div>'
                st.markdown(html_lista, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="background-color: #111111; border: 2px solid #333333; padding: 15px; border-radius: 8px; color: #888; max-width: 550px; font-family: monospace; font-size: 15px; margin-bottom: 20px;">
                        <div>Nenhum pedido na lista neste momento. À espera de novos pedidos...</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 📋 Gestão de Fila e Controlo")

            if tocando_agora:
                titulo_tocando = limpar_nome_musica(tocando_agora.get("musica", {}))
                st.success(f"🎵 A tocar agora: **{titulo_tocando}** (Cliente: {tocando_agora.get('cliente', 'Convidado')})")
                if st.button("⏹️ Terminar Música Atual", key=f"term_{tocando_agora.get('id')}"):
                    terminar_todas_musicas_ativas(provider_token, pedidos)
                    st.success("Música terminada e tela limpa com sucesso!")
                    st.rerun()

            if not pendentes:
                st.write("Fila de pendentes vazia. Os pedidos feitos pelos clientes aparecerão aqui automaticamente.")
            else:
                st.write("### Pedidos Pendentes para Aprovar:")
                for idx, p in enumerate(pendentes, start=1):
                    titulo_musica = limpar_nome_musica(p.get("musica", {}))
                    cliente_nome = p.get("cliente", "Convidado")
                    
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.write(f"**Pedido** - {titulo_musica} *(Cliente: {cliente_nome})*")
                    with col_btn:
                        if st.button(f"▶️ Play", key=f"btn_play_{p.get('id')}"):
                            terminar_todas_musicas_ativas(provider_token, pedidos)
                            atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                            st.success(f"Música '{titulo_musica}' enviada para a tela!")
                            st.rerun()
        else:
            st.info("Nenhum pedido encontrado no Firebase para este prestador. Abra o link do cliente e envie uma música para testar.")
            
    except Exception as e:
        st.error(f"Erro ao carregar os pedidos do Firebase: {e}")

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

    st.markdown("""
        <script>
            setTimeout(function() {
                window.location.reload();
            }, 3000);
        </script>
    """, unsafe_allow_html=True)

    st.title("📺 FFKaraoke — Diretor Palco")
    st.markdown("---")

    try:
        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json?_t={time.time()}"
        response = requests.get(url_firebase, timeout=10)
        
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
            
            tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)
            
            if tocando_agora:
                musica = tocando_agora.get("musica", {})
                
                if isinstance(musica, dict):
                    titulo = musica.get("titulo", musica.get("nome", "Karaoke"))
                    url_video = musica.get("url_cloudinary", "") or musica.get("url", "")
                else:
                    titulo = str(musica)
                    url_video = ""
                
                titulo_limpo = limpar_nome_musica(titulo)
                url_video = obter_url_video_cloudinary(musica, titulo_limpo)
                cantor_name = tocando_agora.get('cliente', 'Convidado')
                
                st.markdown(f"<h2>A tocar: {titulo_limpo} <span style='font-size:16px; color:#aaa;'>(Cantor: {cantor_name})</span></h2>", unsafe_allow_html=True)
                st.caption(f"Link do Vídeo: {url_video}")

                video_html = f"""
                <div style="display: flex; justify-content: center; background: black; padding: 10px; width: 100%;">
                    <video id="karaoke-player" width="100%" height="500px" controls autoplay playsinline style="object-fit: contain; background: black;">
                        <source src="{url_video}" type="video/mp4">
                        O seu navegador não suporta a reprodução deste vídeo.
                    </video>
                </div>
                <script>
                    var video = document.getElementById('karaoke-player');
                    video.play().catch(function(error) {{
                        console.log("Autoplay bloqueado pelo browser:", error);
                    }});
                    video.onerror = function() {{
                        console.error("Erro ao carregar o vídeo do Cloudinary. Verifique se o ficheiro existe na nuvem com o nome correto.");
                    }};
                </script>
                """
                components.html(video_html, height=580)
            else:
                st.info("📺 Fila em espera. A aguardar que o prestador aprove um pedido...")
                if pedidos_ativos:
                    html_lista_geral = '<div style="background-color: #111111; border: 2px solid #333333; padding: 20px; border-radius: 10px; color: #ffffff; font-family: monospace; font-size: 18px; max-width: 800px; margin: 20px auto;">'
                    html_lista_geral += '<div style="color: #FFC107; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #444; padding-bottom: 5px;">PRÓXIMOS NA FILA:</div>'
                    for idx, p in enumerate(pedidos_ativos, start=1):
                        t_limpo = limpar_nome_musica(p.get("musica", {}))
                        c_nome = p.get("cliente", "Convidado")
                        html_lista_geral += f'<div style="padding: 6px 0;"><b>{idx}.</b> <span style="color: #4CAF50;">{t_limpo}</span> <span style="color: #aaa; font-size: 14px;">(Cantor: {c_nome})</span></div>'
                    html_lista_geral += '</div>'
                    st.markdown(html_lista_geral, unsafe_allow_html=True)
        else:
            st.info("Nenhum pedido ativo na TV no momento.")
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
            else:
                show_provider_panel_custom(token)
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
