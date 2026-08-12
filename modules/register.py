import streamlit as st
from utils.db_manager import add_provider, get_all_providers
import uuid
import time

def show_register_page():
    # Remove o fundo da caixa central, deixando apenas a imagem geral de fundo e os estilos dos círculos rotativos
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
        
        /* Animações para os círculos de espera do microfone */
        @keyframes rotateLeft {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(-360deg); }
        }
        @keyframes rotateRight {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes pulseMic {
            0%, 100% { transform: scale(1); filter: drop-shadow(0 0 5px rgba(255,0,0,0.8)); }
            50% { transform: scale(1.08); filter: drop-shadow(0 0 15px rgba(255,0,0,1)); }
        }

        .loader-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin-top: 30px;
            margin-bottom: 20px;
            position: relative;
            height: 220px;
        }
        .mic-icon-center {
            position: absolute;
            font-size: 65px;
            animation: pulseMic 1.5s infinite ease-in-out;
            z-index: 10;
        }
        .circle-outer {
            position: absolute;
            width: 160px;
            height: 160px;
            border: 4px dashed #ff3333;
            border-radius: 50%;
            animation: rotateRight 8s linear infinite;
            border-top-color: transparent;
        }
        .circle-inner {
            position: absolute;
            width: 110px;
            height: 110px;
            border: 4px dashed #ff4d4d;
            border-radius: 50%;
            animation: rotateLeft 6s linear infinite;
            border-bottom-color: transparent;
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
                # Ecrã de espera com o microfone e os dois círculos tracejados vermelhos a rodar em sentidos opostos
                st.markdown("""
                    <div class="loader-container">
                        <div class="circle-outer"></div>
                        <div class="circle-inner"></div>
                        <div class="mic-icon-center">🎤</div>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<h3 style='text-align: center; color: #ff4d4d;'>A aguardar aprovação do Administrador...</h3>", unsafe_allow_html=True)
                st.info("Assim que o Administrador aprovar o seu pagamento e acesso, esta página atualizará automaticamente para o painel.")
                
                time.sleep(3)
                st.rerun()
