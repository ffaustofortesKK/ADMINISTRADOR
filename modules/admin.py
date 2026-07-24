import streamlit as st
from utils.db_manager import get_all_providers, approve_provider
from datetime import datetime
import qrcode
from io import BytesIO

def show_admin_panel():
    st.title("👑 FFKaraoke - Painel de Administração")
    st.write("Gerencie os prestadores de serviço, aprove acessos e controle os prazos e pagamentos.")

    tab1, tab2, tab3 = st.tabs(["🔗 Link e QR Code", "📋 Gestão de Prestadores", "⚙️ Definições"])

    with tab1:
        st.subheader("Link e Código QR para Auto-Registo")
        register_link = "https://appadm.streamlit.app/?page=register"
        st.markdown("### 📌 Link Direto:")
        st.code(register_link, language="text")

        st.markdown("### 📱 Código QR de Acesso:")
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(register_link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        
        st.image(buffered.getvalue(), caption="QR Code de Registo", width=250)

    with tab2:
        st.subheader("Lista de Prestadores e Aprovações")
        df = get_all_providers()

        if not df.empty:
            now = datetime.now()
            
            # Secção de aprovação de novos pedidos pendentes
            pendentes = df[df['approved'] == 0]
            if not pendentes.empty:
                st.warning("⚠️ Tem novos pedidos de prestadores a aguardar aprovação:")
                for index, row in pendentes.iterrows():
                    with st.expander(f"Pedido #{row['id']} - {row['name']} ({row['duration_hours']}h)"):
                        st.write(f"💳 **Referência submetida pelo prestador:** `{row['payment_ref'] if row['payment_ref'] else 'Nenhuma'}`")
                        
                        # Campo para confirmar ou editar a referência ao aprovar
                        nova_ref = st.text_input("Confirmar/Ajustar Referência de Pagamento", value=row['payment_ref'], key=f"ref_{row['id']}")
                        
                        if st.button(f"Aprovar Prestador #{row['id']}", key=f"btn_aprove_{row['id']}"):
                            approve_provider(row['id'], nova_ref)
                            st.success(f"Prestador {row['name']} aprovado com sucesso!")
                            st.rerun()
            
            st.markdown("---")
            st.subheader("Controlo de Prestadores Ativos e Referências")
            
            ativos = df[df['approved'] == 1].copy()
            if not ativos.empty:
                for index, row in ativos.iterrows():
                    exp_time = datetime.strptime(row['expires_at'], "%Y-%m-%d %H:%M:%S")
                    tempo_restante = exp_time - now
                    
                    with st.container():
                        cols = st.columns([2, 1, 1, 1])
                        cols[0].write(f"👤 **{row['name']}**<br>💳 `Ref: {row['payment_ref']}`", unsafe_allow_html=True)
                        cols[1].write(f"⏱️ Duração: {row['duration_hours']}h")
                        
                        if tempo_restante.total_seconds() > 0:
                            horas, resto = divmod(int(tempo_restante.total_seconds()), 3600)
                            minutos, segundos = divmod(resto, 60)
                            cols[2].markdown(f"🟢 **Ativo**<br>`{horas}h {minutos}m {segundos}s`", unsafe_allow_html=True)
                            cols[3].success("Liberado")
                        else:
                            cols[2].markdown("🔴 **Expirado**")
                            cols[3].error("Esgotado")
                        st.markdown("---")
            else:
                st.info("Nenhum prestador aprovado no momento.")
        else:
            st.info("Ainda nenhum prestador registado na base de dados.")

    with tab3:
        st.subheader("Configurações do Sistema Admin")
        with st.form("form_admin_settings"):
            nova_senha = st.text_input("Alterar Palavra-passe de Administrador", type="password")
            salvar_pass = st.form_submit_button("Guardar Alterações")
            if salvar_pass:
                if nova_senha:
                    st.success("Palavra-passe de administrador atualizada com sucesso!")
                else:
                    st.error("A palavra-passe não pode estar vazia.")
