import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from jinja2 import Template

st.set_page_config(page_title="Projeções Económicas", layout="wide")
st.title("Projeções Económicas por Anos")
st.caption("Cenários Base/Pess/Otim e amortização de dívida (SAC/PRICE). Exporta CSV e relatório HTML.")

def amortizacao_schedule(valor, taxa, anos, metodo="SAC"):
    if anos <= 0 or valor <= 0:
        return pd.DataFrame(columns=["Ano","Juros","Amortizacao","Prestacao","Saldo_Final"])
    saldo = valor
    out = []
    if metodo.upper() == "SAC":
        amort_const = valor / anos
        for i in range(1, anos+1):
            juros = saldo * taxa
            prest = amort_const + juros
            saldo = max(0.0, saldo - amort_const)
            out.append([i, juros, amort_const, prest, saldo])
    else:  # PRICE
        r = taxa
        if r == 0:
            prest_const = valor / anos
        else:
            prest_const = valor * r / (1 - (1 + r)**(-anos))
        for i in range(1, anos+1):
            juros = saldo * r
            amort = prest_const - juros
            saldo = max(0.0, saldo - amort)
            out.append([i, juros, amort, prest_const, saldo])
    return pd.DataFrame(out, columns=["Ano","Juros","Amortizacao","Prestacao","Saldo_Final"])

def projecao(vendas0, cv_pct, cf, debt, rate, taxa_irc, capex_pct, dep_anos, nwc_pct, anos, crescimento_list, amort_metodo=None):
    anos_idx = np.arange(1, anos+1)
    vendas = [vendas0 * (1 + crescimento_list[0])]
    for i in range(1, anos):
        vendas.append(vendas[-1] * (1 + crescimento_list[i]))
    vendas = np.array(vendas)

    cv = vendas * cv_pct
    mb = vendas - cv
    ro = mb - cf

    if amort_metodo in ("SAC","PRICE"):
        amort = amortizacao_schedule(debt, rate, anos, metodo=amort_metodo)
        juros_vec = np.zeros(anos)
        for i in range(min(anos, len(amort))):
            juros_vec[i] = amort.loc[i, "Juros"]
        ef = juros_vec
    else:
        ef = np.full(anos, debt * rate)

    rlai = ro - ef
    imposto = np.maximum(rlai, 0) * taxa_irc
    rl = rlai - imposto

    capex = vendas * capex_pct
    dep = np.zeros(anos)
    capex_hist = []
    for t in range(anos):
        capex_hist.append(capex[t])
        janela = capex_hist[max(0, t-dep_anos+1):t+1]
        dep[t] = sum(janela)/dep_anos

    nwc = vendas * nwc_pct
    nwc0 = vendas0 * nwc_pct
    delta_nwc = nwc - np.append(nwc0, nwc[:-1])

    fcff = rl + dep - capex - delta_nwc

    return pd.DataFrame({
        "Ano": anos_idx,
        "Vendas": vendas,
        "CV": cv,
        "MB": mb,
        "CF": cf,
        "RO": ro,
        "EF": ef,
        "RLAI": rlai,
        "Imposto": imposto,
        "RL": rl,
        "Capex": capex,
        "Depreciacao": dep,
        "NWC": nwc,
        "DeltaNWC": delta_nwc,
        "FCFF": fcff
    })

