import pandas as pd
import streamlit as st
import requests
import os
import datetime
import unicodedata
import urllib.parse

# Força o navegador a desabilitar tradutores automáticos que quebram o React DOM
st.markdown(
    '<meta name="google" content="notranslate">', 
    unsafe_allow_html=True
)

st.set_page_config(layout="wide", page_title="Painel GPS", page_icon="🗺️")

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

headers_viacep = {
    "User-Agent": "Projeto-GPS-Bartolomeu/1.0 (bartolomeulima.corecon@gmail.com)",
    "Accept": "application/json"
}

# --- ALAVANCA 100% DINÂMICA: BUSCA LOCALIZAÇÃO SÓ PELO NOME ---
@st.cache_data(show_spinner=False)
def buscar_coordenadas(nome_municipio, uf_registro=""):
    """Consulta a API Nominatim diretamente por texto com alta precisão global"""
    if not nome_municipio or pd.isna(nome_municipio):
        return None
        
    try:
        muni_limpo = str(nome_municipio).strip().lower()
        uf_limpa = str(uf_registro).strip().lower()
        
        # Monta a estratégia de busca textual inteligente baseada na UF informada
        if uf_limpa == "pt":
            termo_completo = f"{muni_limpo}, Portugal"
        elif uf_limpa == "it":
            termo_completo = f"{muni_limpo}, Italy"
        elif uf_limpa:
            termo_completo = f"{muni_limpo}, {uf_limpa.upper()}, Brazil"
        else:
            termo_completo = f"{muni_limpo}, Brazil"
            
        cidade_enc = urllib.parse.quote(termo_completo)
        url = f"https://openstreetmap.org{cidade_enc}&format=jsonv2&limit=1"
        
        resposta = requests.get(url, headers=headers_viacep, timeout=8)
        dados = resposta.json()
        
        if dados and len(dados) > 0:
            return {"lat": float(dados[0]["lat"]), "lon": float(dados[0]["lon"])}
    except Exception:
        pass
        
    return None

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
if st.session_state["acesso_liberado"]:
    lista_colunas_obrigatorias = ["Carimbo de data/hora", "Nome Civil", "Nome Judaico", "E-mail", "Endereço", "Número de telefone", "Perfil de Identidade", "Vinculação Comunitária", "Comentários", "Município", "UF"]
    
    if not os.path.exists("projeto_gps.csv"):
        df_vazio = pd.DataFrame(columns=lista_colunas_obrigatorias)
        df_vazio.to_csv("projeto_gps.csv", sep=",", index=False, encoding="utf-8-sig")

    try:
        df = pd.read_csv("projeto_gps.csv", sep=",", encoding="utf-8-sig", dtype=str, skip_blank_lines=True)
    except Exception:
        df = pd.read_csv("projeto_gps.csv", sep=",", encoding="cp1252", dtype=str, skip_blank_lines=True)
        
    df = df.dropna(how="all")

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
    for col_nome in lista_colunas_obrigatorias:
        if col_nome not in df.columns: df[col_nome] = ""
    for c in df.columns: df[c] = df[c].fillna("").astype(str).str.strip()

    st.sidebar.header("Painel de Controle GPS")
    menu = st.sidebar.radio("Selecione a Ação:", ["🔍 Consultar por Nome", "📝 Editar Cadastro Existente", "🆕 Criar Novo Cadastro do Zero", "🏙️ Mapa por Município", "🗺️ Mapa por Estado"])
    st.sidebar.markdown("---")

    # --- ABA 1: CONSULTA DO BANCO DE DADOS POR NOME ---
    if menu == "🔍 Consultar por Nome":
        st.title("🔍 Consulta de Membros da Comunidade")
        col1, col2 = st.columns(2)
        with col1:
            busca_nome = st.text_input("Digite o Nome Civil ou Nome Judaico para pesquisar:", value="")
        
        if busca_nome.strip():
            termo = busca_nome.lower().strip()
            filtro = df["Nome Civil"].str.lower().str.contains(termo) | df["Nome Judaico"].str.lower().str.contains(termo)
            registros_encontrados = df[filtro]
            
            if not registros_encontrados.empty:
                opcoes_pessoas = {"-- Selecione uma pessoa da lista --": -1}
                for idx, row in registros_encontrados.iterrows():
                    opcoes_pessoas[f"{row['Nome Civil']} ({row['Nome Judaico']}) - {row['Município']}"] = int(idx)
                with col2:
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
            
            muni_membro = str(df.at[p_idx, 'Município']).strip()
            uf_membro = str(df.at[p_idx, 'UF']).strip()
            
            if muni_membro:
                st.markdown(f"#### 🗺️ Localização Geográfica Focalizada — {muni_membro.title()}")
                coords = buscar_coordenadas(muni_membro, uf_membro)
                if coords:
                    df_muni_mapa = pd.DataFrame([{"latitude": float(coords["lat"]), "longitude": float(coords["lon"])}])
                    st.map(df_muni_mapa, size=40, color="#2e7d32", zoom=12)
                else:
                    st.caption("ℹ️ Mapa indisponível para esta localidade.")
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
                        # Rota corrigida e estável com '/ws/'
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
        st.markdown("Selecione qualquer município presente na sua base de dados para focar a visão e listar os membros.")
        
        if not df.empty and "Município" in df.columns:
            df_filtrado_cidades = df[df["Município"].str.strip() != ""]
            df_filtrado_cidades = df_filtrado_cidades[df_filtrado_cidades["Município"].str.lower() != "nan"]
            lista_municipios_reais = sorted(df_filtrado_cidades["Município"].unique())
            
            if lista_municipios_reais:
                cidade_selecionada = st.selectbox("Selecione qual município você deseja analisar:", lista_municipios_reais)
                membros_da_cidade = df[df["Município"].str.lower().str.strip() == cidade_selecionada.lower().strip()]
                total_membros = len(membros_da_cidade)
                
                st.metric(f"📍 Membros em {cidade_selecionada}", total_membros)
                st.markdown("---")
                st.markdown(f"### 📋 Dados Completos dos Membros Localizados em **{cidade_selecionada}**")
                
                st.dataframe(membros_da_cidade, use_container_width=True, hide_index=True)
                st.markdown("---")
                uf_referencia = ""
                if "UF" in membros_da_cidade.columns and not membros_da_cidade.empty:
                    uf_referencia = str(membros_da_cidade["UF"].iloc[0]).strip()
                
                # CHAMADA DA ALAVANCA HÍBRIDA GLOBAL 100% DINÂMICA:
                coords_descobertas = buscar_coordenadas(cidade_selecionada, uf_referencia)
                
                if coords_descobertas:
                    st.markdown("#### 🗺️ Localização Geográfica")
                    tamanho_circulo = int(total_membros) * 45
                    df_ponto_mapa = pd.DataFrame([{
                        "latitude": float(coords_descobertas["lat"]),
                        "longitude": float(coords_descobertas["lon"]),
                        "size": tamanho_circulo
                    }])
                    st.map(df_ponto_mapa, size="size", color="#0056b3")
                else:
                    st.info(f"ℹ️ Nota: O mapa não pôde ser renderizado para {cidade_selecionada}, mas os dados nominais acima estão preservados.")
            else: st.warning("⚠️ Nenhum município válido localizado na coluna.")
        else: st.warning("⚠️ A coluna 'Município' não foi localizada.")

    # --- ABA 5: MAPA POR ESTADO ---
    elif menu == "🗺️ Mapa por Estado":
        st.title("🗺️ Concentração Geo-Comunitária por Estado (UF)")
        st.markdown("Visualização macro mostrando o volume de membros por Estado ou Região Internacional.")
        lista_mapa_estado = []
        
        if not df.empty and "UF" in df.columns:
            df_validos_uf = df[df["UF"].str.strip() != ""]
            df_validos_uf = df_validos_uf[df_validos_uf["UF"].str.lower() != "nan"]
            lista_ufs_reais = sorted(df_validos_uf["UF"].unique())
            
            somas_estados = {}
            for uf_item in lista_ufs_reais:
                total_uf = len(df[df["UF"].str.lower().str.strip() == uf_item.lower().strip()])
                
                # Faz a busca dinâmica em tempo real no globo terrestre usando a própria sigla/nome (Ex: PB, PT, IT)
                coords_uf = buscar_coordenadas(uf_item, uf_item)
                if coords_uf:
                    lista_mapa_estado.append({
                        "latitude": float(coords_uf["lat"]), 
                        "longitude": float(coords_uf["lon"]), 
                        "uf_sigla": uf_item.upper(), 
                        "quantidade": int(total_uf), 
                        "size": int(total_uf) * 150
                    })
        
        if len(lista_mapa_estado) > 0:
            df_mapa_estado = pd.DataFrame(lista_mapa_estado)
            st.metric("🗺️ Estados/Regiões Computadas no Sistema", len(df_mapa_estado))
            st.map(df_mapa_estado, size="size", color="#d32f2f")
            st.markdown("### 📊 Densidade Real Consolidada por Região/Estado:")
            for item in lista_mapa_estado: 
                st.write(f"• **{item['uf_sigla']}:** {item['quantidade']} membro(s) localizado(s).")
        else:
            st.warning("⚠️ Nenhum estado cadastrado com coordenadas válidas foi localizado.")

