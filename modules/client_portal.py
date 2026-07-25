import streamlit as st
from utils.db_manager import get_catalog_songs, add_client_request, get_all_providers

def show_client_portal(provider_token):
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
            btn_entrar = st.form_submit_button("Avançar")
            if btn_entrar:
                if nome_cliente.strip():
                    st.session_state.client_name = nome_cliente.strip()
                    st.rerun()
                else:
                    st.error("Por favor, introduza o seu nome.")
        return

    st.success(f"Cantor(a): **{st.session_state.client_name}**")
    if st.button("🔄 Alterar Nome"):
        st.session_state.client_name = ""
        st.rerun()

    st.markdown("---")
    
    # 2. Pesquisa de Música no Catálogo
    st.subheader("🎵 Pesquisar Música")
    songs_df = get_catalog_songs()
    
    if not songs_df.empty:
        pesquisa = st.text_input("Digite o nome da música ou cantor:", placeholder="Ex: Yuri da Cunha, Perfume...")
        
        if pesquisa:
            filtradas = songs_df[
                songs_df['title'].str.contains(pesquisa, case=False, na=False) | 
                songs_df['artist'].str.contains(pesquisa, case=False, na=False)
            ]
        else:
            filtradas = songs_df

        if not filtradas.empty:
            lista_opcoes = [f"{row['title']} - {row['artist']}" for index, row in filtradas.iterrows()]
            musica_escolhida = st.selectbox("Lista de músicas disponíveis:", options=lista_opcoes)
            
            st.write("Deseja enviar esta música?")
            col_sim, col_nao = st.columns(2)
            
            with col_sim:
                if st.button("Sim", type="primary"):
                    add_client_request(provider_token, st.session_state.client_name, musica_escolhida, 'catalogo')
                    st.success("Seu pedido foi enviado com sucesso aguarde pela sua vez na tela.")
            with col_nao:
                if st.button("Não"):
                    st.info("Pode escolher outra música na lista.")
        else:
            st.info("Nenhuma música encontrada com esse termo.")
    else:
        st.warning("O catálogo de músicas está vazio de momento.")

    st.markdown("---")
    
    # 3. Campo "Não achou? Escreva aqui"
    st.subheader("✍️ Não achou? Escreva aqui o seu pedido")
    with st.form("form_custom_song"):
        pedido_livre = st.text_input("Nome da música ou cantor que gostaria de cantar:")
        enviar_livre = st.form_submit_button("Enviar")
        
        if enviar_livre:
            if pedido_livre.strip():
                add_client_request(provider_token, st.session_state.client_name, pedido_livre.strip(), 'customizado')
                st.success("Seu pedido foi enviado, mais nem todas as músicas existem no formato karaoke.")
            else:
                st.error("Por favor, preencha o campo com o seu pedido.")
