import streamlit as st
from utils.db_manager import create_provider_request

def show_register_page():
    st.title("🎤 FFKaraoke - Registo de Prestador")
    st.write("Preencha os seus dados, a referência de pagamento e escolha o tempo pretendido para solicitar o seu acesso.")

    with st.form("form_auto_registo"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome")
        with col2:
            sobrenome = st.text_input("Sobrenome")
            
        telefone = st.text_input("Número de Telefone")
        
        # Novo campo de Referência de Pagamento
        payment_ref = st.text_input("Referência de Pagamento / Nº de Comprovativo")
        
        duracao_opcao = st.selectbox(
            "Duração Pretendida",
            options=[2, 4],
            format_func=lambda x: f"{x} Horas"
        )

        submitted = st.form_submit_button("Enviar Permissão")

        if submitted:
            if nome.strip() and sobrenome.strip() and telefone.strip() and payment_ref.strip():
                nome_completo = f"{nome.strip()} {sobrenome.strip()} ({telefone.strip()})"
                
                create_provider_request(nome_completo, duracao_opcao, payment_ref.strip())
                
                st.success("Pedido de permissão enviado com sucesso!")
                st.info("O administrador irá analisar e aprovar o seu acesso em breve após validação do pagamento.")
            else:
                st.error("Por favor, preencha todos os campos obrigatórios (Nome, Sobrenome, Telefone e Referência de Pagamento).")