# --- RODAPÉ DISCRETO PADRONIZADO ---
st.markdown("---")
st.markdown("<p style='text-align:right; font-size:12px; color:gray;'>Bartolomeu Lima - Corecon-ES 1541</p>", unsafe_allow_html=True)


# --- FUNÇÃO DE BUSCA HÍBRIDA GLOBAL INTELIGENTE ---
@st.cache_data(show_spinner=False)
def buscar_coordenadas(nome_entrada: str, uf_registro: str = ""):
    """Busca em cache local; Se não achar, localiza dinamicamente na API global"""
    if not nome_entrada:
        return None
        
    def normalizar_local(txt):
        return unicodedata.normalize('NFKD', str(txt)).encode('ascii', 'ignore').decode('utf-8').strip().lower()
        
    nome_limpo = normalizar_local(nome_entrada.split(",")[0])
    uf_limpa = normalizar_local(uf_registro)
    
    # 1. Tentativa na tabela interna mestre
    if nome_limpo in coordenadas_cidades:
        return coordenadas_cidades[nome_limpo]
        
    # 2. Chamada Dinâmica na Internet (OpenStreetMap)
    try:
        if uf_limpa == "pt":
            termo_geo = f"{nome_limpo}, Portugal"
        elif uf_limpa == "it":
            termo_geo = f"{nome_limpo}, Italy"
        elif uf_limpa:
            termo_geo = f"{nome_limpo}, {uf_limpa.upper()}, Brazil"
        else:
            termo_geo = f"{nome_limpo}, Brazil"
            
        cidade_enc = urllib.parse.quote(termo_geo)
        url_busca = f"https://openstreetmap.org{cidade_enc}&format=jsonv2&limit=1"
        
        resposta = requests.get(url_busca, headers=headers_viacep, timeout=6)
        dados = resposta.json()
        
        if dados and len(dados) > 0:
            return {"lat": float(dados[0]["lat"]), "lon": float(dados[0]["lon"])}
    except Exception:
        pass
    return None

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
if st.session_state["acesso_liberado"]:
    lista_colunas_obrigatorias = ["Carimbo de data/hora", "Nome Civil", "Nome Judaico", "E-mail", "Endereço", "Número de telefone", "Perfil de Identidade", "Vinculação Comunitária", "Comentários", "Município", "UF"]
    
    if not os.path.exists("projeto_gps.csv"):
        df_vazio = pd.DataFrame(columns=lista_colunas_obrigatorias)
        df_vazio.to_csv("projeto_gps.csv", sep=",", index=False, encoding="utf-8-sig")

    try:
        df = pd.read_csv("projeto_gps.csv", sep=",", encoding="utf-8-sig", dtype=str, skip_blank_lines=True)
    except Exception:
        df = pd.read_csv("projeto_gps.csv", sep=",", encoding="cp1252", dtype=str, skip_blank_lines=True)
        
    df = df.dropna(how="all")

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
    for col_nome in lista_colunas_obrigatorias:
        if col_nome not in df.columns: df[col_nome] = ""
    for c in df.columns: df[c] = df[c].fillna("").astype(str).str.strip()

    st.sidebar.header("Painel de Controle GPS")
    menu = st.sidebar.radio("Selecione a Ação:", ["🔍 Consultar por Nome", "📝 Editar Cadastro Existente", "🆕 Criar Novo Cadastro do Zero", "🏙️ Mapa por Município", "🗺️ Mapa por Estado"])
    st.sidebar.markdown("---")

    # --- ABA 1: CONSULTA DO BANCO DE DADOS POR NOME ---
    if menu == "🔍 Consultar por Nome":
        st.title("🔍 Consulta de Membros da Comunidade")
        col1, col2 = st.columns(2)
        with col1:
            busca_nome = st.text_input("Digite o Nome Civil ou Nome Judaico para pesquisar:", value="")
        
        if busca_nome.strip():
            termo = busca_nome.lower().strip()
            filtro = df["Nome Civil"].str.lower().str.contains(termo) | df["Nome Judaico"].str.lower().str.contains(termo)
            registros_encontrados = df[filtro]
            
            if not registros_encontrados.empty:
                opcoes_pessoas = {"-- Selecione uma pessoa da lista --": -1}
                for idx, row in registros_encontrados.iterrows():
                    opcoes_pessoas[f"{row['Nome Civil']} ({row['Nome Judaico']}) - {row['Município']}"] = int(idx)
                with col2:
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
            
            muni_membro = str(df.at[p_idx, 'Município']).strip()
            uf_membro = str(df.at[p_idx, 'UF']).strip()
            
            if muni_membro:
                st.markdown(f"#### 🗺️ Localização Geográfica Focalizada — {muni_membro.title()}")
                coords = buscar_coordenadas(muni_membro, uf_membro)
                if coords:
                    df_muni_mapa = pd.DataFrame([{"latitude": float(coords["lat"]), "longitude": float(coords["lon"])}])
                    st.map(df_muni_mapa, size=40, color="#2e7d32", zoom=12)
                else:
                    st.caption("ℹ️ Mapa indisponível para esta localidade.")
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
                        # --- CORREÇÃO: Adicionado a barra /ws/ correta do ViaCEP ---
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
                # --- CORREÇÃO: Adicionado /ws/ na rota ---
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
                        # --- CORREÇÃO: Adicionado a barra /ws/ correta do ViaCEP ---
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
                # --- CORREÇÃO: Adicionado /ws/ na rota ---
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
