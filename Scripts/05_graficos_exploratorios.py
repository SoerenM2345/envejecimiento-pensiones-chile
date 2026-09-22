"""
Graficos exploratorios de validacion (no son el dashboard final) para
confirmar visualmente los hallazgos del procesamiento del Censo 2024,
proyecciones INE y datos de pensiones.

Paleta: se usa la paleta de referencia del skill de dataviz (categorica
azul/naranja para Hombres/Mujeres, azul solido para series unicas).
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

OUT_DATA = Path(__file__).resolve().parent.parent / "Data processed"
OUT_FIG = Path(__file__).resolve().parent.parent / "Outputs" / "figures"
OUT_FIG.mkdir(parents=True, exist_ok=True)

# --- paleta de referencia (dataviz skill) -----------------------------------
BLUE = "#2a78d6"      # categorical slot 1 (Hombres)
ORANGE = "#eb6834"    # categorical slot 2 (Mujeres)
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"

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
# 1) Piramide poblacional nacional — Censo 2024 (edad simple, back-to-back)
# =============================================================================
pir = pd.read_csv(OUT_DATA / "censo_pais_edad_simple.csv")
pir_h = pir[pir.sexo == 1].set_index("edad")["poblacion"].reindex(range(0, 86), fill_value=0)
pir_m = pir[pir.sexo == 2].set_index("edad")["poblacion"].reindex(range(0, 86), fill_value=0)

fig, ax = plt.subplots(figsize=(9, 10))
ages = pir_h.index
ax.barh(ages, -pir_h.values / 1000, height=1.0, color=BLUE, label="Hombres", linewidth=0)
ax.barh(ages, pir_m.values / 1000, height=1.0, color=ORANGE, label="Mujeres", linewidth=0)
ax.axvline(0, color=BASELINE, linewidth=1)
xmax = max(pir_h.max(), pir_m.max()) / 1000 * 1.08
ax.set_xlim(-xmax, xmax)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{abs(x):,.0f}"))
ax.set_xlabel("Miles de personas")
ax.set_ylabel("Edad (años, 85 = 85 y más)")
ax.set_title("Pirámide poblacional de Chile — Censo 2024", fontsize=13, color=INK_PRIMARY, loc="left", pad=14)
ax.text(0, 87.5, "Fuente: Censo 2024, INE (18.48M personas; 85 = top-coded 85 y más)",
        fontsize=8, color=INK_MUTED, ha="center")
for y in (0, 15, 65):
    ax.axhline(y, color=GRIDLINE, linewidth=0.8, zorder=0)
ax.legend(frameon=False, loc="lower right")
ax.grid(axis="x", color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for spine in ("top", "right", "left"):
    ax.spines[spine].set_visible(False)
fig.tight_layout()
fig.savefig(OUT_FIG / "01_piramide_nacional_censo2024.png", dpi=150)
plt.close(fig)

# =============================================================================
# 2) Ranking regional de envejecimiento (% 65+)
# =============================================================================
reg = pd.read_csv(OUT_DATA / "indicadores_region.csv").sort_values("pct_65_mas")
national_avg = 100 * reg["pob_65_mas"].sum() / reg["pob_total"].sum()

fig, ax = plt.subplots(figsize=(8, 7))
bars = ax.barh(reg["region_nombre"], reg["pct_65_mas"], color=BLUE, height=0.62)
ax.axvline(national_avg, color=INK_SECONDARY, linewidth=1.2, linestyle=(0, (4, 3)))
ax.text(national_avg, len(reg) - 0.3, f" Promedio país: {national_avg:.1f}%",
        color=INK_SECONDARY, fontsize=9, va="top")
for bar, val in zip(bars, reg["pct_65_mas"]):
    ax.text(val + 0.15, bar.get_y() + bar.get_height() / 2, f"{val:.1f}%",
            va="center", fontsize=9, color=INK_PRIMARY)
ax.set_xlabel("% de población de 65 años o más")
ax.set_title("Envejecimiento por región — Censo 2024", fontsize=13, color=INK_PRIMARY, loc="left", pad=14)
ax.grid(axis="x", color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
ax.spines["left"].set_color(BASELINE)
ax.spines["bottom"].set_color(BASELINE)
fig.tight_layout()
fig.savefig(OUT_FIG / "02_ranking_regional_pct65mas.png", dpi=150)
plt.close(fig)

# =============================================================================
# 3) Evolucion nacional del envejecimiento 1992-2070 (proyecciones INE) +
#    punto Censo 2024 real superpuesto
# =============================================================================
proy = pd.read_csv(OUT_DATA / "proyeccion_envejecimiento_pais.csv")
censo_2024_pct = 100 * reg["pob_65_mas"].sum() / reg["pob_total"].sum()

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(proy["anio"], proy["pct_65_mas"], color=BLUE, linewidth=2.5, solid_capstyle="round")
ax.scatter([2024], [censo_2024_pct], color=ORANGE, s=55, zorder=5, edgecolor=SURFACE, linewidth=1.5)
ax.annotate(f"Censo 2024: {censo_2024_pct:.1f}%", xy=(2024, censo_2024_pct),
            xytext=(2024 + 3, censo_2024_pct - 3.5), fontsize=9.5, color=INK_PRIMARY,
            arrowprops=dict(arrowstyle="-", color=INK_MUTED, linewidth=0.8))
for yr in (2030, 2050, 2070):
    val = proy.loc[proy.anio == yr, "pct_65_mas"].values[0]
    ax.annotate(f"{val:.0f}%", xy=(yr, val), xytext=(0, 8), textcoords="offset points",
                fontsize=9, color=INK_SECONDARY, ha="center")
ax.set_xlabel("Año")
ax.set_ylabel("% de población de 65 años o más")
ax.set_title("Evolución y proyección del envejecimiento en Chile, 1992–2070",
              fontsize=13, color=INK_PRIMARY, loc="left", pad=14)
ax.text(1992, -6, "Fuente: INE, Estimaciones y proyecciones de población 1992-2070 (base 2024); punto naranja = Censo 2024 real",
        fontsize=8, color=INK_MUTED)
ax.grid(axis="y", color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
ax.spines["left"].set_color(BASELINE)
ax.spines["bottom"].set_color(BASELINE)
fig.tight_layout()
fig.savefig(OUT_FIG / "03_evolucion_envejecimiento_1992_2070.png", dpi=150)
plt.close(fig)

print("Graficos guardados en:", OUT_FIG)
