import streamlit as st
from utils.db_manager import init_db
from modules.admin import show_admin_panel
from modules.register import show_register_page

st.set_page_config(
    page_title="FFKaraoke - Gestão de Acessos",
    page_icon="🎤",
    layout="wide"
)

init_db()

def main():
    # Verificar se o link foi aberto na página de registo
    query_params = st.query_params
    if "page" in query_params and query_params["page"] == "register":
        show_register_page()
        return

    # Caso contrário, mostra o painel de administração na barra lateral
    st.sidebar.title("Painel Admin")
    
    modo = st.sidebar.radio("Navegação", ["Administração", "🔗 Obter Link de Registo"])
    
    if modo == "Administração":
        senha = st.sidebar.text_input("Palavra-passe", type="password")
        if senha == "admin123":
            st.sidebar.success("Sessão Iniciada")
            show_admin_panel()
        else:
            st.title("🔒 FFKaraoke - Área Restrita")
            st.write("Introduza a palavra-passe de administrador na barra lateral.")
            if senha:
                st.error("Palavra-passe incorreta.")
                
    elif modo == "Obter Link de Registo":
        st.title("🔗 Link de Auto-Registo para Prestadores")
        st.write("Partilhe o link abaixo com os prestadores para que eles façam o próprio registo:")
        
        # URL do link de registo público
        base_url = "https://appistrador-8rwwfsyycbappznjx9skot.streamlit.app/?page=register"
        st.code(base_url, language="text")
        st.info("Quando os prestadores acederem a este link, poderão introduzir o Nome, Sobrenome, Telefone e escolher entre 2h ou 4h de acesso.")

if __name__ == "__main__":
    main()