# --- Inputs ---
with st.sidebar:
    st.header("Dados Base (Ano 0)")
    vendas0 = st.number_input("Vendas Ano 0", min_value=0.0, value=25000.0, step=1000.0, format="%.2f")
    cv_pct = st.number_input("CV (% das Vendas)", min_value=0.0, max_value=100.0, value=52.0, step=0.5, format="%.2f")/100.0
    cf = st.number_input("CF (Custos Fixos)", min_value=0.0, value=7500.0, step=1000.0, format="%.2f")
    debt = st.number_input("Dívida Financeira (saldo)", min_value=0.0, value=8000.0, step=1000.0, format="%.2f")
    rate = st.number_input("Taxa de juro (a.a.)", min_value=0.0, max_value=100.0, value=5.0, step=0.25, format="%.2f")/100.0
    taxa_irc = st.number_input("Taxa de IRC", min_value=0.0, max_value=100.0, value=21.0, step=0.5, format="%.2f")/100.0

    st.header("Capex & Depreciação")
    capex_pct = st.number_input("Capex (% das Vendas)", min_value=0.0, max_value=100.0, value=4.0, step=0.5, format="%.2f")/100.0
    dep_anos = st.number_input("Vida útil (anos) para depreciação", min_value=1, max_value=30, value=5, step=1)

    st.header("Fundo de Maneio (NWC)")
    nwc_pct = st.number_input("NWC (% das Vendas)", min_value=0.0, max_value=100.0, value=12.0, step=0.5, format="%.2f")/100.0

    st.header("Horizonte & Crescimento")
    anos = st.number_input("Número de anos", min_value=1, max_value=15, value=5, step=1)
    crescimento_pct = st.number_input("Crescimento BASE (%)", min_value=-100.0, max_value=200.0, value=6.0, step=0.5, format="%.2f")/100.0

    st.markdown("---")
    st.header("Cenários (variações sobre BASE)")
    pess_mult = st.number_input("Pessimista (ex: 0.8 = -20%)", min_value=0.0, max_value=3.0, value=0.8, step=0.05)
    otim_mult  = st.number_input("Otimista (ex: 1.2 = +20%)", min_value=0.0, max_value=3.0, value=1.2, step=0.05)

    st.markdown("---")
    st.header("Curva manual de crescimento (opcional)")
    usar_curva = st.checkbox("Usar curva manual por ano?")
    curva_inputs = []
    if usar_curva:
        for i in range(1, anos+1):
            g = st.number_input(f"g{i} (%)", value=crescimento_pct*100, key=f"gx_{i}", step=0.5, format="%.2f")/100.0
            curva_inputs.append(g)

    st.markdown("---")
    st.header("Amortização da Dívida")
    amort_on = st.checkbox("Ativar amortização?")
    amort_metodo = None
    if amort_on:
        amort_metodo = st.selectbox("Método", ["SAC","PRICE"])

# --- Crescimentos ---
if usar_curva and len(curva_inputs)==anos:
    base_g = curva_inputs
else:
    base_g = [crescimento_pct]*anos
pess_g = [g * pess_mult for g in base_g]
otim_g = [g * otim_mult for g in base_g]

# --- Projeções ---
df_base = projecao(vendas0, cv_pct, cf, debt, rate, taxa_irc, capex_pct, dep_anos, nwc_pct, anos, base_g, amort_metodo)
df_pess = projecao(vendas0, cv_pct, cf, debt, rate, taxa_irc, capex_pct, dep_anos, nwc_pct, anos, pess_g, amort_metodo)
df_otim = projecao(vendas0, cv_pct, cf, debt, rate, taxa_irc, capex_pct, dep_anos, nwc_pct, anos, otim_g, amort_metodo)

# --- KPIs ---
k1,k2,k3,k4 = st.columns(4)
k1.metric("RL final (Base)", f"{df_base['RL'].iloc[-1]:,.0f}".replace(",", " ") + " €")
k2.metric("RL final (Pess)", f"{df_pess['RL'].iloc[-1]:,.0f}".replace(",", " ") + " €")
k3.metric("RL final (Otim)", f"{df_otim['RL'].iloc[-1]:,.0f}".replace(",", " ") + " €")
k4.metric("FCFF acumulado (Base)", f"{df_base['FCFF'].sum():,.0f}".replace(",", " ") + " €")

# --- Gráficos ---
c1, c2 = st.columns(2)
with c1:
    st.subheader("Receitas por cenário")
    df_plot_v = pd.DataFrame({"Ano": df_base["Ano"], "Base": df_base["Vendas"], "Pessimista": df_pess["Vendas"], "Otimista": df_otim["Vendas"]})
    st.plotly_chart(px.line(df_plot_v, x="Ano", y=["Base","Pessimista","Otimista"], markers=True), use_container_width=True)
