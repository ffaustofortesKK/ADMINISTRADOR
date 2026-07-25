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
                
                # Cria o pedido e obtém o token único gerado
                token = create_provider_request(nome_completo, duracao_opcao, payment_ref.strip())
                
                # Guardar o token na sessão para redirecionar de imediato
                st.session_state.new_token = token
                st.session_state.registered_name = nome_completo
                st.success("Pedido de permissão enviado com sucesso!")
            else:
                st.error("Por favor, preencha todos os campos obrigatórios.")

    # Se o registo foi submetido com sucesso nesta sessão, mostrar o link direto para o painel dele
    if "new_token" in st.session_state and st.session_state.new_token:
        st.markdown("---")
        st.success("🎉 O seu registo foi registado com sucesso!")
        st.info("Guarde o link abaixo ou clique nele para aceder ao seu painel de prestador. Assim que o Administrador aprovar no painel, o seu programa abrirá automaticamente aqui:")
        
        token_url = f"https://appadm.streamlit.app/?token={st.session_state.new_token}"
        st.code(token_url, language="text")
        
        st.markdown(f"[🔗 Clique aqui para abrir o seu Painel de Prestador]({token_url})")
