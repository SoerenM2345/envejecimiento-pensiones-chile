"""
Grafico exploratorio (no es el dashboard final) sobre el "Kipppunkt":
el ano en que la poblacion en edad de trabajar (15-64 anios) deja de
crecer y comienza a declinar de forma permanente, segun las proyecciones
INE 1992-2070 (base 2024).

Paleta: se usa la paleta de referencia del skill de dataviz (azul solido
para la serie principal, naranja para el punto de quiebre/kipppunkt).
"""
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

OUT_DATA = Path(__file__).resolve().parent.parent / "Data processed"
OUT_FIG = Path(__file__).resolve().parent.parent / "Outputs" / "figures"
OUT_FIG.mkdir(parents=True, exist_ok=True)

# --- paleta de referencia (dataviz skill) -----------------------------------
BLUE = "#2a78d6"
ORANGE = "#eb6834"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"
DECLINE_FILL = "#fbe4d8"  # tinte suave de ORANGE para la fase de declive

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "text.color": INK_PRIMARY,
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": INK_SECONDARY,
    "xtick.color": INK_MUTED,
    "ytick.color": INK_MUTED,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
})

# =============================================================================
# Datos: poblacion 15-64 anios, 1992-2070 (INE)
# =============================================================================
proy = pd.read_csv(OUT_DATA / "proyeccion_envejecimiento_pais.csv").sort_values("anio")
proy["pob_15_64_mill"] = proy["pob_15_64"] / 1_000_000

peak_row = proy.loc[proy["pob_15_64"].idxmax()]
peak_year = int(peak_row["anio"])
peak_val = peak_row["pob_15_64_mill"]

# primer anio en que la poblacion 15-64 cae respecto al anio anterior
proy["delta"] = proy["pob_15_64"].diff()
kippunkt_year = int(proy.loc[proy["delta"] < 0, "anio"].iloc[0])
kippunkt_val = proy.loc[proy["anio"] == kippunkt_year, "pob_15_64_mill"].values[0]

# =============================================================================
# Grafico
# =============================================================================
fig, ax = plt.subplots(figsize=(11, 6.5))

ax.axvspan(kippunkt_year, proy["anio"].max(), color=DECLINE_FILL, zorder=0)

ax.plot(proy["anio"], proy["pob_15_64_mill"], color=BLUE, linewidth=2.5, solid_capstyle="round")

ax.axvline(kippunkt_year, color=INK_SECONDARY, linewidth=1.2, linestyle=(0, (4, 3)))
ax.scatter([peak_year], [peak_val], color=ORANGE, s=80, zorder=5, edgecolor=SURFACE, linewidth=1.5)

ax.set_xlabel("Ano")
ax.set_ylabel("Poblacion de 15 a 64 anios (millones)")

fig.text(
    0.085, 0.955,
    "Chile: cuando comienza a declinar la poblacion en edad de trabajar",
    fontsize=14, color=INK_PRIMARY,
)
fig.text(
    0.085, 0.915,
    f"Maximo en {peak_year} ({peak_val:.2f}M) — declive permanente desde {kippunkt_year}",
    fontsize=10.5, color=INK_SECONDARY,
)

# ano de quiebre resaltado directamente sobre el eje, en vez de una caja de texto
ticks = sorted(set(range(1990, 2071, 10)) | {kippunkt_year})
ax.set_xticks(ticks)
for label in ax.get_xticklabels():
    if int(label.get_text()) == kippunkt_year:
        label.set_color(INK_SECONDARY)
        label.set_fontweight("bold")

ax.grid(axis="y", color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
ax.spines["left"].set_color(BASELINE)
ax.spines["bottom"].set_color(BASELINE)

fig.text(
    0.085, 0.01,
    "Fuente: INE, Estimaciones y proyecciones de poblacion 1992-2070 (base 2024).",
    fontsize=8, color=INK_MUTED,
)

fig.tight_layout(rect=(0, 0.03, 1, 0.87))
fig.savefig(OUT_FIG / "04_kippunkt_poblacion_edad_trabajar.png", dpi=150)
plt.close(fig)

print(f"Peak poblacion 15-64: {peak_year} ({peak_val:.2f}M)")
print(f"Kipppunkt (1er ano de caida): {kippunkt_year} ({kippunkt_val:.2f}M)")
print("Grafico guardado en:", OUT_FIG / "04_kippunkt_poblacion_edad_trabajar.png")
