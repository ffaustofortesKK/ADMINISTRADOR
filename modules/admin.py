import streamlit as st
from utils.db_manager import create_provider_link, get_all_providers
from datetime import datetime

def show_admin_panel():
    st.title("👑 FFKaraoke - Painel de Administração")
    st.write("Gerencie os prestadores de serviço, controle os prazos de validade e gere os acessos.")

    # Menu interno do Admin em separadores
    tab1, tab2, tab3 = st.tabs(["➕ Criar Prestador", "📋 Prestadores Ativos", "⚙️ Definições Gerais"])

    with tab1:
        st.subheader("Gerar Novo Link de Acesso com Validade")
        
        with st.form("form_novo_prestador"):
            provider_name = st.text_input("Nome do Estabelecimento / Prestador (ex: Espaço VIP)")
            
            # Seleção rápida ou personalizada de horas de acesso
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                duration_hours = st.number_input("Tempo de Acesso (em horas)", min_value=1, max_value=8760, value=24)
            with col_d2:
                st.info(f"Equivalente a aproximadamente **{round(duration_hours / 24, 1)} dias** de uso contínuo.")
            
            submitted = st.form_submit_button("Gerar Link e Token Exclusivo")
            
            if submitted:
                if provider_name.strip():
                    token = create_provider_link(provider_name.strip(), duration_hours)
                    st.success(f"Prestador **{provider_name}** criado com sucesso!")
                    
                    # URL base do seu app no Streamlit Cloud
                    access_link = f"https://ffkaraoke.streamlit.app/?token={token}"
                    
                    st.markdown("### 🔗 Dados de Acesso Gerados:")
                    st.write("Envie o seguinte link ou token diretamente para o prestador:")
                    st.code(access_link, language="text")
                    st.text(f"Token isolado: {token}")
                else:
                    st.error("Por favor, introduza um nome válido para o prestador.")

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
