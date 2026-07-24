import streamlit as st
from utils.db_manager import init_db, get_all_providers
from modules.admin import show_admin_panel
from modules.register import show_register_page
from datetime import datetime

st.set_page_config(
    page_title="FFKaraoke - Gestão de Acessos",
    page_icon="🎤",
    layout="wide"
)

# Inicializar a base de dados em segurança
try:
    init_db()
except Exception as e:
    st.error(f"Erro ao inicializar a base de dados: {e}")

def main():
    try:
        query_params = st.query_params
        
        # 1. Página de Auto-Registo Pública
        if "page" in query_params and query_params["page"] == "register":
            show_register_page()
            return

        # 2. Acesso Individual do Prestador via Token
        if "token" in query_params:
            token = query_params["token"]
            df = get_all_providers()
            
            if not df.empty and 'token' in df.columns:
                prestador = df[df['token'] == token]
                
                if not prestador.empty:
                    row = prestador.iloc[0]
                    if row.get('approved', 0) == 1:
                        now = datetime.now()
                        exp_str = row.get('expires_at')
                        
                        if exp_str:
                            exp_time = datetime.strptime(exp_str, "%Y-%m-%d %H:%M:%S")
                            
                            if now < exp_time:
                                st.title(f"🎤 FFKaraoke - Bem-vindo(a), {row['name']}")
                                st.success("Acesso autorizado pelo Administrador. O seu programa está pronto a ser utilizado!")
                                
                                tempo_restante = exp_time - now
                                horas, resto = divmod(int(tempo_restante.total_seconds()), 3600)
                                minutos, segundos = divmod(resto, 60)
                                
                                st.metric(label="Tempo Restante de Sessão", value=f"{horas:02d}:{minutos:02d}:{segundos:02d}")
                                st.info("Ambiente de Karaokê ativo.")
                                return
                            else:
                                st.error("❌ O seu tempo de acesso expirou.")
                                return
                    else:
                        st.warning("⏳ O seu registo foi efetuado, mas ainda aguarda a aprovação do Administrador.")
                        return
            st.error("Token de acesso inválido ou não encontrado.")
            return

        # 3. Painel de Administração
        st.sidebar.title("Painel Admin")
        senha = st.sidebar.text_input("Palavra-passe", type="password")
        
        if senha == "admin123":
            st.sidebar.success("Sessão Iniciada")
            show_admin_panel()
        else:
            st.title("🔒 FFKaraoke - Área Restrita")
            st.write("Introduza a palavra-passe de administrador na barra lateral para gerir os pedidos e acessos.")
            if senha:
                st.error("Palavra-passe incorreta.")
                
    except Exception as e:
        st.error(fOcorreu um erro ao carregar a aplicação: {e})

if __name__ == "__main__":
    main()
