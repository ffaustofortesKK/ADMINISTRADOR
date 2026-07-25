import streamlit as st
from utils.db_manager import init_db, get_all_providers
from modules.admin import show_admin_panel
from modules.register import show_register_page
from modules.client_portal import show_client_portal
from datetime import datetime
import qrcode
from io import BytesIO
import time
import requests

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
                    
                    # Se ainda não foi aprovado, fica em modo de espera a verificar automaticamente
                    if row.get('approved', 0) == 0:
                        st.warning("⏳ O seu registo foi enviado com sucesso e está a aguardar a aprovação do Administrador.")
                        st.info("Assim que o Administrador aprovar no painel, esta página abrirá automaticamente o seu painel de prestador. Por favor, aguarde...")
                        
                        time.sleep(3)
                        st.rerun()
                        return
                    
                    # SE JÁ ESTIVER APROVADO: Abre automaticamente o perfil completo do prestador
                    now = datetime.now()
                    exp_str = row.get('expires_at')
                    
                    if exp_str:
                        exp_time = datetime.strptime(exp_str, "%Y-%m-%d %H:%M:%S")
                        
                        if now < exp_time:
                            st.title(f"🎤 FFKaraoke - Painel do Prestador: {row['name']}")
                            st.success("Acesso autorizado pelo Administrador! O seu programa está pronto a ser utilizado.")
                            
                            ref_pagamento = row.get('payment_ref', 'N/A')
                            st.info(f"💳 **Referência de Pagamento:** `{ref_pagamento}`")
                            
                            # Contagem decrescente do tempo restante
                            tempo_restante = exp_time - now
                            horas, resto = divmod(int(tempo_restante.total_seconds()), 3600)
                            minutos, segundos = divmod(resto, 60)
                            st.metric(label="Tempo Restante de Sessão", value=f"{horas:02d}:{minutos:02d}:{segundos:02d}")
                            
                            st.markdown("---")
                            
                            # Gerador do Link e QR Code para os Clientes
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
                                st.image(buffered.getvalue(), caption="Aponte a câmara para escolher música", width=200)
                            with col_l2:
                                st.write("Disponibilize este link ou QR Code para que os clientes façam os pedidos de músicas diretamente:")
                                st.code(client_link, language="text")
                                st.info("💡 Os pedidos efetuados pelos clientes aparecem em tempo real abaixo.")

                            st.markdown("---")
                            st.subheader("📋 Fila de Pedidos de Músicas dos Clientes")
                            
                            # Buscar pedidos em tempo real do Firebase deste prestador específico
                            URL_PEDIDOS = f"https://grupoffkaraoke-default-rtdb.firebaseio.com/pedidos_{token}.json"
                            try:
                                res_pedidos = requests.get(f"{URL_PEDIDOS}?nocache={time.time()}", timeout=3).json()
                            except:
                                res_pedidos = None
                            
                            if res_pedidos and isinstance(res_pedidos, dict):
                                lista_pedidos = []
                                for p_id, dados in res_pedidos.items():
                                    if isinstance(dados, dict):
                                        lista_pedidos.append({
                                            "Cliente": dados.get("cantor", "Desconhecido"),
                                            "Música / Pedido": dados.get("musica", "N/A")
                                        })
                                
                                if lista_pedidos:
                                    st.dataframe(lista_pedidos, use_container_width=True)
                                else:
                                    st.info("Ainda nenhum cliente submeteu pedidos de música.")
                            else:
                                st.info("Ainda nenhum cliente submeteu pedidos de música.")
                            
                            # Atualiza a página automaticamente para mostrar novos clientes em tempo real
                            time.sleep(3)
                            st.rerun()
                            
                            return
                        else:
                            st.error("❌ O seu tempo de acesso expirou.")
                            return
            st.error("Token de acesso inválido ou não encontrado.")
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
