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
import cloudinary
import cloudinary.api
import cloudinary.uploader
import cloudinary.search

# Configuração do Cloudinary com as suas credenciais oficiais
cloudinary.config(
    cloud_name="yhwgjh7g",
    api_key="852434629995691",
    api_secret="TU_ejil7wKYY15xHjDcRVfbk6Ow",
    secure=True
)

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

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

st.set_page_config(
    page_title="FFKaraoke - Painel do Cliente",
    page_icon="🎤",
    layout="wide"
)

# --- BLOQUEIO TOTAL E RADICAL DO BOTÃO GERENCIAR APLICATIVO E ELEMENTOS CLOUD ---
st.markdown("""
    <style>
    div[data-testid="stToolbar"], header, footer, 
    div[data-testid="stDecoration"], #MainMenu, 
    .stAppViewerBadge, div[class*="viewerBadge"], 
    iframe[src*="analytics"], div[class*="settings"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    </style>
""", unsafe_allow_html=True)

try:
    init_db()
except Exception:
    pass

def carregar_catalogo_musicas():
    musicas = []
    try:
        resultado = cloudinary.search.Search()\
            .expression('resource_type:video AND asset_folder=karaoke')\
            .max_results(500)\
            .execute()
        for r in resultado.get("resources", []):
            url_secure = r.get("secure_url", "")
            if url_secure and "/upload/" in url_secure and "f_auto,q_auto" not in url_secure:
                url_secure = url_secure.replace("/upload/", "/upload/f_auto,q_auto/")
            filename = r.get("filename", "") or r.get("public_id", "").split("/")[-1]
            if filename.lower().endswith('.cdg'):
                filename = filename[:-4]
            musicas.append({"titulo": filename, "url": url_secure})
    except Exception:
        pass
    
    if not musicas:
        # Fallback local se Cloudinary falhar
        try:
            res_alt = cloudinary.api.resources(resource_type="video", type="upload", max_results=200)
            for r in res_alt.get("resources", []):
                public_id = r.get("public_id", "")
                if "karaoke" in public_id.lower():
                    url_secure = r.get("secure_url", "")
                    if url_secure and "/upload/" in url_secure and "f_auto,q_auto" not in url_secure:
                        url_secure = url_secure.replace("/upload/", "/upload/f_auto,q_auto/")
                    filename = public_id.split("/")[-1]
                    musicas.append({"titulo": filename, "url": url_secure})
        except Exception:
            pass
            
    return musicas

def enviar_pedido_firebase(provider_token, cliente_nome, musica_obj):
    try:
        novo_pedido = {
            "cliente": cliente_nome,
            "musica": musica_obj,
            "estado": "pendente",
            "timestamp": int(time.time() * 1000)
        }
        url = f"{FIREBASE_URL}/pedidos/{provider_token}.json"
        res = requests.post(url, json=novo_pedido, timeout=10)
        return res.status_code == 200
    except Exception:
        return False

def obter_pedidos_prestador(provider_token):
    try:
        url = f"{FIREBASE_URL}/pedidos/{provider_token}.json?_t={time.time()}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            data = res.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
            return pedidos_ativos
    except Exception:
        pass
    return []

