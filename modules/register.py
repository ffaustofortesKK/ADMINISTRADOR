import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

FIREBASE_URL = "https://ffkaraoke-default-rtdb.firebaseio.com"

# --- CÓDIGO DA PÁGINA DE REGISTO DO PRESTADOR ---
def show_register_page():
    st.markdown("""
        <style>
        .stApp {
            background: url('https://cdn.phototourl.com/free/2026-08-09-2e698cdf-874c-4072-805e-f3c6f992d562.png') no-repeat center center fixed !important;
            background-size: cover !important;
            color: #ffffff !important;
            font-weight: bold !important;
        }
        .block-container {
            background-color: transparent !important;
            max-width: 900px !important;
            margin: auto;
            padding: 2.5rem !important;
        }
        h1, h2, h3, h4, h5, h6, p, span, label, div {
            color: #ffffff !important;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
        }
        </style>
    """, unsafe_allow_html=True)

    _, col_centro, _ = st.columns([1, 6, 1])
    
    with col_centro:
        st.title("🎤 FFKaraoke - Registo de Prestador")
        st.write("Preencha os seus dados, indique o estabelecimento e escolha o tempo pretendido para solicitar o seu acesso.")

        if "token_gerado" not in st.session_state:
            st.session_state["token_gerado"] = None

        if not st.session_state["token_gerado"]:
            with st.form("form_register"):
                c1, c2 = st.columns(2)
                with c1:
                    nome = st.text_input("Nome")
                with c2:
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
                    if nome and telefone and estabelecimento:
                        nome_completo = f"{nome} {sobrenome}".strip()
                        token = str(uuid.uuid4()).replace("-", "")[:32]
                        dados_escolha = duracao_opcoes[duracao_escolhida]
                        hours = dados_escolha["horas"]
                        valor_pago = dados_escolha["valor"]
                        
                        payment_ref = f"Estabelecimento: {estabelecimento}"
                        
                        try:
                            add_provider(nome_completo, telefone, payment_ref, hours, token, amount_paid=valor_pago)
                            st.session_state["token_gerado"] = token
                            st.success("Pedido de permissão enviado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao guardar o registo: {e}")
                    else:
                        st.warning("Por favor, preencha todos os campos obrigatórios (Nome, Telefone e Estabelecimento/Restaurante).")

        if st.session_state["token_gerado"]:
            token_atual = st.session_state["token_gerado"]
            df = get_all_providers()
            
            aprovado = False
            recusado = False
            
            if not df.empty and 'token' in df.columns:
                prestador = df[df['token'] == token_atual]
                if not prestador.empty:
                    estado = int(prestador.iloc[0].get('approved', 0))
                    if estado == 1:
                        aprovado = True
                    elif estado == -1:
                        recusado = True

            st.markdown("---")
            
            if aprovado:
                st.success("🎉 O seu perfil foi aprovado pelo Administrador!")
                if st.button("🚀 Clique aqui para abrir o seu Painel de Prestador", type="primary"):
                    st.query_params["token"] = token_atual
                    if "page" in st.query_params:
                        del st.query_params["page"]
                    st.rerun()
            elif recusado:
                st.error("❌ O seu pedido de acesso foi recusado pelo Administrador.")
                st.warning("Por favor, verifique os dados ou o estabelecimento indicado e tente submeter um novo registo.")
                
                if st.button("🔄 Tentar Novamente / Novo Registo"):
                    st.session_state["token_gerado"] = None
                    st.rerun()
            else:
                st.warning("⏳ O seu registo foi enviado com sucesso e está a aguardar a aprovação do Administrador.")
                st.info("Assim que o Administrador aprovar, o botão de acesso aparecerá automaticamente aqui nesta mesma página.")
                
                time.sleep(3)
                st.rerun()
