import time
import requests
import streamlit as st

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

# --- Funções Auxiliares (Ajuste conforme as suas originais) ---
def limpar_nome_musica(musica_field):
    if isinstance(musica_field, dict):
        return musica_field.get("titulo") or musica_field.get("nome") or "Música"
    return str(musica_field)

def atualizar_estado_pedido(token, pedido_id, novo_estado):
    try:
        requests.patch(f"{FIREBASE_URL}/pedidos/{token}/{pedido_id}.json", json={"estado": novo_estado})
    except: pass

def terminar_todas_musicas_ativas(token, pedidos):
    for p in pedidos:
        if p.get("estado") == "aprovado":
            atualizar_estado_pedido(token, p.get("id"), "terminado")

# (Certifique-se que estas funções abaixo chamam as suas APIs corretas)
def obter_video_fundo(token): return "" 
def definir_video_fundo(token, url): pass
def listar_videos_pasta_clipes(): return [] 

# --- A sua função principal, agora dentro do módulo ---
@st.fragment(run_every=3)
def renderizar_gestao_fila_prestador(provider_token):
    try:
        url_firebase = f"{FIREBASE_URL}/pedidos/{provider_token}.json?_t={time.time()}"
        response = requests.get(url_firebase, timeout=10)
        
        pedidos = []
        if response.status_code == 200 and response.json():
            data = response.json()
            pedidos = [{"id": k, **v} for k, v in data.items()]
            
        pedidos_ativos = [p for p in pedidos if p.get("estado") in ["pendente", "aprovado"]]
        pedidos_ativos.sort(key=lambda x: x.get("timestamp", 0))
        
        tocando_agora = next((p for p in pedidos_ativos if p.get("estado") == "aprovado"), None)
        pendentes = [p for p in pedidos_ativos if p.get("estado") == "pendente"]

        # [O resto do seu código HTML/Streamlit aqui...]
        # (Colei exatamente a estrutura que enviou na mensagem anterior)
        if pendentes:
            st.markdown("""<div style="background-color: rgba(0,0,0,0.95); border: 4px solid #FFC107; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
                        <div style="color: #ffffff; font-family: monospace; font-size: 15px; font-weight: bold; margin-bottom: 5px;">Confirmação de Pedido</div>
                        <div style="color: #ffffff; font-family: monospace; font-size: 18px; font-weight: bold;">QUER CANTAR</div>""", unsafe_allow_html=True)
            for p in pendentes:
                titulo_p = limpar_nome_musica(p.get("musica", {}))
                st.write(f"**{titulo_p}**") # simplificado para o exemplo
                if st.button("✅ Sim", key=f"conf_sim_{p.get('id')}"):
                    terminar_todas_musicas_ativas(provider_token, pedidos)
                    atualizar_estado_pedido(provider_token, p.get('id'), 'aprovado')
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 📋 Estado da Fila")
        # (Continue o resto do seu código original aqui...)

    except Exception as e:
        st.error(f"Erro no módulo prestador: {e}")
