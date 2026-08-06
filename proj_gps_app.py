import pandas as pd
import streamlit as st
import requests

st.set_page_config(layout="wide")

# --- TRUQUE CSS: Enxuga o espaço em branco do topo da tela ---
st.markdown(
    """
    <style>
        .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
        [data-testid="stSidebarUserContent"] { padding-top: 1.5rem !important; }
        h1 { margin-top: -1rem !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# Senha fixa para segurança do painel
senha_correta = "ditre123"

if "acesso_liberado" not in st.session_state:
    st.session_state["acesso_liberado"] = False

# --- TELA DE LOGIN ---
if not st.session_state["acesso_liberado"]:
    st.title("🔐 Painel GPS - Autenticação")
    col_login, _ = st.columns(2)
    with col_login:
        senha = st.text_input("Digite a senha para acessar:", type="password")
        if st.button("Entrar", use_container_width=True):
            if senha == senha_correta:
                st.session_state["acesso_liberado"] = True
                st.rerun()
            else:
                st.error("Senha incorreta! Tente novamente.")

# --- APLICATIVO PRINCIPAL LIBERADO ---
if st.session_state["acesso_liberado"]:
    
    # AJUSTADO: Carregamento do arquivo correto 'projeto_gps.csv' com tratamento resiliente de encoding
    try:
        df = pd.read_csv(
            "projeto_gps.csv",
            sep=",",   
            encoding="utf-8-sig",
            dtype={"Município": str, "CEP": str, "Telefone": str}
        )
    except Exception:
        df = pd.read_csv(
            "projeto_gps.csv",
            sep=";",   
            encoding="utf-8-sig",
            dtype={"Município": str, "CEP": str, "Telefone": str}
        )
        
    df.columns = df.columns.str.strip()

    # --- CONSTRUÇÃO DO MENU LATERAL ---
    st.sidebar.header("Painel de Controle GPS")
    menu = st.sidebar.radio(
        "Selecione a Ação:",
        ["🔍 Consultar Cadastro", "📝 Cadastrar / Atualizar Endereços"]
    )
    st.sidebar.markdown("---")

    # --- ABA 1: CONSULTA DO BANCO DE DADOS ---
    if menu == "🔍 Consultar Cadastro":
        st.title("🔍 Consulta de Endereços e Contatos")
        
        if "Município" in df.columns:
            municipios = sorted(df["Município"].dropna().unique())
            muni_sel = st.selectbox("Selecione o município para consultar:", municipios)
            
            if muni_sel:
                resultado = df[df["Município"].astype(str).str.lower().str.strip() == str(muni_sel).lower().strip()]
                
                if not resultado.empty:
                    idx = resultado.index
                    st.subheader(f"📍 Dados Cadastrais — {muni_sel}")
                    
                    # Exibe as colunas dinamicamente se elas existirem no seu CSV
                    for col in df.columns:
                        if col != "Município":
                            val = df.loc[idx, col].values[0]
                            st.write(f"**{col}:** {val if pd.notna(val) else ''}")
                else:
                    st.warning("Município selecionado não possui registros.")
        else:
            st.warning("A coluna 'Município' não foi detectada no arquivo projeto_gps.csv.")


# --- RODAPÉ DISCRETO PADRONIZADO ---
st.markdown("---")
st.markdown("<p style='text-align:right; font-size:12px; color:gray;'>Bartolomeu Lima - Corecon-ES 1541</p>", unsafe_allow_html=True)
st.markdown("[⬅️ Voltar ao Menu Principal](https://streamlit.app)")
