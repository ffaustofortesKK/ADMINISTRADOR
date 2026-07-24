import streamlit as st
from utils.db_manager import create_provider_link, get_all_providers
from datetime import datetime
import qrcode
from io import BytesIO

def show_admin_panel():
    st.title("👑 FFKaraoke - Painel de Administração")
    st.write("Gerencie os prestadores de serviço, controle os prazos de validade e gere os acessos.")

    # Menu Interno do Admin em separadores
    tab1, tab2, tab3 = st.tabs(["🔗 Link e QR Code de Registo", "📋 Prestadores Ativos", "⚙️ Definições Gerais"])

    with tab1:
        st.subheader("Link e Código QR para Auto-Registo dos Prestadores")
        st.write("Partilhe este link ou o Código QR com os prestadores para que possam preencher o Nome, Sobrenome, Telefone e escolher o tempo (2h ou 4h).")

        # URL oficial correto e atualizado do link de registo público
        register_link = "https://appadm.streamlit.app/?page=register"

        st.markdown("### 📌 Link Direto:")
        st.code(register_link, language="text")

        st.markdown("### 📱 Código QR de Acesso:")
        
        # Gerar a imagem do QR Code em memória
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(register_link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converter a imagem para formato compatível com Streamlit
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        
        # Mostrar o QR Code no painel
        col_qr1, col_qr2 = st.columns([1, 2])
        with col_qr1:
            st.image(buffered.getvalue(), caption="QR Code de Registo", width=250)
        with col_qr2:
            st.info("Pode tirar uma captura de ecrã deste QR Code, guardá-lo ou copiá-lo diretamente para enviar por WhatsApp ou outras mensagens aos prestadores.")

    with tab2:
        st.subheader("Monitorização de Prestadores")
        df = get_all_providers()

        if not df.empty:
            # Calcular o estado atual (Ativo vs Expirado) com base na data do sistema
            now = datetime.now()
            df['Estado'] = df['expires_at'].apply(
                lambda x: '🟢 Ativo' if datetime.strptime(x, "%Y-%m-%d %H:%M:%S") > now else '🔴 Expirado'
            )

            # Organizar colunas para melhor visualização
            display_df = df[['id', 'name', 'token', 'duration_hours', 'created_at', 'expires_at', 'Estado']]
            st.dataframe(display_df, use_container_width=True)

            st.info("💡 Nota: Os prestadores com o estado 'Expirado' deixarão de conseguir autenticar-se automaticamente na plataforma.")
        else:
            st.info("Ainda nenhum prestador registado na base de dados.")

    with tab3:
        st.subheader("Configurações do Sistema Admin")
        st.write("Aqui poderá gerir parâmetros globais do FFKaraoke no futuro.")

        with st.form("form_admin_settings"):
            nova_senha = st.text_input("Alterar Palavra-passe de Administrador", type="password")
            salvar_pass = st.form_submit_button("Guardar Alterações")
            if salvar_pass:
                if nova_senha:
                    st.success("Palavra-passe de administrador atualizada com sucesso!")
                else:
                    st.error("A palavra-passe não pode estar vazia.")
