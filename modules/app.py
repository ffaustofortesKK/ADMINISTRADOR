import streamlit as st

# Configuração global da página (título e ícone no navegador)
st.set_page_config(
    page_title="FF Karaoke Professional",
    page_icon="🎤",
    layout="wide"
)

# Importamos a função do prestador que criámos na pasta modules
from modules.prestador import show_prestador_panel

# Executamos o painel do prestador
show_prestador_panel()
