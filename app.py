import time
import requests
import streamlit as st
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
    """Painel personalizado estruturado exatamente conforme a imagem enviada."""
    st.markdown("### 🎤 Bem-vindo, ff fffff!")
    st.markdown("---")
    
    link_cliente = f"/?page=client_register&provider={provider_token}"
    link_tela = f"/?page=client_screen&provider={provider_token}"

    # --- BLOCOS DOS LINKS (CLIENTE E TV) ---
    st.markdown(f"""
        <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 25px; max-width: 800px;">
            <div style="display: flex; align-items: center; background-color: #e8f0fe; border: 1px solid #d2e3fc; padding: 10px 15px; border-radius: 6px;">
                <span style="font-weight: bold; margin-right: 10px;">📎 Cliente:</span>
                <a href="{link_cliente}" target="_blank" style="color: #1a0dab; text-decoration: underline; font-size: 14px;">{link_cliente}</a>
            </div>
            
            <div style="display: flex; align-items: center; background-color: #e8f0fe; border: 1px solid #d2e3fc; padding: 10px 15px; border-radius: 6px;">
                <span style="font-weight: bold; margin-right: 10px;">📺 TV:</span>
                <a href="{link_tela}" target="_blank" style="color: #1a0dab; text-decoration: underline; font-size: 14px;">{link_tela}</a>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- PLAYLIST / FILA DE PEDIDOS CHEGADOS ---
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

            # Caixa com a lista numerada tal como no seu exemplo
            lista_html = ""
            for idx, p in enumerate(pedidos_ativos, start=1):
                musica_obj = p.get("musica", {})
                titulo_musica = musica_obj.get("titulo", "Música") if isinstance(musica_obj, dict) else str(musica_obj)
                cliente_nome = p.get("cliente", "Convidado")
                lista_html += f"<div style='padding: 4px 0;'><b>{idx}-</b> {titulo_musica} <span style='color: #666; font-size: 12px;'>({cliente_nome})</span></div>"

            st.markdown(f"""
                <div style="border: 2px solid #000; background-color: #fff; padding: 15px; border-radius: 4px; max-width: 400px; margin-bottom: 20px;">
                    {lista_html if lista_html else "Fila vazia."}
                </div>
            """, unsafe_allow_html=True)

            if tocando_agora:
                musica_obj = tocando_agora.get("musica", {})
                titulo_tocando = musica_obj.get("titulo", "Karaoke") if isinstance(musica_obj, dict) else str(musica_obj)
                
                st.markdown(f"**A tocar agora:** {titulo_tocando}")
                if st.button("⏹️ Terminar Música Atual", key=f"term_{tocando_agora.get('id')}"):
                    atualizar_estado_pedido(provider_token, tocando_agora.get('id'), 'terminado')
                    st.rerun()

            st.markdown("---")
            st.markdown("### 📋 Gestão de Fila")

            if not pendentes:
                st.write("Fila vazia.")
            else:
                for idx, p in enumerate(pendentes, start=1):
                    musica_obj = p.get("musica", {})
                    titulo_musica = musica_obj.get("titulo", "Música") if isinstance(musica_obj, dict) else str(musica_obj)
                    
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.write(f"#{idx} - {titulo_musica} ({p.get('cliente', 'Convidado')})")
                    with col_btn:
                        if st.button(f"▶️ Play", key=f"btn_play_{p.get('id')}"):
                            if tocando_agora:
                                atualizar_estado_pedido(provider_token, tocando_agora.get('id'), 'terminado')
                            atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                            st.rerun()
        else:
            st.markdown("""
                <div style="border: 2px solid #000; background-color: #fff; padding: 15px; border-radius: 4px; max-width: 400px; margin-bottom: 20px;">
                    Fila vazia.
                </div>
            """, unsafe_allow_html=True)
            st.write("Fila vazia.")
            
    except Exception as e:
        st.error(f"Erro ao carregar os pedidos: {e}")

    st.markdown("---")
    st.markdown("### ⚠️ Pedidos Manuais (Atenção)")
    st.info("Nenhum pedido manual pendente.")

    time.sleep(4)
    st.rerun()

def show_client_screen():
    query_params = st.query_params
    provider_token = query_params.get("provider", None)

    if not provider_token:
        st.error("Tela inválida. Falta o parâmetro do prestador.")
        return

    st.markdown("""
    <style>
    .stApp { background-color: #000000; color: white; }
    .box-header {
        background: linear-gradient(90deg, #1a1a1a, #2c2c2c);
        border: 2px solid #d4af37;
        padding: 10px;
        text-align: center;
        border-radius: 8px;
        color: #d4af37;
        font-weight: bold;
        font-size: 18px;
        letter-spacing: 2px;
        margin-bottom: 15px;
    }
    .card-next {
        background: linear-gradient(135deg, #2b103a, #14081c);
        border: 2px solid #9c27b0;
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 15px;
    }
    .card-fila {
        background-color: #121212;
        border: 1px solid #d4af37;
        padding: 10px;
        border-radius: 8px;
        color: #ffffff;
        margin-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("📺 FFKaraoke — Palco Principal")
    st.markdown("---")

    try:
        response = requests.get(f"{FIREBASE_URL}/pedidos/{provider_token}.json")
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
            
            tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)
            pendentes = [p for p in pedidos_ativos if p.get("estado") == "pendente"]

            col_esquerda, col_direita = st.columns([1.1, 0.9])

            with col_esquerda:
                st.markdown('<div class="box-header">🎙️ FILA DE ESPERA</div>', unsafe_allow_html=True)
                
                if tocando_agora:
                    cliente = tocando_agora.get("cliente", "Convidado")
                    musica = tocando_agora.get("musica", {})
                    titulo = musica.get("titulo", "Karaoke") if isinstance(musica, dict) else str(musica)
                    
                    st.markdown(f"""
                        <div class="card-next">
                            <div style="font-size: 14px; color: #e0b0ff; margin-bottom: 5px;">— A Seguir —</div>
                            <div style="font-size: 22px; font-weight: bold; color: #ffeb3b;">{str(titulo).upper()}</div>
                            <div style="font-size: 12px; color: #ccc; margin-top: 5px;">Cliente: {cliente}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div class="card-next">
                            <div style="font-size: 16px; color: #888;">Nenhuma música de karaoke a tocar no momento.</div>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("**Próximos Pedidos na Fila:**")
                
                if not pendentes:
                    st.info("A fila de karaoke está vazia.")
                else:
                    for idx, p in enumerate(pendentes, start=1):
                        cliente_p = p.get("cliente", "Convidado")
                        musica_p = p.get("musica", {})
                        titulo_p = musica_p.get("titulo", "Música") if isinstance(musica_p, dict) else str(musica_p)
                        
                        st.markdown(f"""
                            <div class="card-fila">
                                <b>{idx}.</b> {titulo_p} <span style="font-size:11px; color:#aaa;">({cliente_p})</span>
                            </div>
                        """, unsafe_allow_html=True)

            with col_direita:
                st.markdown('<div class="box-header">📺 VÍDEO CLIPE (FUNDO)</div>', unsafe_allow_html=True)
                
                if tocando_agora:
                    pedido_id_atual = tocando_agora.get("id")
                    musica = tocando_agora.get("musica", {})
                    
                    url_cloudinary = ""
                    if isinstance(musica, dict):
                        for k, v in musica.items():
                            if isinstance(v, str) and (v.startswith("http://") or v.startswith("https://")):
                                url_cloudinary = v
                                break
                        
                        if not url_cloudinary:
                            for campo in ["url_cloudinary", "url", "link", "secure_url"]:
                                val = musica.get(campo, "")
                                if isinstance(val, str) and (val.startswith("http://") or val.startswith("https://")):
                                    url_cloudinary = val
                                    break
                    elif isinstance(musica, str) and (musica.startswith("http://") or musica.startswith("https://")):
                        url_cloudinary = musica
                    
                    if not url_cloudinary and isinstance(musica, dict):
                        for k, v in musica.items():
                            if isinstance(v, str) and ("res.cloudinary.com" in v or ".mp4" in v):
                                url_cloudinary = v if v.startswith("http") else f"https://{v}"
                                break

                    if url_cloudinary and "cloudinary.com" in url_cloudinary:
                        url_cloudinary = url_cloudinary.rsplit(".", 1)[0] + ".mp4"

                    if url_cloudinary and str(url_cloudinary).startswith("http"):
                        if "ultimo_pedido_tocando" not in st.session_state:
                            st.session_state.ultimo_pedido_tocando = None

                        if st.session_state.ultimo_pedido_tocando != pedido_id_atual:
                            placeholder_contagem = st.empty()
                            for i in [3, 2, 1]:
                                placeholder_contagem.markdown(f"""
                                    <div style="border: 2px solid #d4af37; border-radius: 10px; padding: 40px; text-align: center; background-color: #0d0d0d; min-height: 280px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                                        <h2 style="color: #ffeb3b; margin-bottom: 10px;">A PREPARAR PALCO...</h2>
                                        <h1 style="color: #d4af37; font-size: 80px; margin: 0;">{i}</h1>
                                    </div>
                                """, unsafe_allow_html=True)
                                time.sleep(1)
                            placeholder_contagem.empty()
                            st.session_state.ultimo_pedido_tocando = pedido_id_atual

                        try:
                            st.video(url_cloudinary, format="video/mp4", autoplay=True, muted=True)
                        except Exception:
                            st.error(f"Erro ao carregar o player de vídeo com o link: {url_cloudinary}")
                    else:
                        st.warning(f"⚠️ **Atenção:** O campo de vídeo guardado no Firebase para esta música (`{musica}`) não contém um link web URL válido do Cloudinary.")
                else:
                    st.session_state.ultimo_pedido_tocando = None
                    st.markdown("""
                        <div style="border: 2px solid #d4af37; border-radius: 10px; padding: 20px; text-align: center; background-color: #0d0d0d; min-height: 280px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                            <div style="color: #d4af37; font-size: 35px; margin-bottom: 10px;">📺</div>
                            <span style='color: #aaa;'>Aguardando o prestador selecionar um vídeo clipe no painel de controle...</span>
                        </div>
                    """, unsafe_allow_html=True)
            
            time.sleep(5)
            st.rerun()

        st.info("📺 A aguardar o próximo artista... O ecrã atualizará automaticamente assim que o prestador aprovar um pedido.")
        
    except Exception:
        st.error("Erro ao sincronizar com a base de dados em tempo real.")

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

        if "token" in query_params:
            token = query_params["token"]
            df = get_all_providers()
            
            if not df.empty and 'token' in df.columns:
                prestador = df[df['token'] == token]
                
                if not prestador.empty:
                    row = prestador.iloc[0]
                    if row.get('approved', 0) == 1:
                        now = datetime.now()
                        exp_str = row.get('expires_at')
                        
                        if exp_str:
                            try:
                                exp_time = datetime.strptime(exp_str, "%Y-%m-%d %H:%M:%S")
                                if now < exp_time:
                                    show_provider_panel_custom(token)
                                    return
                                else:
                                    st.error("❌ O seu tempo de acesso expirou.")
                                    return
                            except Exception:
                                show_provider_panel_custom(token)
                                return
                        else:
                            show_provider_panel_custom(token)
                            return
                    else:
                        st.warning("⏳ O seu registo foi efetuado, mas ainda aguarda a aprovação do Administrador.")
                        return
            
            st.error("Token de acesso inválido ou não encontrado.")
            return

        st.sidebar.title("Painel Admin")
        senha = st.sidebar.text_input("Palavra-passe", type="password")
        
        if senha == "admin123":
            st.sidebar.success("Sessão Iniciada")
            show_admin_panel()
        else:
            st.title("🔒 FFKaraoke - Área Restrita")
            st.write("Introduza a palavra-passe de administrador na barra lateral para gerir os pedidos e acessos.")
            if senha:
                st.error("Palavra-passe incorreta.")
                
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar a aplicação: {e}")

if __name__ == "__main__":
    main()
