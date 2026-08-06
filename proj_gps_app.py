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

if "indice_pessoa_consultada" not in st.session_state:
    st.session_state["indice_pessoa_consultada"] = None

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
    
    # Carregamento seguro do arquivo projeto_gps.csv
    try:
        df = pd.read_csv("projeto_gps.csv", sep=";", encoding="utf-8-sig", dtype=str, skip_blank_lines=True)
    except Exception:
        df = pd.read_csv("projeto_gps.csv", sep=",", encoding="utf-8-sig", dtype=str, skip_blank_lines=True)
        
    df = df.dropna(how="all")

    # Mapeamento robusto de cabeçalhos contra variações do Excel
    mapeamento_colunas = {}
    for col in df.columns:
        col_limpa = col.strip().lower().replace("-", "").replace(" ", "")
        if "municip" in col_limpa: mapeamento_colunas[col] = "Município"
        elif "nomecomplet" in col_limpa: mapeamento_colunas[col] = "Nome Completo"
        elif "email" in col_limpa: mapeamento_colunas[col] = "Email"
        elif "nomejudaic" in col_limpa: mapeamento_colunas[col] = "Nome Judaico"
        elif "telefon" in col_limpa: mapeamento_colunas[col] = "Telefone"
        elif "perfil" in col_limpa: mapeamento_colunas[col] = "Perfil Identidade"
        elif "vinculac" in col_limpa: mapeamento_colunas[col] = "Vinculação Comunitária"
        elif "cep" in col_limpa: mapeamento_colunas[col] = "Cep"
        elif "bairro" in col_limpa: mapeamento_colunas[col] = "Bairro"
        elif "enderec" in col_limpa: mapeamento_colunas[col] = "Endereço Completo"

    df = df.rename(columns=mapeamento_colunas)

    # Lista de colunas obrigatórias
    lista_colunas_obrigatorias = ["Nome Completo", "Email", "Nome Judaico", "Telefone", "Perfil Identidade", "Vinculação Comunitária", "Cep", "Bairro", "Endereço Completo"]
    for col_nome in lista_colunas_obrigatorias:
        if col_nome not in df.columns:
            df[col_nome] = ""
    if "Município" not in df.columns:
        df["Município"] = ""

    df["Nome Completo"] = df["Nome Completo"].astype(str).str.strip()
    df["Nome Judaico"] = df["Nome Judaico"].astype(str).str.strip()

    # --- CONSTRUÇÃO DO MENU LATERAL ---
    st.sidebar.header("Painel de Controle GPS")
    menu = st.sidebar.radio(
        "Selecione a Ação:", 
        ["🔍 Consultar por Nome", "📝 Editar Cadastro Existente", "🆕 Criar Novo Cadastro do Zero"]
    )
    st.sidebar.markdown("---")

    # --- ABA 1: CONSULTA DO BANCO DE DADOS POR NOME ---
    if menu == "🔍 Consultar por Nome":
        st.title("🔍 Consulta de Membros da Comunidade")
        busca_nome = st.text_input("Digite o Nome Civil ou Nome Judaico para pesquisar:", value="")
        
        if busca_nome.strip():
            termo = busca_nome.lower().strip()
            filtro = df["Nome Completo"].str.lower().str.contains(termo) | df["Nome Judaico"].str.lower().str.contains(termo)
            registros_encontrados = df[filtro]
            
            if not registros_encontrados.empty:
                opcoes_pessoas = {"-- Selecione uma pessoa da lista --": None}
                for idx, row in registros_encontrados.iterrows():
                    nome_civil = row["Nome Completo"]
                    nome_hud = f" ({row['Nome Judaico']})" if pd.notna(row["Nome Judaico"]) and row["Nome Judaico"].strip() and row["Nome Judaico"].lower() != 'nan' else ""
                    muni_ref = f" - {row['Município']}" if pd.notna(row["Município"]) and row["Município"].strip() and row["Município"].lower() != 'nan' else ""
                    opcoes_pessoas[f"{nome_civil}{nome_hud}{muni_ref}"] = idx
                
                pessoa_sel = st.selectbox("Selecione a pessoa para abrir a ficha:", sorted(opcoes_pessoas.keys()))
                if pessoa_sel and opcoes_pessoas[pessoa_sel] is not None:
                    st.session_state["indice_pessoa_consultada"] = opcoes_pessoas[pessoa_sel]
            else:
                st.session_state["indice_pessoa_consultada"] = None
                st.warning("Nenhuma pessoa foi localizada com esse nome.")
        else:
            st.session_state["indice_pessoa_consultada"] = None
            st.info("💡 Por favor, digite o nome de alguém acima para realizar a consulta.")

        if st.session_state["indice_pessoa_consultada"] is not None:
            p_idx = st.session_state["indice_pessoa_consultada"]
            st.markdown("---")
            st.subheader(f"👤 Ficha Cadastral — {df.loc[p_idx, 'Nome Completo']}")
            
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                st.write(f"**Nome Completo:** {df.loc[p_idx, 'Nome Completo']}")
                st.write(f"**Nome Judaico:** {df.loc[p_idx, 'Nome Judaico'] if pd.notna(df.loc[p_idx, 'Nome Judaico']) and str(df.loc[p_idx, 'Nome Judaico']).lower() != 'nan' else ''}")
                st.write(f"**Email:** {df.loc[p_idx, 'Email'] if pd.notna(df.loc[p_idx, 'Email']) and str(df.loc[p_idx, 'Email']).lower() != 'nan' else ''}")
                st.write(f"**Telefone:** {df.loc[p_idx, 'Telefone'] if pd.notna(df.loc[p_idx, 'Telefone']) and str(df.loc[p_idx, 'Telefone']).lower() != 'nan' else ''}")
            with f_col2:
                st.write(f"**Perfil Identidade:** {df.loc[p_idx, 'Perfil Identidade']}")
                st.write(f"**Vinculação Comunitária:** {df.loc[p_idx, 'Vinculação Comunitária']}")
                st.write(f"**Município de Residência:** {df.loc[p_idx, 'Município']}")
                st.write(f"**Bairro:** {df.loc[p_idx, 'Bairro'] if pd.notna(df.loc[p_idx, 'Bairro']) and str(df.loc[p_idx, 'Bairro']).lower() != 'nan' else ''}")
                st.write(f"**CEP:** {df.loc[p_idx, 'Cep'] if pd.notna(df.loc[p_idx, 'Cep']) and str(df.loc[p_idx, 'Cep']).lower() != 'nan' else ''}")
            st.info(f"📍 **Endereço Completo:** {df.loc[p_idx, 'Endereço Completo'] if pd.notna(df.loc[p_idx, 'Endereço Completo']) and str(df.loc[p_idx, 'Endereço Completo']).lower() != 'nan' else 'Não preenchido'}")
    # --- ABA 2: FORMULÁRIO DE EDIÇÃO DE REGISTROS EXISTENTES ---
    elif menu == "📝 Editar Cadastro Existente":
        st.title("📝 Editar Cadastro Comunitário")
        
        df_validos = df[df["Nome Completo"].str.lower() != "nan"]
        df_validos = df_validos[df_validos["Nome Completo"].str.strip() != ""]
        nomes_cadastrados = sorted(df_validos["Nome Completo"].unique())
        
        nome_alvo = st.selectbox("Selecione o Nome Completo para editar:", nomes_cadastrados, key="nome_cadastro")
        
        if nome_alvo:
            res_cad = df[df["Nome Completo"].str.lower() == nome_alvo.lower().strip()]
            idx_cad = res_cad.index[0] if not res_cad.empty else None

            with st.form("form_gps_editar"):
                col_esq, col_dir = st.columns(2)
                with col_esq:
                    st.markdown("### 👤 Dados de Identificação")
                    muni_i = st.text_input("Município de Residência:", value=str(df.at[idx_cad, "Município"]) if pd.notna(df.at[idx_cad, "Município"]) and str(df.at[idx_cad, "Município"]).lower() != "nan" else "")
                    email_i = st.text_input("E-mail de Contato:", value=str(df.at[idx_cad, "Email"]) if pd.notna(df.at[idx_cad, "Email"]) and str(df.at[idx_cad, "Email"]).lower() != "nan" else "")
                    nome_j_i = st.text_input("Nome Judaico / Hebraico:", value=str(df.at[idx_cad, "Nome Judaico"]) if pd.notna(df.at[idx_cad, "Nome Judaico"]) and str(df.at[idx_cad, "Nome Judaico"]).lower() != "nan" else "")
                    tel_i = st.text_input("Telefone / WhatsApp:", value=str(df.at[idx_cad, "Telefone"]) if pd.notna(df.at[idx_cad, "Telefone"]) and str(df.at[idx_cad, "Telefone"]).lower() != "nan" else "")
                    
                    lista_perfis = ["Judeu", "Bnei Anussim", "Simpatizante"]
                    v_p = str(df.at[idx_cad, "Perfil Identidade"]).strip()
                    idx_p = lista_perfis.index(v_p) if v_p in lista_perfis else 2
                    perfil_i = st.selectbox("Perfil Identidade:", lista_perfis, index=idx_p)
                    v_v = str(df.at[idx_cad, "Vinculação Comunitária"]).strip()
                    vinculo_i = st.text_input("Vinculação Comunitária:", value=v_v if v_v.lower() != "nan" else "Isolado (Sem comunidade)")
                
                with col_dir:
                    st.markdown("### 🏢 Endereço Coletado via CEP")
                    v_c = str(df.at[idx_cad, "Cep"]).strip()
                    cep_i = st.text_input("CEP (Apenas 8 números):", value=v_c if v_c.lower() != "nan" else "", max_chars=8)
                    
                    rua_a, bairro_auto, cid_auto, uf_auto = "", "", "", ""
                    if cep_i.strip().isdigit() and len(cep_i.strip()) == 8:
                        try:
                            j_cep = requests.get(f"https://viacep.com.br{cep_i.strip()}/json/").json()
                            if "erro" not in j_cep:
                                rua_a, bairro_auto, cid_auto, uf_auto = j_cep.get("logradouro", ""), j_cep.get("bairro", ""), j_cep.get("localidade", ""), j_cep.get("uf", "")
                                st.caption(f"📍 Mapeado: {rua_a}, {bairro_auto} - {cid_auto}/{uf_auto}")
                        except: pass
                    
                    rua_i = st.text_input("Logradouro (Rua/Avenida):", value=rua_a if rua_a else "")
                    num_i = st.text_input("Número / Complemento:")
                    v_b = str(df.at[idx_cad, "Bairro"]).strip()
                    bairro_i = st.text_input("Bairro:", value=bairro_auto if bairro_auto else (v_b if v_b.lower() != "nan" else ""))
                
                st.markdown("---")
                aceite_lgpd = st.checkbox("Consinto com o tratamento dos dados sob as regras da LGPD.", key="lgpd_edit")
                if st.form_submit_button("💾 Salvar Alterações", use_container_width=True):
                    if not aceite_lgpd: st.error("Você precisa aceitar os termos da LGPD.")
                    else:
                        df.at[idx_cad, "Município"] = muni_i
                        df.at[idx_cad, "Email"] = email_i
                        df.at[idx_cad, "Nome Judaico"] = nome_j_i
                        df.at[idx_cad, "Telefone"] = tel_i
                        df.at[idx_cad, "Perfil Identidade"] = perfil_i
                        df.at[idx_cad, "Vinculação Comunitária"] = vinculo_i
                        df.at[idx_cad, "Cep"] = cep_i
                        df.at[idx_cad, "Bairro"] = bairro_i
                        # 🌟 AJUSTE SOLICITADO: Endereço completo concatenando Rua, Nº, Bairro, Cidade/UF e CEP 🌟
                        if rua_i: df.at[idx_cad, "Endereço Completo"] = f"{rua_i}, nº {num_i} - {bairro_i}, {muni_i}/{uf_auto if uf_auto else 'PB'}, CEP: {cep_i}"
                        df[["Município"] + lista_colunas_obrigatorias].to_csv("projeto_gps.csv", sep=";", index=False, encoding="utf-8-sig")
                        st.success("Cadastro atualizado!")
                        st.balloons()

    # --- ABA 3: INCLUSÃO DE NOVOS REGISTROS DO ZERO ---
    elif menu == "🆕 Criar Novo Cadastro do Zero":
        st.title("🆕 Criar Novo Cadastro Comunitário")
        st.markdown("Preencha as informações para registrar um novo membro do zero na base de dados.")
        
        with st.form("form_gps_novo"):
            col_esq, col_dir = st.columns(2)
            with col_esq:
                st.markdown("### 👤 Informações Pessoais")
                n_nome = st.text_input("Nome Completo Civil (Obrigatório):")
                n_judaico = st.text_input("Nome Judaico / Hebraico:")
                n_email = st.text_input("E-mail:")
                n_telefone = st.text_input("Telefone / WhatsApp (Com DDD):")
                n_perfil = st.selectbox("Como se identifica em relação ao Judaísmo?", ["Judeu", "Bnei Anussim", "Simpatizante"])
                n_vinculo = st.text_input("Participa de alguma Comunidade/Sinagoga?", value="Isolado (Sem comunidade)")
            
            with col_dir:
                st.markdown("### 🏢 Endereço Residencial")
                n_cep = st.text_input("Digite o CEP (Apenas 8 números):", max_chars=8)
                n_muni = st.text_input("Município / Cidade:")
                
                rua_n, bairro_n, uf_n = "", "", "PB"
                if n_cep.strip().isdigit() and len(n_cep.strip()) == 8:
                    try:
                        j_n = requests.get(f"https://viacep.com.br{n_cep.strip()}/json/").json()
                        if "erro" not in j_n:
                            rua_n, bairro_n, n_muni, uf_n = j_n.get("logradouro", ""), j_n.get("bairro", ""), j_n.get("localidade", ""), j_n.get("uf", "")
                            st.caption(f"📍 Localizado: {rua_n}, {bairro_n} - {n_muni}/{uf_n}")
                    except: pass
                
                n_rua = st.text_input("Logradouro (Rua/Avenida):", value=rua_n)
                n_numero = st.text_input("Número / Complemento:")
                n_bairro = st.text_input("Bairro:", value=bairro_n)
            
            st.markdown("---")
            n_lgpd = st.checkbox("Consinto com o tratamento dos dados sob as regras da LGPD.", key="lgpd_novo")
            
            if st.form_submit_button("💾 Salvar Novo Cadastro do Zero", use_container_width=True):
                if not n_nome.strip(): st.error("O campo 'Nome Completo Civil' é obrigatório!")
                elif not n_lgpd: st.error("Você precisa aceitar os termos da LGPD.")
                else:
                    # Monta a linha com o novo registro estruturado na mesma ordem solicitada
                    n_endereco_completo = f"{n_rua}, nº {n_numero} - {n_bairro}, {n_muni}/{uf_n}, CEP: {n_cep}" if n_rua else ""
                    nova_linha = {
                        "Município": n_muni, "Nome Completo": n_nome.strip(), "Email": n_email,
                        "Nome Judaico": n_judaico, "Telefone": n_telefone, "Perfil Identidade": n_perfil,
                        "Vinculação Comunitária": n_vinculo, "Cep": n_cep, "Bairro": n_bairro,
                        "Endereço Completo": n_endereco_completo
                    }
                    df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
                    df[["Município"] + lista_colunas_obrigatorias].to_csv("projeto_gps.csv", sep=";", index=False, encoding="utf-8-sig")
                    st.success(f"🎉 {n_nome} foi cadastrado com sucesso no banco de dados GPS!")
                    st.balloons()

# --- RODAPÉ DISCRETO PADRONIZADO ---
st.markdown("---")
st.markdown("<p style='text-align:right; font-size:12px; color:gray;'>Bartolomeu Lima - Corecon-ES 1541</p>", unsafe_allow_html=True)
