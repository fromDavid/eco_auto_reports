import streamlit as st

st.set_page_config(page_title="Economia + Python", layout="wide")
st.title("Economia + Python • MVP")
st.caption("Dashboard principal. Usa o menu lateral “Pages” para navegar.")

st.markdown("""
**Páginas incluídas:**
- Indicadores (inflação, PIB, desemprego)
- Projeções Económicas (Base/Pess/Otim + amortização dívida)

**Dica:** carrega CSVs próprios na página de Indicadores para usar dados reais.
""")
