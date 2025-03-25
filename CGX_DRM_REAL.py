# Gerar nova versão otimizada do app.py com visual simples, foco em performance e componentes nativos do Streamlit

streamlit_simplificado_code = """
# app.py - Painel COGEX DRM (versão simples, nativa para Streamlit Cloud)

import streamlit as st
import pandas as pd

# ============ CONFIGURAÇÃO ============
st.set_page_config(layout="wide", page_title="Painel COGEX - DRM", page_icon="⚖️")

# ============ LOGIN BÁSICO ============
USUARIOS = {
    "COGEX": "X",
    "jesusmjunior2021@gmail.com": "@280360"
}

with st.sidebar:
    st.title("🔐 Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if usuario not in USUARIOS or USUARIOS[usuario] != senha:
        st.warning("Digite usuário e senha para acessar o painel.")
        st.stop()

# ============ CABEÇALHO ============
st.title("⚖️ Painel de Prestação de Contas DRM - COGEX")
st.markdown("Análise simples e objetiva dos dados de conformidade e receita das serventias extrajudiciais")

# ============ LEITURA DA BASE ONLINE ============
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQFkt94_9-JFD7JitT28Yqe_S0awybvb9qneZ7XqMG925w-XZ1ITSYocQk7nE8J-rgiC7rvsNl0MWVZ/pub?gid=1686411433&single=true&output=csv"

@st.cache_data
def carregar_dados(url):
    df = pd.read_csv(url)
    df = df.dropna(axis=1, how='all')
    df = df.dropna(subset=['Ano', 'Mês', 'DATA_DO_RECOLHIMENTO'], how='any')
    df['Ano'] = df['Ano'].astype(str).str.extract(r'(\\d{4})').astype(int)
    df['Mês'] = df['Mês'].fillna('01').astype(str).str.zfill(2)
    df['DATA_DO_RECOLHIMENTO'] = pd.to_datetime(df['DATA_DO_RECOLHIMENTO'], errors='coerce')
    df['data_referencia'] = pd.to_datetime(df['Ano'].astype(str) + '-' + df['Mês'], errors='coerce') + pd.offsets.MonthEnd(0)
    df['prazo_envio_dias'] = (df['DATA_DO_RECOLHIMENTO'] - df['data_referencia']).dt.days
    df['conforme'] = df['prazo_envio_dias'] <= 10
    df['status_envio'] = df['conforme'].map({True: 'OK', False: 'FALHO'})
    return df

df = carregar_dados(csv_url)

# ============ LIMPEZA DO CAMPO ARQUIVO ============
def extrair_municipio_ano(arquivo):
    if isinstance(arquivo, str):
        partes = arquivo.replace("-", " ").replace("_", " ").split()
        municipio = next((p for p in partes if p.isalpha() and len(p) > 3), "DESCONHECIDO")
        ano = next((p for p in partes if p.isdigit() and len(p) == 4), "0000")
        return municipio.upper(), ano
    return "DESCONHECIDO", "0000"

df[['municipio_extraido', 'ano_extraido']] = df['Arquivo'].apply(lambda x: pd.Series(extrair_municipio_ano(x)))

# ============ FILTROS ============
st.sidebar.markdown("## 🎯 Filtros")
ano = st.sidebar.selectbox("Ano", sorted(df['Ano'].unique()))
status = st.sidebar.selectbox("Status Envio", ['Todos', 'OK', 'FALHO'])
municipios = ['Todos'] + sorted(df['municipio_extraido'].dropna().unique())
municipio = st.sidebar.selectbox("Município", municipios)

dados = df[df['Ano'] == ano]
if status != 'Todos':
    dados = dados[dados['status_envio'] == status]
if municipio != 'Todos':
    dados = dados[dados['municipio_extraido'] == municipio]

# ============ MÉTRICAS ============
col1, col2, col3 = st.columns(3)
col1.metric("📂 Registros", len(dados))
col2.metric("📈 Prazo Médio (dias)", round(dados['prazo_envio_dias'].mean(), 2))
col3.metric("✅ % Conformidade", f"{round((dados['conforme'].sum()/len(dados))*100, 2)}%")

# ============ TABELA ============
st.markdown("### 📋 Tabela de Dados Filtrados")
st.dataframe(dados[['municipio_extraido', 'Ano', 'Mês', 'prazo_envio_dias', 'status_envio']], use_container_width=True)

# ============ GRÁFICOS SIMPLES ============
st.markdown("### 📊 Gráficos")

if 'TOTAL_DA_RECEITA_BRUTA' in dados.columns:
    receita = dados.groupby('municipio_extraido')['TOTAL_DA_RECEITA_BRUTA'].sum().sort_values(ascending=False)
    st.bar_chart(receita)

status_chart = dados['status_envio'].value_counts()
st.bar_chart(status_chart)
"""

# Salvar como app simples para nuvem
simple_app_path = "/mnt/data/app_streamlit_simples.py"
with open(simple_app_path, "w") as f:
    f.write(streamlit_simplificado_code)

simple_app_path
