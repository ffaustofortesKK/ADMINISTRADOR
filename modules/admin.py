    </style>
        """, unsafe_allow_html=True)

        if not st.session_state.get("admin_logged", False):
            st.title("🔒 FFKaraoke - Área Restrita (Administrador)")
            
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
                                    <div style="background: rgba(0,0,0,0.95); border: 2px solid #FFC107; padding: 12px; border-radius: 6px; margin-bottom: 10px;">
                                        <b>Prestador:</b> {r_data.get('nome_prestador')} (Token: {tok})<br>
                                        <b>Referência / Comprovativo:</b> {r_data.get('referencia')}<br>
                                        <b>Duração Solicitada:</b> {r_data.get('tempo_plano')}
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    col_s, col_n = st.columns(2)
                                    with col_s:
                                        if st.button("✅ Aprovar Reforço", key=f"aprov_ref_{tok}_{r_id}"):
                                            r_data["approved"] = 1
                                            requests.put(f"{FIREBASE_URL}/reforcos_aprovados/{tok}/{r_id}.json", json=r_data)
                                            requests.delete(f"{FIREBASE_URL}/reforcos_pendentes/{tok}/{r_id}.json")
                                            st.success("Reforço aprovado e acumulado com sucesso!")
                                            st.rerun()
                                    with col_n:
                                        if st.button("❌ Recusar Reforço", key=f"rec_ref_{tok}_{r_id}"):
                                            requests.delete(f"{FIREBASE_URL}/reforcos_pendentes/{tok}/{r_id}.json")
                                            st.warning("Reforço recusado.")
                                            st.rerun()
                    if not tem_reforcos:
                        st.info("Nenhum pedido de reforço pendente neste momento.")
                else:
                    st.info("Nenhum pedido de reforço pendente neste momento.")
            except Exception as e:
                st.warning(f"Não foi possível carregar os reforços pendentes: {e}")

            show_admin_panel()
                
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar a aplicação: {e}")

if __name__ == "__main__":
    main()
