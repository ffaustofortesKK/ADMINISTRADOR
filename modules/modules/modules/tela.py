import streamlit as st

st.set_page_config(
    page_title="FF Karaoke - Tela",
    page_icon="📺",
    layout="wide"
)

from modules.tela import show_tela_panel

show_tela_panel()
