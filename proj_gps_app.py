import pandas as pd
import streamlit as st
import requests
import os
import datetime

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

# --- TABELA INTERNA DE COORDENADAS MESTRE NACIONAL BLINDADA ---
coordenadas_cidades = {
    "vitoria": [-20.3155, -40.3128], "joao pessoa": [-7.1198, -34.8450],
    "campina grande": [-7.2247, -35.8772], "santa rita": [-7.1139, -34.9736],
    "patos": [-7.0269, -37.2797], "guarabira": [-6.8547, -35.4914],
    "cabedelo": [-6.9811, -34.8339], "vila velha": [-20.3297, -40.2925],
    "serra": [-20.1287, -40.3078], "cariacica": [-20.2639, -40.4201],
    "recife": [-8.0578, -34.8829], "salvador": [-12.9714, -38.5014],
    "maceio": [-9.6658, -35.7350], "aracaju": [-10.9111, -37.0717],
    "natal": [-5.7950, -35.2094], "fortaleza": [-3.7319, -38.5267],
    "teresina": [-5.0928, -42.8038], "sao luis": [-2.5307, -44.3068],
    "belo horizonte": [-19.9173, -43.9345], "brasilia": [-15.7942, -47.8822], 
    "sao paulo": [-23.5505, -46.6333], "rio de janeiro": [-22.9068, -43.1729],
    "manaus": [-3.1190, -60.0217], "curitiba": [-25.4284, -49.2733],
    "florianopolis": [-27.5954, -48.5480], "porto alegre": [-30.0346, -51.2177],
    "goiania": [-16.6869, -49.2648], "cuiaba": [-15.6010, -56.0949],
    "campo grande": [-20.4697, -54.6201], "belem": [-1.4558, -48.4902]
}

coordenadas_estados = {
    "pb": [-7.1198, -36.5000], "es": [-19.7500, -40.5000], "mg": [-18.5122, -44.5550],
    "pe": [-8.2833, -35.0730], "rn": [-5.7950, -36.5000], "ce": [-5.0000, -39.5000], 
    "ba": [-12.5000, -41.5000], "sp": [-23.5500, -46.6333], "rj": [-22.9068, -43.1729],
    "pr": [-24.5000, -51.5000], "sc": [-27.2500, -50.5000], "rs": [-30.0000, -53.5000],
    "am": [-3.1190, -60.0217], "df": [-15.7942, -47.8822], "al": [-9.5713, -36.7820],
    "se": [-10.5740, -37.3857], "pi": [-7.7183, -42.7289], "ma": [-4.9609, -45.2744],
    "go": [-15.8270, -49.8362], "mt": [-12.6819, -56.9211], "ms": [-20.7722, -54.7852],
    "pa": [-5.5368, -52.2955], "pt": [38.7223, -9.1393], "ro": [-10.8300, -62.8200],
    "rr": [-1.9900, -61.3300], "ap": [1.4100, -51.7700], "ac": [-9.0200, -70.8100]
}

tradutor_uf = {
    "paraiba": "pb", "pb": "pb", "espirito santo": "es", "es": "es",
    "minas gerais": "mg", "mg": "mg", "pernambuco": "pe", "pe": "pe",
    "rio grande do norte": "rn", "rn": "rn", "ceara": "ce", "ce": "ce",
    "bahia": "ba", "ba": "ba", "sao paulo": "sp", "sp": "sp", "rio de janeiro": "rj", "rj": "rj",
    "parana": "pr", "pr": "pr", "santa catarina": "sc", "sc": "sc", "rio grande do sul": "rs", "rs": "rs",
    "amazonas": "am", "am": "am", "distrito federal": "df", "df": "df", "alagoas": "al", "al": "al",
    "sergipe": "se", "se": "se", "piaui": "pi", "pi": "pi", "maranhao": "ma", "ma": "ma",
    "goias": "go", "go": "go", "mato grosso": "mt", "mt": "mt", "mato grosso do sul": "ms", "ms": "ms",
    "para": "pa", "pa": "pa", "portugal":"pt","rondonia": "ro", "ro": "ro","roraima": "rr", "rr": "rr",
    "acre": "ac", "ac": "ac"
}

