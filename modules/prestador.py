import time
import streamlit as st
import firebase_db

def renderizar_gestao_fila_prestador(provider_token):
    """Gestão da fila de reprodução, aprovação de pedidos e painel de controlo do prestador."""
    st.subheader("📺 Fila de Reprodução e Gestão de Pedidos")
    
    placeholder = st.empty()
    auto_refresh = st.toggle("Ativar atualização automática", value=True)
    
    while True:
        with placeholder.container():
            pedidos = firebase_db.buscar_pedidos_prestador(provider_token)
            pedidos_ativos = [p for p in pedidos if p.get('estado') in ['pendente', 'aprovado']]
            
            if not pedidos_ativos:
                st.info("A aguardar novos pedidos de músicas...")
            else:
                st.write(f"### Fila Atual ({len(pedidos_ativos)} pedidos)")
                
                tocando_agora = next((p for p in pedidos_ativos if p.get('estado') == 'aprovado'), None)
                
                if tocando_agora:
                    musica_obj = tocando_agora.get('musica', {})
                    titulo_musica = musica_obj.get('titulo', 'Karaoke') if isinstance(musica_obj, dict) else str(musica_obj)
                    st.success(f"🎵 **A Tocar Agora:** {titulo_musica} (Pedida por: {tocando_agora.get('cliente')})")
                    if st.button("Marcar como Terminado", key=f"term_{tocando_agora.get('id')}"):
                        firebase_db.atualizar_estado_pedido(provider_token, tocando_agora.get('id'), 'terminado')
                        st.rerun()
                
                st.write("---")
                st.write("**Próximos na Fila:**")
                for p in pedidos_ativos:
                    musica_obj = p.get('musica', {})
                    titulo_musica = musica_obj.get('titulo', 'Karaoke') if isinstance(musica_obj, dict) else str(musica_obj)
                    
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.text(f"{titulo_musica} ({p.get('cliente')})")
                    with col2:
                        estado_atual = p.get('estado')
                        st.text(f"Estado: {estado_atual}")
                    with col3:
                        if estado_atual == 'pendente':
                            if st.button("Aprovar", key=f"apr_{p.get('id')}"):
                                firebase_db.atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                                st.rerun()
                                
        if not auto_refresh:
            break
            
        time.sleep(4)
        st.rerun()

def show_provider_panel_custom(token):
    if not token:
        st.error("Acesso não autorizado. Por favor, aceda através do link válido fornecido na sua aprovação.")
        return

    st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffeb3b !important; }
    * { color: #ffeb3b !important; }
    .link-row {
        background: linear-gradient(180deg, #111, #050505);
        border: 1px solid #ffeb3b;
        border-radius: 8px;
        padding: 12px 18px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0px 0px 10px rgba(255,235,59,0.1);
        max-width: 600px; 
    }
    .link-title {
        color: #ffeb3b !important;
        font-weight: bold;
        font-size: 15px;
    }
    .btn-link {
        background-color: #1a1a1a;
        color: #ffeb3b !important;
        border: 1px solid #ffeb3b;
        border-radius: 6px;
        padding: 6px 20px;
        text-decoration: none;
        font-weight: bold;
        font-size: 14px;
        transition: all 0.3s ease;
    }
    .btn-link:hover {
        background-color: #ffeb3b;
        color: #000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <h2 style='color: #FFC107 !important; font-family: monospace;'>
            🎤 <span style='color: #FFC107 !important;'>PERFIL DO PRESTADOR</span> <span style='color: #ffeb3b !important;'>— FF Karaoke</span>
        </h2>
    """, unsafe_allow_html=True)
    st.markdown("---")

    base_domain = "https://appadm.streamlit.app"
    link_registo_cliente = f"{base_domain}/?page=client_register&provider={token}"
    link_tela_cliente = f"{base_domain}/?page=client_screen&provider={token}"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="link-row">
            <div class="link-title">📝 Registo do Cliente</div>
            <div><a href="{link_registo_cliente}" target="_blank" class="btn-link">link</a></div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="link-row">
            <div class="link-title">📺 Tela de Vídeos</div>
            <div><a href="{link_tela_cliente}" target="_blank" class="btn-link">link</a></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    renderizar_gestao_fila_prestador(token)
