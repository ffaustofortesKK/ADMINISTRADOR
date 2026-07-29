import sys
import os

# Configuração estrita do caminho absoluto para evitar erros de importação
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

utils_path = os.path.join(current_dir, "utils")
if utils_path not in sys.path:
    sys.path.insert(0, utils_path)

modules_path = os.path.join(current_dir, "modules")
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

import time
import datetime
import requests
import urllib.parse
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import cloudinary
import cloudinary.api
import cloudinary.uploader
import cloudinary.search

# Configuração do Cloudinary com as suas credenciais oficiais
cloudinary.config(
    cloud_name="yhwgjh7g",
    api_key="852434629995691",
    api_secret="TU_ejil7wKYY15xHjDcRVfbk6Ow",
    secure=True
)

# Importações seguras com fallbacks para evitar crash total da aplicação
try:
    from utils.db_manager import init_db, get_all_providers, delete_provider, add_provider_record
except Exception:
    def init_db(): pass
    def get_all_providers(): 
        return pd.DataFrame(columns=['token', 'approved', 'nome_prestador', 'data_registo'])
    def delete_provider(token): pass
    def add_provider_record(token, nome): pass

FIREBASE_URL = "https://grupoffkaraoke-default-rtdb.firebaseio.com"

st.set_page_config(
    page_title="FFKaraoke - Painel de Administração e Gestão",
    page_icon="🎤",
    layout="wide"
)

# --- BLOQUEIO TOTAL E RADICAL DO BOTÃO GERENCIAR APLICATIVO E ELEMENTOS CLOUD ---
st.markdown("""
    <style>
    div[data-testid="stToolbar"], header, footer, 
    div[data-testid="stDecoration"], #MainMenu, 
    .stAppViewerBadge, div[class*="viewerBadge"], 
    iframe[src*="analytics"], div[class*="settings"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    </style>
""", unsafe_allow_html=True)

try:
    init_db()
except Exception:
    pass

def carregar_todos_pedidos_historico():
    """Carrega todos os pedidos do Firebase para relatórios e estatísticas"""
    pedidos_totais = []
    try:
        url = f"{FIREBASE_URL}/pedidos.json"
        res = requests.get(url, timeout=10)
        if res.status_code == 200 and res.json():
            data = res.json()
            for token_prestador, lista_p in data.items():
                if isinstance(lista_p, dict):
                    for pid, pdata in lista_p.items():
                        if isinstance(pdata, dict):
                            pdata["token_prestador"] = token_prestador
                            pdata["id"] = pid
                            # Converter timestamp em datetime
                            ts = pdata.get("timestamp", 0)
                            if ts:
                                try:
                                    pdata["datetime"] = datetime.datetime.fromtimestamp(ts / 1000.0)
                                except Exception:
                                    pdata["datetime"] = datetime.datetime.now()
                            else:
                                pdata["datetime"] = datetime.datetime.now()
                            pedidos_totais.append(pdata)
    except Exception:
        pass
    return pedidos_totais

