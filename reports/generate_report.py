from pathlib import Path
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]
data_dir = ROOT / "data"
tpl_dir = ROOT / "templates"
build_dir = ROOT / "reports" / "build"
charts_dir = build_dir / "charts"
build_dir.mkdir(parents=True, exist_ok=True)
charts_dir.mkdir(parents=True, exist_ok=True)

# Carregar dados
infl = pd.read_csv(data_dir / "inflacao.csv", parse_dates=["data"])
pib = pd.read_csv(data_dir / "pib.csv", parse_dates=["data"])
un = pd.read_csv(data_dir / "desemprego.csv", parse_dates=["data"])

infl = infl[infl["pais"]=="Portugal"].sort_values("data")
pib = pib[pib["pais"]=="Portugal"].sort_values("data")
un = un[un["pais"]=="Portugal"].sort_values("data")

# Gráficos (matplotlib simples)
plt.figure(); plt.plot(infl["data"], infl["inflacao_yoy"]); plt.title("Inflação YoY – Portugal")
infl_chart = charts_dir / "inflacao.png"; plt.savefig(infl_chart, bbox_inches="tight"); plt.close()

plt.figure(); plt.plot(pib["data"], pib["pib"]); plt.title("PIB (índice) – Portugal")
pib_chart = charts_dir / "pib.png"; plt.savefig(pib_chart, bbox_inches="tight"); plt.close()

plt.figure(); plt.plot(un["data"], un["desemprego"]); plt.title("Desemprego – Portugal")
un_chart = charts_dir / "desemprego.png"; plt.savefig(un_chart, bbox_inches="tight"); plt.close()

# Render HTML
env = Environment(loader=FileSystemLoader(str(tpl_dir)))
template = env.get_template("report.html")
html = template.render(
    generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    inflacao_ultimo=round(float(infl["inflacao_yoy"].iloc[-1]),2),
    inflacao_media12=round(float(infl["inflacao_yoy"].tail(12).mean()),2),
    inflacao_dp12=round(float(infl["inflacao_yoy"].tail(12).std()),2),
    inflacao_chart_path=f"charts/{infl_chart.name}",
    pib_chart_path=f"charts/{pib_chart.name}",
    desemprego_chart_path=f"charts/{un_chart.name}",
).encode("utf-8")

out = build_dir / "relatorio.html"
out.write_bytes(html)
print(f"Relatório gerado: {out}")
