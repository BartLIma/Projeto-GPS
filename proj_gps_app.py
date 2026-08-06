import pandas as pd
import streamlit as st
import requests
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

# Inicializa variáveis de controle de estado para matar o loop infinito da busca
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
    
    # Carregamento seguro da base 'projeto_gps.csv'
    try:
        df = pd.read_csv(
            "projeto_gps.csv",
            sep=";",   
            encoding="utf-8-sig",
            dtype=str,
            skip_blank_lines=True
        )
    except Exception:
        df = pd.read_csv(
            "projeto_gps.csv",
            sep=",",   
            encoding="utf-8-sig",
            dtype=str,
            skip_blank_lines=True
        )
        
    df.columns = df.columns.str.strip().str.replace('﻿', '')
    df = df.dropna(how="all")

    # Garante as colunas vitais
    for col_vital in ["Nome Completo", "Nome Judaico", "Município"]:
        if col_vital not in df.columns:
            df[col_vital] = ""

    df["Nome Completo"] = df["Nome Completo"].astype(str).str.strip()
    df["Nome Judaico"] = df["Nome Judaico"].astype(str).str.strip()

    # --- CONSTRUÇÃO DO MENU LATERAL ---
    st.sidebar.header("Painel de Controle GPS")
    menu = st.sidebar.radio(
        "Selecione a Ação:",
        ["🔍 Consultar por Nome", "📝 Cadastrar / Atualizar Endereços"]
    )
    st.sidebar.markdown("---")

    # --- ABA 1: CONSULTA DO BANCO DE DADOS POR NOME ---
    if menu == "🔍 Consultar por Nome":
        st.title("🔍 Consulta de Membros da Comunidade")
        
        # Caixa de texto de busca
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
                    
                    label_visual = f"{nome_civil}{nome_hud}{muni_ref}"
                    opcoes_pessoas[label_visual] = idx
                
                pessoa_sel = st.selectbox("Selecione a pessoa para abrir a ficha:", sorted(opcoes_pessoas.keys()))
                
                # Armazena a escolha de forma fixa na sessão para blindar contra o re-run
                if pessoa_sel and opcoes_pessoas[pessoa_sel] is not None:
                    st.session_state["indice_pessoa_consultada"] = opcoes_pessoas[pessoa_sel]
            else:
                st.session_state["indice_pessoa_consultada"] = None
                st.warning("Nenhuma pessoa foi localizada com esse nome na base de dados.")
        else:
            st.session_state["indice_pessoa_consultada"] = None
            st.info("💡 Por favor, digite o nome de alguém acima para realizar a consulta cadastral.")

        # Exibe a Ficha de Dados fixa se houver uma pessoa selecionada na memória da sessão
        if st.session_state["indice_pessoa_consultada"] is not None:
            p_idx = st.session_state["indice_pessoa_consultada"]
            st.markdown("---")
            st.subheader(f"👤 Ficha Cadastral — {df.loc[p_idx, 'Nome Completo']}")
            
            # Divide a exibição das informações em duas colunas para melhor aproveitamento visual
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
            
            st.info(f"📍 **Endereço Completo:** {df.loc[p_idx, 'Endereço Completo'] if pd.notna(df.loc[p_idx, 'Endereço Completo']) and str(df.loc[p_idx, 'Endereço Completo']).lower() != 'nan' else 'Não preenchido'}")
    # --- ABA 2: FORMULÁRIO ONLINE DE CAPTAÇÃO E ATUALIZAÇÃO POR NOME (LGPD) ---
    elif menu == "📝 Cadastrar / Atualizar Endereços":
        st.title("📝 Formulário de Posicionamento e Identidade Sefardita")
        st.markdown("Selecione o seu nome para atualizar o seu endereço ou preencher suas informações de afinidade comunitária.")

        df_validos = df[df["Nome Completo"].str.lower() != "nan"]
        df_validos = df_validos[df_validos["Nome Completo"].str.strip() != ""]
        nomes_cadastrados = sorted(df_validos["Nome Completo"].unique())
        
        nome_alvo = st.selectbox("Selecione o seu Nome Completo para atualizar:", nomes_cadastrados, key="nome_cadastro")
        
        if nome_alvo:
            res_cad = df[df["Nome Completo"].str.lower() == nome_alvo.lower().strip()]
            idx_cad = res_cad.index if not res_cad.empty else None

            with st.form("form_gps_cadastro"):
                col_esq, col_dir = st.columns(2)
                
                with col_esq:
                    st.markdown("### 👤 Informações de Contato e Identidade")
                    v_municipio = str(df.loc[idx_cad, "Município"].values[0]).strip() if idx_cad is not None and "Município" in df.columns and pd.notna(df.loc[idx_cad, "Município"].values[0]) else ""
                    v_email = str(df.loc[idx_cad, "Email"].values[0]).strip() if idx_cad is not None and "Email" in df.columns and pd.notna(df.loc[idx_cad, "Email"].values[0]) else ""
                    v_nome_jud = str(df.loc[idx_cad, "Nome Judaico"].values[0]).strip() if idx_cad is not None and "Nome Judaico" in df.columns and pd.notna(df.loc[idx_cad, "Nome Judaico"].values[0]) else ""
                    v_tel = str(df.loc[idx_cad, "Telefone"].values[0]).strip() if idx_cad is not None and "Telefone" in df.columns and pd.notna(df.loc[idx_cad, "Telefone"].values[0]) else ""
                    
                    municipio_input = st.text_input("Município de Residência:", value=v_municipio if v_municipio.lower() != 'nan' else "")
                    email_contato = st.text_input("E-mail de Contato:", value=v_email if v_email.lower() != 'nan' else "")
                    nome_judaico = st.text_input("Nome Judaico / Hebraico (Se houver):", value=v_nome_jud if v_nome_jud.lower() != 'nan' else "")
                    tel_contato = st.text_input("Telefone / WhatsApp (Com DDD):", value=v_tel if v_tel.lower() != 'nan' else "")

                    st.markdown("---")
                    st.markdown("### 📜 Identidade e Afinidade Cultural")
                    
                    v_perfil = str(df.loc[idx_cad, "Perfil Identidade"].values[0]).strip() if idx_cad is not None and "Perfil Identidade" in df.columns and pd.notna(df.loc[idx_cad, "Perfil Identidade"].values[0]) else "Simpatizante"
                    lista_perfis = ["Judeu", "Bnei Anussim", "Simpatizante"]
                    idx_perfil_padrao = lista_perfis.index(v_perfil) if v_perfil in lista_perfis else 2
                    
                    perfil_identidade = st.selectbox("Como você se identifica em relação ao Judaísmo?", lista_perfis, index=idx_perfil_padrao)
                    
                    v_vinculo = str(df.loc[idx_cad, "Vinculação Comunitária"].values[0]).strip() if idx_cad is not None and "Vinculação Comunitária" in df.columns and pd.notna(df.loc[idx_cad, "Vinculação Comunitária"].values[0]) else "Isolado (Sem comunidade)"
                    vinculo_comunidade = st.text_input("Participa de alguma Comunidade/Sinagoga/Núcleo? (Se não, digite Isolado):", value=v_vinculo if v_vinculo.lower() != 'nan' else "Isolado (Sem comunidade)")

                with col_dir:
                    st.markdown("### 🏢 Localização Geográfica")
                    v_cep_antigo = str(df.loc[idx_cad, "Cep"].values[0]).strip() if idx_cad is not None and "Cep" in df.columns and pd.notna(df.loc[idx_cad, "Cep"].values[0]) else ""
                    cep_input = st.text_input("Digite o CEP residencial (Apenas 8 números):", value=v_cep_antigo if v_cep_antigo.lower() != 'nan' else "", max_chars=8)
                    
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
                    bairro = st.text_input("Bairro:", value=bairro_final if bairro_final.lower() != 'nan' else "")
                    
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
                        
                        # Atualiza as variáveis usando atribuição indexada estável (.at)
                        df.at[idx_cad, "Município"] = municipio_input
                        df.at[idx_cad, "Email"] = email_contato
                        df.at[idx_cad, "Nome Judaico"] = nome_judaico
                        df.at[idx_cad, "Telefone"] = tel_contato
                        df.at[idx_cad, "Perfil Identidade"] = perfil_identidade
                        df.at[idx_cad, "Vinculação Comunitária"] = vinculo_comunidade
                        df.at[idx_cad, "Cep"] = cep_input
                        df.at[idx_cad, "Bairro"] = bairro
                        
                        if endereco_gerado:
                            df.at[idx_cad, "Endereço Completo"] = endereco_gerado
                        
                        ordem_final_colunas = ["Município"] + lista_colunas_obrigatorias
                        df = df[ordem_final_colunas]
                        
                        df.to_csv("projeto_gps.csv", sep=";", index=False, encoding="utf-8-sig")
                        st.success(f"🎉 Cadastro de {nome_alvo} atualizado com sucesso em conformidade com a LGPD!")
                        st.balloons()
                    else:
                        st.error("Erro operacional: Linha de registro inválida no CSV.")

# --- RODAPÉ DISCRETO PADRONIZADO ---
st.markdown("---")
st.markdown("<p style='text-align:right; font-size:12px; color:gray;'>Bartolomeu Lima - Corecon-ES 1541</p>", unsafe_allow_html=True)
