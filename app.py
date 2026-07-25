import streamlit as st
from modules.tela import show_tela_panel
from cliente import show_cliente_panel

st.set_page_config(
    page_title="FF Karaoke - Sistema Completo",
    page_icon="🎤",
    layout="wide"
)

# Menu lateral para escolher o painel
st.sidebar.title("🎛️ Navegação FF Karaoke")
opcao = st.sidebar.selectbox("Escolha o Painel:", ["Tela (Pública/Fila)", "Painel do Cliente"])

st.sidebar.markdown("---")
st.sidebar.info("Sistema integrado de gestão de fila de karaoke.")

# Carrega o painel selecionado
if opcao == "Tela (Pública/Fila)":
    show_tela_panel()
elif opcao == "Painel do Cliente":
    show_cliente_panel()
