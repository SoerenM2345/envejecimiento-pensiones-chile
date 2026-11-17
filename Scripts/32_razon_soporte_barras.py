"""
Barras de «cotizantes por persona de 65+» en Chile: años pasados observados (2010-2024) y escenario con cobertura constante
(2030-2070). Misma serie que el punto crítico del KPI 1.2 (Dashboards/components/critical_point.py, escenario base de
config/escenarios.yaml): cotizantes de diciembre con región sobre la población 65+ del Censo 2024 (nivel INE × 0,930).
Salida: Outputs/figures/07_cotizantes_por_65_barras.png
"""
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import yaml

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "Dashboards"))
from components import critical_point as cp  # noqa: E402

DATOS = RAIZ / "Data processed"
ANIOS_PASADO = [2010, 2015, 2020]          # años observados que se suman al dato 2024
ANIO_DATO = 2024                            # último año con Censo (el Censo manda)
ANIOS_ESCENARIO = [2030, 2040, 2050, 2070]
COLOR_DATO, COLOR_ESC = "#1B2A41", "#527C83"

cfg = yaml.safe_load(open(RAIZ / "config" / "escenarios.yaml"))
esc = cp.Escenario(crec_salarial=cfg["crecimiento_salario_real"]["base"], carga_max=cfg["tope_carga"]["base"], pgu_250=cfg["pgu_250"])
serie = cp.serie_pais(pd.read_csv(DATOS / "kpi_pc_nacional.csv"), pd.read_csv(DATOS / "proyeccion_envejecimiento_pais.csv"),
                      pd.read_csv(DATOS / "kpi_pc_parametros_reforma.csv"), esc)
razon = serie.set_index("anio").razon_soporte if "anio" in serie.columns else serie.razon_soporte

observados = ANIOS_PASADO + [ANIO_DATO]
anios = observados + ANIOS_ESCENARIO
valores = [float(razon[a]) for a in anios]
colores = [COLOR_DATO] * len(observados) + [COLOR_ESC] * len(ANIOS_ESCENARIO)

fig, ax = plt.subplots(figsize=(11, 6.5))
barras = ax.bar([str(a) for a in anios], valores, color=colores, width=0.7)
for b, v in zip(barras, valores):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.04, f"{v:.2f}", ha="center", va="bottom", fontsize=16)
ax.set_ylim(0, max(valores) * 1.15)
ax.set_yticks([])
for lado in ("top", "right", "left"):
    ax.spines[lado].set_visible(False)
ax.spines["bottom"].set_color("#b8bcc0")
ax.tick_params(axis="x", labelsize=17, length=6, color="#b8bcc0")
fig.suptitle("Cotizantes por persona de 65+, Chile (desde 2030: escenario con cobertura constante)", x=0.03, ha="left", fontsize=15,
             fontweight="bold", color="#2F3B45")
ax.legend(handles=[Patch(color=COLOR_DATO, label="Dato observado"), Patch(color=COLOR_ESC, label="Escenario")],
          loc="upper right", frameon=False, ncol=2, fontsize=14)
fig.tight_layout(rect=(0, 0, 1, 0.94))
salida = RAIZ / "Outputs" / "figures" / "07_cotizantes_por_65_barras.png"
fig.savefig(salida, dpi=200, facecolor="white")
print(salida)
print({a: round(v, 2) for a, v in zip(anios, valores)})
