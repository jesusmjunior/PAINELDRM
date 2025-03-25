import streamlit as st
import pandas as pd

# ========== CONFIG STREAMLIT ==========
st.set_page_config(layout="wide", page_title="Painel COGEX DRM", page_icon="⚖️")

# ========== LOGIN ==========
USUARIOS = {"COGEX": "X"}
with st.sidebar:
    st.title("🔐 Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if usuario not in USUARIOS or USUARIOS[usuario] != senha:
        st.warning("Acesso negado. Informe credenciais válidas.")
        st.stop()

# ========== TÍTULO ==========
st.title("⚖️ Painel COGEX - Prestação de Contas DRM")
st.markdown("Visualização simplificada de conformidade cartorial baseada nos dados enviados.")

# ========== CARREGAMENTO DINÂMICO (.CSV ou .XLSX) ==========
arquivo = st.file_uploader("📁 Envie a base DRM (.xlsx ou .csv)", type=["xlsx", "csv"])

if arquivo:
    if arquivo.name.endswith(".csv"):
        df = pd.read_csv(arquivo)
    else:
        df = pd.read_excel(arquivo)

    # Padronizar colunas
    df.columns = df.columns.str.strip().str.upper().str.replace(" ", "_").str.replace("Ç", "C")

    # Mapear nomes possíveis
    col_ano = next((c for c in df.columns if "ANO" in c), None)
    col_mes = next((c for c in df.columns if "MES" in c), None)
    col_data = next((c for c in df.columns if "RECOLHIMENTO" in c), None)
    col_arquivo = next((c for c in df.columns if "ARQUIVO" in c), None)

    if not all([col_ano, col_mes, col_data]):
        st.error("❌ Colunas essenciais ausentes: Ano, Mês ou Data do Recolhimento.")
        st.stop()

    # Normalização
    df['ANO'] = df[col_ano].astype(str).str.extract(r'(\\d{4})').astype(int)
    df['MES'] = df[col_mes].fillna('01').astype(str).str.zfill(2)
    df['DATA_RECOLHIMENTO'] = pd.to_datetime(df[col_data], errors='coerce')
    df['DATA_REFERENCIA'] = pd.to_datetime(df['ANO'].astype(str) + '-' + df['MES']) + pd.offsets.MonthEnd(0)
    df['ATRASO_DIAS'] = (df['DATA_RECOLHIMENTO'] - df['DATA_REFERENCIA']).dt.days
    df['CONFORME'] = df['ATRASO_DIAS'] <= 10
    df['STATUS_ENVIO'] = df['CONFORME'].map({True: 'OK', False: 'FALHO'})

    # Sanitização do campo Arquivo para extrair município/ano
    def extrair_municipio_ano(valor):
        if isinstance(valor, str):
            partes = valor.replace("-", " ").replace("_", " ").split()
            municipio = next((p for p in partes if p.isalpha() and len(p) > 3), "DESCONHECIDO")
            ano = next((p for p in partes if p.isdigit() and len(p) == 4), "0000")
            return municipio.upper(), ano
        return "DESCONHECIDO", "0000"

    if col_arquivo:
        df[['MUNICIPIO_EXTRAIDO', 'ANO_EXTRAIDO']] = df[col_arquivo].apply(lambda x: pd.Series(extrair_municipio_ano(x)))
    else:
        df['MUNICIPIO_EXTRAIDO'] = "NÃO IDENTIFICADO"
        df['ANO_EXTRAIDO'] = df['ANO'].astype(str)

    # ========== FILTROS ==========
    st.sidebar.markdown("## 🎯 Filtros")
    ano = st.sidebar.selectbox("Ano", sorted(df['ANO'].unique()))
    status = st.sidebar.selectbox("Status Envio", ['Todos', 'OK', 'FALHO'])
    municipios = ['Todos'] + sorted(df['MUNICIPIO_EXTRAIDO'].dropna().unique())
    municipio = st.sidebar.selectbox("Município (Extraído)", municipios)

    dados = df[df['ANO'] == ano]
    if status != 'Todos':
        dados = dados[dados['STATUS_ENVIO'] == status]
    if municipio != 'Todos':
        dados = dados[dados['MUNICIPIO_EXTRAIDO'] == municipio]

    # ========== KPIs ==========
    col1, col2, col3 = st.columns([1, 1, 1.618])
    col1.metric("📂 Registros", len(dados))
    col2.metric("📈 Prazo Médio", f"{round(dados['ATRASO_DIAS'].mean(), 2)} dias")
    col3.metric("✅ % Conformidade", f"{round((dados['CONFORME'].sum()/len(dados))*100, 2)}%")

    # ========== TABELA ==========
    st.markdown("### 📋 Tabela de Dados Filtrados")
    st.dataframe(dados[['MUNICIPIO_EXTRAIDO', 'ANO', 'MES', 'DATA_RECOLHIMENTO', 'ATRASO_DIAS', 'STATUS_ENVIO']], use_container_width=True)

    # ========== GRÁFICOS ==========
    st.markdown("### 📊 Gráficos")
    st.bar_chart(dados['STATUS_ENVIO'].value_counts())

else:
    st.info("⚠️ Envie uma planilha para começar.")


# Salvar versão final
