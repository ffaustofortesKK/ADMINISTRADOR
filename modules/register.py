import streamlit as st
import uuid
import time
import sqlite3
import pandas as pd

# Funções de Base de Dados integradas diretamente para evitar erros de caminhos em falta
def get_connection():
    return sqlite3.connect('database.db', check_same_thread=False)

def get_all_providers():
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM providers", conn)
        return df
    except Exception:
        # Se a tabela ainda não existir, retorna um DataFrame vazio com as colunas necessárias
        return pd.DataFrame(columns=['id', 'name', 'phone', 'payment_ref', 'expires_at', 'token', 'approved', 'amount_paid'])
    finally:
        conn.close()

def add_provider(name, phone, payment_ref, hours, token, amount_paid=0.0):
    conn = get_connection()
    cursor = conn.cursor()
    # Cria a tabela caso ela não exista
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            payment_ref TEXT,
            expires_at TEXT,
            token TEXT,
            approved INTEGER DEFAULT 0,
            amount_paid REAL DEFAULT 0.0
        )
    ''')
    
    # Calcula a data de expiração com base nas horas selecionadas
    from datetime import datetime, timedelta
    expires_at = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO providers (name, phone, payment_ref, expires_at, token, approved, amount_paid)
        VALUES (?, ?, ?, ?, ?, 0, ?)
    ''', (name, phone, payment_ref, expires_at, token, amount_paid))
    
    conn.commit()
    conn.close()

def reject_provider(token):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE providers SET approved = -1 WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def show_register_page():
    # Remove o fundo da caixa central, deixando apenas a imagem geral de fundo
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
        
        /* Animações para os círculos de espera */
        @keyframes spinLeft {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(-360deg); }
        }
        @keyframes spinRight {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes pulseMic {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        .waiting-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 30px;
            text-align: center;
        }
        
        .circles-wrapper {
            position: relative;
            width: 180px;
            height: 180px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 25px;
        }
        
        .circle-red {
            position: absolute;
            width: 170px;
            height: 170px;
            border: 4px dashed #ff4d4d;
            border-radius: 50%;
            animation: spinLeft 8s linear infinite;
        }
        
        .circle-yellow {
            position: absolute;
            width: 130px;
            height: 130px;
            border: 4px dashed #FFC107;
            border-radius: 50%;
            animation: spinRight 6s linear infinite;
        }
        
        .mic-icon {
            font-size: 60px;
            z-index: 2;
            animation: pulseMic 1.5s ease-in-out infinite;
        }
        </style>
    """, unsafe_allow_html=True)

    _, col_centro, _ = st.columns([1, 6, 1])
    
    with col_centro:
        st.title("Cadastramento do Prestador")
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
                        nome_completo = f"{nome} {sobrenome} ({estabelecimento})".strip()
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
            if not df.empty and 'token' in df.columns:
                prestador = df[df['token'] == token_atual]
                if not prestador.empty:
                    if int(prestador.iloc[0].get('approved', 0)) == 1:
                        aprovado = True

            st.markdown("---")
            
            if aprovado:
                st.success("🎉 O seu perfil foi aprovado pelo Administrador!")
                
                if st.button("🚀 Clique aqui para abrir o seu Painel de Prestador", type="primary"):
                    st.query_params["token"] = token_atual
                    if "page" in st.query_params:
                        del st.query_params["page"]
                    st.rerun()
            else:
                # Ecrã de espera com o microfone e os círculos rotativos
                st.markdown("""
                    <div class="waiting-container">
                        <div class="circles-wrapper">
                            <div class="circle-red"></div>
                            <div class="circle-yellow"></div>
                            <div class="mic-icon">🎤</div>
                        </div>
                        <h3 style="color: #FFC107; margin-bottom: 10px;">Aguardando Aprovação</h3>
                        <p style="color: #ffffff; font-size: 15px;">O seu registo foi enviado com sucesso e está a aguardar a validação do Administrador.</p>
                        <p style="color: #aaa; font-size: 13px;">Assim que for aprovado, esta página atualizar-se-á automaticamente.</p>
                    </div>
                """, unsafe_allow_html=True)
                
                time.sleep(3)
                st.rerun()
