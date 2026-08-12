import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import uuid

FIREBASE_URL = "https://ffkaraoke-default-rtdb.firebaseio.com"

def get_all_providers():
    try:
        response = requests.get(f"{FIREBASE_URL}/providers.json", timeout=10)
        if response.status_code == 200 and response.json():
            return pd.DataFrame.from_dict(response.json(), orient='index')
    except Exception:
        pass
    return pd.DataFrame()

def custom_show_register_page():
    url_fundo_painel = "https://cdn.phototourl.com/free/2026-08-03-694a4a2e-9914-4da8-93b2-87538a4805ab.png"
    url_logotipo = "https://cdn.phototourl.com/free/2026-08-03-8b13edf5-0257-491d-ab78-f0d5329ffc15.jpg"
    
    st.markdown(f"""
    <style>
    .stApp {{
        background: url("{url_fundo_painel}") no-repeat center center fixed !important;
        background-size: cover !important;
    }}
    
    .block-container {{
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
        padding-left: 4rem !important;
        padding-right: 4rem !important;
        background: rgba(0, 0, 0, 0.90) !important;
        border-radius: 12px;
        margin-top: 2rem;
        margin-bottom: 2rem;
        border: 4px solid #FFC107 !important;
        color: #ffffff !important;
    }}

    h1, h2, h3, h4, h5, h6, p, label, span, div {{
        color: #ffffff !important;
        font-weight: bold !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
    }}
    
    .stTextInput input, .stSelectbox select, div[data-baseweb="select"] {{
        background-color: #111111 !important;
        color: #ffffff !important;
        border: 2px solid #FFC107 !important;
        font-weight: bold !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    if "token_pendente_prestador" in st.session_state and st.session_state["token_pendente_prestador"]:
        token_atual = st.session_state["token_pendente_prestador"]
        nome_prestador_temp = st.session_state.get("nome_pendente_prestador", "Prestador")
        
        aprovado = False
        recusado = False
        
        try:
            df_prov = get_all_providers()
            if not df_prov.empty and 'token' in df_prov.columns:
                match = df_prov[df_prov['token'] == token_atual]
                if not match.empty:
                    estado = int(match.iloc[0].get('approved', 0))
                    if estado == 1:
                        aprovado = True
                    elif estado == -1:
                        recusado = True
        except Exception:
            pass

        # Se foi recusado pelo administrador
        if recusado:
            st.markdown(f"""
                <div style="text-align: center; padding: 40px; font-family: monospace;">
                    <h1 style="color: #ff3333; font-size: 38px; margin-bottom: 20px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">PEDIDO RECUSADO</h1>
                    <p style="color: #ffffff; font-size: 20px; font-weight: bold; margin-bottom: 30px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Lamentamos, mas o seu pedido de acesso foi recusado pelo Administrador.</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 Submeter Novo Registo", use_container_width=True):
                if "token_pendente_prestador" in st.session_state:
                    del st.session_state["token_pendente_prestador"]
                if "nome_pendente_prestador" in st.session_state:
                    del st.session_state["nome_pendente_prestador"]
                st.rerun()
            return

        # Se foi aprovado — Redireciona diretamente para o painel de trabalho definindo o parâmetro na URL
        if aprovado:
            st.markdown(f"""
                <div style="text-align: center; padding: 40px; font-family: monospace;">
                    <h1 style="color: #FFC107; font-size: 38px; margin-bottom: 20px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">SEJA BEM VINDO, {nome_prestador_temp.upper()}!</h1>
                    <p style="color: #ffffff; font-size: 20px; font-weight: bold; margin-bottom: 30px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">O seu registo foi aprovado com sucesso!</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Limpa o estado pendente e injeta o token do prestador na URL para abrir o painel correto
            if "token_pendente_prestador" in st.session_state:
                del st.session_state["token_pendente_prestador"]
            if "nome_pendente_prestador" in st.session_state:
                del st.session_state["nome_pendente_prestador"]
                
            st.query_params["prestador"] = token_atual
            st.rerun()
            return
        
        # Enquanto estiver pendente (Ecrã de espera com polling automático)
        st.markdown(f"""
            <style>
            @keyframes spinMic {{
                0% {{ transform: rotate(0deg) scale(1); }}
                50% {{ transform: rotate(180deg) scale(1.15); filter: drop-shadow(0 0 15px #FFC107); }}
                100% {{ transform: rotate(360deg) scale(1); }}
            }}
            @keyframes marqueeWait {{
                0% {{ transform: translateX(100vw); }}
                100% {{ transform: translateX(-100%); }}
            }}
            .waiting-container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 30px 20px;
                text-align: center;
                font-family: monospace;
            }}
            .logo-wait {{
                width: 130px;
                height: 130px;
                border-radius: 50%;
                border: 4px solid #FFC107;
                object-fit: cover;
                margin-bottom: 25px;
                box-shadow: 0 0 25px rgba(255, 193, 7, 0.4);
            }}
            .mic-spinning {{
                font-size: 70px;
                display: inline-block;
                animation: spinMic 2.5s infinite linear;
                margin: 20px 0;
            }}
            .wait-footer {{
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100vw;
                background: #111;
                border-top: 4px solid #FFC107;
                padding: 12px 0;
                z-index: 99999;
                overflow: hidden;
                white-space: nowrap;
            }}
            .wait-track {{
                display: inline-block;
                white-space: nowrap;
                animation: marqueeWait 18s linear infinite;
                color: #FFC107;
                font-size: 16px;
                font-weight: bold;
                font-family: monospace;
                text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
            }}
            </style>

            <div class="waiting-container">
                <img src="{url_logotipo}" class="logo-wait" />
                <h2 style="color: #FFC107; margin-bottom: 10px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">REGISTO SUBMETIDO COM SUCESSO!</h2>
                <p style="color: #ffffff; font-size: 15px; max-width: 600px; margin: 0 auto; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Aguardando validação e aprovação pelo Administrador...</p>
                <div class="mic-spinning">🎤</div>
                <p style="color: #ffffff; font-size: 14px; margin-top: 15px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">Token do Pedido: <b>{token_atual}</b></p>
            </div>

            <div class="wait-footer">
                <div class="wait-track">
                    Seja bem vindo ao Grupo FF Karaoke, aguarde aprovação do seu registo ou ligue para 921204050 para confirmar. &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; • &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Seja bem vindo ao Grupo FF Karaoke, aguarde aprovação do seu registo ou ligue para 921204050 para confirmar.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Faz polling a cada 3 segundos para detetar automaticamente se o admin aprovou
        time.sleep(3)
        st.rerun()
        return

    if "original_show_register_page" in globals() and original_show_register_page:
        try:
            original_show_register_page()
            return
        except Exception:
            pass

    # Formulário de Registo (só executa se NÃO houver token pendente na sessão)
    st.markdown("<h1>🎤 FFKaraoke - Registo de Prestador</h1>", unsafe_allow_html=True)
    st.markdown("<p>Preencha os seus dados e escolha a duração pretendida para solicitar o seu acesso.</p>", unsafe_allow_html=True)
    
    with st.form("form_registo_prestador_custom"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome")
        with col2:
            sobrenome = st.text_input("Sobrenome")
            
        telefone = st.text_input("Número de Telefone")
        duracao = st.selectbox(
            "Duração Pretendida", 
            options=[
                "2 Horas - 12 Mil Kwanzas", 
                "3 Horas - 15 Mil Kwanzas", 
                "4 Horas - 20 Mil Kwanzas"
            ]
        )
        submitted = st.form_submit_button("Enviar Permissão")
        if submitted:
            if not nome or not telefone:
                st.error("Por favor, preencha todos os campos obrigatórios.")
            else:
                referencia_fake = "Plano Selecionado Direto"
                try:
                    from utils.db_manager import save_provider_request
                    token_gerado = save_provider_request(nome, sobrenome, telefone, referencia_fake, duracao)
                    st.session_state["token_pendente_prestador"] = token_gerado
                    st.session_state["nome_pendente_prestador"] = f"{nome} {sobrenome}".strip()
                    st.rerun()
                except Exception as e:
                    import uuid
                    token_gerado = str(uuid.uuid4())[:8]
                    nome_completo = f"{nome} {sobrenome}".strip()
                    dados_reg = {
                        "nome_prestador": nome_completo,
                        "telefone": telefone,
                        "referencia": referencia_fake,
                        "tempo_plano": duracao,
                        "approved": 0,
                        "token": token_gerado,
                        "data_registo": str(datetime.now())
                    }
                    try:
                        requests.put(f"https://ffkaraoke-default-rtdb.firebaseio.com/prestadores_pendentes/{token_gerado}.json", json=dados_reg, timeout=10)
                        st.session_state["token_pendente_prestador"] = token_gerado
                        st.session_state["nome_pendente_prestador"] = nome_completo
                        st.rerun()
                    except Exception as err:
                        st.error(f"Erro ao submeter registo: {err}")
