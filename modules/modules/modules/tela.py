import streamlit as st

def show_tela_panel(prestador_slug="bfa_w"):
    # Estilização CSS personalizada para replicar exatamente o layout da imagem
    st.markdown("""
    <style>
    body {
        background: #070707;
        color: white;
    }
    .main {
        background: #070707;
    }
    .card-title {
        background: linear-gradient(180deg, #111, #050505);
        border: 2px solid #D4AF37;
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        color: #D4AF37;
        font-weight: bold;
        font-size: 24px;
        box-shadow: 0px 0px 20px rgba(212,175,55,.25);
        margin-bottom: 20px;
    }
    .card-next {
        background: linear-gradient(180deg, #1a0b2e, #0a0412);
        border: 2px solid #9C27B0;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        box-shadow: 0px 0px 30px rgba(156,39,176,0.4);
        margin-bottom: 15px;
    }
    .item-fila {
        background: linear-gradient(180deg, #111, #050505);
        border: 2px solid #D4AF37;
        border-radius: 12px;
        padding: 15px 20px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        box-shadow: 0px 0px 15px rgba(212,175,55,.15);
    }
    .badge-num {
        background: #D4AF37;
        color: black;
        font-weight: bold;
        border-radius: 50%;
        width: 35px;
        height: 35px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-right: 15px;
        font-size: 18px;
    }
    .player-box {
        background: linear-gradient(180deg, #111, #050505);
        border: 2px solid #D4AF37;
        border-radius: 20px;
        height: 600px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: 0px 0px 25px rgba(212,175,55,.25);
        text-align: center;
        padding: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Layout de duas colunas principais
    col_fila, col_video = st.columns([1, 1])

    with col_fila:
        # Cabeçalho Fila de Espera
        st.markdown("""
        <div class="card-title">
            🎤 FILA DE ESPERA
        </div>
        """, unsafe_allow_html=True)

        # Em Destaque: Á Seguir
        st.markdown("""
        <div class="card-next">
            <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                <span style="background: #D4AF37; color: black; font-weight: bold; border-radius: 50%; width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; margin-right: 10px;">1</span>
                <span style="color: #D4AF37; letter-spacing: 3px; font-weight: bold;">— Á Seguir —</span>
            </div>
            <h1 style="color: #FFD700; margin: 0; font-size: 36px; text-shadow: 0px 0px 10px rgba(255,215,0,0.5);">DANIEL AMORES</h1>
        </div>
        """, unsafe_allow_html=True)

        # Restantes itens da fila (2 a 6)
        participantes = [
            ("2", "MARIA SOUSA"),
            ("3", "JOÃO PEDRO"),
            ("4", "ANA LÚCIA"),
            ("5", "CARLOS MENDES"),
            ("6", "PATRÍCIA LEAL")
        ]

        for num, nome in participantes:
            st.markdown(f"""
            <div class="item-fila">
                <div class="badge-num">{num}</div>
                <div style="font-size: 20px; font-weight: bold; color: white;">👤 {nome}</div>
            </div>
            """, unsafe_allow_html=True)

    with col_video:
        # Cabeçalho Vídeo Clipe (Fundo)
        st.markdown("""
        <div class="card-title">
            📺 VÍDEO CLIPE (FUNDO)
        </div>
        """, unsafe_allow_html=True)

        # Área do Player / Ecrã de Espera
        st.markdown("""
        <div class="player-box">
            <div style="font-size: 50px; margin-bottom: 15px;">📺</div>
            <p style="color: #ccc; font-size: 18px; max-width: 350px; line-height: 1.5;">
                Aguardando o prestador selecionar um vídeo clipe no painel de controle...
            </p>
        </div>
        """, unsafe_allow_html=True)
