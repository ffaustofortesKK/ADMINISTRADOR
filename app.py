import streamlit as st
from utils.db_manager import init_db, get_all_providers
from modules.admin import show_admin_panel
from modules.register import show_register_page
from modules.provider import show_provider_panel
from datetime import datetime

st.set_page_config(
    page_title="FFKaraoke - Gestão de Acessos",
    page_icon="🎤",
    layout="wide"
)

try:
    init_db()
except Exception as e:
    st.error(f"Erro ao inicializar a base de dados: {e}")

def main():
    try:
        query_params = st.query_params
        
        # 1. Página de Auto-Registo Pública do Prestador
        if "page" in query_params and query_params["page"] == "register":
            show_register_page()
            return

        # 2. Página de Auto-Registo de Clientes (Gerada pelo Prestador)
        if "page" in query_params and query_params["page"] == "client_register":
            provider_token = query_params.get("provider", "Desconhecido")
            st.title("🎤 FFKaraoke - Registo de Pedido do Cliente")
            st.write(f"Faça o seu pedido de música para o prestador responsável (Ref: `{provider_token[:8]}...`)")
            # Aqui poderá adicionar o formulário do cliente futuramente
            st.info("O formulário de registo de pedidos do cliente está pronto a ser configurado.")
            return

        # 3. Tela de Apresentação de Vídeos / Pedidos do Cliente
        if "page" in query_params and query_params["page"] == "client_screen":
            provider_token = query_params.get("provider", "Desconhecido")
            st.title("📺 FFKaraoke — Tela de Apresentação de Vídeos")
            st.info(f"Ecrã de exibição em tempo real ligado ao prestador (`{provider_token[:8]}...`). Os vídeos pedidos aparecerão aqui.")
            return

        # 4. Acesso Individual do Prestador via Token
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
                                # Chama o painel do prestador com os seus links exclusivos
                                show_provider_panel()
                                return
                            else:
                                st.error("❌ O seu tempo de acesso expirou.")
                                return
                    else:
                        st.warning("⏳ O seu registo foi efetuado, mas ainda aguarda a aprovação do Administrador.")
                        return
            
            st.error("Token de acesso inválido ou não encontrado.")
            return

        # 5. Painel de Administração
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
        st.error(f"Ocorreu um erro ao carregar a aplicação: {e}")

if __name__ == "__main__":
    main()
