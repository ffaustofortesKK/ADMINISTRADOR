import streamlit as st
from utils.db_manager import get_all_providers, approve_provider

def show_admin_panel():
    st.title("👑 Painel de Administração - FFKaraoke")
    st.subheader("Gestão de Pedidos de Acesso de Prestadores")
    
    df = get_all_providers()
    
    if df.empty:
        st.info("Nenhum pedido de registo encontrado na base de dados.")
        return
        
    # Filtra ou mostra todos
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Aprovar Prestador Pendente")
    
    # Selecionar prestadores não aprovados
    pendentes = df[df['approved'] == 0] if 'approved' in df.columns else df
    
    if not pendentes.empty:
        prestador_escolhido = st.selectbox(
            "Selecione o prestador para aprovar:", 
            pendentes['id'].astype(str) + " - " + pendentes['name']
        )
        
        if st.button("✅ Aprovar Acesso", type="primary"):
            p_id = int(prestador_escolhido.split(" - ")[0])
            approve_provider(p_id)
            st.success("Prestador aprovado com sucesso! O acesso foi libertado.")
            st.rerun()
    else:
        st.success("Não existem pedidos pendentes de aprovação.")
