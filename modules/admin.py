import streamlit as st
import time
import pandas as pd
from datetime import datetime
import sqlite3

# Funções de suporte de base de dados para o Admin
def get_connection():
    return sqlite3.connect('database.db', check_same_thread=False)

def get_all_providers():
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM providers", conn)
        return df
    except Exception:
        return pd.DataFrame(columns=['id', 'name', 'phone', 'payment_ref', 'expires_at', 'token', 'approved', 'amount_paid'])
    finally:
        conn.close()

def get_active_providers():
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM providers WHERE approved = 1", conn)
        return df
    except Exception:
        return pd.DataFrame(columns=['id', 'name', 'phone', 'payment_ref', 'expires_at', 'token', 'approved', 'amount_paid'])
    finally:
        conn.close()

def approve_provider(token):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE providers SET approved = 1 WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def reject_provider(token):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE providers SET approved = -1 WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def get_total_revenue():
    df = get_all_providers()
    if df.empty or 'amount_paid' not in df.columns:
        return 0.0
    return float(df[df['approved'].astype(str).isin(['1', '0', '-1'])]['amount_paid'].sum())

def show_admin_panel():
    st.markdown("""
    <style>
    .stApp {
        background: url('https://cdn.phototourl.com/free/2026-08-03-694a4a2e-9914-4da8-93b2-87538a4805ab.png') no-repeat center center fixed !important;
        background-size: cover !important;
        color: #ffffff !important;
        font-weight: bold !important;
    }
    .block-container {
        background-color: rgba(0, 0, 0, 0.75) !important;
        border: 4px solid #FFC107 !important;
        border-radius: 12px;
        padding: 3rem !important;
    }
    .link-box {
        background: rgba(17, 17, 17, 0.9);
        border: 1px solid #D4AF37;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        color: white !important;
    }
    .link-box b, .link-box a {
        color: #FFD700 !important;
    }
    .badge-pendente-global {
        background-color: #ff3333;
        color: #000000;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 900;
        font-size: 16px;
        display: inline-block;
        box-shadow: 0px 0px 10px rgba(255, 51, 51, 0.5);
    }
    p, span, label, h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
    }
    </style>
    """, unsafe_allow_html=True)

    placeholder = st.empty()

    with placeholder.container():
        df_all = get_all_providers()
        df_active = get_active_providers()
        
        pendentes_count = 0
        if not df_all.empty and 'approved' in df_all.columns:
            pendentes_count = len(df_all[df_all['approved'].astype(str).isin(['0', 'pendente'])])

        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            st.subheader("🛠️ Painel de Administração — FF Karaoke")
        with col_t2:
            if pendentes_count > 0:
                st.markdown(f"<div style='text-align: right;'>⏳ <span class='badge-pendente-global'>{pendentes_count}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align: right;'>✅ Sem Pendentes</div>", unsafe_allow_html=True)
                
        st.markdown("---")

        aba1, aba2, aba3, aba4 = st.tabs([
            "🔗 Link e QR Registo", 
            "⏳ Pedidos e Aprovação", 
            "📊 Gestão Total", 
            "📈 Relatórios e Estatísticas"
        ])

        with aba1:
            st.subheader("🔗 Portal do Prestadores")
            st.write("Partilhe este link ou o QR Code com os prestadores para que possam submeter os seus dados.")
            base_url = "https://appadm.streamlit.app/?page=register"
            
            col_l, col_q = st.columns([3, 1])
            with col_l:
                st.markdown(f"""
                <div class="link-box">
                    <b>Link Direto de Registo:</b><br>
                    <a href="{base_url}" target="_blank" style="color: #FFD700; font-size: 16px;">{base_url}</a>
                </div>
                """, unsafe_allow_html=True)
                st.info("Os prestadores que acederem a este link poderão preencher o nome, contacto e tempo pretendido.")
            with col_q:
                qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={base_url}"
                st.image(qr_api_url, width=140, caption="QR Code de Registo")

        with aba2:
            st.subheader("📋 Pedidos de Registo Pendentes")
            st.write("Analise as informações enviadas por cada prestador e aprove ou recuse o acesso.")
            
            if df_all.empty:
                st.info("Nenhum prestador registado na base de dados.")
            else:
                pendentes = df_all[df_all['approved'].astype(str).isin(['0', 'pendente'])]
                
                if pendentes.empty:
                    st.success("Não existem pedidos de registo pendentes neste momento.")
                else:
                    col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([2, 2, 2, 2, 2])
                    with col_h1: st.markdown("<h4 style='color: #FFC107;'>Nome</h4>", unsafe_allow_html=True)
                    with col_h2: st.markdown("<h4 style='color: #FFC107;'>Telefone</h4>", unsafe_allow_html=True)
                    with col_h3: st.markdown("<h4 style='color: #FFC107;'>Estabelecimento</h4>", unsafe_allow_html=True)
                    with col_h4: st.markdown("<h4 style='color: #FFC107;'>Duração Solicitada</h4>", unsafe_allow_html=True)
                    with col_h5: st.markdown("<h4 style='color: #FFC107; text-align: right;'>Ações</h4>", unsafe_allow_html=True)
                    
                    st.markdown("<hr style='margin: 5px 0 15px 0; border-color: #FFC107;'>", unsafe_allow_html=True)

                    for index, row in pendentes.iterrows():
                        nome = row.get('name', 'Desconhecido')
                        telefone = row.get('phone', 'N/A')
                        payment_ref = row.get('payment_ref', 'N/A')
                        expires_at = row.get('expires_at', 'N/A')
                        token = row.get('token', '')
                        
                        col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns([2, 2, 2, 2, 2])
                        
                        with col_r1: st.markdown(f"🎤 {nome}")
                        with col_r2: st.markdown(f"📞 {telefone}")
                        with col_r3: st.markdown(f"🏠 {payment_ref}")
                        with col_r4: st.markdown(f"⏱️ {expires_at}")
                        with col_r5:
                            sub_c1, sub_c2 = st.columns(2)
                            with sub_c1:
                                if st.button("❌ Recusar", key=f"btn_recusar_{token}"):
                                    reject_provider(token)
                                    st.warning(f"Pedido de {nome} recusado.")
                                    st.rerun()
                            with sub_c2:
                                if st.button("✅ Aprovar", key=f"btn_aprovar_{token}"):
                                    approve_provider(token)
                                    st.success(f"Prestador {nome} aprovado com sucesso!")
                                    st.rerun()
                                    
                        st.markdown("<hr style='margin: 10px 0; border-color: rgba(255,193,7,0.3);'>", unsafe_allow_html=True)

        with aba3:
            st.subheader("📑 Gestão Total de Prestadores Ativos")
            st.write("Apenas prestadores com licença ativa.")
            
            if df_active.empty:
                st.info("Nenhum prestador com sessão ativa no momento.")
            else:
                agora = datetime.now()
                lista_gestao = []
                
                for idx, row in df_active.iterrows():
                    try:
                        expira = pd.to_datetime(row['expires_at'])
                        tempo_restante = expira - agora
                        
                        if tempo_restante.total_seconds() > 0:
                            horas_restantes = int(tempo_restante.total_seconds() // 3600)
                            minutos_restantes = int((tempo_restante.total_seconds() % 3600) // 60)
                            contagem = f"⏳ {horas_restantes}h {minutos_restantes}m restantes"
                        else:
                            contagem = "⚠️ Expirado"
                    except:
                        contagem = "N/A"
                        
                    lista_gestao.append({
                        'Nome': row.get('name', ''),
                        'Telefone': row.get('phone', ''),
                        'Ref. Pagamento': row.get('payment_ref', ''),
                        'Valor Pago (Kz)': row.get('amount_paid', 0),
                        'Tempo Restante': contagem,
                        'Expira em': row.get('expires_at', '')
                    })
                
                df_gestao_view = pd.DataFrame(lista_gestao)
                st.dataframe(df_gestao_view, use_container_width=True, hide_index=True)

        with aba4:
            st.subheader("📈 Relatórios Financeiros e Histórico Completo")
            total_recebido = get_total_revenue()
            total_prestadores = len(df_all) if not df_all.empty else 0
            aprovados_count = len(df_all[df_all['approved'].astype(str) == '1']) if not df_all.empty else 0
            
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1: st.metric(label="💳 Total Geral Faturado", value=f"{total_recebido:,.2f} Kz")
            with col_m2: st.metric(label="🎤 Total de Prestadores Registados", value=total_prestadores)
            with col_m3: st.metric(label="✅ Aprovados vs ⏳ Pendentes", value=f"{aprovados_count} / {pendentes_count}")
                
            st.markdown("---")
            st.subheader("📜 Histórico Geral de Registos")
            
            if df_all.empty:
                st.info("Sem dados estatísticos registados.")
            else:
                tabela_relatorio = df_all[['id', 'name', 'phone', 'payment_ref', 'amount_paid', 'expires_at', 'approved']].copy()
                tabela_relatorio.columns = ['ID', 'Nome', 'Telefone', 'Ref. Pagamento', 'Valor (Kz)', 'Data/Expiração', 'Estado']
                
                def formatar_estado(val):
                    val_str = str(val).strip().lower()
                    if val_str in ['1', 'true', 'aprovado']:
                        return "✅ Aprovado"
                    elif val_str in ['-1', 'recusado', 'rejected']:
                        return "❌ Recusado"
                    else:
                        return "⏳ Pendente"

                tabela_relatorio['Estado'] = tabela_relatorio['Estado'].apply(formatar_estado)
                st.dataframe(tabela_relatorio, use_container_width=True, hide_index=True)

    time.sleep(10)
    st.rerun()
