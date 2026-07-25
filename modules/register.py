import streamlit as st
from utils.db_manager import add_provider, get_all_providers
import uuid
import time

def show_register_page():
    st.title("🎤 FFKaraoke - Registo de Prestador")
    st.write("Preencha os seus dados, a referência de pagamento e escolha o tempo pretendido para solicitar o seu acesso.")

    if "token_gerado" not in st.session_state:
        st.session_state["token_gerado"] = None

    if not st.session_state["token_gerado"]:
        with st.form("form_register"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome")
            with col2:
                sobrenome = st.text_input("Sobrenome")
                
            telefone = st.text_input("Número de Telefone")
            payment_ref = st.text_input("Referência de Pagamento / Nº de Comprovativo")
            
            duracao_opcoes = {"2 Horas": 2, "4 Horas": 4, "6 Horas": 6, "12 Horas": 12, "24 Horas": 24}
            duracao_escolhida = st.selectbox("Duração Pretendida", list(duracao_opcoes.keys()))
            
            submitted = st.form_submit_button("Enviar Permissão")
            
            if submitted:
                if nome and telefone and payment_ref:
                    nome_completo = f"{nome} {sobrenome}".strip()
                    token = str(uuid.uuid4()).replace("-", "")[:32]
                    hours = duracao_opcoes[duracao_escolhida]
                    
                    try:
                        add_provider(nome_completo, telefone, payment_ref, hours, token)
                        st.session_state["token_gerado"] = token
                        st.success("Pedido de permissão enviado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao guardar o registo: {e}")
                else:
                    st.warning("Por favor, preencha todos os campos obrigatórios.")
    
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
            
            # Botão interativo que abre o painel na MESMA página/aba instantaneamente
            if st.button("🚀 Clique aqui para abrir o seu Painel de Prestador", type="primary"):
                st.query_params["token"] = token_atual
                if "page" in st.query_params:
                    del st.query_params["page"]
                st.rerun()
        else:
            st.warning("⏳ O seu registo foi enviado com sucesso e está a aguardar a aprovação do Administrador.")
            st.info("Assim que o Administrador aprovar, o botão de acesso aparecerá automaticamente aqui nesta mesma página.")
            
            time.sleep(3)
            st.rerun()
