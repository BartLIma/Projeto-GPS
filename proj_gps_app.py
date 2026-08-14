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
