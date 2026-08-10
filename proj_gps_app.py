import pandas as pd
import streamlit as st
import requests
import os

st.set_page_config(layout="wide")

# --- TRUQUE CSS: Enxuga os recuos superiores para otimizar o campo de visão ---
st.markdown(
    """
    <style>
        .block-container { padding-top: 1.2rem !important; padding-bottom: 1rem !important; }
        [data-testid="stSidebarUserContent"] { padding-top: 1.2rem !important; }
        h1 { margin-top: -1.2rem !important; margin-bottom: 0.5rem !important; }
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
    
    # Nova lista de colunas na ordem exata do seu formulário do Google
    lista_colunas_obrigatorias = ["Nome Civil", "Nome Judaico", "E-mail", "Endereço", "Número de telefone", "Perfil de Identidade", "Vinculação Comunitária", "Comentários", "Município", "UF"]
    
    # Se o arquivo sumir, o Python recria a estrutura básica com o separador de vírgula (sep=",")
    if not os.path.exists("projeto_gps.csv"):
        df_vazio = pd.DataFrame(columns=lista_colunas_obrigatorias)
        df_vazio.to_csv("projeto_gps.csv", sep=",", index=False, encoding="utf-8-sig")

    # 🌟 TRAVA MESTRE: Força o Pandas a ler o arquivo priorizando a VÍRGULA (sep=",") 🌟
    try:
        df = pd.read_csv("projeto_gps.csv", sep=",", encoding="utf-8-sig", dtype=str, skip_blank_lines=True)
    except Exception:
        df = pd.read_csv("projeto_gps.csv", sep=",", encoding="utf-8-sig", dtype=str, skip_blank_lines=True)
        
    df = df.dropna(how="all")

    # Mapeamento robusto adaptado aos novos nomes exatos do Google Forms
    mapeamento_colunas = {}
    for col in df.columns:
        col_limpa = col.strip().lower().replace("-", "").replace(" ", "").replace("_", "")
        if "municip" in col_limpa: mapeamento_colunas[col] = "Município"
        elif "uf" in col_limpa or "estado" in col_limpa: mapeamento_colunas[col] = "UF"
        elif "nomecivil" in col_limpa or "nomecomplet" in col_limpa: mapeamento_colunas[col] = "Nome Civil"
        elif "email" in col_limpa: mapeamento_colunas[col] = "E-mail"
        elif "nomejudaic" in col_limpa: mapeamento_colunas[col] = "Nome Judaico"
        elif "numerodetelefone" in col_limpa or "telefon" in col_limpa: mapeamento_colunas[col] = "Número de telefone"
        elif "perfil" in col_limpa: mapeamento_colunas[col] = "Perfil de Identidade"
        elif "vinculac" in col_limpa: mapeamento_colunas[col] = "Vinculação Comunitária"
        elif "enderec" in col_limpa or "logradour" in col_limpa: mapeamento_colunas[col] = "Endereço"
        elif "comentar" in col_limpa: mapeamento_colunas[col] = "Comentários"

    df = df.rename(columns=mapeamento_colunas)

    for col_nome in lista_colunas_obrigatorias:
        if col_nome not in df.columns: df[col_nome] = ""

    for c in df.columns:
        df[c] = df[c].fillna("").astype(str).str.strip()

    headers_viacep = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    st.sidebar.header("Painel de Controle GPS")
    menu = st.sidebar.radio("Selecione a Ação:", ["🔍 Consultar por Nome", "📝 Editar Cadastro Existente", "🆕 Criar Novo Cadastro do Zero"])
    st.sidebar.markdown("---")

    # --- ABA 1: CONSULTA DO BANCO DE DADOS POR NOME ---
    if menu == "🔍 Consultar por Nome":
        st.title("🔍 Consulta de Membros da Comunidade")
        busca_nome = st.text_input("Digite o Nome Civil ou Nome Judaico para pesquisar:", value="")
        
        if busca_nome.strip():
            termo = busca_nome.lower().strip()
            filtro = df["Nome Civil"].str.lower().str.contains(termo) | df["Nome Judaico"].str.lower().str.contains(termo)
            registros_encontrados = df[filtro]
            
            if not registros_encontrados.empty:
                opcoes_pessoas = {"-- Selecione uma pessoa da lista --": None}
                for idx, row in registros_encontrados.iterrows():
                    nome_civ = row["Nome Civil"]
                    nome_hud = f" ({row['Nome Judaico']})" if row["Nome Judaico"] and row["Nome Judaico"].lower() != 'nan' else ""
                    muni_ref = f" - {row['Município']}" if row["Município"] and row["Município"].lower() != 'nan' else ""
                    opcoes_pessoas[f"{nome_civ}{nome_hud}{muni_ref}"] = idx
                
                pessoa_sel = st.selectbox("Selecione a pessoa para abrir a ficha:", sorted(opcoes_pessoas.keys()))
                if p_idx := opcoes_pessoas.get(pessoa_sel):
                    st.session_state["indice_persona_consultada"] = p_idx
            else:
                st.session_state["indice_persona_consultada"] = None
                st.warning("Nenhuma pessoa foi localizada com esse nome na base de dados.")
        else:
            st.session_state["indice_persona_consultada"] = None
            st.info("💡 Por favor, digite o nome de alguém acima para realizar a consulta cadastral.")

        if st.session_state["indice_persona_consultada"] is not None:
            p_idx = st.session_state["indice_persona_consultada"]
            st.markdown("---")
            st.subheader(f"👤 Ficha Cadastral — {df.loc[p_idx, 'Nome Civil']}")
            
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                st.write(f"**Nome Civil:** {df.loc[p_idx, 'Nome Civil']}")
                st.write(f"**Nome Judaico:** {df.loc[p_idx, 'Nome Judaico'] if df.loc[p_idx, 'Nome Judaico'].lower() != 'nan' else ''}")
                st.write(f"**E-mail:** {df.loc[p_idx, 'E-mail'] if df.loc[p_idx, 'E-mail'].lower() != 'nan' else ''}")
                st.write(f"**Número de telefone:** {df.loc[p_idx, 'Número de telefone'] if df.loc[p_idx, 'Número de telefone'].lower() != 'nan' else ''}")
            with f_col2:
                st.write(f"**Perfil de Identidade:** {df.loc[p_idx, 'Perfil de Identidade']}")
                st.write(f"**Vinculação Comunitária:** {df.loc[p_idx, 'Vinculação Comunitária']}")
                muni_txt = df.loc[p_idx, 'Município']
                est_txt = df.loc[p_idx, 'UF']
                st.write(f"**Localidade:** {muni_txt if muni_txt.lower() != 'nan' else ''} / {est_txt if est_txt.lower() != 'nan' else ''}")
            
            v_en = df.loc[p_idx, 'Endereço']
            txt_en = v_en if v_en.lower() != 'nan' else 'Não preenchido'
            st.info(f"📍 **Endereço Completo:** {txt_en}")
            
            v_com = df.loc[p_idx, 'Comentários']
            txt_com = str(v_com).strip() if v_com.lower() != 'nan' else ""
            st.text_area("🗒️ Comentários / Histórico Comunitário:", value=txt_com, height=100, disabled=True)
                # --- ABA 2: FORMULÁRIO DE EDIÇÃO DE REGISTROS EXISTENTES ---
    elif menu == "📝 Editar Cadastro Existente":
        st.subheader("📝 Editar Cadastro Comunitário")
        
        df_validos = df[df["Nome Civil"].str.lower() != "nan"]
        df_validos = df_validos[df_validos["Nome Civil"].str.strip() != ""]
        nomes_cadastrados = sorted(df_validos["Nome Civil"].unique())
        
        nome_alvo = st.selectbox("Selecione o Nome Civil para carregar:", nomes_cadastrados, key="nome_cadastro")
        
        if nome_alvo:
            registro_filtrado = df[df["Nome Civil"].str.lower() == nome_alvo.lower().strip()]
            
            if not registro_filtrado.empty:
                idx_real_salvamento = int(registro_filtrado.index[0])

                st.markdown("### 🏢 Validação Postal Geográfica (Opcional para consulta via CEP)")
                cep_busca = st.text_input("Digite um CEP para consulta rápida (8 números):", max_chars=8)
                
                rua_a, bairro_auto, cid_auto, uf_auto = "", "", "", ""
                if cep_busca.strip().isdigit() and len(cep_busca.strip()) == 8:
                    try:
                        req = requests.get(f"https://viacep.com.br{cep_busca.strip()}/json/", headers=headers_viacep, timeout=4)
                        if req.status_code == 200:
                            j_cep = req.json()
                            if "erro" not in j_cep:
                                rua_a = j_cep.get("logradouro", "")
                                bairro_auto = j_cep.get("bairro", "")
                                cid_auto = j_cep.get("localidade", "")
                                uf_auto = j_cep.get("uf", "")
                                st.success(f"📍 ViaCEP Encontrado: {rua_a}, {bairro_auto} - {cid_auto}/{uf_auto}")
                    except Exception: pass

                v_muni = str(df.at[idx_real_salvamento, "Município"]).strip()
                v_est = str(df.at[idx_real_salvamento, "UF"]).strip()
                v_end_antigo = str(df.at[idx_real_salvamento, "Endereço"]).strip()
                v_com_antigo = str(df.at[idx_real_salvamento, "Comentários"]).strip()

                with st.form("form_gps_editar_real"):
                    col_esq, col_dir = st.columns(2)
                    with col_esq:
                        st.markdown("### 👤 Dados de Identificação")
                        email_i = st.text_input("E-mail de Contato:", value=str(df.at[idx_real_salvamento, "E-mail"]) if str(df.at[idx_real_salvamento, "E-mail"]).lower() != "nan" else "")
                        nome_j_i = st.text_input("Nome Judaico / Hebraico:", value=str(df.at[idx_real_salvamento, "Nome Judaico"]) if str(df.at[idx_real_salvamento, "Nome Judaico"]).lower() != "nan" else "")
                        tel_i = st.text_input("Número de telefone:", value=str(df.at[idx_real_salvamento, "Número de telefone"]) if str(df.at[idx_real_salvamento, "Número de telefone"]).lower() != "nan" else "")
                        
                        lista_perfis = ["Judeu", "Bnei Anussim", "Simpatizante"]
                        v_p = str(df.at[idx_real_salvamento, "Perfil de Identidade"]).strip()
                        idx_p = lista_perfis.index(v_p) if v_p in lista_perfis else 2
                        perfil_i = st.selectbox("Perfil de Identidade:", lista_perfis, index=idx_p)
                        vinculo_i = st.text_input("Vinculação Comunitária:", value=str(df.at[idx_real_salvamento, "Vinculação Comunitária"]))
                    
                    with col_dir:
                        st.markdown("### 🏢 Localização Geográfica")
                        rua_i = st.text_input("Endereço Completo (Logradouro, nº, Bairro):", value=f"{rua_a}, nº  - {bairro_auto}" if rua_a else (v_end_antigo if v_end_antigo.lower() != 'nan' else ''))
                        muni_i = st.text_input("Município de Residência:", value=cid_auto if cid_auto else (v_muni if v_muni.lower() != "nan" else ""))
                        estado_i = st.text_input("UF / Estado:", value=uf_auto if uf_auto else (v_est if v_est.lower() != "nan" else ""))
                    
                    st.markdown("---")
                    coment_i = st.text_area("🗒️ Comentários / Histórico Comunitário:", value=v_com_antigo if v_com_antigo.lower() != "nan" else "", height=100)
                    
                    st.markdown("---")
                    aceite_lgpd = st.checkbox("Consinto com o tratamento dos dados sob as regras da LGPD.", key="lgpd_edit")
                    
                    if st.form_submit_button("💾 Gerar Linha Alterada para o Excel", use_container_width=True):
                        if not aceite_lgpd: 
                            st.error("Você precisa aceitar os termos da LGPD.")
                        else:
                            st.success("🎉 Linha estruturada! Passe o mouse sobre a tabela abaixo e clique no ícone de cópia para colar no seu Excel.")
                            # 🌟 AJUSTE: O separador interno na visualização respeita a ordenação com Município e UF no final
                            df_copia = pd.DataFrame([[nome_alvo, nome_j_i, email_i, rua_i, tel_i, perfil_i, vinculo_i, coment_i, muni_i, estado_i]], 
                                                    columns=lista_colunas_obrigatorias)
                            st.dataframe(df_copia, use_container_width=False)
            else:
                st.error("Membro não localizado na base de dados.")
    # --- ABA 3: INCLUSÃO DE NOVOS REGISTROS DO ZERO ---
    elif menu == "🆕 Criar Novo Cadastro do Zero":
        st.subheader("🆕 Criar Novo Cadastro Comunitário")
        
        st.markdown("### 🏢 Validação Postal")
        n_cep = st.text_input("Digite o CEP residencial (Apenas 8 números):", max_chars=8, key="cep_novo_membro")
        rua_n, bairro_n, muni_n, uf_n = "", "", "", ""
        if n_cep.strip().isdigit() and len(n_cep.strip()) == 8:
            try:
                req_n = requests.get(f"https://viacep.com.br{n_cep.strip()}/json/", headers=headers_viacep, timeout=4)
                if req_n.status_code == 200:
                    j_n = req_n.json()
                    if "erro" not in j_n:
                        rua_n = j_n.get("logradouro", "")
                        bairro_n = j_n.get("bairro", "")
                        muni_n = j_n.get("localidade", "")
                        uf_n = j_n.get("uf", "")
                        st.success(f"📍 Localizado: {rua_n}, {bairro_n} - {muni_n}/{uf_n}")
            except: pass

        with st.form("form_gps_novo"):
            col_esq, col_dir = st.columns(2)
            with col_esq:
                st.markdown("### 👤 Informações Pessoais")
                n_nome = st.text_input("Nome Civil (Obrigatório):")
                n_judaico = st.text_input("Nome Judaico / Hebraico:")
                n_email = st.text_input("E-mail:")
                n_telefone = st.text_input("Número de telefone (WhatsApp com DDD):")
                n_perfil = st.selectbox("Como se identifica em relação ao Judaísmo?", ["Judeu", "Bnei Anussim", "Simpatizante"], key="novo_perfil_sel")
                n_vinculo = st.text_input("Participa de alguma Comunidade/Sinagoga?", value="Isolado (Sem comunidade)")
            
            with col_dir:
                st.markdown("### 🏡 Ajuste do Endereço")
                n_rua = st.text_input("Endereço Completo (Logradouro, nº, Bairro):", value=f"{rua_n}, nº  - {bairro_n}" if rua_n else "")
                n_muni = st.text_input("Município / Cidade:", value=muni_n)
                n_estado = st.text_input("UF / Estado:", value=uf_n)
            
            st.markdown("---")
            n_coment = st.text_area("🗒️ Comentários / Histórico Comunitário Inicial:", value="", height=100)
            
            st.markdown("---")
            n_lgpd = st.checkbox("Consinto com o tratamento dos dados sob as regras da LGPD.", key="lgpd_novo")
            
            if st.form_submit_button("💾 Gerar Nova Linha para o Excel", use_container_width=True):
                if not n_nome.strip(): st.error("O campo 'Nome Civil' é obrigatório!")
                elif not n_lgpd: st.error("Você precisa aceitar os termos da LGPD.")
                else:
                    st.success(f"🎉 Linha para {n_nome} gerada com sucesso! Passe o mouse sobre a tabela abaixo e clique no ícone de cópia (📋) no canto direito para colar no seu Excel.")
                    
                    # 🌟 GERAÇÃO EXATA: Respeita a ordem com o Município e a UF no fim da linha do Excel
                    df_novo_membro_copia = pd.DataFrame([[n_nome.strip(), n_judaico, n_email, n_rua, n_telefone, n_perfil, n_vinculo, n_coment, n_muni, n_estado]], 
                                            columns=lista_colunas_obrigatorias)
                    st.dataframe(df_novo_membro_copia, use_container_width=False)

# --- RODAPÉ DISCRETO PADRONIZADO ---
st.markdown("---")
st.markdown("<p style='text-align:right; font-size:12px; color:gray;'>Bartolomeu Lima - Corecon-ES 1541</p>", unsafe_allow_html=True)

