import streamlit as st
from utils.db_manager import init_db
from modules.admin import show_admin_panel

# Configuração da página de administração
st.set_page_config(
    page_title="FFKaraoke - Administração",
    page_icon="👑",
    layout="wide"
)

# Inicializar a base de dados SQLite
init_db()

def main():
    st.sidebar.title("Painel Admin")
    
    # Proteção simples por senha para o Administrador
    senha = st.sidebar.text_input("Palavra-passe", type="password")
    
    # Palavra-passe de acesso ao painel
    if senha == "admin123":
        st.sidebar.success("Sessão Iniciada")
        show_admin_panel()
    else:
        st.title("🔒 FFKaraoke - Área Restrita")
        st.write("Por favor, introduza a palavra-passe correta na barra lateral para aceder ao painel de administração.")
        if senha:
            st.error("Palavra-passe incorreta.")

if __name__ == "__main__":
    main()
