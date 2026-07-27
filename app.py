import time
import requests
import urllib.parse
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from utils.db_manager import init_db, get_all_providers
from modules.admin import show_admin_panel
from modules.register import show_register_page
from modules.client import show_client_page

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
    """Atualiza o estado do pedido no Firebase."""
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}/{pedido_id}/estado.json"
        response = requests.put(url, json=novo_estado)
        return response.status_code == 200
    except Exception:
        return False

def show_provider_panel_custom(provider_token):
    """Painel personalizado do prestador."""
    st.markdown("### 🎤 Painel do Prestador — FF Karaoke")
    st.markdown("---")
    
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
                    musica_obj = p.get("musica", {})
                    titulo_musica = musica_obj.get("titulo", "Música") if isinstance(musica_obj, dict) else str(musica_obj)
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
                musica_obj = tocando_agora.get("musica", {})
                titulo_tocando = musica_obj.get("titulo", "Karaoke") if isinstance(musica_obj, dict) else str(musica_obj)
                st.success(f"🎵 A tocar agora: **{titulo_tocando}** (Cliente: {tocando_agora.get('cliente', 'Convidado')})")
                if st.button("⏹️ Terminar Música Atual", key=f"term_{tocando_agora.get('id')}"):
                    atualizar_estado_pedido(provider_token, tocando_agora.get('id'), 'terminado')
                    st.rerun()

            if not pendentes:
                st.write("Fila vazia.")
            else:
                for idx, p in enumerate(pendentes, start=1):
                    musica_obj = p.get("musica", {})
                    titulo_musica = musica_obj.get("titulo", "Música") if isinstance(musica_obj, dict) else str(musica_obj)
                    cliente_nome = p.get("cliente", "Convidado")
                    
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.write(f"**#{idx}** - {titulo_musica} *(Cliente: {cliente_nome})*")
                    with col_btn:
                        if st.button(f"▶️ Play #{idx}", key=f"btn_play_{p.get('id')}"):
                            if tocando_agora:
                                atualizar_estado_pedido(provider_token, tocando_agora.get('id'), 'terminado')
                            atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                            st.rerun()
        else:
            st.write("Fila vazia.")
            
    except Exception as e:
        st.error(f"Erro ao carregar os pedidos: {e}")

    time.sleep(4)
    st.rerun()

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

    try:
        response = requests.get(f"{FIREBASE_URL}/pedidos/{provider_token}.json")
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
            
            tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)
            
            if tocando_agora:
                musica = tocando_agora.get("musica", {})
                
                if isinstance(musica, dict):
                    titulo = musica.get("titulo", "Karaoke")
                    # Procura em todas as chaves possíveis onde o link real possa estar guardado
                    url_video = (
                        musica.get("url_cloudinary") or 
                        musica.get("url") or 
                        musica.get("link") or 
                        musica.get("secure_url") or
                        ""
                    )
                else:
                    titulo = str(musica)
                    url_video = ""
                
                st.markdown(f"<h2>A tocar: {titulo}</h2>", unsafe_allow_html=True)
                
                # Validação rigorosa: se não houver um link HTTP real guardado, avisamos para verificar o registo no Firebase
                if not url_video or "http" not in url_video:
                    st.error("❌ O objeto desta música no Firebase não contém um link válido do Cloudinary ('url_cloudinary'). O link gerado por título falhou porque o ficheiro não existe com esse nome exato na nuvem.")
                    st.info("💡 **Solução:** Garanta que ao selecionar a música no painel do cliente, o link direto do Cloudinary é gravado corretamente no Firebase.")
                else:
                    # Aplica a otimização se o link existir
                    if "/upload/" in url_video and "f_mp4" not in url_video:
                        url_video = url_video.replace("/upload/", "/upload/f_mp4,q_auto,vc_h264,ac_aac/")
                    
                    st.markdown(f"🔗 **Link Cloudinary:** [Abrir Vídeo]({url_video})", unsafe_allow_html=True)
                    
                    video_html = f"""
                    <div style="display: flex; justify-content: center; background: black; padding: 10px; width: 100%;">
                        <video width="100%" height="450px" controls autoplay playsinline style="object-fit: contain; background: black;">
                            <source src="{url_video}" type="video/mp4">
                            O seu navegador não suporta a reprodução deste vídeo.
                        </video>
                    </div>
                    """
                    components.html(video_html, height=500)
            else:
                st.info("A aguardar início de reprodução...")
        else:
            st.info("Nenhum pedido ativo na TV.")
    except Exception as e:
        st.error(f"Erro de sincronização: {e}")

    time.sleep(5)
    st.rerun()

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
