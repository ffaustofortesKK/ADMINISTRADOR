def show_provider_panel_custom(provider_token):
    st.markdown("### 🎤 Painel do Prestador — FF Karaoke")
    st.markdown(f"<p style='color: #888; font-size: 13px;'>Token Ativo: <code>{provider_token}</code></p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Auto-refresh a cada 3 segundos para capturar novos pedidos instantaneamente
    st.markdown("""
        <script>
            setTimeout(function() {
                window.location.reload();
            }, 3000);
        </script>
    """, unsafe_allow_html=True)

    # Construção correta dos links
    host_dominio = st.context.headers.get('Host', 'grupoffkaraoke.streamlit.app')
    link_cliente_rel = f"/?page=client_register&prestador={provider_token}"
    link_tv_rel = f"/?page=client_screen&prestador={provider_token}"
    
    link_cliente_absoluto = f"https://{host_dominio}{link_cliente_rel}"
    qr_url_cliente = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(link_cliente_absoluto)}"

    # Layout em colunas nativas do Streamlit para alinhar perfeitamente os links e o QR Code
    col_links, col_qr = st.columns([3, 1])
    
    with col_links:
        st.markdown(f"""
            <div style="background-color: #e8f0fe; border: 1px solid #d2e3fc; padding: 12px 15px; border-radius: 8px; margin-bottom: 10px;">
                <span style="font-size: 14px; color: #202124;">📎 <b>Link do Cliente:</b><br><a href="{link_cliente_rel}" target="_blank" rel="noopener noreferrer" style="color: #1a73e8; text-decoration: none; word-break: break-all;">{link_cliente_rel}</a></span>
            </div>
            <div style="background-color: #e8f0fe; border: 1px solid #d2e3fc; padding: 12px 15px; border-radius: 8px;">
                <span style="font-size: 14px; color: #202124;">📺 <b>Link da TV:</b><br><a href="{link_tv_rel}" target="_blank" rel="noopener noreferrer" style="color: #1a73e8; text-decoration: none; word-break: break-all;">{link_tv_rel}</a></span>
            </div>
        """, unsafe_allow_html=True)
        
    with col_qr:
        st.markdown("<p style='font-size: 12px; font-weight: bold; text-align: center; margin-bottom: 4px;'>📱 QR Code</p>", unsafe_allow_html=True)
        st.image(qr_url_cliente, width=150)

    st.markdown("---")
    st.markdown("### 🎬 Fila de Pedidos Atual")

    try:
        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json?_t={time.time()}"
        response = requests.get(url_firebase, timeout=10)
        
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
            
            tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)
            pendentes = [p for p in pedidos_ativos if p.get("estado") == "pendente"]

            if pedidos_ativos:
                html_lista = '<div style="background-color: #111111; border: 2px solid #333333; padding: 15px; border-radius: 8px; color: #ffffff; max-width: 550px; font-family: monospace; font-size: 15px; margin-bottom: 20px;">'
                html_lista += '<div style="color: #4CAF50; font-weight: bold; margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px;">ESTADO DA FILA:</div>'
                for idx, p in enumerate(pedidos_ativos, start=1):
                    titulo_musica = limpar_nome_musica(p.get("musica", {}))
                    cliente_nome = p.get("cliente", "Convidado")
                    estado_atual = p.get("estado")
                    badge = "🎵 [A Tocar]" if estado_atual == "aprovado" else "⏳ [Pendente]"
                    cor_badge = "#4CAF50" if estado_atual == "aprovado" else "#FFC107"
                    html_lista += f'<div style="padding: 4px 0;"><b>{idx}.</b> {titulo_musica} <span style="color:#aaa; font-size:13px;">({cliente_nome})</span> <span style="color:{cor_badge}; font-size:12px; float:right;">{badge}</span></div>'
                html_lista += '</div>'
                st.markdown(html_lista, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="background-color: #111111; border: 2px solid #333333; padding: 15px; border-radius: 8px; color: #888; max-width: 550px; font-family: monospace; font-size: 15px; margin-bottom: 20px;">
                        <div>Nenhum pedido na lista neste momento. À espera de novos pedidos...</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 📋 Gestão de Fila e Controlo")

            if tocando_agora:
                titulo_tocando = limpar_nome_musica(tocando_agora.get("musica", {}))
                st.success(f"🎵 A tocar agora: **{titulo_tocando}** (Cliente: {tocando_agora.get('cliente', 'Convidado')})")
                if st.button("⏹️ Terminar Música Atual", key=f"term_{tocando_agora.get('id')}"):
                    terminar_todas_musicas_ativas(provider_token, pedidos)
                    st.success("Música terminada e tela limpa com sucesso!")
                    st.rerun()

            if not pendentes:
                st.write("Fila de pendentes vazia. Os pedidos feitos pelos clientes aparecerão aqui automaticamente.")
            else:
                st.write("### Pedidos Pendentes para Aprovar:")
                for idx, p in enumerate(pendentes, start=1):
                    titulo_musica = limpar_nome_musica(p.get("musica", {}))
                    cliente_nome = p.get("cliente", "Convidado")
                    
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.write(f"**Pedido** - {titulo_musica} *(Cliente: {cliente_nome})*")
                    with col_btn:
                        if st.button(f"▶️ Play", key=f"btn_play_{p.get('id')}"):
                            terminar_todas_musicas_ativas(provider_token, pedidos)
                            atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                            st.success(f"Música '{titulo_musica}' enviada para a tela!")
                            st.rerun()
        else:
            st.info("Nenhum pedido encontrado no Firebase para este prestador. Abra o link do cliente e envie uma música para testar.")
            
    except Exception as e:
        st.error(f"Erro ao carregar os pedidos do Firebase: {e}")
