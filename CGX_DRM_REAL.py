import streamlit as st
import pandas as pd

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(layout="wide", page_title="Painel COGEX", page_icon="⚖️")

# ==================== LOGIN BÁSICO ====================
USUARIOS = {"COGEX": "X"}
with st.sidebar:
    st.title("🔐 Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if usuario not in USUARIOS or USUARIOS[usuario] != senha:
        st.warning("Acesso restrito. Digite usuário e senha.")
        st.stop()

# ==================== ESTILO PERSONALIZADO ====================
st.markdown('''
<style>
body {
    background-image: url("https://i.imgur.com/6fztjPp.png");
    background-size: cover;
    background-position: center;
}
h1, h2, h3 {
    color: #7B1E3B;
}
div[data-testid="metric-container"] {
    background-color: #f5f5f5;
    border-radius: 0.5rem;
    padding: 10px;
}
</style>
''', unsafe_allow_html=True)

# ==================== CABEÇALHO ====================
st.markdown("## ⚖️ Painel de Prestação de Contas DRM - COGEX")
st.markdown("Análise de conformidade cartorial baseada em dados oficiais")

# ==================== LEITURA DO CSV ONLINE ====================
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQFkt94_9-JFD7JitT28Yqe_S0awybvb9qneZ7XqMG925w-XZ1ITSYocQk7nE8J-rgiC7rvsNl0MWVZ/pub?gid=1686411433&single=true&output=csv"

@st.cache_data
def carregar_dados(url):
    df = pd.read_csv(url)
    df = df.dropna(how='all', axis=1)
    df = df.dropna(subset=['Ano', 'Mês', 'DATA_DO_RECOLHIMENTO'], how='any')
    df['Ano'] = df['Ano'].astype(str).str.extract(r'(\\d{4})').astype(int)
    df['Mês'] = df['Mês'].fillna('01').astype(str).str.zfill(2)
    df['DATA_DO_RECOLHIMENTO'] = pd.to_datetime(df['DATA_DO_RECOLHIMENTO'], errors='coerce')
    df['data_referencia'] = pd.to_datetime(df['Ano'].astype(str) + '-' + df['Mês']) + pd.offsets.MonthEnd(0)
    df['prazo_envio_dias'] = (df['DATA_DO_RECOLHIMENTO'] - df['data_referencia']).dt.days
    df['conforme'] = df['prazo_envio_dias'] <= 10
    df['status_envio'] = df['conforme'].map({True: 'OK', False: 'FALHO'})
    return df

df = carregar_dados(csv_url)

# ==================== EXTRAÇÃO DE MUNICÍPIO E ANO DO ARQUIVO ====================
def extrair_municipio_ano(arquivo):
    if isinstance(arquivo, str):
        partes = arquivo.replace("-", " ").replace("_", " ").split()
        municipio = next((p for p in partes if p.isalpha() and len(p) > 3), "DESCONHECIDO")
        ano = next((p for p in partes if p.isdigit() and len(p) == 4), "0000")
        return municipio.upper(), ano
    return "DESCONHECIDO", "0000"

df[['municipio_extraido', 'ano_extraido']] = df['Arquivo'].apply(lambda x: pd.Series(extrair_municipio_ano(x)))

# ==================== FILTROS ====================
st.sidebar.markdown("## 🎯 Filtros")
ano = st.sidebar.selectbox("Ano", sorted(df['Ano'].unique()))
status = st.sidebar.selectbox("Status", ['Todos', 'OK', 'FALHO'])
municipios = ['Todos'] + sorted(df['municipio_extraido'].dropna().unique())
municipio = st.sidebar.selectbox("Município", municipios)

dados = df[df['Ano'] == ano]
if status != 'Todos':
    dados = dados[dados['status_envio'] == status]
if municipio != 'Todos':
    dados = dados[dados['municipio_extraido'] == municipio]

# ==================== KPIs ====================
col1, col2, col3 = st.columns([1, 1, 1.618])  # proporção áurea
col1.metric("📂 Registros", len(dados))
col2.metric("📈 Prazo Médio", f"{round(dados['prazo_envio_dias'].mean(), 2)} dias")
col3.metric("✅ % Conformidade", f"{round((dados['conforme'].sum()/len(dados))*100, 2)}%")

# ==================== TABELA ====================
st.markdown("### 📋 Tabela de Dados")
st.dataframe(dados[['municipio_extraido', 'Ano', 'Mês', 'prazo_envio_dias', 'status_envio']], use_container_width=True)

# ==================== GRÁFICOS ====================
st.markdown("### 📊 Gráficos")

if 'TOTAL_DA_RECEITA_BRUTA' in dados.columns:
    st.bar_chart(dados.groupby('municipio_extraido')['TOTAL_DA_RECEITA_BRUTA'].sum())

st.bar_chart(dados['status_envio'].value_counts())
