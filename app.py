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
    page_title="FFKaraoke - Painel do Prestador",
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

        # 2. Portal do Cliente
        if "client_view" in query_params:
            token_prestador = query_params["client_view"]
            show_client_portal(token_prestador)
            return

        # 3. Acesso Individual do Prestador via Token (Tudo na mesma página)
        if "token" in query_params:
            token = query_params["token"]
            df = get_all_providers()
            
            if not df.empty and 'token' in df.columns:
                prestador = df[df['token'] == token]
                
                if not prestador.empty:
                    row = prestador.iloc[0]
                    
                    # Se ainda não foi aprovado pelo ADM
                    if row.get('approved', 0) == 0:
                        st.title("🎤 FFKaraoke - Estado do Registo")
                        st.warning("⏳ O seu registo foi enviado com sucesso e está a aguardar a aprovação do Administrador.")
                        st.info("Assim que o Administrador aprovar, esta mesma página atualizar-se-á automaticamente para o seu painel de prestador. Por favor, aguarde...")
                        
                        time.sleep(3)
                        st.rerun()
                        return
                    
                    # SE JÁ ESTIVER APROVADO: Carrega o painel completo na mesma página
                    now = datetime.now()
                    exp_str = row.get('expires_at')
                    
                    if exp_str:
                        exp_time = datetime.strptime(exp_str, "%Y-%m-%d %H:%M:%S")
                        
                        if now < exp_time:
                            nome_prestador = row['name']
                            slug_prestador = token
                            
                            st.title(f"🎤 Bem-vindo, {nome_prestador}!")
                            
                            tempo_restante = exp_time - now
                            horas, resto = divmod(int(tempo_restante.total_seconds()), 3600)
                            minutos, segundos = divmod(resto, 60)
                            st.caption(f"⏱️ Tempo restante de sessão: **{horas:02d}h {minutos:02d}m {segundos:02d}s** | 💳 Ref: `{row.get('payment_ref', 'N/A')}`")
                            
                            st.markdown("---")
                            
                            col_links, col_qr = st.columns([4, 1])
                            
                            with col_links:
                                client_link = f"https://appcliente.streamlit.app/?prestador={slug_prestador}"
                                tv_link = f"https://ffktela.streamlit.app/?prestador={slug_prestador}"
                                
                                st.markdown(f"🔗 **Cliente:** [{client_link}]({client_link})")
                                st.markdown(f"📺 **TV:** [{tv_link}]({tv_link})")
                            
                            with col_qr:
                                qr = qrcode.QRCode(version=1, box_size=5, border=1)
                                qr.add_data(client_link)
                                qr.make(fit=True)
                                img = qr.make_image(fill_color="black", back_color="white")
                                buffered = BytesIO()
                                img.save(buffered, format="PNG")
                                st.image(buffered.getvalue(), width=100)

                            st.markdown("---")
                            
                            st.subheader("🎬 Playlist de Vídeos Clipes (Fundo da TV)")
                            col_busca_cli, col_btn_cli = st.columns([3, 1])
                            with col_busca_cli:
                                clipe_pesquisa = st.text_input("Pesquisar clipe na pasta:", placeholder="Digite o nome do clipe...")
                            with col_btn_cli:
                                st.write("")
                                st.write("")
                                if st.button("🚀 Enviar Clipe para Tela", use_container_width=True):
                                    if clipe_pesquisa:
                                        st.success(f"Clipe '{clipe_pesquisa}' enviado para a tela!")
                                    else:
                                        st.warning("Insira o nome do clipe.")

                            st.markdown("---")
                            
                            st.subheader("⚡ Seleção Manual (Nome exato do ficheiro)")
                            col_man, col_btn_man = st.columns([4, 1])
                            with col_man:
                                nome_ficheiro_manual = st.text_input("Nome do ficheiro (ex: nome_do_video.mp4):", label_visibility="collapsed", placeholder="Nome do ficheiro (ex: nome_do_video.mp4)")
                            with col_btn_man:
                                if st.button("📤 Enviar Manual", use_container_width=True):
                                    if nome_ficheiro_manual:
                                        st.success(f"Ficheiro '{nome_ficheiro_manual}' enviado com sucesso!")
                                    else:
                                        st.warning("Insira o nome do ficheiro.")

                            st.markdown("---")
                            
                            st.subheader("📋 Gestão de Fila")
                            
                            URL_PEDIDOS = f"https://grupoffkaraoke-default-rtdb.firebaseio.com/pedidos_{slug_prestador}.json"
                            try:
                                res_pedidos = requests.get(f"{URL_PEDIDOS}?nocache={time.time()}", timeout=2).json()
                            except:
                                res_pedidos = None
                            
                            if res_pedidos and isinstance(res_pedidos, dict):
                                for p_id, dados in res_pedidos.items():
                                    if isinstance(dados, dict):
                                        c_nome = dados.get("cantor", "Desconhecido")
                                        c_musica = dados.get("musica", "N/A")
                                        
                                        col_f1, col_f2, col_f3 = st.columns([6, 1, 1])
                                        col_f1.write(f"🎤 **{c_nome}** - {c_musica}")
                                        if col_f2.button("🗑️", key=f"del_{p_id}"):
                                            requests.delete(f"https://grupoffkaraoke-default-rtdb.firebaseio.com/pedidos_{slug_prestador}/{p_id}.json")
                                            st.rerun()
                                        if col_f3.button("✏️", key=f"edit_{p_id}"):
                                            st.toast(f"A editar pedido de {c_nome}")
                            else:
                                st.write("A fila de músicas está vazia.")
                            
                            st.markdown("")
                            if st.button("▶ FORÇAR INÍCIO DE MÚSICA (IMEDIATO)", type="primary"):
                                st.success("Comando enviado: Início de música forçado na tela!")

                            st.markdown("---")
                            
                            st.subheader("⚠️ Pedidos Manuais (Atenção)")
                            tem_manual = False
                            if res_pedidos and isinstance(res_pedidos, dict):
                                for p_id, dados in res_pedidos.items():
                                    if isinstance(dados, dict) and str(dados.get("musica", "")).startswith("PEDIDO:"):
                                        tem_manual = True
                                        st.warning(f"🔔 **Cliente:** {dados.get('cantor')} | **Pedido:** {dados.get('musica')}")
                            
                            if not tem_manual:
                                st.success("Nenhum pedido manual pendente.")

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
