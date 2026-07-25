import streamlit as st
from utils.db_manager import get_all_providers, approve_provider

def show_admin_panel():
    # Estilização visual integrada para o ADM
    st.markdown("""
    <style>
    .adm-card {
        background: linear-gradient(180deg, #111, #050505);
        border: 2px solid #D4AF37;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0px 0px 15px rgba(212,175,55,0.15);
    }
    .stButton button {
        background: linear-gradient(180deg, #D4AF37, #AA8C2C);
        color: black;
        font-weight: bold;
        border-radius: 10px;
        width: 100%;
        padding: 8px;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("### 🛠️ Painel de Gestão e Aprovação de Prestadores")
    st.write("Gerencie os pedidos de acesso e verifique os comprovativos de pagamento dos prestadores.")
    st.markdown("---")

    df = get_all_providers()

    if df.empty:
        st.info("Nenhum prestador registado na base de dados.")
        return

    # Listar todos os prestadores registados
    for index, row in df.iterrows():
        nome = row.get('name', 'Desconhecido')
        telefone = row.get('phone', 'N/A')
        payment_ref = row.get('payment_ref', 'N/A')
        expires_at = row.get('expires_at', 'N/A')
        token = row.get('token', '')
        aprovado = int(row.get('approved', 0))

        status_badge = "✅ Aprovado" if aprovado == 1 else "⏳ Pendente"
        status_color = "#4CAF50" if aprovado == 1 else "#FFC107"

        st.markdown(f"""
        <div class="adm-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h3 style="color: #D4AF37; margin: 0;">🎤 {nome}</h3>
                <span style="background-color: {status_color}; color: black; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 14px;">{status_badge}</span>
            </div>
            <p style="margin: 4px 0; color: #ccc;"><b>📞 Telefone:</b> {telefone}</p>
            <p style="margin: 4px 0; color: #ccc;"><b>💳 Ref. de Pagamento:</b> <code>{payment_ref}</code></p>
            <p style="margin: 4px 0; color: #ccc;"><b>⏱️ Duração/Expira em:</b> {expires_at}</p>
        </div>
        """, unsafe_allow_html=True)

        # Botão de aprovação fora do HTML para manter a interatividade do Streamlit
        if aprovado == 0:
            col_b1, col_b2 = st.columns([1, 3])
            with col_b1:
                if st.button("✅ Aprovar", key=f"btn_apr_{token}"):
                    approve_provider(token)
                    st.success(f"Prestador {nome} aprovado com sucesso!")
                    st.rerun()
        else:
            st.markdown("<p style='color: #4CAF50; font-size: 13px; margin-top: -10px;'>Acesso liberado para este prestador.</p>", unsafe_allow_html=True)

        st.markdown("---")
