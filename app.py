def show_client_screen():
    query_params = st.query_params
    provider_token = query_params.get("prestador") or query_params.get("provider", None)

    if not provider_token:
        st.error("Tela inválida. Falta o parâmetro do prestador.")
        return

    st.markdown("""
    <style>
    .stApp { background-color: #000000; color: white; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📺 FFKaraoke — Diretor Palco")
    st.markdown("---")

    try:
        response = requests.get(f"{FIREBASE_URL}/pedidos/{provider_token}.json")
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
            pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
            
            tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)
            
            if tocando_agora:
                musica = tocando_agora.get("musica", {})
                
                if isinstance(musica, dict):
                    titulo = musica.get("titulo", musica.get("nome", "Karaoke"))
                    url_video = musica.get("url_cloudinary", "") or musica.get("url", "")
                else:
                    titulo = str(musica)
                    url_video = ""
                
                if url_video and "http" in url_video:
                    if "res.cloudinary.com" in url_video and "/upload/" in url_video and "f_auto,q_auto" not in url_video:
                        url_video = url_video.replace("/upload/", "/upload/f_auto,q_auto/")
                else:
                    cloud_name = "yhwgjh7g"
                    titulo_limpo = titulo.strip()
                    encoded_title = urllib.parse.quote(titulo_limpo + ".mp4")
                    url_video = f"https://res.cloudinary.com/{cloud_name}/video/upload/f_auto,q_auto/{encoded_title}"
                
                st.markdown(f"<h2>A tocar: {titulo}</h2>", unsafe_allow_html=True)
                st.caption(f"Link do Vídeo: {url_video}")

                video_html = f"""
                <div style="display: flex; justify-content: center; background: black; padding: 10px; width: 100%;">
                    <video id="karaoke-player" width="100%" height="500px" controls autoplay playsinline style="object-fit: contain; background: black;">
                        <source src="{url_video}" type="video/mp4">
                        <source src="{url_video}" type="video/webm">
                        O seu navegador não suporta a reprodução deste vídeo.
                    </video>
                </div>
                <script>
                    var video = document.getElementById('karaoke-player');
                    video.onerror = function() {{
                        console.error("Erro ao carregar o vídeo do Cloudinary. Verifique se o ficheiro existe na nuvem.");
                    }};
                </script>
                """
                components.html(video_html, height=580)
            else:
                st.info("A aguardar início de reprodução...")
        else:
            st.info("Nenhum pedido ativo na TV.")
    except Exception as e:
        st.error(f"Erro de sincronização: {e}")

    time.sleep(5)
    st.rerun()
