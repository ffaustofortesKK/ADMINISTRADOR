import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import uuid

FIREBASE_URL = "https://ffkaraoke-default-rtdb.firebaseio.com"

# Função auxiliar para buscar prestadores (caso não exista no seu utils)
def get_all_providers():
    try:
        response = requests.get(f"{FIREBASE_URL}/providers.json", timeout=10)
        if response.status_code == 200 and response.json():
            return pd.DataFrame.from_dict(response.json(), orient='index')
    except Exception:
        pass
    return pd.DataFrame()

# --- CÓDIGO DA PÁGINA DE REGISTO DO PRESTADOR ---
def show_register_page():
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

    # Verifica se já existe um token pendente na sessão
    token_sessao = st.session_state.get("token_pendente_prestador") or st.session_state.get("token_gerado")

    if token_sessao:
        token_atual = token_sessao
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
                if "token_gerado" in st.session_state:
                    del st.session_state["token_gerado"]
                if "nome_pendente_prestador" in st.session_state:
                    del st.session_state["nome_pendente_prestador"]
                st.rerun()
            return

        # Se foi aprovado
        if aprovado:
            st.markdown(f"""
                <div style="text-align: center; padding: 40px; font-family: monospace;">
                    <h1 style="color: #FFC107; font-size: 38px; margin-bottom: 20px; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">SEJA BEM VINDO, {nome_prestador_temp.upper()}!</h1>
                    <p style="color: #ffffff; font-size: 20px; font-weight: bold; margin-bottom: 30px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9);">O seu registo foi aprovado com sucesso!</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 Entrar no Painel", use_container_width=True):
                st.query_params["token"] = token_atual
                if "page" in st.query_params:
                    del st.query_params["page"]
                if "token_pendente_prestador" in st.session_state:
                    del st.session_state["token_pendente_prestador"]
                st.rerun()
            return
        
        # Enquanto estiver pendente - Ecrã de espera com animação
        url_logotipo = "https://cdn.phototourl.com/free/2026-08-03-8b13edf5-0257-491d-ab78-f0d5329ffc15.jpg"
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
        
        time.sleep(3)
        st.rerun()
        return

    # Formulário de Registo Customizado
    st.markdown("<h1>🎤 FFKaraoke - Registo de Prestador</h1>", unsafe_allow_html=True)
    st.markdown("<p>Preencha os seus dados, indique o estabelecimento e escolha a duração pretendida para solicitar o seu acesso.</p>", unsafe_allow_html=True)
    
    with st.form("form_registo_prestador_custom"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome")
        with col2:
            sobrenome = st.text_input("Sobrenome")
            
        telefone = st.text_input("Número de Telefone")
        estabelecimento = st.text_input("Estabelecimento / Restaurante")
        
        duracao_opcoes = {
            "2 Horas - 12 Mil Kwanzas": {"horas": 2, "valor": 12000.0},
            "3 Horas - 15 Mil Kwanzas": {"horas": 3, "valor": 15000.0},
            "4 Horas - 20 Mil Kwanzas": {"horas": 4, "valor": 20000.0}
        }
        
        duracao_escolhida = st.selectbox("Contrato", list(duracao_opcoes.keys()))
        submitted = st.form_submit_button("Enviar Permissão")
        
        if submitted:
            if not nome or not telefone or not estabelecimento:
                st.error("Por favor, preencha todos os campos obrigatórios (Nome, Telefone e Estabelecimento).")
            else:
                nome_completo = f"{nome} {sobrenome}".strip()
                token_gerado = str(uuid.uuid4()).replace("-", "")[:32]
                dados_escolha = duracao_opcoes[duracao_escolhida]
                hours = dados_escolha["horas"]
                valor_pago = dados_escolha["valor"]
                
                payment_ref = f"Estabelecimento: {estabelecimento}"
                
                # Tenta usar a função global se existir, caso contrário faz o put direto no Firebase
                try:
                    from utils.db_manager import add_provider
                    add_provider(nome_completo, telefone, payment_ref, hours, token_gerado, amount_paid=valor_pago)
                    st.session_state["token_pendente_prestador"] = token_gerado
                    st.session_state["token_gerado"] = token_gerado
                    st.session_state["nome_pendente_prestador"] = nome_completo
                    st.success("Pedido de permissão enviado com sucesso!")
                    st.rerun()
                except Exception:
                    dados_reg = {
                        "nome_prestador": nome_completo,
                        "name": nome_completo,
                        "telefone": telefone,
                        "phone": telefone,
                        "estabelecimento": estabelecimento,
                        "payment_ref": payment_ref,
                        "tempo_plano": duracao_escolhida,
                        "hours": hours,
                        "amount_paid": valor_pago,
                        "approved": 0,
                        "token": token_gerado,
                        "data_registo": str(datetime.now())
                    }
                    try:
                        requests.put(f"{FIREBASE_URL}/prestadores_pendentes/{token_gerado}.json", json=dados_reg, timeout=10)
                        requests.put(f"{FIREBASE_URL}/providers/{token_gerado}.json", json=dados_reg, timeout=10)
                        st.session_state["token_pendente_prestador"] = token_gerado
                        st.session_state["token_gerado"] = token_gerado
                        st.session_state["nome_pendente_prestador"] = nome_completo
                        st.rerun()
                    except Exception as err:
                        st.error(f"Erro ao submeter registo: {err}")
