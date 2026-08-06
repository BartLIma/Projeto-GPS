import pandas as pd
import streamlit as st
import requests

st.set_page_config(layout="wide")

# --- TRUQUE CSS: Otimiza o espaço em branco do topo da tela ---
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

# Carregar a planilha CSV (separador ponto e vírgula)
df = pd.read_csv(
    "secretarios_cosems_pb.csv",
    sep=";", 
    encoding="utf-8-sig",
    on_bad_lines="skip",
    header=0
)
df.columns = df.columns.str.strip()

# --- CONSTRUÇÃO DO MENU LATERAL ---
st.sidebar.title("🎛️ Painel de Controle")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Selecione a Ação:",
    ["🔍 Consultar Secretário", "📝 Atualizar / Cadastrar Dados"]
)

# --- ABA 1: CONSULTA DE SECRETÁRIOS (Seu código original preservado e otimizado) ---
if menu == "🔍 Consultar Secretário":
    st.title("Consulta Secretários de Saúde - Paraíba")

    municipios = sorted(df["Municipio"].dropna().unique())
    municipio = st.selectbox("Selecione o município:", municipios)

    if municipio:
        resultado = df[df["Municipio"].str.lower().str.strip() == municipio.lower().strip()]
        
        if not resultado.empty:
            idx = resultado.index[0]
            secretario = df.loc[idx, "Secretario"]
            email = df.loc[idx, "Email"]
            email_inst = df.loc[idx, "Email Institucional"]
            telefone = df.loc[idx, "Telefone"]
            telefone_inst = df.loc[idx, "Telefone Institucional"]
            endereco = df.loc[idx, "Endereço da SEMUS"]
            fundo_saude = df.loc[idx, "Fundo de Saúde"]
            cnpj = df.loc[idx, "CNPJ"]
            regiao = df.loc[idx, "Região de Saúde"]
            
            telefones = f"{telefone} / {telefone_inst}" if pd.notna(telefone) or pd.notna(telefone_inst) else ""
            
            st.subheader(f"Município: {municipio}")
            st.write(f"**Secretário:** {secretario if pd.notna(secretario) else ''}")
            st.write(f"**E-mail:** {email if pd.notna(email) else ''}")
            st.write(f"**E-mail Institucional:** {email_inst if pd.notna(email_inst) else ''}")
            st.write(f"**Telefones:** {telefones}")
            st.write(f"**Endereço da Secretaria de Saúde:** {endereco if pd.notna(endereco) else ''}")
            st.write(f"**Fundo de Saúde:** {fundo_saude if pd.notna(fundo_saude) else ''}")
            st.write(f"**CNPJ:** {cnpj if pd.notna(cnpj) else ''}")
            st.write(f"**Região de Saúde (CIR):** {regiao if pd.notna(regiao) else ''}")
        else:
            st.warning("Município não encontrado na base de dados.")
    # --- ABA 2: FORMULÁRIO ONLINE DE CAPTAÇÃO ADAPTADO À LGPD ---
    elif menu == "📝 Cadastrar / Atualizar Endereços":
        st.title("📝 Formulário de Posicionamento e Identidade Sefardita")
        st.markdown("Preencha os campos abaixo de forma consciente. Os dados coletados estão protegidos sob as diretrizes da LGPD.")

        if "Município" in df.columns:
            municipios_cad = sorted(df["Município"].dropna().unique())
            muni_cad_sel = st.selectbox("Selecione o município de residência:", municipios_cad, key="muni_cadastro")
            
            if muni_cad_sel:
                res_cad = df[df["Município"].astype(str).str.lower().str.strip() == str(muni_cad_sel).lower().strip()]
                idx_cad = res_cad.index if not res_cad.empty else None

                with st.form("form_gps_cadastro"):
                    col_esq, col_dir = st.columns(2)
                    
                    with col_esq:
                        st.markdown("### 👤 Informações de Contato")
                        v_responsavel = str(df.loc[idx_cad, "Nome Completo"].values).strip() if idx_cad is not None and "Nome Completo" in df.columns and pd.notna(df.loc[idx_cad, "Nome Completo"].values) else ""
                        v_email = str(df.loc[idx_cad, "Email"].values).strip() if idx_cad is not None and "Email" in df.columns and pd.notna(df.loc[idx_cad, "Email"].values) else ""
                        v_tel = str(df.loc[idx_cad, "Telefone"].values).strip() if idx_cad is not None and "Telefone" in df.columns and pd.notna(df.loc[idx_cad, "Telefone"].values) else ""
                        
                        nome_resp = st.text_input("Nome Completo:", value=v_responsavel)
                        email_contato = st.text_input("E-mail de Contato:", value=v_email)
                        tel_contato = st.text_input("Telefone / WhatsApp (Com DDD):", value=v_tel)

                        st.markdown("---")
                        st.markdown("### 📜 Identidade e Afinidade Cultural")
                        
                        # 🌟 CAMPOS SOLICITADOS: Judeu, Bnei Anussim ou Simpatizante 🌟
                        v_perfil = str(df.loc[idx_cad, "Perfil Identidade"].values).strip() if idx_cad is not None and "Perfil Identidade" in df.columns and pd.notna(df.loc[idx_cad, "Perfil Identidade"].values) else "Simpatizante"
                        lista_perfis = ["Judeu", "Bnei Anussim", "Simpatizante"]
                        idx_perfil_padrao = lista_perfis.index(v_perfil) if v_perfil in lista_perfis else 2
                        
                        perfil_identidade = st.selectbox("Como você se identifica em relação ao Judaísmo?", lista_perfis, index=idx_perfil_padrao)
                        
                        v_vinculo = str(df.loc[idx_cad, "Vinculação Comunitária"].values).strip() if idx_cad is not None and "Vinculação Comunitária" in df.columns and pd.notna(df.loc[idx_cad, "Vinculação Comunitária"].values) else "Isolado (Sem comunidade)"
                        vinculo_comunidade = st.text_input("Participa de alguma Comunidade/Sinagoga/Núcleo? (Se não, digite Isolado):", value=v_vinculo)

                    with col_dir:
                        st.markdown("### 🏢 Localização Geográfica")
                        cep_input = st.text_input("Digite o CEP residencial (Apenas 8 números):", max_chars=8)
                        
                        logradouro_auto = ""
                        bairro_auto = ""
                        localidade_auto = ""
                        uf_auto = ""

                        if json_cep := (requests.get(f"https://viacep.com.br{cep_input.strip()}/json/").json() if (cep_input.strip().isdigit() and len(cep_input.strip()) == 8) else None):
                            if "erro" not in json_cep:
                                logradouro_auto, bairro_auto, localidade_auto, uf_auto = json_cep.get("logradouro", ""), json_cep.get("bairro", ""), json_cep.get("localidade", ""), json_cep.get("uf", "")
                                st.caption(f"📍 Endereço Mapeado: {logradouro_auto}, {bairro_auto} - {localidade_auto}/{uf_auto}")
                            else:
                                st.caption("⚠️ CEP não localizado na base postal.")

                        rua = st.text_input("Logradouro (Rua/Avenida):", value=logradouro_auto if logradouro_auto else "")
                        numero_predio = st.text_input("Número / Complemento / Casa:")
                        bairro = st.text_input("Bairro:", value=bairro_auto if bairro_auto else "")
                        
                        endereco_gerado = f"{rua}, nº {numero_predio} - {bairro}, CEP: {cep_input}" if rua else ""

                    # 🌟 TRAVA LEGAL DA LGPD: Caixa de consentimento obrigatória 🌟
                    st.markdown("---")
                    st.markdown("#### 🛡️ Termo de Consentimento e Privacidade (LGPD)")
                    st.caption("De acordo com a Lei nº 13.709/2018 (LGPD), informamos que os seus dados de convicção religiosa e localização serão armazenados em ambiente seguro com a finalidade exclusiva de mapeamento e integração geo-comunitária, sendo proibido o compartilhamento público de dados identificáveis.")
                    aceite_lgpd = st.checkbox("Estou ciente e dou meu consentimento livre e esclarecido para o tratamento dos meus dados pessoais sensíveis neste projeto.")

                    botao_salvar_gps = st.form_submit_button("💾 Confirmar e Salvar no Banco de Dados GPS", use_container_width=True)
                    
                    if botao_salvar_gps:
                        # Verifica se o usuário marcou a caixa da LGPD antes de salvar
                        if not aceite_lgpd:
                            st.error("❌ Gravação cancelada! Você precisa aceitar o Termo de Consentimento da LGPD para realizar o cadastro.")
                        elif idx_cad is not None:
                            # Cria colunas caso não existam no CSV
                            for col_nome in ["Nome Completo", "Email", "Telefone", "Perfil Identidade", "Vinculação Comunitária", "Endereço Completo"]:
                                if col_nome not in df.columns: df[col_nome] = ""
                            
                            # Grava os dados tratados
                            df.loc[idx_cad, "Nome Completo"] = nome_resp
                            df.loc[idx_cad, "Email"] = email_contato
                            df.loc[idx_cad, "Telefone"] = tel_contato
                            df.loc[idx_cad, "Perfil Identidade"] = perfil_identidade
                            df.loc[idx_cad, "Vinculação Comunitária"] = vinculo_comunidade
                            
                            if endereco_gerado:
                                df.loc[idx_cad, "Endereço Completo"] = endereco_gerado
                            
                            df.to_csv("cad_proj_gps.csv", sep=";", index=False, encoding="utf-8-sig")
                            st.success(f"🎉 Cadastro realizado com sucesso em conformidade com a LGPD para o município de {muni_cad_sel}!")
                            st.balloons()
                        else:
                            st.error("Erro operacional: Linha de município inválida no CSV.")
        else:
            st.error("Erro crítico: A coluna 'Município' precisa existir no arquivo cad_proj_gps.csv.")

# --- RODAPÉ DISCRETO PADRONIZADO ---
st.markdown("---")
st.markdown("<p style='text-align:right; font-size:12px; color:gray;'>Bartolomeu Lima - Corecon-ES 1541</p>", unsafe_allow_html=True)
st.markdown("[⬅️ Voltar ao Menu Principal](https://streamlit.app)")
