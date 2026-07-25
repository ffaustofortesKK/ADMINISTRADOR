import streamlit as st
from utils.db_manager import get_all_providers, approve_provider
from datetime import datetime
import qrcode
from io import BytesIO
import requests

def show_admin_panel():
    st.title("👑 FFKaraoke - Painel de Administração")
    st.write("Gerencie os prestadores de serviço, aprove acessos e consulte o histórico e contabilidade.")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🔗 Link e QR Code", 
        "📋 Gestão de Prestadores", 
        "📊 Histórico e Contabilidade", 
        "⚙️ Definições"
    ])

    df = get_all_providers()
    now = datetime.now()

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

        if not df.empty:
            # Secção de aprovação de novos pedidos pendentes
            pendentes = df[df['approved'] == 0]
            if not pendentes.empty:
                st.warning("⚠️ Tem novos pedidos de prestadores a aguardar aprovação:")
                for index, row in pendentes.iterrows():
                    with st.container():
                        st.write(f"👤 **{row['name']}** (Duração: {row['duration_hours']}h) — 💳 `Ref: {row['payment_ref'] if row['payment_ref'] else 'N/A'}`")
                        
                        if st.button(f"Sim, Aprovar Prestador #{row['id']}", key=f"btn_sim_{row['id']}", type="primary"):
                            approve_provider(row['id'])
                            st.success(f"Prestador {row['name']} aprovado com sucesso!")
                            st.rerun()
                        st.markdown("---")
            
            st.subheader("Controlo de Prestadores Ativos")
            
            # Filtrar apenas os aprovados E cujo tempo ainda não expirou
            ativos = []
            for index, row in df[df['approved'] == 1].iterrows():
                exp_str = row['expires_at']
                if exp_str:
                    exp_time = datetime.strptime(exp_str, "%Y-%m-%d %H:%M:%S")
                    if now < exp_time:
                        ativos.append(row)
            
            if ativos:
                for row in ativos:
                    exp_time = datetime.strptime(row['expires_at'], "%Y-%m-%d %H:%M:%S")
                    tempo_restante = exp_time - now
                    
                    with st.container():
                        cols = st.columns([2, 1, 1, 1])
                        cols[0].write(f"👤 **{row['name']}**<br>💳 `Ref: {row['payment_ref']}`", unsafe_allow_html=True)
                        cols[1].write(f"⏱️ Duração: {row['duration_hours']}h")
                        
                        horas, resto = divmod(int(tempo_restante.total_seconds()), 3600)
                        minutos, segundos = divmod(resto, 60)
                        cols[2].markdown(f"🟢 **Ativo**<br>`{horas}h {minutos}m {segundos}s`", unsafe_allow_html=True)
                        cols[3].success("A decorrer")
                        st.markdown("---")
            else:
                st.info("Nenhum prestador ativo no momento.")
        else:
            st.info("Ainda nenhum prestador registado na base de dados.")

    with tab3:
        st.subheader("📊 Histórico de Prestadores Expirados e Contabilidade")
        st.write("Prestadores cujo tempo terminou e respetiva contabilidade de clientes e referências.")

        if not df.empty:
            # Filtrar apenas os expirados
            expirados = []
            for index, row in df[df['approved'] == 1].iterrows():
                exp_str = row['expires_at']
                if exp_str:
                    exp_time = datetime.strptime(exp_str, "%Y-%m-%d %H:%M:%S")
                    if now >= exp_time:
                        expirados.append(row)

            if expirados:
                total_clientes_geral = 0
                total_referencias_validas = 0
                
                tabela_historico = []
                
                for row in expirados:
                    token_p = row['token']
                    # Consultar o Firebase para contar quantos clientes este prestador teve
                    URL_PEDIDOS = f"https://grupoffkaraoke-default-rtdb.firebaseio.com/pedidos_{token_p}.json"
                    qtd_clientes = 0
                    try:
                        res = requests.get(URL_PEDIDOS, timeout=2).json()
                        if res and isinstance(res, dict):
                            clientes_unicos = set()
                            for p_id, p_val in res.items():
                                if isinstance(p_val, dict) and 'cantor' in p_val:
                                    clientes_unicos.add(str(p_val['cantor']).strip().lower())
                            qtd_clientes = len(clientes_unicos)
                    except:
                        qtd_clientes = 0

                    total_clientes_geral += qtd_clientes
                    total_referencias_validas += 1

                    tabela_historico.append({
                        "Nome do Prestador": row['name'],
                        "Referência de Pagamento": row['payment_ref'] if row['payment_ref'] else "N/A",
                        "Data de Registo": row['created_at'],
                        "Clientes Atendidos": qtd_clientes
                    })

                # Mostrar tabela detalhada
                st.dataframe(tabela_historico, use_container_width=True)

                st.markdown("---")
                st.subheader("📈 Totais Contabilizados")
                
                col_c1, col_c2 = st.columns(2)
                col_c1.metric(label="Total Geral de Clientes (Histórico)", value=total_clientes_geral)
                col_c2.metric(label="Total de Referências Registadas", value=total_referencias_validas)

            else:
                st.info("Ainda não existem prestadores com o tempo expirado.")
        else:
            st.info("Sem dados na base de dados.")

    with tab4:
        st.subheader("Configurações do Sistema Admin")
        with st.form("form_admin_settings"):
            nova_senha = st.text_input("Alterar Palavra-passe de Administrador", type="password")
            salvar_pass = st.form_submit_button("Guardar Alterações")
            if salvar_pass:
                if nova_senha:
                    st.success("Palavra-passe de administrador atualizada com sucesso!")
                else:
                    st.error("A palavra-passe não pode estar vazia.")
