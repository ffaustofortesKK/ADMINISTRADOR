import streamlit as st
from utils.db_manager import init_db, get_all_providers, get_client_requests
from modules.admin import show_admin_panel
from modules.register import show_register_page
from modules.client_portal import show_client_portal
from datetime import datetime
import qrcode
from io import BytesIO

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
        
        # 1. Página de Auto-Registo Pública para Prestadores
        if "page" in query_params and query_params["page"] == "register":
            show_register_page()
            return

        # 2. Portal do Cliente (via QR Code / Link do Prestador)
        if "client_view" in query_params:
            token_prestador = query_params["client_view"]
            show_client_portal(token_prestador)
            return

        # 3. Acesso Individual do Prestador via Token
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
                                st.title(f"🎤 FFKaraoke - Painel do Prestador: {row['name']}")
                                st.success("Acesso autorizado pelo Administrador. O seu programa está pronto!")
                                
                                ref_pagamento = row.get('payment_ref', 'N/A')
                                st.info(f"💳 **Referência de Pagamento:** `{ref_pagamento}`")
                                
                                # Temporizador de sessão
                                tempo_restante = exp_time - now
                                horas, resto = divmod(int(tempo_restante.total_seconds()), 3600)
                                minutos, segundos = divmod(resto, 60)
                                st.metric(label="Tempo Restante de Sessão", value=f"{horas:02d}:{minutos:02d}:{segundos:02d}")
                                
                                st.markdown("---")
                                
                                # Gerador de Link / QR Code para os Clientes escanearem
                                st.subheader("📱 QR Code e Link para os seus Clientes")
                                base_url = "https://appadm.streamlit.app/"
                                client_link = f"{base_url}?client_view={token}"
                                
                                col_l1, col_l2 = st.columns([1, 2])
                                with col_l1:
                                    qr = qrcode.QRCode(version=1, box_size=8, border=2)
                                    qr.add_data(client_link)
                                    qr.make(fit=True)
                                    img = qr.make_image(fill_color="black", back_color="white")
                                    buffered = BytesIO()
                                    img.save(buffered, format="PNG")
                                    st.image(buffered.getvalue(), caption="Mostre este QR ao Cliente", width=200)
                                with col_l2:
                                    st.write("Partilhe este link ou deixe os clientes lerem o QR Code para escolherem as músicas:")
                                    st.code(client_link, language="text")
                                    st.info("💡 Assim que os clientes escolherem as músicas, elas aparecerão em tempo real na lista abaixo.")

                                st.markdown("---")
                                st.subheader("📋 Fila de Pedidos de Músicas dos Clientes")
                                
                                requests_df = get_client_requests(token)
                                if not requests_df.empty:
                                    st.dataframe(
                                        requests_df[['client_name', 'song_choice', 'request_type', 'created_at']],
                                        use_container_width=True,
                                        column_config={
                                            "client_name": "Cliente",
                                            "song_choice": "Música Escolhida / Pedido",
                                            "request_type": "Tipo de Pedido",
                                            "created_at": "Hora do Pedido"
                                        }
                                    )
                                else:
                                    st.info("Ainda nenhum cliente submeteu pedidos de música.")
                                
                                return
                            else:
                                st.error("❌ O seu tempo de acesso expirou.")
                                return
                    else:
                        st.warning("⏳ O seu registo aguarda a aprovação do Administrador.")
                        return
            st.error("Token de acesso inválido.")
            return

        # 4. Painel de Administração
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