with c2:
    st.subheader("Resultado Líquido por cenário")
    df_plot_rl = pd.DataFrame({"Ano": df_base["Ano"], "Base": df_base["RL"], "Pessimista": df_pess["RL"], "Otimista": df_otim["RL"]})
    st.plotly_chart(px.line(df_plot_rl, x="Ano", y=["Base","Pessimista","Otimista"], markers=True), use_container_width=True)

st.subheader("FCFF por cenário")
df_plot_fcff = pd.DataFrame({"Ano": df_base["Ano"], "Base": df_base["FCFF"], "Pessimista": df_pess["FCFF"], "Otimista": df_otim["FCFF"]})
st.plotly_chart(px.bar(df_plot_fcff, x="Ano", y=["Base","Pessimista","Otimista"]), use_container_width=True)

# --- Tabelas ---
st.markdown("### Tabelas detalhadas")
tabs = st.tabs(["Base","Pessimista","Otimista"])
for tab, d in zip(tabs, [df_base, df_pess, df_otim]):
    with tab:
        st.dataframe(d.style.format({
            "Vendas":"{:,.0f} €", "CV":"{:,.0f} €", "MB":"{:,.0f} €", "CF":"{:,.0f} €", "RO":"{:,.0f} €",
            "EF":"{:,.0f} €", "RLAI":"{:,.0f} €", "Imposto":"{:,.0f} €", "RL":"{:,.0f} €",
            "Capex":"{:,.0f} €", "Depreciacao":"{:,.0f} €", "NWC €":"{:,.0f} €", "DeltaNWC":"{:,.0f} €", "FCFF":"{:,.0f} €"
        }), use_container_width=True)

# --- Exportações ---
st.markdown("### Exportar")
def to_csv_bytes(df): return df.to_csv(index=False).encode("utf-8")
cA, cB, cC = st.columns(3)
cA.download_button("CSV – Base", to_csv_bytes(df_base), file_name="projecoes_base.csv", mime="text/csv")
cB.download_button("CSV – Pess", to_csv_bytes(df_pess), file_name="projecoes_pess.csv", mime="text/csv")
cC.download_button("CSV – Otim", to_csv_bytes(df_otim), file_name="projecoes_otim.csv", mime="text/csv")

html_tpl = Template("<html><head><meta charset='utf-8'><title>Relatorio Projecoes</title></head><body>"
                    "<h1>Projecoes Economicas – Cenarios</h1>"
                    "<p>Gerado em {{ ts }} | Cresc.Base={{ base_growth*100 }}% | PessMult={{ pess_mult }} | OtimMult={{ otim_mult }} | Amortizacao={{ amort if amort else 'Nao' }}</p>"
                    "<h2>Resumo</h2>"
                    "<ul><li>RL final (Base): {{ base_rl }}</li><li>RL final (Pess): {{ pess_rl }}</li><li>RL final (Otim): {{ otim_rl }}</li></ul>"
                    "<ul><li>FCFF acumulado (Base): {{ base_fcff }}</li><li>Pess: {{ pess_fcff }}</li><li>Otim: {{ otim_fcff }}</li></ul>"
                    "</body></html>")
html = html_tpl.render(
    ts=datetime.now().strftime("%Y-%m-%d %H:%M"),
    base_growth=(sum(base_g)/len(base_g) if len(base_g)>0 else 0.0),
    pess_mult=pess_mult, otim_mult=otim_mult,
    amort=amort_metodo,
    base_rl=f"{df_base['RL'].iloc[-1]:,.0f}",
    pess_rl=f"{df_pess['RL'].iloc[-1]:,.0f}",
    otim_rl=f"{df_otim['RL'].iloc[-1]:,.0f}",
    base_fcff=f"{df_base['FCFF'].sum():,.0f}",
    pess_fcff=f"{df_pess['FCFF'].sum():,.0f}",
    otim_fcff=f"{df_otim['FCFF'].sum():,.0f}"
).encode("utf-8")
st.download_button("Exportar Relatório (HTML) – Comparativo", html, file_name="relatorio_projecoes_cenarios.html", mime="text/html")
