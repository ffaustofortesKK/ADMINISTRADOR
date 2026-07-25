import streamlit as st
from utils.db_manager import add_provider, get_all_providers
import uuid

def show_register_page():
    st.title("🎤 FFKaraoke - Registo de Prestador")
    st.write("Preencha os seus dados, a referência de pagamento e escolha o tempo pretendido para solicitar o seu acesso.")

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
                    st.success("Pedido de permissão enviado com sucesso!")
                    st.session_state["token_gerado"] = token
                    st.session_state["registado_sucesso"] = True
                except Exception as e:
                    st.error(f"Erro ao guardar o registo: {e}")
            else:
                st.warning("Por favor, preencha todos os campos obrigatórios.")

    # Se o registo foi submetido com sucesso, exibe apenas a mensagem limpa e o link de acesso direto
    if st.session_state.get("registado_sucesso", False):
        token_atual = st.session_state.get("token_gerado", "")
        link_painel = f"https://appadm.streamlit.app/?token={token_atual}"
        
        st.markdown("---")
        st.success("O seu registo foi efetuado com sucesso!")
        st.markdown(f"👉 **[Clique aqui para abrir o seu Painel de Prestador]({link_painel})**")