def show_admin_panel_extended():
    st.markdown("## ⚙️ Painel de Administração — FF Karaoke Cloud")
    st.markdown("Gerenciamento completo de prestadores, filas ativas, histórico e relatórios estatísticos.")
    st.markdown("---")

    aba_gestao, aba_historico, aba_estatisticas = st.tabs([
        "📊 Gestão Total (Tempo Real)", 
        "📜 Histórico de Prestadores", 
        "📈 Relatório e Estatísticas"
    ])

    with aba_gestao:
        st.markdown("### ⏱️ Gestão Total — Prestadores Ativos e Tempo a Contar")
        df_prestadores = get_all_providers()
        
        if df_prestadores.empty:
            st.info("Nenhum prestador registado no sistema.")
        else:
            # Adicionar contagem de tempo desde o registo
            dados_exibicao = []
            agora = datetime.datetime.now()
            
            for idx, row in df_prestadores.iterrows():
                token = row.get("token", "")
                nome = row.get("nome_prestador", "Prestador Sem Nome")
                data_reg_str = row.get("data_registo", str(agora))
                
                # Calcular tempo decorrido
                try:
                    data_reg = datetime.datetime.strptime(data_reg_str, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    try:
                        data_reg = datetime.datetime.fromisoformat(data_reg_str)
                    except Exception:
                        data_reg = agora
                
                delta = agora - data_reg
                dias = delta.days
                horas, resto = divmod(delta.seconds, 3600)
                minutos, segundos = divmod(resto, 60)
                
                tempo_decorrido_str = f"{dias} dias, {horas:02d}h {minutos:02d}m {segundos:02d}s" if dias > 0 else f"{horas:02d}h {minutos:02d}m {segundos:02d}s"
                
                dados_exibicao.append({
                    "Token": token,
                    "Nome / Prestador": nome,
                    "Data de Registo": data_reg_str,
                    "Tempo Ativo / Corrido": tempo_decorrido_str
                })
            
            df_display = pd.DataFrame(dados_exibicao)
            st.dataframe(df_display, use_container_width=True)
            
            if st.button("🔄 Atualizar Tempos e Fila"):
                st.rerun()

    with aba_historico:
        st.markdown("### 📜 Histórico de Prestadores Registados")
        st.markdown("Consulte a data exata em que cada prestador fez o registo e execute a remoção se necessário.")
        
        df_prestadores = get_all_providers()
        if df_prestadores.empty:
            st.info("Nenhum registo encontrado no histórico.")
        else:
            for idx, row in df_prestadores.iterrows():
                token = row.get("token", "")
                nome = row.get("nome_prestador", "Prestador Sem Nome")
                data_reg = row.get("data_registo", "Data não registada")
                
                col_info, col_del = [st.collab_column if hasattr(st, 'collab_column') else st.columns([4, 1])[0], st.columns([4, 1])[1]] if False else st.columns([4, 1])
                
                with col_info:
                    st.markdown(f"""
                        <div style="background: #111827; border: 1px solid #374151; padding: 12px; border-radius: 8px; margin-bottom: 8px; font-family: monospace;">
                            <b>Prestador:</b> {nome} <br>
                            <span style="color: #9ca3af; font-size: 13px;">Token: <code>{token}</code></span><br>
                            <span style="color: #4CAF50; font-size: 13px;">📅 Data do Registo: {data_reg}</span>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col_del:
                    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️ Apagar", key=f"del_hist_{token}"):
                        try:
                            delete_provider(token)
                            st.success(f"Registo de '{nome}' apagado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao apagar registo: {e}")

    with aba_estatisticas:
        st.markdown("### 📈 Relatório e Estatísticas de Pedidos")
        st.markdown("Totalização de itens pedidos divididos por períodos semanal e mensal.")
        
        todos_pedidos = carregar_todos_pedidos_historico()
        
        if not todos_pedidos:
            st.warning("Ainda não existem dados de pedidos suficientes para gerar o relatório estatístico.")
        else:
            df_peds = pd.DataFrame(todos_pedidos)
            
            # Garantir coluna datetime válida
            if "datetime" in df_peds.columns:
                agora = datetime.datetime.now()
                
                # Adicionar colunas auxiliares para agrupamento
                df_peds["Semana"] = df_peds["datetime"].dt.strftime("%Y-W%V")
                df_peds["Mês"] = df_peds["datetime"].dt.strftime("%Y-%m")
                
                st.markdown("#### 📅 Resumo Mensal")
                resumo_mensal = df_peds.groupby("Mês").size().reset_index(name="Total de Pedidos")
                st.dataframe(resumo_mensal, use_container_width=True)
                
                st.markdown("#### 📅 Resumo Semanal")
                resumo_semanal = df_peds.groupby("Semana").size().reset_index(name="Total de Pedidos")
                st.dataframe(resumo_semanal, use_container_width=True)
                
                st.markdown("#### 🎵 Músicas Mais Pedidas (Top Geral)")
                if "musica" in df_peds.columns:
                    def extrair_titulo_musica(m):
                        if isinstance(m, dict):
                            return m.get("titulo", m.get("nome", "Desconhecida"))
                        return str(m)
                    
                    df_peds["Titulo_Musica"] = df_peds["musica"].apply(extrair_titulo_musica)
                    top_musicas = df_peds["Titulo_Musica"].value_counts().reset_index()
                    top_musicas.columns = ["Música", "Total de Execuções/Pedidos"]
                    st.dataframe(top_musicas.head(10), use_container_width=True)
            else:
                st.error("Erro ao processar as datas dos pedidos.")

def main():
    try:
        query_params = st.query_params
        token = query_params.get("prestador") or query_params.get("token") or query_params.get("provider")
        
        if not token:
            # Painel de Administração Central
            if not st.session_state.get("admin_logged", False):
                st.title("🔒 FFKaraoke - Área Restrita de Administrador")
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
                show_admin_panel_extended()
        else:
            st.error("Acesso direcionado por token inválido para este endpoint de administração.")
    except Exception as e:
        st.error(f"Ocorreu um erro crítico na aplicação: {e}")

if __name__ == "__main__":
    main()
