import streamlit as st
import datetime
import time

st.set_page_config(page_title="FF Karaoke Cloud", page_icon="🎤", layout="wide")

# Initialize session state for mock database / state management
if "provider_logged_in" not in st.session_state:
    st.session_state.provider_logged_in = True
if "provider_name" not in st.session_state:
    st.session_state.provider_name = "CARLOS"
if "remaining_seconds" not in st.session_state:
    st.session_state.remaining_seconds = 35 * 60  # e.g., 35 minutes remaining to test alert, or change to 7200 for 2 hours
if "refill_requests" not in st.session_state:
    st.session_state.refill_requests = [
        {"id": 1, "provider": "CARLOS", "hours": 2, "amount": "12.000 Kz", "proof": "Ref_12345", "status": "Pendente"}
    ]
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

st.markdown("""
<style>
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.2; }
        100% { opacity: 1; }
    }
    .alert-banner {
        background-color: #ff4b4b;
        color: white;
        padding: 15px;
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        border-radius: 8px;
        animation: blink 1s infinite;
        margin-bottom: 20px;
    }
    .green-btn {
        background-color: #28a745 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("Navigação")
app_mode = st.sidebar.radio("Escolha o Painel", ["Painel do Prestador", "Gestão do Administrador"])

# --- PAINEL DO PRESTADOR ---
if app_mode == "Painel do Prestador":
    # Cabeçalho dinâmico com o nome do prestador
    st.markdown(f"## PAINEL DO PRESTADOR: {st.session_state.provider_name}")
    
    # Contagem decrescente e Alerta de tempo (<= 30 minutos / 1800 segundos)
    if st.session_state.remaining_seconds <= 1800:
        st.markdown(
            '<div class="alert-banner">O SEU TEMPO ESTA TERMINANDO. PARA QUE NÃO PERCAS OS SEUS REGISTOS PEÇA REFORÇO DE TEMPO</div>', 
            unsafe_allow_html=True
        )
    
    # Format remaining time
    hours_left = st.session_state.remaining_seconds // 3600
    minutes_left = (st.session_state.remaining_seconds % 3600) // 60
    seconds_left = st.session_state.remaining_seconds % 60
    time_str = f"{hours_left:02d}:{minutes_left:02d}:{seconds_left:02d}"
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.metric(label="Tempo Restante de Licença", value=time_str)
    with col2:
        if st.session_state.remaining_seconds <= 1800:
            st.warning("⚠️ Tempo crítico! Faça o seu reforço.")
            with st.expander("🚀 Pedido de Reforço Rápido"):
                refill_option = st.selectbox(
                    "Selecione a Duração e Valor",
                    [
                        "2 Horas - 12 Mil Kwanzas",
                        "3 Horas - 15 Mil Kwanzas",
                        "4 Horas - 20 Mil Kwanzas"
                    ]
                )
                proof_code = st.text_input("Comprovativo / Referência de Pagamento")
                if st.button("Enviar Pedido de Reforço"):
                    hours_val = 2 if "2 Horas" in refill_option else (3 if "3 Horas" in refill_option else 4)
                    amount_val = "12.000 Kz" if hours_val == 2 else ("15.000 Kz" if hours_val == 3 else "20.000 Kz")
                    st.session_state.refill_requests.append({
                        "id": len(st.session_state.refill_requests) + 1,
                        "provider": st.session_state.provider_name,
                        "hours": hours_val,
                        "amount": amount_val,
                        "proof": proof_code,
                        "status": "Pendente"
                    })
                    st.success("Pedido de reforço enviado com sucesso!")

    st.divider()

    # Seção de Vídeo Clipe
    st.markdown("### Gestão de Vídeo Clipe")
    search_query = st.text_input("Pesquisar Vídeo Clipe na Biblioteca")
    
    # Botão com cor verde para Pesquisar Vídeo clipe
    st.markdown("""
        <style>
        div.stButton > button:first-child {
            background-color: #28a745;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if st.button("Pesquisar Vídeo clipe"):
        st.info(f"A pesquisar por: {search_query}...")

    # Registro Inicial de Novos Prestadores (Sem campos de referência/comprovativo)
    st.divider()
    with st.expander("Registo / Configuração Inicial de Novo Prestador"):
        new_name = st.text_input("Nome do Prestador")
        new_email = st.text_input("Email de Contato")
        if st.button("Registar Prestador"):
            if new_name:
                st.session_state.provider_name = new_name.upper()
                st.success(f"Prestador {st.session_state.provider_name} registado com sucesso sem exigência de comprovativo inicial!")

# --- GESTÃO DO ADMINISTRADOR ---
elif app_mode == "Gestão do Administrador":
    st.markdown("## PAINEL DO ADMINISTRADOR - GESTÃO TOTAL")
    
    admin_tab1, admin_tab2 = st.tabs(["Gestão de Prestadores", "Reforço (Aprovações)"])
    
    with admin_tab1:
        st.subheader("Lista de Prestadores Ativos")
        st.write(f"Prestador atual em foco: **{st.session_state.provider_name}**")
        st.write(f"Tempo restante: {st.session_state.remaining_seconds // 60} minutos")
        
    with admin_tab2:
        st.subheader("Gestão de Pedidos de Reforço")
        
        if not st.session_state.refill_requests:
            st.info("Nenhum pedido de reforço pendente.")
        else:
            for req in st.session_state.refill_requests:
                cols = st.columns([2, 2, 2, 2, 2])
                cols[0].write(f"**{req['provider']}**")
                cols[1].write(f"{req['hours']} Horas ({req['amount']})")
                cols[2].write(f"Ref: {req['proof']}")
                cols[3].write(f"Status: {req['status']}")
                
                if req['status'] == "Pendente":
                    btn_col1, btn_col2 = cols[4].columns(2)
                    if btn_col1.button("Sim", key=f"sim_{req['id']}"):
                        req['status'] = "Aprovado"
                        # Soma automática ao tempo restante (horas convertidas em segundos)
                        st.session_state.remaining_seconds += req['hours'] * 3600
                        st.success(f"Pedido de {req['provider']} aprovado! {req['hours']} horas adicionadas.")
                        st.rerun()
                    if btn_col2.button("Não", key=f"nao_{req['id']}"):
                        req['status'] = "Rejeitado"
                        st.warning(f"Pedido de {req['provider']} rejeitado.")
                        st.rerun()
