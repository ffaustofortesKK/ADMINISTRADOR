import streamlit as st
import time
import pandas as pd
import requests
from datetime import datetime
from utils.db_manager import get_all_providers, get_active_providers, approve_provider, get_total_revenue

FIREBASE_URL = "https://ffkaraoke-default-rtdb.firebaseio.com"

def show_admin_panel():
    st.markdown("""
    <style>
    /* Remove o fundo preto e aplica a imagem como fundo com cobertura total */
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
    .adm-card {
        background: linear-gradient(180deg, rgba(17,17,17,0.9), rgba(5,5,5,0.9));
        border: 2px solid #D4AF37;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0px 0px 15px rgba(212,175,55,0.15);
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
            pendentes_count = len(df_all[df_all['approved'].astype(int) == 0])

        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            st.subheader("🛠️ Painel de Administração — FF Karaoke")
        with col_t2:
            if pendentes_count > 0:
                st.markdown(f"⏳ Pendentes: <span class='badge-pendente-global'>{pendentes_count}</span>", unsafe_allow_html=True)
            else:
                st.markdown("✅ Sem Pendentes", unsafe_allow_html=True)
                
        st.markdown("---")

        aba1, aba2, aba3, aba4 = st.tabs([
            "🔗 Link e QR Registo", 
            "⏳ Pedidos e Aprovação", 
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
        # ABA 2: Pedidos e Aprovação (Novos Registos e Reforços de Tempo)
        # -------------------------------------------------------------
        with aba2:
            st.subheader("📋 Pedidos de Registo Pendentes")
            st.write("Analise as informações enviadas por cada prestador e aprove ou recuse o acesso conforme a confirmação do pagamento.")
            
            if df_all.empty:
                st.info("Nenhum prestador registado na base de dados.")
            else:
                pendentes = df_all[df_all['approved'].astype(int) == 0]
                
                if pendentes.empty:
                    st.success("Não existem novos pedidos de registo pendentes.")
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
                        
                        col_aprov, col_recus = st.columns(2)
                        with col_aprov:
                            if st.button(f"✅ Aprovar Prestador", key=f"btn_aprovar_{token}"):
                                approve_provider(token)
                                st.success(f"Prestador {nome} aprovado com sucesso!")
                                st.rerun()
                        with col_recus:
                            if st.button(f"❌ Recusar Prestador", key=f"btn_recusar_{token}"):
                                try:
                                    # Atualiza o estado para -1 (Recusado) para notificar o prestador no ecrã de espera
                                    requests.patch(f"{FIREBASE_URL}/prestadores/{token}.json", json={"approved": -1}, timeout=10)
                                    st.warning(f"Registo de {nome} marcado como recusado.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao recusar prestador: {e}")
                                    
                        st.markdown("---")

            # --- SECÇÃO DE REFORÇOS DE TEMPO PENDENTES ---
            st.markdown("---")
            st.subheader("⚡ Gestão de Reforços de Tempo Pendentes")
            
            try:
                res_all_ref = requests.get(f"{FIREBASE_URL}/reforcos_pendentes.json", timeout=10)
                if res_all_ref.status_code == 200 and res_all_ref.json():
                    all_refs = res_all_ref.json()
                    tem_reforcos = False
                    
                    for tok, refs_dict in all_refs.items():
                        if isinstance(refs_dict, dict):
                            for r_id, r_data in refs_dict.items():
                                if r_data.get("approved", 0) == 0:
                                    tem_reforcos = True
                                    st.markdown(f"""
                                    <div class="adm-card">
                                        <h3 style="color: #D4AF37; margin-top: 0;">⚡ Reforço: {r_data.get('nome_prestador')}</h3>
                                        <p style="margin: 4px 0; color: #ccc;"><b>🔑 Token:</b> {tok}</p>
                                        <p style="margin: 4px 0; color: #ccc;"><b>💳 Referência / Comprovativo:</b> <code>{r_data.get('referencia')}</code></p>
                                        <p style="margin: 4px 0; color: #ccc;"><b>⏱️ Duração Solicitada:</b> {r_data.get('tempo_plano')}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    col_s, col_n = st.columns(2)
                                    with col_s:
                                        if st.button("✅ Aprovar Reforço", key=f"aprov_ref_{tok}_{r_id}"):
                                            r_data["approved"] = 1
                                            requests.put(f"{FIREBASE_URL}/reforcos_aprovados/{tok}/{r_id}.json", json=r_data)
                                            requests.delete(f"{FIREBASE_URL}/reforcos_pendentes/{tok}/{r_id}.json")
                                            st.success("Reforço aprovado com sucesso!")
                                            st.rerun()
                                            
                                    with col_n:
                                        if st.button("❌ Recusar Reforço", key=f"rec_ref_{tok}_{r_id}"):
                                            requests.delete(f"{FIREBASE_URL}/reforcos_pendentes/{tok}/{r_id}.json")
                                            st.warning("Reforço recusado.")
                                            st.rerun()
                                            
                                    st.markdown("---")
                                    
                    if not tem_reforcos:
                        st.info("Nenhum pedido de reforço pendente neste momento.")
                else:
                    st.info("Nenhum pedido de reforço pendente neste momento.")
                    
            except Exception as e:
                st.warning(f"Não foi possível carregar os reforços pendentes: {e}")

        # -------------------------------------------------------------
        # ABA 3: Gestão Total (Ativos com contagem decrescente de tempo)
        # -------------------------------------------------------------
        with aba3:
            st.subheader("📑 Gestão Total de Prestadores Ativos (Com Contagem Decrescente)")
            st.write("Apenas prestadores com licença ativa. Assim que o tempo expirar, o prestador desaparece automaticamente daqui.")
            
            if df_active.empty:
                st.info("Nenhum prestador com sessão ativa no momento.")
            else:
                agora = datetime.now()
                lista_gestao = []
                
                for idx, row in df_active.iterrows():
                    expira = pd.to_datetime(row['expires_at'])
                    tempo_restante = expira - agora
                    
                    if tempo_restante.total_seconds() > 0:
                        horas_restantes = int(tempo_restante.total_seconds() // 3600)
                        minutos_restantes = int((tempo_restante.total_seconds() % 3600) // 60)
                        contagem = f"⏳ {horas_restantes}h {minutos_restantes}m restantes"
                    else:
                        contagem = "⚠️ Expirado"
                        
                    lista_gestao.append({
                        'Nome': row['name'],
                        'Telefone': row['phone'],
                        'Ref. Pagamento': row['payment_ref'],
                        'Valor Pago (Kz)': row['amount_paid'],
                        'Tempo Restante': contagem,
                        'Expira em': row['expires_at']
                    })
                
                df_gestao_view = pd.DataFrame(lista_gestao)
                st.dataframe(df_gestao_view, use_container_width=True, hide_index=True)

        # -------------------------------------------------------------
        # ABA 4: Relatórios e Estatísticas (Histórico Completo)
        # -------------------------------------------------------------
        with aba4:
            st.subheader("📈 Relatórios Financeiros e Histórico Completo")
            st.write("Registo integral de todas as transações, valores e tempos solicitados (incluindo licenças expiradas).")
            
            total_recebido = get_total_revenue()
            total_prestadores = len(df_all) if not df_all.empty else 0
            aprovados_count = len(df_all[df_all['approved'].astype(int) == 1]) if not df_all.empty else 0
            
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric(label="💳 Total Geral Faturado", value=f"{total_recebido:,.2f} Kz")
            with col_m2:
                st.metric(label="🎤 Total de Prestadores Registados", value=total_prestadores)
            with col_m3:
                st.metric(label="✅ Aprovados vs ⏳ Pendentes", value=f"{aprovados_count} / {pendentes_count}")
                
            st.markdown("---")
            st.subheader("📜 Histórico Geral de Registos")
            
            if df_all.empty:
                st.info("Sem dados estatísticos registados.")
            else:
                tabela_relatorio = df_all[['id', 'name', 'phone', 'payment_ref', 'amount_paid', 'expires_at', 'approved']].copy()
                tabela_relatorio.columns = ['ID', 'Nome', 'Telefone', 'Ref. Pagamento', 'Valor (Kz)', 'Data/Expiração', 'Estado']
                tabela_relatorio['Estado'] = tabela_relatorio['Estado'].apply(lambda x: "✅ Aprovado" if int(x) == 1 else ("❌ Recusado" if int(x) == -1 else "⏳ Pendente"))
                
                st.dataframe(tabela_relatorio, use_container_width=True, hide_index=True)

    time.sleep(10)
    st.rerun()
