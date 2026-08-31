import pandas as pd
import streamlit as st
import requests
import os
import datetime
import streamlit as st

# Força o navegador a desabilitar tradutores automáticos que quebram o React DOM
st.set_page_col_config = st.markdown(
    '<meta name="google" content="notranslate">', 
    unsafe_allow_html=True
)

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

import streamlit as st

# 1. Coordenadas geográficas de GPS (Latitude e Longitude) das Cidades
# Dica: Cadastre as chaves sempre em letras MINÚSCULAS e sem siglas para facilitar a busca
coordenadas_cidades = {
    "campina grande": {"lat": -7.2306, "lon": -35.8811},
    "lisboa": {"lat": 38.7223, "lon": -9.1393},
    "viçosa": {"lat": -20.7546, "lon": -42.8814},
    "piranhas": {"lat": -9.6242, "lon": -37.7536},
    "recife": {"lat": -8.0539, "lon": -34.8811},
    "porto alegre": {"lat": -30.0346, "lon": -51.2177},
    "ipojuca": {"lat": -8.3981, "lon": -35.0614},
    "santos": {"lat": -23.9608, "lon": -46.3339},
    "palhoça": {"lat": -27.6414, "lon": -48.6672},
    "manaus": {"lat": -3.1190, "lon": -60.0217},
    "brasília": {"lat": -15.7801, "lon": -47.9292},
    "timóteo": {"lat": -19.5828, "lon": -42.6414},
    "colombo": {"lat": -25.2917, "lon": -49.2242},
    "são luiz gonzaga": {"lat": -28.4081, "lon": -54.9606},
    "salvador": {"lat": -12.9714, "lon": -38.5014},
    "rio de janeiro": {"lat": -22.9068, "lon": -43.1729},
    "fortaleza": {"lat": -3.7319, "lon": -38.5267},
    "ponta grossa": {"lat": -25.0950, "lon": -50.1614},
    "oeiras - lisboa": {"lat": 38.6969, "lon": -9.3044},
    "belo horizonte": {"lat": -19.9167, "lon": -43.9345},
    "sobral": {"lat": -3.6847, "lon": -40.3497},
    "goiânia": {"lat": -16.6869, "lon": -49.2648},
    "divinópolis": {"lat": -20.1431, "lon": -44.8908},
    "florianópolis": {"lat": -27.5954, "lon": -48.5480},
    "guaraciaba do norte": {"lat": -4.1672, "lon": -40.7481},
    "garanhuns": {"lat": -8.8906, "lon": -36.4928},
    "ceilândia norte": {"lat": -15.8181, "lon": -48.1064},
    "natal": {"lat": -5.7945, "lon": -35.2110},
    "londrina": {"lat": -23.3106, "lon": -51.1628},
    "lagoa santa": {"lat": -19.6411, "lon": -43.8903},
    "itumbiara": {"lat": -18.4194, "lon": -49.2139},
    "braga": {"lat": 41.5454, "lon": -8.4265},
    "ruy barbosa": {"lat": -12.2839, "lon": -40.4064},
    "nova lima": {"lat": -19.9856, "lon": -43.8503},
    "cascavel": {"lat": -24.9558, "lon": -53.4553},
    "teresina": {"lat": -5.0920, "lon": -42.8034},
    "são paulo": {"lat": -23.5505, "lon": -46.6333},
    "passo fundo": {"lat": -28.2586, "lon": -52.4089},
    "maceió": {"lat": -9.6658, "lon": -35.7350},
    "belém": {"lat": -1.4558, "lon": -48.4902},
    "cariacica": {"lat": -20.3364, "lon": -40.4200},
    "guarujá": {"lat": -23.9931, "lon": -46.2564},
    "balneário camboriú": {"lat": -26.9926, "lon": -48.6347},
    "são vicente": {"lat": -23.9631, "lon": -46.3919},
    "balsas": {"lat": -7.5325, "lon": -46.1375},
    "araucária": {"lat": -25.5925, "lon": -49.4103},
    "capanema": {"lat": -1.1983, "lon": -47.1736},
    "palmas": {"lat": -10.1838, "lon": -48.3336},
    "nova iorque": {"lat": -6.7408, "relative_lon": -44.0414},
    "curitiba": {"lat": -25.4290, "lon": -49.2671},
    "vitória": {"lat": -20.3155, "lon": -40.3128},
    "mauá": {"lat": -23.6678, "lon": -46.4614},
    "araçuaí": {"lat": -16.8494, "lon": -42.4414},
    "seixal": {"lat": 38.6436, "lon": -9.1009},
    "bauru": {"lat": -22.3147, "lon": -49.0586},
    "irati": {"lat": -25.4672, "lon": -50.6511},
    "camboriú": {"lat": -27.0253, "lon": -48.6539},
    "aracaju": {"lat": -10.9472, "lon": -37.0731},
    "águas de são pedro": {"lat": -22.5986, "lon": -47.8739},
    "são lourenço": {"lat": -22.1158, "lon": -45.0547},
    "aparecida de goiânia": {"lat": -16.8219, "lon": -49.2458},
    "caruaru": {"lat": -8.2839, "lon": -35.9753},
    "cacoal": {"lat": -11.4428, "lon": -61.4425},
    "caxias do sul": {"lat": -29.1678, "lon": -51.1794},
    "jardim paulista": {"lat": -23.5686, "lon": -46.6636},
    "canela": {"lat": -29.3664, "lon": -50.8122},
    "vale do aço": {"lat": -19.4975, "lon": -42.5458},
    "piumhi": {"lat": -20.4633, "lon": -45.9581},
    "campinas": {"lat": -22.9056, "lon": -47.0608},
    "alcobaça": {"lat": -17.5161, "lon": -39.1958},
    "nova iguaçu": {"lat": -22.7561, "lon": -43.4608},
    "parnamirim": {"lat": -5.9156, "lon": -35.2628},
    "guarulhos": {"lat": -23.4539, "lon": -46.5333},
    "blumenau": {"lat": -26.9194, "lon": -49.0661},
    "rio das ostras": {"lat": -22.5261, "lon": -41.9442},
    "marechal deodoro": {"lat": -9.7114, "lon": -35.8958},
    "feira de santana": {"lat": -12.2564, "lon": -38.9631},
    "são bernardo do campo": {"lat": -23.6939, "lon": -46.5650},
    "eusébio": {"lat": -3.8914, "lon": -38.4522},
    "redenção": {"lat": -7.0264, "lon": -50.0264},
    "milão": {"lat": 45.4642, "lon": 9.1900},
    "joinville": {"lat": -26.3044, "lon": -48.8456},
    "petrópolis": {"lat": -22.5111, "lon": -43.1778},
    "são josé": {"lat": -27.6144, "lon": -48.6231},
    "maracanaú": {"lat": -3.8767, "lon": -38.6253},
    "porto velho": {"lat": -8.7619, "lon": -63.9039}
    "araçuaí": {"lat": -16°51'00", "lon": -42°04'12"}
}

# Dicionário de conversão e padronização de estados (UFs)
# Coordenadas geográficas centrais para os estados da lista (formato minúsculo)
coordenadas_estados = {
    "pb": [-7.1198, -36.5000],  # Paraíba
    "pt": [39.3999, -8.2245],   # Portugal (PT)
    "rs": [-30.0000, -53.5000], # Rio Grande do Sul
    "pr": [-24.5000, -51.5000], # Paraná
    "pe": [-8.2833, -35.0730],  # Pernambuco
    "sp": [-23.5500, -46.6333], # São Paulo
    "sc": [-27.2500, -50.5000], # Santa Catarina
    "am": [-3.1190, -60.0217],  # Amazonas
    "df": [-15.7942, -47.8822], # Distrito Federal
    "mg": [-18.5122, -44.5550], # Minas Gerais
    "ba": [-12.5000, -41.5000], # Bahia
    "rj": [-22.9068, -43.1729], # Rio de Janeiro
    "ce": [-5.0000, -39.5000],  # Ceará
    "go": [-15.8270, -49.8362], # Goiás
    "rn": [-5.7950, -36.5000],  # Rio Grande do Norte
    "pi": [-7.7183, -42.7289],  # Piauí
    "al": [-9.5713, -36.7820],  # Alagoas
    "pa": [-5.5300, -52.2900],  # Pará
    "es": [-19.7500, -40.5000], # Espírito Santo
    "ma": [-4.9609, -45.2744],  # Maranhão
    "to": [-10.1838, -48.3336], # Tocantins
    "se": [-10.5740, -37.3857], # Sergipe
    "ro": [-11.5000, -63.0000], # Rondônia
    "it": [41.8719, 12.5674]    # Itália (IT)
}

# 3. Função de busca Tolerante a Falhas de Digitação
def buscar_coordenadas(nome_entrada: str):
    """ Remove siglas, espaços extras e busca a cidade de forma segura """
    if not nome_entrada:
        return None
    
    # Remove eventuais siglas (ex: "Santos, SP" vira apenas "santos")
    nome_limpo = nome_entrada.split(",")[0].strip().lower()
    
    # Faz a busca direta no dicionário de cidades
    return coordenadas_cidades.get(nome_limpo, None)


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
                
                # --- 📊 SEÇÃO DA TABELA (OBRIGATÓRIA): Sempre aparece na tela ---
                st.markdown("---")
                st.markdown(f"### 📋 Dados Completos dos Membros Localizados em **{cidade_selecionada}**")
                st.markdown("A tabela abaixo mostra todas as informações originais da sua planilha para esta localidade.")
                
                st.dataframe(
                    membros_da_cidade, 
                    use_container_width=True, 
                    hide_index=True
                )
                st.markdown("---")
                
                # --- 🗺️ SEÇÃO DO MAPA (INDEPENDENTE): Se falhar, não esconde a tabela ---
                cep_referencia = ""
                for _, row in membros_da_cidade.iterrows():
                    if "Cep" in df.columns and str(row["Cep"]).strip().isdigit() and len(str(row["Cep"]).strip()) == 8:
                        cep_referencia = str(row["Cep"]).strip()
                        break
                        
                latitude_descoberta, longitude_descoberta = None, None
                cidade_busca_chave = cidade_selecionada.lower().strip()
                
                if cidade_busca_chave in coordenadas_cidades:
                    coords_contingencia = coordenadas_cidades[cidade_busca_chave]
                    latitude_descoberta = float(coords_contingencia["lat"])
                    longitude_descoberta = float(coords_contingencia["lon"])
                
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
                            latitude_descoberta = float(req_osm["lat"])
                            longitude_descoberta = float(req_osm["lon"])
                    except: pass
                
                # Renderiza o mapa apenas se as coordenadas forem válidas, sem travar o app
                if latitude_descoberta is not None and longitude_descoberta is not None:
                    st.markdown("#### 🗺️ Localização Geográfica")
                    tamanho_circulo = int(total_membros) * 45
                    df_ponto_mapa = pd.DataFrame([{
                        "latitude": latitude_descoberta,
                        "longitude": longitude_descoberta,
                        "size": tamanho_circulo
                    }])
                    st.map(df_ponto_mapa, size="size", color="#0056b3")
                else:
                    st.info(f"ℹ️ Nota: O mapa não pôde ser renderizado para {cidade_selecionada} devido à ausência de coordenadas de GPS, mas os dados nominais acima estão preservados.")
                    
            else: st.warning("⚠️ Nenhum município válido localizado na coluna.")
        else: st.warning("⚠️ A coluna 'Município' não foi localizada.")

          # --- ABA 5: MAPA POR ESTADO ---
    elif menu == "🗺️ Mapa por Estado":
        st.title("🗺️ Concentração Geo-Comunitária por Estado (UF)")
        st.markdown("Visualização macro mostrando o volume de membros por Estado do Brasil.")
        lista_mapa_estado = []
        
        # Dicionário de tradução local
        tradutor_uf_local = {
            "ac": "ac", "al": "al", "ap": "ap", "am": "am", "ba": "ba", "ce": "ce",
            "df": "df", "es": "es", "go": "go", "ma": "ma", "mt": "mt", "ms": "ms",
            "mg": "mg", "pa": "pa", "pb": "pb", "pr": "pr", "pe": "pe", "pi": "pi",
            "rj": "rj", "rn": "rn", "rs": "rs", "ro": "ro", "rr": "rr", "sc": "sc",
            "sp": "sp", "se": "se", "to": "to", "pt": "pt", "it": "it"
        }
        
        if not df.empty and "UF" in df.columns:
            somas_estados = {}
            for _, row in df.iterrows():
                uf_crua = str(row["UF"]).strip().lower().replace("í", "i").replace("ã", "a") if row["UF"] else ""
                if not uf_crua or uf_crua == "nan":
                    continue
                
                uf_oficial = tradutor_uf_local.get(uf_crua, uf_crua)
                if uf_oficial in coordenadas_estados:
                    somas_estados[uf_oficial] = somas_estados.get(uf_oficial, 0) + 1
            
            for uf_chave, total in somas_estados.items():
                coords = coordenadas_estados[uf_chave]
                # CORREÇÃO CRUCIAL: Acessando o índice [0] para lat e [1] para lon
                lista_mapa_estado.append({
                    "latitude": float(coords[0]), 
                    "longitude": float(coords[1]), 
                    "uf_sigla": uf_chave.upper(), 
                    "quantidade": int(total), 
                    "size": int(total) * 150
                })
        
        if len(lista_mapa_estado) > 0:
            df_mapa_estado = pd.DataFrame(lista_mapa_estado)
            st.metric("🗺️ Estados Computados no Brasil + Portugal + Itália", len(df_mapa_estado))
            st.map(df_mapa_estado, size="size", color="#d32f2f")
            st.markdown("### 📊 Densidade Real Consolidada por Estado (UF) + Portugal + Itália:")
            for item in lista_mapa_estado: 
                st.write(f"• **{item['uf_sigla']}:** {item['quantidade']} membro(s) localizado(s).")
        else:
            st.warning("⚠️ Nenhum estado cadastrado foi localizado.")

# --- RODAPÉ DISCRETO PADRONIZADO ---
st.markdown("---")
st.markdown("<p style='text-align:right; font-size:12px; color:gray;'>Bartolomeu Lima - Corecon-ES 1541</p>", unsafe_allow_html=True)
