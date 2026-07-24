import streamlit as st
from utils.db_manager import create_provider_link

def show_register_page():
    st.title("🎤 FFKaraoke - Registo de Prestador")
    st.write("Preencha os seus dados e escolha o tempo pretendido para solicitar o seu acesso à plataforma.")

    with st.form("form_auto_registo"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome")
        with col2:
            sobrenome = st.text_input("Sobrenome")
            
        telefone = st.text_input("Número de Telefone")
        
        # Opção de duração solicitada pelo utilizador
        duracao_opcao = st.selectbox(
            "Duração Pretendida",
            options=[2, 4],
            format_func=lambda x: f"{x} Horas"
        )

        submitted = st.form_submit_button("Enviar Permissão")

        if submitted:
            if nome.strip() and sobrenome.strip() and telefone.strip():
                nome_completo = f"{nome.strip()} {sobrenome.strip()} ({telefone.strip()})"
                
                # Cria o registo na base de dados com a duração escolhida (2 ou 4 horas)
                token = create_provider_link(nome_completo, duracao_opcao)
                
                st.success("Pedido de permissão enviado com sucesso!")
                st.markdown("### O seu Token de Acesso:")
                st.code(token, language="text")
                st.info("Guarde este token num local seguro para conseguir aceder à plataforma quando aprovado.")
            else:
                st.error("Por favor, preencha todos os campos obrigatórios (Nome, Sobrenome e Telefone).")
