import pandas as pd
import streamlit as st
import requests

st.set_page_config(layout="wide")

# --- TRUQUE CSS: Enxuga ao máximo os recuos superiores para ganhar campo de visão ---
st.markdown(
    """
    <style>
        .block-container { padding-top: 1.2rem !important; padding-bottom: 1rem !important; }
        [data-testid="stSidebarUserContent"] { padding-top: 1.2rem !important; }
        h1 { margin-top: -1rem !important; margin-bottom: 0.5rem !important; }
        h3 { margin-top: 0.5rem !important; margin-bottom: 0.5rem !important; }
        .stMarkdown p { margin-bottom: 0.4rem !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# Senha fixa para segurança do painel
senha_correta = "ditre123"

if "acesso_liberado" not in st.session_state:
    st.session_state["acesso_liberado"] = False

if "indice_persona_consultada" not in st.session_state:
    st.session_state["indice_persona_consultada"] = None

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

    # Mapeamento de cabeçalhos contra variações do Excel
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

    # Lista rígida de colunas obrigatórias na mesma ordem solicitada
    lista_colunas_obrigatorias = ["Nome Completo", "Email", "Nome Judaico", "Telefone", "Perfil Identidade", "Vinculação Comunitária", "Cep", "Bairro", "Endereço Completo"]
    for col_nome in lista_colunas_obrigatorias:
        if col_nome not in df.columns:
            df[col_nome] = ""
    if "Município" not in df.columns:
        df["Município"] = ""

    df["Nome Completo"] = df["Nome Completo"].astype(str).str.strip()
    df["Nome Judaico"] = df["Nome Judaico"].astype(str).str.strip()

    # Cabeçalho de requisição seguro para a API do CEP não bloquear o app
    headers_viacep = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

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
                    st.session_state["indice_persona_consultada"] = opcoes_pessoas[pessoa_sel]
            else:
                st.session_state["indice_persona_consultada"] = None
                st.warning("Nenhuma pessoa foi localizada com esse nome.")
        else:
            st.session_state["indice_persona_consultada"] = None
            st.info("💡 Por favor, digite o nome de alguém acima para realizar a consulta.")

        if st.session_state["indice_persona_consultada"] is not None:
            p_idx = st.session_state["indice_persona_consultada"]
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
            
            v_en = df.loc[p_idx, 'Endereço Completo']
            v_br = df.loc[p_idx, 'Bairro']
            v_cp = df.loc[p_idx, 'Cep']
            
            txt_en = v_en if pd.notna(v_en) and str(v_en).lower() != 'nan' else 'Não preenchido'
            txt_br = v_br if pd.notna(v_br) and str(v_br).lower() != 'nan' else 'Não preenchido'
            txt_cp = v_cp if pd.notna(v_cp) and str(v_cp).lower() != 'nan' else 'Não preenchido'
            
            st.info(f"📍 **Logradouro:** {txt_en} | 🏷️ **Bairro:** {txt_br} | 📮 **CEP:** {txt_cp}")
    # --- ABA 2: FORMULÁRIO DE EDIÇÃO DE REGISTROS EXISTENTES ---
    elif menu == "📝 Editar Cadastro Existente":
        st.title("📝 Editar Cadastro Comunitário")
        
        df_validos = df[df["Nome Completo"].str.lower() != "nan"]
        df_validos = df_validos[df["Nome Completo"].str.strip() != ""]
        nomes_cadastrados = sorted(df_validos["Nome Completo"].unique())
        
        nome_alvo = st.selectbox("Selecione o Nome Completo para editar:", nomes_cadastrados, key="nome_cadastro")
        
        if nome_alvo:
            registro_filtrado = df[df["Nome Completo"].str.lower() == nome_alvo.lower().strip()]
            
            if not registro_filtrado.empty:
                idx_real_salvamento = int(registro_filtrado.index[0])

                st.markdown("### 🏢 Validação Postal Geográfica")
                v_c = str(df.at[idx_real_salvamento, "Cep"]).strip()
                cep_i = st.text_input("Digite ou altere o CEP residencial (8 números):", value=v_c if v_c.lower() != "nan" else "", max_chars=8)
                
                rua_a, bairro_auto, cid_auto, uf_auto = "", "", "", ""
                if cep_i.strip().isdigit() and len(cep_i.strip()) == 8:
                    try:
                        # CORREÇÃO: Passando cabeçalhos Mozilla para evitar bloqueio da API do CEP
                        j_cep = requests.get(f"https://viacep.com.br{cep_i.strip()}/json/", headers=headers_viacep).json()
                        if "erro" not in j_cep:
                            rua_a = j_cep.get("logradouro", "")
                            bairro_auto = j_cep.get("bairro", "")
                            cid_auto = j_cep.get("localidade", "")
                            uf_auto = j_cep.get("uf", "")
                            st.success(f"📍 ViaCEP Localizado: {rua_a}, {bairro_auto} - {cid_auto}/{uf_auto}")
                        else:
                            st.warning("⚠️ CEP não localizado na base postal nacional.")
                    except:
                        st.error("⚠️ Falha de conexão na verificação automatizada.")

                v_muni = str(df.at[idx_real_salvamento, "Município"]).strip()
                v_b = str(df.at[idx_real_salvamento, "Bairro"]).strip()
                v_end_completo_antigo = str(df.at[idx_real_salvamento, "Endereço Completo"]).strip()
                rua_vazia_padrao = ""
                if v_end_completo_antigo and ", nº" in v_end_completo_antigo:
                    rua_vazia_padrao = v_end_completo_antigo.split(", nº")[0]

                with st.form("form_gps_editar_real"):
                    col_esq, col_dir = st.columns(2)
                    with col_esq:
                        st.markdown("### 👤 Dados de Identificação")
                        muni_i = st.text_input("Município de Residência:", value=cid_auto if cid_auto else (v_muni if v_muni.lower() != "nan" else ""))
                        email_i = st.text_input("E-mail de Contato:", value=str(df.at[idx_real_salvamento, "Email"]) if pd.notna(df.at[idx_real_salvamento, "Email"]) and str(df.at[idx_real_salvamento, "Email"]).lower() != "nan" else "")
                        nome_j_i = st.text_input("Nome Judaico / Hebraico:", value=str(df.at[idx_real_salvamento, "Nome Judaico"]) if pd.notna(df.at[idx_real_salvamento, "Nome Judaico"]) and str(df.at[idx_real_salvamento, "Nome Judaico"]).lower() != "nan" else "")
                        tel_i = st.text_input("Telefone / WhatsApp:", value=str(df.at[idx_real_salvamento, "Telefone"]) if pd.notna(df.at[idx_real_salvamento, "Telefone"]) and str(df.at[idx_real_salvamento, "Telefone"]).lower() != "nan" else "")
                        
                        lista_perfis = ["Judeu", "Bnei Anussim", "Simpatizante"]
                        v_p = str(df.at[idx_real_salvamento, "Perfil Identidade"]).strip()
                        idx_p = lista_perfis.index(v_p) if v_p in lista_perfis else 2
                        perfil_i = st.selectbox("Perfil Identidade:", lista_perfis, index=idx_p)
                        
                        v_v = str(df.at[idx_real_salvamento, "Vinculação Comunitária"]).strip()
                        vinculo_i = st.text_input("Vinculação Comunitária:", value=v_v if v_v.lower() != "nan" else "Isolado (Sem comunidade)")
                    
                    with col_dir:
                        st.markdown("### 🏢 Ajuste Fino do Endereço")
                        rua_i = st.text_input("Logradouro (Rua/Avenida):", value=rua_a if rua_a else rua_vazia_padrao)
                        num_i = st.text_input("Número / Complemento / Casa:")
                        bairro_i = st.text_input("Bairro:", value=bairro_auto if bairro_auto else (v_b if v_b.lower() != "nan" else ""))
                    
                    st.markdown("---")
                    aceite_lgpd = st.checkbox("Consinto com o tratamento dos dados sob as regras da LGPD.", key="lgpd_edit")
                    
                    if st.form_submit_button("💾 Salvar Alterações", use_container_width=True):
                        if not aceite_lgpd: 
                            st.error("Você precisa aceitar os termos da LGPD.")
                        else:
                            df.at[idx_real_salvamento, "Município"] = muni_i
                            df.at[idx_real_salvamento, "Email"] = email_i
                            df.at[idx_real_salvamento, "Nome Judaico"] = nome_j_i
                            df.at[idx_real_salvamento, "Telefone"] = tel_i
                            df.at[idx_real_salvamento, "Perfil Identidade"] = perfil_i
                            df.at[idx_real_salvamento, "Vinculação Comunitária"] = vinculo_i
                            df.at[idx_real_salvamento, "Cep"] = cep_i
                            df.at[idx_real_salvamento, "Bairro"] = bairro_i
                            
                            if rua_i: 
                                df.at[idx_real_salvamento, "Endereço Completo"] = f"{rua_i}, nº {num_i}"
                            
                            ordem_final_colunas = ["Município"] + lista_colunas_obrigatorias
                            df[ordem_final_colunas].to_csv("projeto_gps.csv", sep=";", index=False, encoding="utf-8-sig")
                            st.success("Cadastro atualizado com sucesso!")
                            st.balloons()
            else:
                st.error("Membro não localizado na base de dados.")

    # --- ABA 3: INCLUSÃO DE NOVOS REGISTROS DO ZERO ---
    elif menu == "🆕 Criar Novo Cadastro do Zero":
        st.title("🆕 Criar Novo Cadastro Comunitário")
        st.markdown("Preencha as informações para registrar um novo membro do zero na base de dados.")
        
        st.markdown("### 🏢 Validação Postal")
        n_cep = st.text_input("Digite o CEP residencial (8 números):", max_chars=8, key="cep_novo_membro")
        rua_n, bairro_n, muni_n, uf_n = "", "", "", "PB"
        if n_cep.strip().isdigit() and len(n_cep.strip()) == 8:
            try:
                j_n = requests.get(f"https://viacep.com.br{n_cep.strip()}/json/", headers=headers_viacep).json()
                if "erro" not in j_n:
                    rua_n, bairro_n, muni_n, uf_n = j_n.get("logradouro", ""), j_n.get("bairro", ""), j_n.get("localidade", ""), j_n.get("uf", "")
                    st.success(f"📍 Localizado: {rua_n}, {bairro_n} - {muni_n}/{uf_n}")
            except: pass

        with st.form("form_gps_novo"):
            col_esq, col_dir = st.columns(2)
            with col_esq:
                st.markdown("### 👤 Informações Pessoais")
                n_nome = st.text_input("Nome Completo Civil (Obrigatório):")
                n_judaico = st.text_input("Nome Judaico / Hebraico:")
                n_email = st.text_input("E-mail:")
                n_telefone = st.text_input("Telefone / WhatsApp (Com DDD):")
                
                # 🌟 CORREÇÃO: Caixa ativada para seleção de Perfil Identidade no Novo Cadastro 🌟
                n_perfil = st.selectbox("Como se identifica em relação ao Judaísmo?", ["Judeu", "Bnei Anussim", "Simpatizante"], key="novo_perfil_sel")
                n_vinculo = st.text_input("Participa de alguma Comunidade/Sinagoga?", value="Isolado (Sem comunidade)")
            
            with col_dir:
                st.markdown("### 🏡 Ajuste Fino do Endereço")
                n_muni = st.text_input("Município / Cidade:", value=muni_n)
                n_rua = st.text_input("Logradouro (Rua/Avenida):", value=rua_n)
                n_numero = st.text_input("Número / Complemento:")
                n_bairro = st.text_input("Bairro:", value=bairro_n)
            
            st.markdown("---")
            n_lgpd = st.checkbox("Consinto com o tratamento dos dados sob as regras da LGPD.", key="lgpd_novo")
            
            if st.form_submit_button("💾 Salvar Novo Cadastro do Zero", use_container_width=True):
                if not n_nome.strip(): st.error("O campo 'Nome Completo Civil' é obrigatório!")
                elif not n_lgpd: st.error("Você precisa aceitar os termos da LGPD.")
                else:
                    n_endereco_completo = f"{n_rua}, nº {n_numero}" if n_rua else ""
                    
                    # 🌟 CORREÇÃO CRÍTICA DE GRAVAÇÃO: Cria o dicionário mapeando rigorosamente todas as colunas
                    nova_linha = {
                        "Município": str(n_muni).strip(),
                        "Nome Completo": str(n_nome).strip(),
                        "Email": str(n_email).strip(),
                        "Nome Judaico": str(n_judaico).strip(),
                        "Telefone": str(n_telefone).strip(),
                        "Perfil Identidade": str(n_perfil).strip(),
                        "Vinculação Comunitária": str(n_vinculo).strip(),
                        "Cep": str(n_cep).strip(),
                        "Bairro": str(n_bairro).strip(),
                        "Endereço Completo": n_endereco_completo
                    }
                    df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
                    st.success(f"🎉 {n_nome} foi cadastrado com sucesso no banco de dados GPS!")
                    st.balloons()

# --- RODAPÉ DISCRETO PADRONIZADO ---
st.markdown("---")
st.markdown("<p style='text-align:right; font-size:12px; color:gray;'>Bartolomeu Lima - Corecon-ES 1541</p>", unsafe_allow_html=True)