headers_viacep = {
    "User-Agent": "Projeto-GPS-Bartolomeu/1.0 (bartolomeulima.corecon@gmail.com)",
    "Accept": "application/json"
}

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
            else: st.error("Senha incorreta! Tente novamente.")
# --- APLICATIVO PRINCIPAL LIBERADO ---
if st.session_state["acesso_liberado"]:
    
    lista_colunas_obrigatorias = [
        "Carimbo de data/hora", "Nome Civil", "Nome Judaico", "E-mail", 
        "Endereço", "Número de telefone", "Perfil de Identidade", 
        "Vinculação Comunitária", "Comentários", "Município", "UF"
    ]
    
    # Garante a existência do arquivo com cabeçalho correto se não existir
    if not os.path.exists("projeto_gps.csv"):
        df_vazio = pd.DataFrame(columns=lista_colunas_obrigatorias)
        df_vazio.to_csv("projeto_gps.csv", sep=",", index=False, encoding="utf-8-sig")

    # Inicializa df como um DataFrame vazio preventivamente
    df = pd.DataFrame(columns=lista_colunas_obrigatorias)

    # Tenta ler o arquivo tratando codificações diferentes
    try:
        df_lido = pd.read_csv("projeto_gps.csv", sep=",", encoding="utf-8-sig", dtype=str, skip_blank_lines=True)
        if isinstance(df_lido, pd.DataFrame):
            df = df_lido
    except Exception:
        try:
            df_lido = pd.read_csv("projeto_gps.csv", sep=",", encoding="cp1252", dtype=str, skip_blank_lines=True)
            if isinstance(df_lido, pd.DataFrame):
                df = df_lido
        except Exception as e:
            st.error(f"Erro crítico ao ler o banco de dados: {e}")

    # Remove linhas totalmente nulas e garante que df continua sendo DataFrame
    df = df.dropna(how="all")
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(columns=lista_colunas_obrigatorias)

    # Mapeamento e normalização inteligente de colunas
    mapeamento_colunas = {}
    for col in df.columns:
        col_limpa = col.strip().lower().replace("-", "").replace(" ", "").replace("_", "").replace("/", "").replace("í", "i").replace("ê", "e").replace("á", "a").replace("ó", "o").replace("ã", "a")
        if "carimbo" in col_limpa or "datahora" in col_limpa: mapeamento_colunas[col] = "Carimbo de data/hora"
        elif "municip" in col_limpa: mapeamento_colunas[col] = "Município"
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
    
    # Assegura que todas as colunas obrigatórias existam no DataFrame
    for col_nome in lista_colunas_obrigatorias:
        if col_nome not in df.columns: 
            df[col_nome] = ""
            
    # Executa a limpeza preventiva de strings (A antiga linha 126 agora está blindada)
    for c in df.columns: 
        df[c] = df[c].fillna("").astype(str).str.strip()

    # --- BARRA LATERAL ---
    st.sidebar.header("Painel de Controle GPS")
    menu = st.sidebar.radio("Selecione a Ação:", ["🔍 Consultar por Nome", "📝 Editar Cadastro Existente", "🆕 Criar Novo Cadastro do Zero", "🏙️ Mapa por Município", "🗺️ Mapa por Estado"])
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
                opcoes_pessoas = {"-- Selecione uma pessoa da lista --": -1}
                for idx, row in registros_encontrados.iterrows():
                    opcoes_pessoas[f"{row['Nome Civil']} ({row['Nome Judaico']}) - {row['Município']}"] = int(idx)
                
                pessoa_sel = st.selectbox("Selecione a pessoa para abrir a ficha:", sorted(opcoes_pessoas.keys()))
                p_idx_escolhido = opcoes_pessoas.get(pessoa_sel)
                if p_idx_escolhido is not None and p_idx_escolhido >= 0:
                    st.session_state["indice_persona_consultada"] = p_idx_escolhido
            else:
                st.session_state["indice_persona_consultada"] = None
                st.warning("Nenhuma pessoa foi localizada.")
        else:
            st.session_state["indice_persona_consultada"] = None
            st.info("💡 Por favor, digite o nome de alguém acima para realizar a consulta.")

        if st.session_state["indice_persona_consultada"] is not None:
            p_idx = st.session_state["indice_persona_consultada"]
            st.markdown("---")
            st.subheader(f"👤 Ficha Cadastral — {df.at[p_idx, 'Nome Civil']}")
            
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                st.write(f"**Nome Civil:** {df.at[p_idx, 'Nome Civil']}")
                st.write(f"**Nome Judaico:** {df.at[p_idx, 'Nome Judaico']}")
                st.write(f"**E-mail:** {df.at[p_idx, 'E-mail']}")
                st.write(f"**Número de telefone:** {df.at[p_idx, 'Número de telefone']}")
            with f_col2:
                st.write(f"**Perfil de Identidade:** {df.at[p_idx, 'Perfil de Identidade']}")
                st.write(f"**Vinculação Comunitária:** {df.at[p_idx, 'Vinculação Comunitária']}")
                st.write(f"**Localidade:** {df.at[p_idx, 'Município']} / {df.at[p_idx, 'UF']}")
                st.write(f"**Data de Cadastro:** {df.at[p_idx, 'Carimbo de data/hora']}")
            
            st.info(f"📍 **Endereço Completo:** {df.at[p_idx, 'Endereço']}")
            st.text_area("🗒️ Comentários:", value=df.at[p_idx, 'Comentários'], height=80, disabled=True)
            
            muni_membro = str(df.at[p_idx, 'Município']).lower().strip()
            if muni_membro in coordenadas_cidades:
                st.markdown(f"#### 🗺️ Localização Geográfica Focalizada — {muni_membro.title()}")
                coords = coordenadas_cidades[muni_membro]
                df_muni_mapa = pd.DataFrame([{
                    "latitude": float(coords[0]), 
                    "longitude": float(coords[1])
                }])
                st.map(df_muni_mapa, size=30, color="#2e7d32")
            else:
                st.caption("ℹ️ Mapa em nível de rua indisponível para este município.")
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

                st.markdown("### 🏢 Validação Postal Geográfica")
                cep_busca = st.text_input("Digite um CEP para consulta rápida (8 números):", max_chars=8)
                rua_a, bairro_auto, cid_auto, uf_auto = "", "", "", ""
                if cep_busca.strip().isdigit() and len(cep_busca.strip()) == 8:
                    try:
                        req = requests.get(f"https://viacep.com.br{cep_busca.strip()}/json/", headers=headers_viacep, timeout=4)
                        if req.status_code == 200:
                            j_cep = req.json()
                            if "erro" not in j_cep:
                                rua_a, bairro_auto, cid_auto, uf_auto = j_cep.get("logradouro", ""), j_cep.get("bairro", ""), j_cep.get("localidade", ""), j_cep.get("uf", "")
                                st.success(f"📍 ViaCEP Encontrado: {rua_a}, {bairro_auto} - {cid_auto}/{uf_auto}")
                    except Exception: pass

                v_carimbo = str(df.at[idx_real_salvamento, "Carimbo de data/hora"]).strip()
                v_muni = str(df.at[idx_real_salvamento, "Município"]).strip()
                v_est = str(df.at[idx_real_salvamento, "UF"]).strip()
                v_end_antigo = str(df.at[idx_real_salvamento, "Endereço"]).strip()
                v_com_antigo = str(df.at[idx_real_salvamento, "Comentários"]).strip()

                with st.form("form_gps_editar_real"):
                    col_esq, col_dir = st.columns(2)
                    with col_esq:
                        st.markdown("### 👤 Dados de Identificação")
                        email_i = st.text_input("E-mail de Contato:", value=str(df.at[idx_real_salvamento, "E-mail"]))
                        nome_j_i = st.text_input("Nome Judaico / Hebraico:", value=str(df.at[idx_real_salvamento, "Nome Judaico"]))
                        tel_i = st.text_input("Número de telefone:", value=str(df.at[idx_real_salvamento, "Número de telefone"]))
                        lista_perfis = ["Judeu", "Bnei Anussim", "Simpatizante"]
                        v_p = str(df.at[idx_real_salvamento, "Perfil de Identidade"]).strip()
                        idx_p = lista_perfis.index(v_p) if v_p in lista_perfis else 2
                        perfil_i = st.selectbox("Perfil de Identidade:", lista_perfis, index=idx_p)
                        vinculo_i = st.text_input("Vinculação Comunitária:", value=str(df.at[idx_real_salvamento, "Vinculação Comunitária"]))
                    with col_dir:
                        st.markdown("### 🏢 Localização Geográfica")
                        rua_i = st.text_input("Endereço Completo (Logradouro, nº, Bairro):", value=f"{rua_a}, nº  - {bairro_auto}" if rua_a else v_end_antigo)
                        muni_i = st.text_input("Município de Residência:", value=cid_auto if cid_auto else v_muni)
                        estado_i = st.text_input("UF / Estado:", value=uf_auto if uf_auto else v_est)
                    
                    st.markdown("---")
                    coment_i = st.text_area("🗒️ Comentários / Histórico Comunitário:", value=v_com_antigo, height=100)
                    aceite_lgpd = st.checkbox("Consinto com o tratamento dos dados sob as regras da LGPD.", key="lgpd_edit")
                    
                    if st.form_submit_button("💾 Gerar Linha Alterada para o Excel", use_container_width=True):
                        if not aceite_lgpd: st.error("Você precisa aceitar os termos da LGPD.")
                        else:
                            st.success("🎉 Linha estruturada! Clique no ícone de cópia para colar no seu Excel.")
                            df_copia = pd.DataFrame([[v_carimbo, nome_alvo, nome_j_i, email_i, rua_i, tel_i, perfil_i, vinculo_i, coment_i, muni_i, estado_i]], columns=lista_colunas_obrigatorias)
                            st.dataframe(df_copia, use_container_width=False)

    # --- ABA 3: INCLUSÃO DE NOVOS REGISTROS DO ZERO ---
    elif menu == "🆕 Criar Novo Cadastro do Zero":
        st.subheader("🆕 Criar Novo Cadastro Comunitário")
        n_cep = st.text_input("Digite o CEP residencial (Apenas 8 números):", max_chars=8, key="cep_novo_membro")
        rua_n, bairro_n, muni_n, uf_n = "", "", "", ""
        if n_cep.strip().isdigit() and len(n_cep.strip()) == 8:
            try:
                req_n = requests.get(f"https://viacep.com.br{n_cep.strip()}/json/", headers=headers_viacep, timeout=4)
                if req_n.status_code == 200:
                    j_n = req_n.json()
                    if "erro" not in j_n:
                        rua_n, bairro_n, muni_n, uf_n = j_n.get("logradouro", ""), j_n.get("bairro", ""), j_n.get("localidade", ""), j_n.get("uf", "")
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
            n_lgpd = st.checkbox("Consinto com o tratamento dos dados sob as regras da LGPD.", key="lgpd_novo")
            
            if st.form_submit_button("💾 Gerar Nova Linha para o Excel", use_container_width=True):
                if not n_nome.strip(): st.error("O campo 'Nome Civil' é obrigatório!")
                elif not n_lgpd: st.error("Você precisa aceitar os termos da LGPD.")
                else:
                    st.success(f"🎉 Linha para {n_nome} gerada com sucesso! Clique no ícone de cópia (📋) para colar no Excel.")
                    agora_carimbo = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    df_novo_membro_copia = pd.DataFrame([[agora_carimbo, n_nome.strip(), n_judaico, n_email, n_rua, n_telefone, n_perfil, n_vinculo, n_coment, n_muni, n_estado]], columns=lista_colunas_obrigatorias)
                    st.dataframe(df_novo_membro_copia, use_container_width=False)
    # --- ABA 4: MAPA POR MUNICÍPIO ---
    elif menu == "🏙️ Mapa por Município":
        st.title("🏙️ Mapa de Distribuição por Município")
        st.markdown("Selecione qualquer município presente na sua base de dados para focar a visão.")
        
        if not df.empty and "Município" in df.columns:
            df_filtrado_cidades = df[df["Município"].str.strip() != ""]
            df_filtrado_cidades = df_filtrado_cidades[df_filtrado_cidades["Município"].str.lower() != "nan"]
            lista_municipios_reais = sorted(df_filtrado_cidades["Município"].unique())
            
            if lista_municipios_reais:
                cidade_selecionada = st.selectbox("Selecione qual município você deseja analisar no mapa:", lista_municipios_reais)
                membros_da_cidade = df[df["Município"].str.lower().str.strip() == cidade_selecionada.lower().strip()]
                total_membros = len(membros_da_cidade)
                
                st.metric(f"📍 Membros em {cidade_selecionada}", total_membros)
                
                cep_referencia = ""
                for _, row in membros_da_cidade.iterrows():
                    if "Cep" in df.columns and str(row["Cep"]).strip().isdigit() and len(str(row["Cep"]).strip()) == 8:
                        cep_referencia = str(row["Cep"]).strip()
                        break
                        
                latitude_descoberta, longitude_descoberta = None, None
                cidade_busca_chave = cidade_selecionada.lower().strip()
                
                if cidade_busca_chave in coordenadas_cidades:
                    coords_contingencia = coordenadas_cidades[cidade_busca_chave]
                    latitude_descoberta = float(coords_contingencia[0])
                    longitude_descoberta = float(coords_contingencia[1])
                
                if latitude_descoberta is None and cep_referencia:
                    try:
                        url_geo = f"https://thepro.com.br{cep_referencia}"
                        req_geo = requests.get(url_geo, headers=headers_viacep, timeout=4).json()
                        if "lat" in req_geo and "lng" in req_geo:
                            latitude_descoberta = float(req_geo["lat"])
                            longitude_descoberta = float(req_geo["lng"])
                    except: pass
                
                if latitude_descoberta is None:
                    try:
                        url_osm = f"https://openstreetmap.org{cidade_selecionada},+Brazil"
                        req_osm = requests.get(url_osm, headers=headers_viacep, timeout=4).json()
                        if req_osm:
                            latitude_descoberta = float(req_osm[0]["lat"])
                            longitude_descoberta = float(req_osm[0]["lon"])
                    except: pass
                
                if latitude_descoberta is not None and longitude_descoberta is not None:
                    tamanho_circulo = int(total_membros) * 45
                    df_ponto_mapa = pd.DataFrame([{
                        "latitude": latitude_descoberta,
                        "longitude": longitude_descoberta,
                        "size": tamanho_circulo
                    }])
                    st.map(df_ponto_mapa, size="size", color="#0056b3")
                else:
                    st.warning(f"ℹ️ Não foi possível obter as coordenadas geográficas para {cidade_selecionada}.")
            else: st.warning("⚠️ Nenhum município válido localizado na coluna.")
        else: st.warning("⚠️ A coluna 'Município' não foi localizada.")

    # --- ABA 5: MAPA POR ESTADO ---
    elif menu == "🗺️ Mapa por Estado":
        st.title("🗺️ Concentração Geo-Comunitária por Estado (UF)")
        st.markdown("Visualização macro mostrando o volume de membros por Estado do Brasil.")
        lista_mapa_estado = []
        
        if not df.empty and "UF" in df.columns:
            somas_estados = {}
            for _, row in df.iterrows():
                uf_bruta = str(row["UF"]).strip().lower().replace("í", "i").replace("ã", "a")
                if not uf_bruta or uf_bruta == "nan":
                    continue
                
                uf_oficial = tradutor_uf.get(uf_bruta, uf_bruta)
                if uf_oficial in coordenadas_estados:
                    somas_estados[uf_oficial] = somas_estados.get(uf_oficial, 0) + 1
            
            for uf_chave, total in somas_estados.items():
                coords = coordenadas_estados[uf_chave]
                lista_mapa_estado.append({
                    "latitude": float(coords[0]), 
                    "longitude": float(coords[1]), 
                    "uf_sigla": uf_chave.upper(), 
                    "quantidade": int(total), 
                    "size": int(total) * 150
                })
        
        if len(lista_mapa_estado) > 0:
            df_mapa_estado = pd.DataFrame(lista_mapa_estado)
            st.metric("🗺️ Estados Computados no Brasil + Portugal", len(df_mapa_estado))
            st.map(df_mapa_estado, size="size", color="#d32f2f")
            st.markdown("### 📊 Densidade Real Consolidada por Estado (UF) + Portugal:")
            for item in lista_mapa_estado: 
                st.write(f"• **{item['uf_sigla']}:** {item['quantidade']} membro(s) localizado(s).")
        else: st.warning("⚠️ Nenhum estado cadastrado foi localizado.")

# --- RODAPÉ DISCRETO PADRONIZADO ---
st.markdown("---")
st.markdown("<p style='text-align:right; font-size:12px; color:gray;'>Bartolomeu Lima - Corecon-ES 1541</p>", unsafe_allow_html=True)
