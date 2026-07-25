import streamlit as st
from utils.db_manager import get_all_providers, approve_provider
import sqlite3

def show_admin_panel():
    st.title("👑 Painel de Administração - FFKaraoke")
    st.write("Gerencie os acessos, valide pagamentos e controle os prestadores da plataforma.")
    
    df = get_all_providers()
    
    tab1, tab2 = st.tabs(["📋 Lista de Prestadores / Pedidos", "⚙️ Gestão Avançada"])
    
    with tab1:
        st.subheader("Estado dos Registos e Acessos")
        
        if df.empty:
            st.info("Nenhum prestador registado até ao momento.")
            return
            
        # Exibir tabela formatada
        st.dataframe(df, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Aprovação Rápida de Prestadores")
        
        # Filtrar apenas quem ainda não está aprovado (approved == 0)
        if 'approved' in df.columns:
            pendentes = df[df['approved'] == 0]
            
            if not pendentes.empty:
                prestador_opcoes = {f"{row['name']} (Ref: {row['payment_ref']}) - ID: {row['id']}": row['id'] for index, row in pendentes.iterrows()}
                
                escolha = st.selectbox("Selecione o prestador pendente:", list(prestador_opcoes.keys()))
                
                if st.button("✅ Aprovar Acesso", type="primary"):
                    p_id = prestador_opcoes[escolha]
                    approve_provider(p_id)
                    st.success("Acesso aprovado com sucesso! O prestador já pode utilizar a plataforma.")
                    st.rerun()
            else:
                st.success("Não existem pedidos pendentes de aprovação neste momento.")
                
    with tab2:
        st.subheader("Operações de Manutenção")
        st.write("Ferramentas de controlo direto na base de dados.")
        
        if not df.empty:
            prestador_todos = {f"{row['name']} (ID: {row['id']})": row['id'] for index, row in df.iterrows()}
            escolha_del = st.selectbox("Selecione um prestador para eliminar da base de dados:", list(prestador_todos.keys()))
            
            if st.button("🗑️ Eliminar Prestador Selecionado", type="secondary"):
                p_id_del = prestador_todos[escolha_del]
                
                # Executa a remoção direta
                try:
                    conn = sqlite3.connect("karaoke_admin.db")
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM providers WHERE id = ?", (p_id_del,))
                    conn.commit()
                    conn.close()
                    st.success("Prestador eliminado com sucesso.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao eliminar: {e}")
        else:
            st.info("Nenhum registo disponível para gerir.")