@st.fragment(run_every=3)
def renderizar_painel_cliente_por_prestador(provider_token):
    st.markdown("""
        <style>
            .stApp { background-color: #0b0f19; color: #ffffff; }
            .main-title { color: #ffffff; font-family: monospace; font-size: 26px; font-weight: bold; margin-bottom: 5px; display: flex; align-items: center; gap: 10px; }
            .subtitle { color: #9ca3af; font-family: monospace; font-size: 14px; margin-bottom: 25px; }
            .footer-box {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px 20px;
                margin-top: 40px;
                font-family: monospace;
                font-size: 13px;
                color: #e2e8f0;
                display: flex;
                flex-direction: column;
                gap: 6px;
                max-width: 420px;
            }
            .status-card {
                background: #111827;
                border: 2px solid #FFC107;
                border-radius: 12px;
                padding: 30px 20px;
                text-align: center;
                margin-top: 20px;
                box-shadow: 0 0 20px rgba(255, 193, 7, 0.2);
            }
            @keyframes bounceMic {
                0%, 100% { transform: translateY(0) rotate(0deg); }
                50% { transform: translateY(-8px) rotate(5deg); }
            }
            .mic-icon-big {
                font-size: 70px;
                display: inline-block;
                animation: bounceMic 1s infinite ease-in-out;
                margin: 15px 0;
            }
        </style>
    """, unsafe_allow_html=True)

    # Verificar se o cliente já tem um pedido ativo nesta sessão
    pedido_ativo_id = st.session_state.get(f"pedido_id_{provider_token}")
    cliente_nome_sessao = st.session_state.get(f"cliente_nome_{provider_token}", "")

    pedidos_atuais = obter_pedidos_prestador(provider_token)
    
    # Encontrar a posição do pedido do cliente na fila ativa
    posicao_encontrada = None
    estado_atual = None
    if pedido_ativo_id:
        for idx, p in enumerate(pedidos_atuais, start=1):
            if p.get("id") == pedido_ativo_id:
                posicao_encontrada = idx
                estado_atual = p.get("estado")
                break

    # Se o pedido foi concluído ou removido, limpa a sessão
    if pedido_ativo_id and not posicao_encontrada:
        st.session_state.pop(f"pedido_id_{provider_token}", None)
        st.rerun()

    if posicao_encontrada is not None:
        # TELA EXATA SOLICITADA QUANDO O CLIENTE FAZ O PEDIDO
        col_esq, col_dir = st.columns([1, 1])
        
        with col_esq:
            st.markdown('<div class="main-title">🔍 Pesquisar Música</div>', unsafe_allow_html=True)
            st.markdown('<div class="subtitle">Digite o nome da música ou artista:</div>', unsafe_allow_html=True)
            st.text_input("", placeholder="Ex: Landrick, Nani...", disabled=True, key="input_disabled_search")
            
            # Caixa de rodapé idêntica à referência visual
            st.markdown("""
                <div class="footer-box">
                    <div>🛍️ <b>Instagram:</b> ff.karaoke</div>
                    <div>📞 <b>Contacto para Eventos Privados:</b> 955099159</div>
                    <div>💬 <b>WhatsApp:</b> 955099159</div>
                </div>
            """, unsafe_allow_html=True)

        with col_dir:
            st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: flex-end; gap: 8px; margin-top: 10px;">
                    <span style="font-size: 24px;">🎤</span>
                    <span style="color: #4CAF50; font-family: monospace; font-size: 22px; font-weight: bold;">Encontra-se na posição {posicao_encontrada}º</span>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("""
                <div class="status-card">
                    <div class="mic-icon-big">🎙️</div>
                    <div style="color: #FFC107; font-family: monospace; font-size: 18px; font-weight: bold; margin-top: 10px;">Aguarde pela sua vez</div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 Atualizar / Fazer Novo Pedido", key="btn_cancelar_pedido"):
                st.session_state.pop(f"pedido_id_{provider_token}", None)
                st.rerun()

    else:
        # TELA NORMAL DE PESQUISA E PEDIDO DE MÚSICA
        col_esq, col_dir = st.columns([1, 1])
        
        with col_esq:
            st.markdown('<div class="main-title">🔍 Pesquisar Música</div>', unsafe_allow_html=True)
            st.markdown('<div class="subtitle">Digite o nome da música ou artista:</div>', unsafe_allow_html=True)
            
            with st.form(key="form_pedido_cliente"):
                cliente_nome = st.text_input("Seu Nome / Apelido:", value=cliente_nome_sessao, placeholder="Digite o seu nome...")
                termo_busca = st.text_input("Pesquisa de Música:", placeholder="Ex: Landrick, Nani...")
                
                lista_musicas = carregar_catalogo_musicas()
                
                # Filtrar músicas com base no termo digitado
                musicas_filtradas = []
                if termo_busca:
                    termo_lower = termo_busca.lower()
                    musicas_filtradas = [m for m in lista_musicas if termo_lower in m['titulo'].lower()]
                else:
                    musicas_filtradas = lista_musicas[:50] # Mostrar primeiras 50 por defeito

                escolha_musica_label = "Selecione a música na lista abaixo:"
                opcoes_musicas = {m['titulo']: m for m in musicas_filtradas}
                
                musica_selecionada_titulo = st.selectbox(
                    escolha_musica_label, 
                    options=list(opcoes_musicas.keys()) if opcoes_musicas else ["Nenhuma música encontrada"]
                )
                
                submitted_pedido = st.form_submit_button("🎤 Pedir Música")
                
                if submitted_pedido:
                    if not cliente_nome.strip():
                        st.error("Por favor, insira o seu nome antes de fazer o pedido.")
                    elif not opcoes_musicas or musica_selecionada_titulo == "Nenhuma música encontrada":
                        st.error("Por favor, selecione uma música válida.")
                    else:
                        musica_obj = opcoes_musicas[musica_selecionada_titulo]
                        st.session_state[f"cliente_nome_{provider_token}"] = cliente_nome
                        
                        sucesso = enviar_pedido_firebase(provider_token, cliente_nome, musica_obj)
                        if sucesso:
                            time.sleep(0.5)
                            # Obter o ID do pedido recém-criado para fixar na tela
                            novos_pedidos = obter_pedidos_prestador(provider_token)
                            if novos_pedidos:
                                # O último pedido do cliente na lista
                                meu_pedido = [p for p in novos_pedidos if p.get("cliente") == cliente_nome]
                                if meu_pedido:
                                    st.session_state[f"pedido_id_{provider_token}"] = meu_pedido[-1].get("id")
                            st.success("Pedido enviado com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao enviar o pedido. Tente novamente.")

            st.markdown("""
                <div class="footer-box">
                    <div>🛍️ <b>Instagram:</b> ff.karaoke</div>
                    <div>📞 <b>Contacto para Eventos Privados:</b> 955099159</div>
                    <div>💬 <b>WhatsApp:</b> 955099159</div>
                </div>
            """, unsafe_allow_html=True)

        with col_dir:
            st.markdown("""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; border: 2px dashed #334155; border-radius: 12px; padding: 40px; text-align: center; margin-top: 30px;">
                    <div style="font-size: 60px; margin-bottom: 15px;">🎵</div>
                    <h3 style="color: #FFC107; font-family: monospace; margin-bottom: 10px;">FF KARAOKE CLOUD</h3>
                    <p style="color: #9ca3af; font-family: monospace; font-size: 14px; max-width: 300px; line-height: 1.5;">Pesquise a sua música favorita, insira o seu nome e envie o seu pedido diretamente para a fila do evento!</p>
                </div>
            """, unsafe_allow_html=True)

def show_client_page_custom():
    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider", None)

    if not provider_token:
        st.error("Link de cliente inválido. Falta o parâmetro do prestador.")
        return

    renderizar_painel_cliente_por_prestador(provider_token)

def main():
    try:
        query_params = st.query_params
        
        if "page" in query_params and query_params["page"] == "client_register":
            show_client_page_custom()
            return
            
        # Caso acedido diretamente sem rota específica
        token = query_params.get("prestador") or query_params.get("provider")
        if token:
            renderizar_painel_cliente_por_prestador(token)
        else:
            st.error("Parâmetro de prestador em falta. Utilize o link oficial fornecido pelo prestador.")
            
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar a página: {e}")

if __name__ == "__main__":
    main()
