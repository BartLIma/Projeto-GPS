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
    
    # Carregamento seguro da base 'projeto_gps.csv'
    try:
        df = pd.read_csv(
            "projeto_gps.csv",
            sep=",",   
            encoding="utf-8-sig",
            dtype=str  # Lê tudo temporariamente como texto para evitar conflitos de tipos
        )
    except Exception:
        df = pd.read_csv(
            "projeto_gps.csv",
            sep=";",   
            encoding="utf-8-sig",
            dtype=str
        )
        
    # Limpa todos os espaços das colunas
    df.columns = df.columns.str.strip()
    
    # 🌟 TRAVA DE SEGURANÇA MESTRE: Força a primeira coluna a se chamar 'Município'
    # Isso elimina qualquer erro gerado pelo caractere invisível (BOM) do Excel
    novas_colunas = list(df.columns)
    novas_colunas[0] = "Município"
    df.columns = novas_colunas

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
        
        # Como forçamos o nome acima, este bloco sempre será verdadeiro
        if "Município" in df.columns:
            df["Município"] = df["Município"].astype(str).str.strip()
            municipios = sorted(df["Município"].dropna().unique())
            if "nan" in municipios: municipios.remove("nan")
            
            muni_sel = st.selectbox("Selecione o município para consultar:", municipios)
            
            if muni_sel:
                resultado = df[df["Município"].str.lower() == muni_sel.lower().strip()]
                
                if not resultado.empty:
                    idx = resultado.index
                    st.subheader(f"📍 Dados Cadastrais — {muni_sel}")
                    
                    # Exibe os campos na tela respeitando o layout limpo
                    for col in df.columns:
                        if col != "Município":
                            val = df.loc[idx, col].values[0] # Pega o valor puro
                            st.write(f"**{col}:** {val if pd.notna(val) and str(val).lower() != 'nan' else ''}")
                else:
                    st.warning("Município selecionado não possui registros.")

    # --- ABA 2: FORMULÁRIO ONLINE DE CAPTAÇÃO E ATUALIZAÇÃO (LGPD) ---
    elif menu == "📝 Cadastrar / Atualizar Endereços":
        st.title("📝 Formulário de Posicionamento e Identidade Sefardita")
        st.markdown("Preencha os campos abaixo de forma consciente. Os dados coletados estão protegidos sob as diretrizes da LGPD.")

        if "Município" in df.columns:
            df["Município"] = df["Município"].astype(str).str.strip()
            municipios_cad = sorted(df["Município"].unique())
            if "nan" in municipios_cad: municipios_cad.remove("nan")
            
            muni_cad_sel = st.selectbox("Selecione o município de residência:", municipios_cad, key="muni_cadastro")
            
            if muni_cad_sel:
                res_cad = df[df["Município"].str.lower() == muni_cad_sel.lower().strip()]
                idx_cad = res_cad.index if not res_cad.empty else None

                with st.form("form_gps_cadastro"):
                    col_esq, col_dir = st.columns(2)
                    
                    with col_esq:
                        st.markdown("### 👤 Informações de Contato e Identidade")
                        v_responsavel = str(df.loc[idx_cad, "Nome Completo"].values[0]).strip() if idx_cad is not None and "Nome Completo" in df.columns and pd.notna(df.loc[idx_cad, "Nome Completo"].values[0]) else ""
                        v_email = str(df.loc[idx_cad, "Email"].values[0]).strip() if idx_cad is not None and "Email" in df.columns and pd.notna(df.loc[idx_cad, "Email"].values[0]) else ""
                        v_nome_jud = str(df.loc[idx_cad, "Nome Judaico"].values[0]).strip() if idx_cad is not None and "Nome Judaico" in df.columns and pd.notna(df.loc[idx_cad, "Nome Judaico"].values[0]) else ""
                        v_tel = str(df.loc[idx_cad, "Telefone"].values[0]).strip() if idx_cad is not None and "Telefone" in df.columns and pd.notna(df.loc[idx_cad, "Telefone"].values[0]) else ""
                        
                        nome_resp = st.text_input("Nome Completo:", value=v_responsavel)
                        email_contato = st.text_input("E-mail de Contato:", value=v_email)
                        nome_judaico = st.text_input("Nome Judaico / Hebraico (Se houver):", value=v_nome_jud)
                        tel_contato = st.text_input("Telefone / WhatsApp (Com DDD):", value=v_tel)

                        st.markdown("---")
                        st.markdown("### 📜 Identidade e Afinidade Cultural")
                        
                        v_perfil = str(df.loc[idx_cad, "Perfil Identidade"].values[0]).strip() if idx_cad is not None and "Perfil Identidade" in df.columns and pd.notna(df.loc[idx_cad, "Perfil Identidade"].values[0]) else "Simpatizante"
                        lista_perfis = ["Judeu", "Bnei Anussim", "Simpatizante"]
                        idx_perfil_padrao = lista_perfis.index(v_perfil) if v_perfil in lista_perfis else 2
                        
                        perfil_identidade = st.selectbox("Como você se identifica em relação ao Judaísmo?", lista_perfis, index=idx_perfil_padrao)
                        
                        v_vinculo = str(df.loc[idx_cad, "Vinculação Comunitária"].values[0]).strip() if idx_cad is not None and "Vinculação Comunitária" in df.columns and pd.notna(df.loc[idx_cad, "Vinculação Comunitária"].values[0]) else "Isolado (Sem comunidade)"
                        vinculo_comunidade = st.text_input("Participa de alguma Comunidade/Sinagoga/Núcleo? (Se não, digite Isolado):", value=v_vinculo)

                    with col_dir:
                        st.markdown("### 🏢 Localização Geográfica")
                        v_cep_antigo = str(df.loc[idx_cad, "Cep"].values[0]).strip() if idx_cad is not None and "Cep" in df.columns and pd.notna(df.loc[idx_cad, "Cep"].values[0]) else ""
                        cep_input = st.text_input("Digite o CEP residencial (Apenas 8 números):", value=v_cep_antigo, max_chars=8)
                        
                        logradouro_auto = ""
                        bairro_auto = ""
                        localidade_auto = ""
                        uf_auto = ""

                        if cep_input.strip().isdigit() and len(cep_input.strip()) == 8:
                            try:
                                json_cep = requests.get(f"https://viacep.com.br{cep_input.strip()}/json/").json()
                                if "erro" not in json_cep:
                                    logradouro_auto = json_cep.get("logradouro", "")
                                    bairro_auto = json_cep.get("bairro", "")
                                    localidade_auto = json_cep.get("localidade", "")
                                    uf_auto = json_cep.get("uf", "")
                                    st.caption(f"📍 Endereço Mapeado: {logradouro_auto}, {bairro_auto} - {localidade_auto}/{uf_auto}")
                                else:
                                    st.caption("⚠️ CEP não localizado na base postal.")
                            except Exception:
                                st.caption("⚠️ Erro de conexão com o servidor de busca postal.")

                        rua = st.text_input("Logradouro (Rua/Avenida):", value=logradouro_auto if logradouro_auto else "")
                        numero_predio = st.text_input("Número / Complemento / Casa:")
                        
                        v_bairro_antigo = str(df.loc[idx_cad, "Bairro"].values[0]).strip() if idx_cad is not None and "Bairro" in df.columns and pd.notna(df.loc[idx_cad, "Bairro"].values[0]) else ""
                        bairro_final = bairro_auto if bairro_auto else v_bairro_antigo
                        bairro = st.text_input("Bairro:", value=bairro_final)
                        
                        endereco_gerado = f"{rua}, nº {numero_predio}" if rua else ""

                    # Trava legal da LGPD
                    st.markdown("---")
                    st.markdown("#### 🛡️ Termo de Consentimento e Privacidade (LGPD)")
                    st.caption("De acordo com a Lei nº 13.709/2018 (LGPD), informamos que os seus dados de convicção religiosa e localização serão armazenados em ambiente seguro com a finalidade exclusiva de mapeamento e integração geo-comunitária, sendo proibido o compartilhamento público de dados identificáveis.")
                    aceite_lgpd = st.checkbox("Estou ciente e dou meu consentimento livre e esclarecido para o tratamento dos meus dados pessoais sensíveis neste projeto.")

                    botao_salvar_gps = st.form_submit_button("💾 Confirmar e Salvar no Banco de Dados GPS", use_container_width=True)
                    
                    if botao_salvar_gps:
                        if not aceite_lgpd:
                            st.error("❌ Gravação cancelada! Você precisa marcar a caixa do Termo de Consentimento da LGPD para realizar o cadastro.")
                        elif idx_cad is not None:
                            lista_colunas_obrigatorias = ["Nome Completo", "Email", "Nome Judaico", "Telefone", "Perfil Identidade", "Vinculação Comunitária", "Cep", "Bairro", "Endereço Completo"]
                            for col_nome in lista_colunas_obrigatorias:
                                if col_nome not in df.columns: df[col_nome] = ""
                            
                            # Gravação higienizada e direta
                            df.loc[idx_cad, "Nome Completo"] = nome_resp
                            df.loc[idx_cad, "Email"] = email_contato
                            df.loc[idx_cad, "Nome Judaico"] = nome_judaico
                            df.loc[idx_cad, "Telefone"] = tel_contato
                            df.loc[idx_cad, "Perfil Identidade"] = perfil_identidade
                            df.loc[idx_cad, "Vinculação Comunitária"] = vinculo_comunidade
                            df.loc[idx_cad, "Cep"] = cep_input
                            df.loc[idx_cad, "Bairro"] = bairro
                            
                            if endereco_gerado:
                                df.loc[idx_cad, "Endereço Completo"] = endereco_gerado
                            
                            # Reordena o DataFrame forçando o alinhamento idêntico ao solicitado
                            ordem_final_colunas = ["Município"] + lista_colunas_obrigatorias
                            df = df[ordem_final_colunas]
                            
                            df.to_csv("projeto_gps.csv", sep=",", index=False, encoding="utf-8-sig")
                            st.success(f"🎉 Cadastro realizado em conformidade com a LGPD para o município de {muni_cad_sel}!")
                            st.balloons()
                        else:
                            st.error("Erro operacional: Linha de município inválida no CSV.")
        else:
            st.error("Erro crítico: A coluna 'Município' precisa existir no arquivo projeto_gps.csv.")

# --- RODAPÉ DISCRETO PADRONIZADO ---
st.markdown("---")
st.markdown("<p style='text-align:right; font-size:12px; color:gray;'>Bartolomeu Lima - Corecon-ES 1541</p>", unsafe_allow_html=True)
st.markdown("[⬅️ Voltar ao Menu Principal](https://streamlit.app)")
