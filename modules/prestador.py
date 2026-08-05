import streamlit as st
import streamlit.components.v1 as components
import requests

# Configuração e variáveis globais do sistema FF Karaoke
FIREBASE_URL = "https://ffkaraoke-default-rtdb.firebaseio.com"

def obter_video_fundo(token):
    try:
        res = requests.get(f"{FIREBASE_URL}/config_fundo/{token}.json", timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return ""

def renderizar_ecra_tv(provider_token):
    try:
        res_pedidos = requests.get(f"{FIREBASE_URL}/pedidos/{provider_token}.json", timeout=10)
        pedidos_ativos = []
        tocando_agora = None

        if res_pedidos.status_code == 200 and res_pedidos.json():
            dados = res_pedidos.json()
            if isinstance(dados, dict):
                for p_id, p_val in dados.items():
                    if isinstance(p_val, dict):
                        p_val['id'] = p_id
                        estado = p_val.get('estado', 'pendente')
                        if estado == 'tocando':
                            tocando_agora = p_val
                        elif estado in ['ativo', 'pendente']:
                            pedidos_ativos.append(p_val)

        st.markdown("""
        <style>
            .stApp { background-color: #000000; color: #FFC107; }
            h1, h2, h3, h4, h5, h6, p, span, label, div { color: #FFC107 !important; }
        </style>
        """, unsafe_allow_html=True)

        if tocando_agora:
            video_url = tocando_agora.get('video_url', '')
            cliente_nome = tocando_agora.get('cliente', 'Convidado')
            
            video_html = f"""
            <div id="countdown-screen" style="display: flex; justify-content: center; align-items: center; height: 700px; background: #000000; color: #FFC107; font-size: 100px; font-weight: bold; font-family: monospace; border: 4px solid #FFC107; border-radius: 12px;">
                3
            </div>
            
            <div id="karaoke-container" style="display: none; position: relative; width: 100%; text-align: center; background: #000000; border: 4px solid #FFC107; border-radius: 12px; padding: 10px;">
                <h3 style="color: #FFC107; font-family: monospace; margin-bottom: 10px;">🎤 A CANTAR AGORA: {cliente_nome.upper()}</h3>
                <video id="karaoke-player" width="100%" height="550px" playsinline controlslist="nodownload noremoteplayback" disablepictureinpicture style="object-fit: contain; background: black; border-radius: 8px;">
                    <source src="{video_url}" type="video/mp4">
                    O seu navegador não suporta vídeo.
                </video>
                <button onclick="stopKaraoke()" style="margin-top: 15px; background: #FFC107; color: black; border: none; padding: 10px 20px; font-weight: bold; border-radius: 5px; cursor: pointer;">Terminar Música</button>
            </div>

            <script>
                var count = 3;
                var cdScreen = document.getElementById('countdown-screen');
                var timer = setInterval(function() {
                    count--;
                    if (count > 0) {
                        cdScreen.innerText = count;
                    } else if (count === 0) {
                        cdScreen.innerText = "🎤 CANTE!";
                    } else {
                        clearInterval(timer);
                        cdScreen.style.display = 'none';
                        document.getElementById('karaoke-container').style.display = 'block';
                        var video = document.getElementById('karaoke-player');
                        video.muted = false;
                        video.play().catch(e => { video.muted = true; video.play(); });
                    }
                }, 1000);

                function stopKaraoke() {
                    var pedidoId = "{tocando_agora.get('id')}";
                    var token = "{provider_token}";
                    fetch("{FIREBASE_URL}/pedidos/" + token + "/" + pedidoId + "/estado.json", {
                        method: 'PUT',
                        body: JSON.stringify('terminado'),
                        headers: { 'Content-Type': 'application/json' }
                    }).then(() => { setTimeout(() => window.location.reload(), 300); });
                }

                var video = document.getElementById('karaoke-player');
                if (video) { video.onended = function() { stopKaraoke(); }; }
            </script>
            """
            components.html(video_html, height=750, scrolling=False)
        else:
            url_clipe_fundo = obter_video_fundo(provider_token)
            proximo_cantor = pedidos_ativos[0] if pedidos_ativos else None

            col_esq, col_dir = st.columns([1, 1])
            with col_esq:
                if proximo_cantor:
                    st.markdown(f'<div style="border: 4px solid #FFC107; border-radius: 10px; padding: 15px; background: rgba(0,0,0,0.95); margin-bottom: 15px;"><b>Á SEGUIR:</b> {proximo_cantor.get("cliente", "Convidado").upper()}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="border: 4px solid #FFC107; border-radius: 10px; padding: 15px; text-align: center; background: rgba(0,0,0,0.95); margin-bottom: 15px;"><h2>🎤 FILA DE ESPERA VAZIA</h2></div>', unsafe_allow_html=True)
            with col_dir:
                if url_clipe_fundo:
                    st.video(url_clipe_fundo)
                else:
                    st.markdown('<div style="border: 4px solid #FFC107; border-radius: 10px; padding: 50px; text-align: center;">📺 Aguardando vídeo clipe de fundo...</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro de sincronização na TV: {e}")

@st.fragment(run_every=3)
def renderizar_gestao_fila_prestador(provider_token):
    st.markdown("""
        <style>
        .stApp, .block-container { background-color: #000000 !important; color: #FFC107 !important; }
        h1, h2, h3, h4, h5, h6, p, span, label, div { color: #FFC107 !important; }
        </style>
    """, unsafe_allow_html=True)
    
    st.title(f"Painel do Prestador - Token: {provider_token}")
    
    try:
        res = requests.get(f"{FIREBASE_URL}/pedidos/{provider_token}.json", timeout=10)
        if res.status_code == 200 and res.json():
            pedidos = res.json()
            st.write("Pedidos na Fila carregados com sucesso.")
            # Aqui podes manter ou adaptar a tua tabela/gestão de pedidos atual
            for p_id, p_val in pedidos.items():
                if isinstance(p_val, dict):
                    st.markdown(f"- **Cliente:** {p_val.get('cliente')} | **Música:** {p_val.get('musica')} | **Estado:** {p_val.get('estado')}")
        else:
            st.info("Nenhum pedido na fila neste momento.")
    except Exception as e:
        st.error(f"Erro ao carregar os pedidos do Firebase: {e}")

def show_provider_panel_custom(provider_token):
    renderizar_gestao_fila_prestador(provider_token)
