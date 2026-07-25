import streamlit as st
from utils.db_manager import get_all_providers, approve_provider, get_total_revenue

def show_admin_panel():
    st.markdown("""
    <style>
    .adm-card {
        background: linear-gradient(180deg, #111, #050505);
        border: 2px solid #D4AF37;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0px 0px 15px rgba(212,175,55,0.15);
    }
    .link-box {
        background: #111;
        border: 1px solid #D4AF37;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    st.subheader("🛠️ Painel de Administração — FF Karaoke")
    st.markdown("---")

    # Obter dados atualizados da base de dados para contagem e listagem
    df = get_all_providers()
    
    # Calcular quantidade de pendentes para mostrar o sinal/número na aba
    pendentes_count = 0
    if not df.empty and 'approved' in df.columns:
        # Garante conversão segura para inteiro comparando com 0
        pendentes_count = len(df[df['approved'].astype(int) == 0])

    # Rótulo dinâmico com o sinalizador/número de pendentes
    label_aba2 = f"⏳ Pedidos e Aprovação ({pendentes_count})" if pendentes_count > 0 else "⏳ Pedidos e Aprovação"

    # Criação das 4 abas solicitadas
    aba1, aba2, aba3, aba4 = st.tabs([
        "🔗 Link e QR Registo", 
        label_aba2, 
        "📊 Gestão Total", 
        "📈 Relatórios e Estatísticas"
    ])

    # -------------------------------------------------------------
    # ABA 1: Link e QR Code para o Registo de Prestadores
    # -------------------------------------------------------------
    with aba1:
        st.subheader("🔗 Portal de Auto-Registo de Prestadores")
        st.write("Partilhe este link ou o QR Code com os prestadores para que possam submeter os seus dados e comprovativo de pagamento.")
        
        base_url = "https://appadm.streamlit.app/?page=register"
        
        col_l, col_q = st.columns([3, 1])
        with col_l:
            st.markdown(f"""
            <div class="link-box">
                <b>Link Direto de Registo:</b><br>
                <a href="{base_url}" target="_blank" style="color: #FFD700; font-size: 16px;">{base_url}</a>
            </div>
            """, unsafe_allow_html=True)
            st.info("Os prestadores que acederem a este link poderão preencher o nome, contacto, referência de pagamento e tempo pretendido.")
            
        with col_q:
            qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={base_url}"
            st.image(qr_api_url, width=140, caption="QR Code de Registo")

    # -------------------------------------------------------------
    # ABA 2: Pedidos e Aprovação dos Prestadores
    # -------------------------------------------------------------
    with aba2:
        st.subheader("📋 Pedidos de Registo Pendentes")
        st.write("Analise as informações enviadas por cada prestador e aprove o acesso conforme a confirmação do pagamento.")
        
        if df.empty:
            st.info("Nenhum prestador registado na base de dados.")
        else:
            # Filtro rigoroso para capturar os prestadores pendentes (approved == 0)
            pendentes = df[df['approved'].astype(int) == 0]
            
            if pendentes.empty:
                st.success("Não existem pedidos de registo pendentes neste momento.")
            else:
                for index, row in pendentes.iterrows():
                    nome = row.get('name', 'Desconhecido')
                    telefone = row.get('phone', 'N/A')
                    payment_ref = row.get('payment_ref', 'N/A')
                    expires_at = row.get('expires_at', 'N/A')
                    token = row.get('token', '')
                    
                    st.markdown(f"""
                    <div class="adm-card">
                        <h3 style="color: #D4AF37; margin-top: 0;">🎤 {nome}</h3>
                        <p style="margin: 4px 0; color: #ccc;"><b>📞 Telefone:</b> {telefone}</p>
                        <p style="margin: 4px 0; color: #ccc;"><b>💳 Referência de Pagamento:</b> <code>{payment_ref}</code></p>
                        <p style="margin: 4px 0; color: #ccc;"><b>⏱️ Duração Solicitada / Expira:</b> {expires_at}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"✅ Aprovar Prestador {nome}", key=f"btn_aprovar_{token}"):
                        approve_provider(token)
                        st.success(f"Prestador {nome} aprovado com sucesso!")
                        st.rerun()
                    st.markdown("---")

    # -------------------------------------------------------------
    # ABA 3: Gestão Total (Registo completo: dia, valor, tempo)
    # -------------------------------------------------------------
    with aba3:
        st.subheader("📑 Gestão Total de Prestadores Registados")
        st.write("Histórico completo contendo a data de registo, valor pago, tempo solicitado e estado atual.")
        
        if df.empty:
            st.info("Nenhum registo encontrado na base de dados.")
        else:
            tabela_exibicao = df[['id', 'name', 'phone', 'payment_ref', 'amount_paid', 'expires_at', 'approved']].copy()
            tabela_exibicao.columns = ['ID', 'Nome', 'Telefone', 'Ref. Pagamento', 'Valor (Kz)', 'Expira em / Tempo', 'Estado']
            tabela_exibicao['Estado'] = tabela_exibicao['Estado'].apply(lambda x: "✅ Aprovado" if int(x) == 1 else "⏳ Pendente")
            
            st.dataframe(tabela_exibicao, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------
    # ABA 4: Relatórios e Estatísticas
    # -------------------------------------------------------------
    with aba4:
        st.subheader("📈 Relatórios Financeiros e Operacionais")
        
        total_recebido = get_total_revenue()
        total_prestadores = len(df) if not df.empty else 0
        aprovados_count = len(df[df['approved'].astype(int) == 1]) if not df.empty else 0
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric(label="💳 Total Geral Faturado", value=f"{total_recebido:,.2f} Kz")
        with col_m2:
            st.metric(label="🎤 Total de Prestadores", value=total_prestadores)
        with col_m3:
            st.metric(label="✅ Aprovados vs ⏳ Pendentes", value=f"{aprovados_count} / {pendentes_count}")
            
        st.markdown("---")
        st.info("Painel de controlo otimizado para monitorização de receitas e fluxo de ativações de prestadores de karaoke.")
