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
# --- ABA 2: COLETA ONLINE E ATUALIZAÇÃO VIA FORMULÁRIO ---
elif menu == "📝 Cadastrar Novo" or menu == "📝 Atualizar / Cadastrar Dados":
    st.title("📝 Atualização Cadastral dos Secretários")
    st.markdown("Selecione o seu município para carregar os dados atuais e preencha as atualizações abaixo.")

    municipios_cad = sorted(df["Municipio"].dropna().unique())
    muni_sel = st.selectbox("Selecione o seu município para atualizar:", municipios_cad, key="muni_cad")

    if muni_sel:
        # Filtra o registro existente na tabela para servir de base
        res_cad = df[df["Municipio"].str.lower().str.strip() == muni_sel.lower().strip()]
        idx_cad = res_cad.index[0] if not res_cad.empty else None

        # Criação do formulário estruturado de captação
        with st.form("form_cadastro"):
            col_esq, col_dir = st.columns(2)
            
            with col_esq:
                novo_sec = st.text_input("Nome do Secretário:", value=str(df.loc[idx_cad, "Secretario"]) if idx_cad is not None and pd.notna(df.loc[idx_cad, "Secretario"]) else "")
                novo_email = st.text_input("E-mail Pessoal:", value=str(df.loc[idx_cad, "Email"]) if idx_cad is not None and pd.notna(df.loc[idx_cad, "Email"]) else "")
                novo_email_inst = st.text_input("E-mail Institucional:", value=str(df.loc[idx_cad, "Email Institucional"]) if idx_cad is not None and pd.notna(df.loc[idx_cad, "Email Institucional"]) else "")
                novo_tel = st.text_input("Telefone Celular:", value=str(df.loc[idx_cad, "Telefone"]) if idx_cad is not None and pd.notna(df.loc[idx_cad, "Telefone"]) else "")
                novo_tel_inst = st.text_input("Telefone Institucional:", value=str(df.loc[idx_cad, "Telefone Institucional"]) if idx_cad is not None and pd.notna(df.loc[idx_cad, "Telefone Institucional"]) else "")

            with col_dir:
                # 💡 O Pulo do Gato: Sistema de captação inteligente de Endereço por CEP
                cep_input = st.text_input("Digite o CEP da Secretaria (Apenas números):", max_chars=8)
                logradouro_auto = ""
                bairro_auto = ""
                localidade_auto = ""
                uf_auto = ""

                # Consulta automática à API ViaCEP se o usuário digitar os 8 dígitos
                if cep_input.strip().isdigit() and len(cep_input.strip()) == 8:
                    try:
                        requisicao = requests.get(f"https://viacep.com.br{cep_input.strip()}/json/")
                        dados_cep = requisicao.json()
                        if "erro" not in dados_cep:
                            logradouro_auto = dados_cep.get("logradouro", "")
                            bairro_auto = dados_cep.get("bairro", "")
                            localidade_auto = dados_cep.get("localidade", "")
                            uf_auto = dados_cep.get("uf", "")
                            st.caption(f"📍 Endereço Encontrado: {logradouro_auto}, {bairro_auto} - {localidade_auto}/{uf_auto}")
                        else:
                            st.caption("⚠️ CEP não localizado na base postal nacional.")
                    except:
                        st.caption("⚠️ Falha temporária ao conectar com o serviço de CEP.")

                # Campos de endereço preenchidos dinamicamente pela busca do CEP
                rua = st.text_input("Logradouro (Rua/Av/Praça):", value=logradouro_auto if logradouro_auto else "")
                numero_semus = st.text_input("Número do prédio da Secretaria:")
                bairro = st.text_input("Bairro:", value=bairro_auto if bairro_auto else "")
                
                # Monta a string completa de endereço padronizada para o seu Excel
                texto_endereco_final = f"{rua}, nº {numero_semus} - {bairro}" if rua else ""
                
                novo_fundo = st.text_input("Fundo de Saúde:", value=str(df.loc[idx_cad, "Fundo de Saúde"]) if idx_cad is not None and pd.notna(df.loc[idx_cad, "Fundo de Saúde"]) else "")
                novo_cnpj = st.text_input("CNPJ da Secretaria:", value=str(df.loc[idx_cad, "CNPJ"]) if idx_cad is not None and pd.notna(df.loc[idx_cad, "CNPJ"]) else "")
                novo_regiao = st.text_input("Região de Saúde (CIR):", value=str(df.loc[idx_cad, "Região de Saúde"]) if idx_cad is not None and pd.notna(df.loc[idx_cad, "Região de Saúde"]) else "")

            # Botão de envio disparado de dentro do formulário
            botao_salvar = st.form_submit_button("💾 Confirmar e Salvar Alterações", use_container_width=True)
            
            if botao_salvar:
                if idx_cad is not None:
                    # Atualiza os dados na linha correspondente do DataFrame em memória
                    df.loc[idx_cad, "Secretario"] = novo_sec
                    df.loc[idx_cad, "Email"] = novo_email
                    df.loc[idx_cad, "Email Institucional"] = novo_email_inst
                    df.loc[idx_cad, "Telefone"] = novo_tel
                    df.loc[idx_cad, "Telefone Institucional"] = novo_tel_inst
                    df.loc[idx_cad, "Fundo de Saúde"] = novo_fundo
                    df.loc[idx_cad, "CNPJ"] = novo_cnpj
                    df.loc[idx_cad, "Região de Saúde"] = novo_regiao
                    
                    # Salva o novo endereço apenas se a pessoa preencheu os campos do CEP
                    if texto_endereco_final:
                        df.loc[idx_cad, "Endereço da SEMUS"] = texto_endereco_final
                    
                    # Sobrescreve o arquivo CSV original de forma automática e transparente
                    df.to_csv("secretarios_cosems_pb.csv", sep=";", index=False, encoding="utf-8-sig")
                    st.success(f"🎉 Dados do município de {muni_sel} atualizados com sucesso na base de dados!")
                    st.balloons()
                else:
                    st.error("Erro interno: Falha ao mapear a linha do município selecionado.")

# --- RODAPÉ DISCRETO PADRONIZADO ---
st.markdown("---")
st.markdown(
    "<p style='text-align:right; font-size:12px; color:green;'>Bartolomeu Lima - Corecon-ES 1541</p>",
    unsafe_allow_html=True
)

# Link de retorno integrado
st.markdown("[⬅️ Voltar ao Menu](https://menu1app.streamlit.app/)")
