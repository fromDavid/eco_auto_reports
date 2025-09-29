import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Indicadores", layout="wide")
st.title("Indicadores Económicos (demo com CSVs)")

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

tab1, tab2, tab3 = st.tabs(["Inflação", "PIB", "Desemprego"])

with tab1:
    st.subheader("Inflação YoY")
    up = st.file_uploader("Carregar CSV (colunas: data,pais,inflacao_yoy)", type=["csv"], key="infl")
    if up:
        df = pd.read_csv(up, parse_dates=["data"])
    else:
        df = pd.read_csv(DATA_DIR / "inflacao.csv", parse_dates=["data"])
    pais = st.selectbox("País", sorted(df["pais"].unique()))
    dff = df[df["pais"] == pais].sort_values("data")
    fig = px.line(dff, x="data", y="inflacao_yoy", title=f"Inflação YoY – {pais}")
    st.plotly_chart(fig, use_container_width=True)
    if len(dff) >= 12:
        c1,c2,c3 = st.columns(3)
        c1.metric("Último", f"{dff['inflacao_yoy'].iloc[-1]:.2f}%")
        c2.metric("Média 12m", f"{dff['inflacao_yoy'].tail(12).mean():.2f}%")
        c3.metric("Desvio-padrão 12m", f"{dff['inflacao_yoy'].tail(12).std():.2f} pp")

with tab2:
    st.subheader("PIB (índice)")
    up = st.file_uploader("Carregar CSV (colunas: data,pais,pib)", type=["csv"], key="pib")
    if up:
        df = pd.read_csv(up, parse_dates=["data"])
    else:
        df = pd.read_csv(DATA_DIR / "pib.csv", parse_dates=["data"])
    pais = st.selectbox("País (PIB)", sorted(df["pais"].unique()))
    dff = df[df["pais"] == pais].sort_values("data")
    dff["QoQ_%"] = dff["pib"].pct_change() * 100
    dff["YoY_%"] = dff["pib"].pct_change(4) * 100
    fig = px.line(dff, x="data", y="pib", title=f"PIB – {pais}")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(dff.tail(12), use_container_width=True)

with tab3:
    st.subheader("Desemprego (%)")
    up = st.file_uploader("Carregar CSV (colunas: data,pais,desemprego)", type=["csv"], key="un")
    if up:
        df = pd.read_csv(up, parse_dates=["data"])
    else:
        df = pd.read_csv(DATA_DIR / "desemprego.csv", parse_dates=["data"])
    paises = st.multiselect("Países", sorted(df["pais"].unique()), default=sorted(df["pais"].unique())[:1])
    dff = df[df["pais"].isin(paises)].sort_values("data")
    fig = px.line(dff, x="data", y="desemprego", color="pais", title="Desemprego – comparação")
    st.plotly_chart(fig, use_container_width=True)
