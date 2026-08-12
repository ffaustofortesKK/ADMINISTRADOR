import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

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
        color: #ffffff;
        padding: 9px 21px;
        border-radius: 50%;
        font-weight: 900;
        font-size: 24px;
        display: inline-block;
        box-shadow: 0px 0px 14px rgba(255, 51, 51, 0.7);
        text-align: center;
        min-width: 52px;
    }
    p, span, label, h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
    }
    </style>
    """, unsafe_allow_html=True)

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
            st.markdown(f"⏳ <span class='badge-pendente-global'>{pendentes_count}</span>", unsafe_allow_html=True)
        else:
            st.markdown("✅ Sem Pendentes", unsafe_allow_html=True)
            
    st.markdown("---")

    aba1, aba2, aba3, aba4 = st.tabs([
        "🔗 Link e QR Registo", 
        "⏳ Pedidos e Aprovação", 
        "📊 Gestão Total", 
        "📈 Relatórios e Estatísticas"
    ])

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
                # Cabeçalho da grelha
                st.markdown("""
                <div style="background: linear-gradient(180deg, rgba(30,30,30,0.95), rgba(15,15,15,0.95)); border: 2px solid #FFC107; border-radius: 6px 6px 0 0; padding: 8px 12px; margin-bottom: 0px; border-bottom: 1px solid #FFC107;">
                """, unsafe_allow_html=True)
                
                hc1, hc2, hc3, hc4, hc5 = st.columns([2.0, 1.8, 1.8, 2.6, 1.8])
                with hc1:
                    st.markdown("<div style='text-align: center; font-weight: bold; color: #FFD700; font-size: 20px;'>Nome</div>", unsafe_allow_html=True)
                with hc2:
                    st.markdown("<div style='text-align: center; font-weight: bold; color: #FFD700; font-size: 20px;'>Telefone:</div>", unsafe_allow_html=True)
                with hc3:
                    st.markdown("<div style='text-align: center; font-weight: bold; color: #FFD700; font-size: 20px;'>Estabelecimento</div>", unsafe_allow_html=True)
                with hc4:
                    st.markdown("<div style='text-align: center; font-weight: bold; color: #FFD700; font-size: 20px;'>Duração Solicitada</div>", unsafe_allow_html=True)
                with hc5:
                    st.markdown("<div style='text-align: center; font-weight: bold; color: #FFD700; font-size: 20px;'>Ações</div>", unsafe_allow_html=True)
                    
                st.markdown('</div>', unsafe_allow_html=True)

                for index, row in pendentes.iterrows():
                    nome = row.get('name', 'Desconhecido')
                    telefone = row.get('phone', 'N/A')
                    estabelecimento = row.get('estabelecimento', row.get('venue', 'N/A'))
                    payment_ref = row.get('payment_ref', 'N/A')
                    amount_paid = row.get('amount_paid', 'N/A')
                    expires_at = row.get('expires_at', 'N/A')
                    token = row.get('token', '')
                    
                    # Linhas compactas com texto dos dados (Nome, Telefone, Estabelecimento) aumentado em 80% (cerca de 24px)
                    st.markdown("""
                    <div style="background: linear-gradient(180deg, rgba(17,17,17,0.95), rgba(5,5,5,0.95)); border-left: 2px solid #FFC107; border-right: 2px solid #FFC107; border-bottom: 2px solid #FFC107; padding: 2px 8px; margin-bottom: 3px;">
                    """, unsafe_allow_html=True)
                    
                    rc1, rc2, rc3, rc4, rc5 = st.columns([2.0, 1.8, 1.8, 2.6, 1.8])
                    
                    with rc1:
                        st.markdown(f"""
                        <div style="border-right: 2px solid #444; padding-right: 4px; line-height: 1.1; margin-top: 2px; font-size: 24px;">
                            🎤 <b style="color: #ffffff;">{nome}</b>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with rc2:
                        st.markdown(f"""
                        <div style="border-right: 2px solid #444; padding-right: 4px; line-height: 1.1; margin-top: 2px; font-size: 24px;">
                            📞 <b style="color: #FFD700;">{telefone}</b>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with rc3:
                        st.markdown(f"""
                        <div style="border-right: 2px solid #444; padding-right: 4px; line-height: 1.1; margin-top: 2px; font-size: 24px;">
                            🏠 <b style="color: #FFD700;">{estabelecimento}</b>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with rc4:
                        st.markdown(f"""
                        <div style="border-right: 2px solid #444; padding-right: 4px; line-height: 1.0; margin-top: 1px; font-size: 15px;">
                            <b style="color: #ffffff;">{expires_at}</b><br><span style='font-size: 12px; color: #FFD700;'>Ref: {payment_ref} ({amount_paid})</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with rc5:
                        b_col1, b_col2 = st.columns(2)
                        with b_col1:
                            if st.button("❌ Recusar", key=f"btn_rec_{token}"):
                                try:
                                    atualizado = False
                                    for node in ["providers", "prestadores", "prestadores_pendentes"]:
                                        resp = requests.get(f"{FIREBASE_URL}/{node}.json", timeout=10)
                                        if resp.status_code == 200 and resp.json():
                                            dados = resp.json()
                                            for key, val in dados.items():
                                                if isinstance(val, dict) and val.get("token") == token:
                                                    requests.patch(f"{FIREBASE_URL}/{node}/{key}.json", json={"approved": -1}, timeout=10)
                                                    atualizado = True
                                                    
                                    if not atualizado:
                                        requests.patch(f"{FIREBASE_URL}/providers/{token}.json", json={"approved": -1}, timeout=10)
                                        requests.patch(f"{FIREBASE_URL}/prestadores/{token}.json", json={"approved": -1}, timeout=10)
                                        
                                    st.warning(f"Registo de {nome} recusado com sucesso e enviado para o histórico.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao recusar: {e}")
                        with b_col2:
                            if st.button("✅ Aprovar", key=f"btn_aprov_{token}"):
                                approve_provider(token)
                                st.success(f"Prestador {nome} aprovado com sucesso!")
                                st.rerun()
                            
                    st.markdown('</div>', unsafe_allow_html=True)

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
                                <div style="background: linear-gradient(180deg, rgba(17,17,17,0.95), rgba(5,5,5,0.95)); border: 2px solid #FFC107; border-radius: 6px; padding: 8px; margin-bottom: 8px;">
                                    <b>⚡ Reforço:</b> {r_data.get('nome_prestador')} | <b>Duração:</b> {r_data.get('tempo_plano')} | <b>Ref:</b> <code>{r_data.get('referencia')}</code>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                rc1, rc2, rc3 = st.columns([6, 1.2, 1.2])
                                with rc2:
                                    if st.button("❌ Recusar", key=f"rec_ref_{tok}_{r_id}"):
                                        requests.delete(f"{FIREBASE_URL}/reforcos_pendentes/{tok}/{r_id}.json")
                                        st.warning("Reforço recusado.")
                                        st.rerun()
                                with rc3:
                                    if st.button("✅ Aprovar", key=f"aprov_ref_{tok}_{r_id}"):
                                        r_data["approved"] = 1
                                        requests.put(f"{FIREBASE_URL}/reforcos_aprovados/{tok}/{r_id}.json", json=r_data)
                                        requests.delete(f"{FIREBASE_URL}/reforcos_pendentes/{tok}/{r_id}.json")
                                        st.success("Reforço aprovado!")
                                        st.rerun()
                                st.markdown("<hr style='margin: 8px 0; border-color: #333;'>", unsafe_allow_html=True)
                                
                if not tem_reforcos:
                    st.info("Nenhum pedido de reforço pendente neste momento.")
            else:
                st.info("Nenhum pedido de reforço pendente neste momento.")
        except Exception as e:
            st.warning(f"Não foi possível carregar os reforços pendentes: {e}")

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

    with aba4:
        st.subheader("📈 Relatórios Financeiros e Histórico Completo")
        st.write("Registo integral de todas as transações, valores e tempos solicitados (incluindo licenças expiradas e recusadas).")
        
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


def main():
    try:
        query_params = st.query_params
        
        if "page" in query_params and query_params["page"] == "register":
            if original_show_register_page:
                original_show_register_page()
            else:
                st.error("Página de registo não disponível.")
            return

        if "page" in query_params and query_params["page"] == "client_register":
            show_client_page()
            return

        token = query_params.get("prestador") or query_params.get("token") or query_params.get("provider")
        
        if token:
            df = get_all_providers()
            if df.empty or 'token' not in df.columns or not (df['token'] == token).any():
                show_provider_panel_center(token)
                return
                
            prior_prestador = df[df['token'] == token]
            if not prior_prestador.empty:
                row = prior_prestador.iloc[0]
                status_aprov = int(row.get('approved', 1))
                if status_aprov == 1:
                    show_provider_panel_custom(token)
                    return
                elif status_aprov == -1:
                    st.error("❌ O seu registo foi recusado pelo Administrador. Por favor, verifique os dados ou entre em contacto.")
                    return
                else:
                    st.warning("⏳ O seu registo aguarda aprovação do Administrador.")
                    return
            else:
                show_provider_panel_custom(token)
                return
            
        st.markdown("""
            <style>
            .stApp {
                background-color: #000000 !important;
                color: #ffffff !important;
                font-weight: bold !important;
            }
            .block-container {
                background-color: #000000 !important;
                border: 4px solid #FFC107 !important;
                border-radius: 12px;
                padding: 3rem !important;
            }
            h1, h2, h3, h4, h5, h6, p, span, label, div, button, input {
                font-weight: bold !important;
                text-shadow: 1px 1px 3px rgba(0,0,0,0.9);
            }
            </style>
        """, unsafe_allow_html=True)

        if not st.session_state.get("admin_logged", False):
            st.title("🔒 FFKaraoke - (Administrador)")
            with st.form("form_admin_login"):
                senha = st.text_input("Palavra-passe de Administrador", type="password")
                submitted = st.form_submit_button("Entrar")
                if submitted:
                    if senha == "ffkaraoke2026" or senha == "admin123":
                        st.session_state["admin_logged"] = True
                        st.success("Sessão iniciada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Palavra-passe incorreta.")

        if st.session_state.get("admin_logged", False):
            show_admin_panel()
                
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar a aplicação: {e}")

if __name__ == "__main__":
    main()
