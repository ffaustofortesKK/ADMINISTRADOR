import streamlit as st
from utils.db_manager import get_catalog_songs, add_client_request, get_all_providers

def show_client_portal(provider_token):
    # Validar se o token do prestador existe e está ativo
    df_prov = get_all_providers()
    prestador = df_prov[df_prov['token'] == provider_token]
    
    if prestador.empty:
        st.error("❌ Link de prestador inválido ou inexistente.")
        return

    row_prov = prestador.iloc[0]
    if row_prov.get('approved', 0) != 1:
        st.warning("⏳ Este painel de prestador encontra-se temporariamente inativo ou expirado.")
        return

    st.title("🎤 FFKaraoke - Escolha a sua Música")
    st.write(f"Bem-vindo(a) ao espaço de karaoke gerido por **{row_prov['name']}**!")

    # 1. Registo do Nome do Cliente
    if "client_name" not in st.session_state:
        st.session_state.client_name = ""

    if not st.session_state.client_name:
        with st.form("form_client_login"):
            nome_cliente = st.text_input("Introduza o seu Nome para começar:")
            btn_entrar = st.form_submit_button("Avançar para o Catálogo")
            if btn_entrar:
                if nome_cliente.strip():
                    st.session_state.client_name = nome_cliente.strip()
                    st.rerun()
                else:
                    st.error("Por favor, introduza o seu nome.")
        return

    st.success(cantor := f"Cantor(a): **{st.session_state.client_name}**")
    if st.button("🔄 Alterar Nome"):
        st.session_state.client_name = ""
        st.rerun()

    st.markdown("---")
    
    # Abas para Escolher do Catálogo ou Escrever Pedido Personalizado
    tab_cat, tab_custom = st.tabs(["🎵 Pesquisar no Catálogo", "✍️ Não achou? Escreva aqui"])

    with tab_cat:
        st.subheader("Pesquisa de Músicas Disponíveis")
        songs_df = get_catalog_songs()
        
        if not songs_df.empty:
            pesquisa = st.text_input("Pesquisar por título ou artista:", placeholder="Ex: Yuri da Cunha, Perfume...")
            
            if pesquisa:
                filtradas = songs_df[
                    songs_df['title'].str.contains(pesquisa, case=False, na=False) | 
                    songs_df['artist'].str.contains(pesquisa, case=False, na=False)
                ]
            else:
                filtradas = songs_df

            if not filtradas.empty:
                # Criar formato de seleção amigável
                lista_opcoes = [f"{row['title']} - {row['artist']}" for index, row in filtradas.iterrows()]
                musica_escolhida = st.selectbox("Selecione a música pretendida:", options=lista_opcoes)
                
                # Confirmação antes de enviar (Sim / Não)
                st.write("Confirma o envio desta música para a fila de espera?")
                col_sim, col_nao = st.columns(2)
                
                with col_sim:
                    if st.button("✅ Sim, Enviar Pedido", type="primary"):
                        add_client_request(provider_token, st.session_state.client_name, musica_escolhida, 'catalogo')
                        st.success("🎉 O seu pedido foi enviado com sucesso! Aguarde pela sua vez na tela.")
                with col_nao:
                    if st.button("❌ Escolher Outra"):
                        st.info("Pode selecionar outra música na lista acima.")
            else:
                st.info("Nenhuma música encontrada com esse termo.")
        else:
            st.warning("O catálogo de músicas está vazio de momento.")

    with tab_custom:
        st.subheader("Pedir Música Personalizada")
        st.write("Caso não encontre a música que pretende cantar no catálogo acima, escreva abaixo o nome do cantor e da música:")
        
        with st.form("form_custom_song"):
            pedido_livre = st.text_area("Escreva aqui o seu pedido (Nome da música e Cantor):", placeholder="Ex: C4 Pedro - Vamos Ficar")
            enviar_livre = st.form_submit_button("Enviar Pedido Personalizado")
            
            if enviar_livre:
                if pedido_livre.strip():
                    add_client_request(provider_token, st.session_state.client_name, pedido_livre.strip(), 'customizado')
                    st.success("Seu pedido foi enviado, mais nem todas as músicas existem no formato karaoke.")
                else:
                    st.error("Por favor, escreva o nome da música ou cantor.")
