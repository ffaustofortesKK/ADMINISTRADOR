import streamlit as st
from utils.db_manager import get_all_providers, approve_provider

def show_admin_panel():
    st.subheader("📋 Painel de Gestão de Prestadores")
    st.write("Aqui pode visualizar e aprovar os novos prestadores registados.")

    df = get_all_providers()

    if df.empty:
        st.info("Nenhum prestador registado até o momento.")
        return

    st.markdown("---")

    # Percorrer cada prestador na base de dados
    for index, row in df.iterrows():
        prestador_id = row.get('id')
        nome = row.get('name', 'Desconhecido')
        telefone = row.get('phone', 'N/A')
        payment_ref = row.get('payment_ref', 'N/A')
        token = row.get('token', '')
        aprovado = int(row.get('approved', 0))

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.markdown(f"**Nome:** {nome}")
            st.markdown(f"**Telefone:** {telefone}")

        with col2:
            st.markdown(f"**Comprovativo / Ref:** `{payment_ref}`")
            status_txt = "✅ Aprovado" if aprovado == 1 else "⏳ Pendente"
            st.markdown(f"**Estado:** {status_txt}")

        with col3:
            if aprovado == 0:
                if st.button("Aprovar", key=f"btn_apr_{token}"):
                    approve_provider(token)
                    st.success(f"Prestador {nome} aprovado com sucesso!")
                    st.rerun()
            else:
                st.markdown("Aprovado")

        st.markdown("---")
