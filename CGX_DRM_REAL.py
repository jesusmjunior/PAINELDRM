# app.py — Painel COGEX DRM com login multiusuário, layout institucional e dados CSV online

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np

# ===================== CONFIGURAÇÃO DE PÁGINA =====================
st.set_page_config(layout="wide", page_title="Painel COGEX DRM", page_icon="⚖️")

# ===================== LOGIN MULTIUSUÁRIO =====================
USUARIOS = {
    "COGEX": "X",
    "jesusmjunior2021@gmail.com": "@280360"
}

with st.sidebar:
    st.markdown("## 🔐 Login de Acesso")
    usuario = st.text_input("Usuário (e-mail ou nome)")
    senha = st.text_input("Senha", type="password")
    if usuario not in USUARIOS or USUARIOS[usuario] != senha:
        st.warning("Digite suas credenciais para acessar o painel.")
        st.stop()

# ===================== CSS PERSONALIZADO =====================
css = '''
<style>
body {
    background-image: url("https://i.imgur.com/6fztjPp.png");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}
div.block-container {
    padding-top: 2rem;
}
h1, h2, h3, h4 {
    color: #7B1E3B;
    font-family: 'Source Sans Pro', sans-serif;
}
.stSelectbox label, .stRadio label, .stNumberInput label {
    color: #F2C94C;
    font-weight: bold;
}
hr {
    border-top: 1px solid #7B1E3B;
    margin-top: 1rem;
    margin-bottom: 1rem;
}
</style>
'''
st.markdown(css, unsafe_allow_html=True)

# ===================== CABEÇALHO =====================
st.markdown("<h1 style='text-align: center;'>⚖️ Painel COGEX - DRM 2024</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #000000;'>Análise de Conformidade Cartorial com Estética Institucional</h4>", unsafe_allow_html=True)
st.markdown("---")

# ===================== LEITURA DE DADOS ONLINE =====================
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

# ===================== EXTRAÇÃO MUNICÍPIO E ANO DO CAMPO ARQUIVO =====================
def extrair_municipio_ano(valor):
    if isinstance(valor, str):
        partes = valor.replace("-", " ").replace("_", " ").split()
        municipio = next((p for p in partes if p.isalpha() and len(p) > 3), "DESCONHECIDO")
        ano = next((p for p in partes if p.isdigit() and len(p) == 4), "0000")
        return municipio.upper(), ano
    return "DESCONHECIDO", "0000"

df[['municipio_extraido', 'ano_extraido']] = df['Arquivo'].apply(lambda x: pd.Series(extrair_municipio_ano(x)))

# ===================== INTERFACE DO PAINEL =====================
col1, col2 = st.columns([1, 1.618])  # proporção phi

with col1:
    ano = st.selectbox("🗓️ Ano", sorted(df['Ano'].unique()))
    status = st.radio("📌 Status de Envio", ['Todos', 'OK', 'FALHO'])
    municipios = ['Todos'] + sorted(df['municipio_extraido'].dropna().unique())
    municipio = st.selectbox("🏛️ Município Extraído", municipios)

with col2:
    dados = df[df['Ano'] == ano]
    if municipio != 'Todos':
        dados = dados[dados['municipio_extraido'] == municipio]
    if status != 'Todos':
        dados = dados[dados['status_envio'] == status]

    st.markdown("### 📊 KPIs Institucionais")
    st.metric("📈 Prazo Médio", f"{round(dados['prazo_envio_dias'].mean(), 2)} dias")
    st.metric("✅ % Conformidade", f"{round((dados['conforme'].sum()/len(dados))*100, 2)}%")
    st.metric("📂 Registros Visíveis", len(dados))

st.markdown("---")
col3, col4 = st.columns(2)

with col3:
    if 'TOTAL_DA_RECEITA_BRUTA' in dados.columns:
        fig1 = px.bar(dados, x='municipio_extraido', y='TOTAL_DA_RECEITA_BRUTA',
                    title='Receita Bruta por Município',
                    color_discrete_sequence=['#7B1E3B'])
        st.plotly_chart(fig1, use_container_width=True)

with col4:
    fig2 = px.pie(dados, names='status_envio',
                  title='Status de Envio',
                  color_discrete_sequence=['#7B1E3B', '#F2C94C'])
    st.plotly_chart(fig2, use_container_width=True)

if 'PRESTAÇÃO_DE_CONTAS' in dados.columns:
    motivos = dados['PRESTAÇÃO_DE_CONTAS'].value_counts().reset_index()
    motivos.columns = ['Motivo', 'Ocorrências']
    fig3 = px.bar(motivos, x='Motivo', y='Ocorrências',
                  title='Motivos de Inconformidade',
                  color_discrete_sequence=['#000000'])
    st.plotly_chart(fig3, use_container_width=True)
