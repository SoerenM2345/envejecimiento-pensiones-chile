"""
Grafico exploratorio (no es el dashboard final) que compara la piramide
poblacional de Chile (Censo 2024, INE) con la de Alemania (Basisjahr 2024,
Destatis) en un mismo estilo, para contrastar el nivel de envejecimiento de
ambos paises.

Eje x en % de la poblacion total de cada pais (no en personas), porque
Alemania tiene ~4,5 veces la poblacion de Chile: solo asi las dos formas son
comparables visualmente. Ambas piramides se top-codean a "85 y mas" (asi lo
entrega el Censo 2024 chileno; para Alemania se sumo la cola de edad simple
85-99+ del dato original).

Paleta: se usa la paleta de referencia del skill de dataviz (azul/naranja
para Hombres/Mujeres); tonos claros = menores de 65 anios, tonos solidos =
65 anios y mas, con una linea roja marcando ese umbral en ambos paneles.

Genera dos figuras:
  1. 05_piramide_chile_alemania_2024.png            -> solo el umbral de 65
  2. 06_piramide_chile_alemania_2024_tramos_edad.png -> ademas del umbral de
     65, una segunda linea roja en 15 anios (frontera 0-14 / 15-64), para
     marcar los tres tramos de edad de golpe.

Tambien imprime, para cada pais, el % de poblacion en 0-14 / 15-64 / 65+.
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "Data processed"
OUT_FIG = Path(__file__).resolve().parent.parent / "Outputs" / "figures"
OUT_FIG.mkdir(parents=True, exist_ok=True)

# --- paleta de referencia (dataviz skill) -----------------------------------
BLUE = "#2a78d6"
ORANGE = "#eb6834"
RED = "#e34948"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"

UMBRAL_VEJEZ = 65
EDAD_TOPE = 85  # ambas piramides se top-codean a "85 y mas" para poder compararlas


def lighten(hex_color: str, ratio: float = 0.55) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r2 = round(r + (255 - r) * ratio)
    g2 = round(g + (255 - g) * ratio)
    b2 = round(b + (255 - b) * ratio)
    return f"#{r2:02x}{g2:02x}{b2:02x}"


BLUE_LIGHT = lighten(BLUE)
ORANGE_LIGHT = lighten(ORANGE)

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


def piramide_pct(h_edad: pd.Series, m_edad: pd.Series, tope: int = EDAD_TOPE):
    """Recibe series edad->poblacion (H y M) y devuelve (h_pct, m_pct) con
    edad top-codeada a `tope` y expresadas en % de la poblacion total del
    pais (H+M), para que ambos paneles sean comparables aunque Alemania
    tenga ~4,5 veces la poblacion de Chile."""
    h = h_edad.reindex(range(0, tope + 1), fill_value=0).copy()
    m = m_edad.reindex(range(0, tope + 1), fill_value=0).copy()
    if h_edad.index.max() > tope:
        h.loc[tope] += h_edad[h_edad.index > tope].sum()
    if m_edad.index.max() > tope:
        m.loc[tope] += m_edad[m_edad.index > tope].sum()
    total = h.sum() + m.sum()
    return h / total * 100, m / total * 100, int(total)


# =============================================================================
# Datos: Censo 2024 (Chile) vs Basisjahr 2024 Destatis (Alemania)
# =============================================================================
censo_pais = pd.read_csv(DATA / "censo_pais_edad_simple.csv")
alemania = pd.read_csv(DATA / "alemania_piramide_edad_simple_2024.csv")

h_cl_raw = censo_pais[censo_pais.sexo == 1].set_index("edad")["poblacion"]
m_cl_raw = censo_pais[censo_pais.sexo == 2].set_index("edad")["poblacion"]
h_cl, m_cl, total_cl = piramide_pct(h_cl_raw, m_cl_raw)

h_de_raw = alemania[alemania.sexo == "H"].set_index("edad")["poblacion"]
m_de_raw = alemania[alemania.sexo == "M"].set_index("edad")["poblacion"]
h_de, m_de, total_de = piramide_pct(h_de_raw, m_de_raw)

xmax = max(h_cl.max(), m_cl.max(), h_de.max(), m_de.max()) * 1.08

# =============================================================================
# Indicadores por tramo de edad (0-14 / 15-64 / 65+), para las dos piramides
# =============================================================================
UMBRAL_NINEZ = 15  # limite inferior del tramo 15-64 (frontera con 0-14)


def indicadores_tramo(h_edad: pd.Series, m_edad: pd.Series):
    total = h_edad.sum() + m_edad.sum()
    pob = h_edad.add(m_edad, fill_value=0)
    pob_0_14 = pob[pob.index <= UMBRAL_NINEZ - 1].sum()
    pob_15_64 = pob[(pob.index >= UMBRAL_NINEZ) & (pob.index <= UMBRAL_VEJEZ - 1)].sum()
    pob_65_mas = pob[pob.index >= UMBRAL_VEJEZ].sum()
    return {
        "pct_0_14": 100 * pob_0_14 / total,
        "pct_15_64": 100 * pob_15_64 / total,
        "pct_65_mas": 100 * pob_65_mas / total,
    }


ind_cl = indicadores_tramo(h_cl_raw, m_cl_raw)
ind_de = indicadores_tramo(h_de_raw, m_de_raw)

for nombre, ind in (("Chile", ind_cl), ("Alemania", ind_de)):
    print(f"{nombre}: 0-14 = {ind['pct_0_14']:.2f}% | 15-64 = {ind['pct_15_64']:.2f}% | "
          f"65+ = {ind['pct_65_mas']:.2f}%")


# =============================================================================
# Grafico: dos paneles lado a lado, mismo estilo, con las lineas de umbral
# que se pidan (65 anios siempre; opcionalmente tambien 15 anios)
# =============================================================================
def graficar(umbrales: list[int], out_name: str, nota_umbral: str):
    fig, axes = plt.subplots(1, 2, figsize=(13, 9), sharey=True)

    paneles = [
        (axes[0], h_cl, m_cl, f"Chile — Censo 2024 ({total_cl:,} hab.)".replace(",", ".")),
        (axes[1], h_de, m_de, f"Alemania — Destatis, base 2024 ({total_de:,} hab.)".replace(",", ".")),
    ]

    for ax, h, m, titulo in paneles:
        ages = h.index
        h_colors = [BLUE_LIGHT if edad < UMBRAL_VEJEZ else BLUE for edad in ages]
        m_colors = [ORANGE_LIGHT if edad < UMBRAL_VEJEZ else ORANGE for edad in ages]
        ax.barh(ages, -h.values, height=1.0, color=h_colors, linewidth=0)
        ax.barh(ages, m.values, height=1.0, color=m_colors, linewidth=0)
        ax.axvline(0, color=BASELINE, linewidth=1)
        for y in umbrales:
            ax.axhline(y, color=RED, linewidth=1.5, linestyle=(0, (2, 2)))
        ax.set_xlim(-xmax, xmax)
        ax.set_ylim(-1, EDAD_TOPE + 1)
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{abs(x):.1f}%"))
        ax.set_title(titulo, fontsize=11.5, color=INK_PRIMARY, pad=10)
        ax.grid(axis="x", color=GRIDLINE, linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.spines["left"].set_color(BASELINE)
        ax.spines["bottom"].set_color(BASELINE)

    axes[0].set_ylabel("Edad (años, 85 = 85 y más)")
    axes[0].set_xlabel("% de la población total del país")
    axes[1].set_xlabel("% de la población total del país")

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=BLUE, label="Hombres (65 y más)"),
        plt.Rectangle((0, 0), 1, 1, color=BLUE_LIGHT, label="Hombres (< 65)"),
        plt.Rectangle((0, 0), 1, 1, color=ORANGE, label="Mujeres (65 y más)"),
        plt.Rectangle((0, 0), 1, 1, color=ORANGE_LIGHT, label="Mujeres (< 65)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.02), fontsize=9)

    fig.suptitle("Pirámide poblacional: Chile vs. Alemania, 2024", fontsize=14.5, color=INK_PRIMARY,
                 x=0.12, y=1.06, ha="left")
    fig.text(
        0.5, 1.0,
        "Eje x en % de la población total de cada país (no en personas); ambas se top-codean a \"85 y más\". "
        + nota_umbral,
        fontsize=9.5, color=INK_SECONDARY, ha="center", va="top",
    )
    fig.text(
        0.0, -0.06,
        "Fuentes: INE, Censo 2024 (Chile). Destatis, 14ª Bevölkerungsvorausberechnung, Basisjahr 2024 "
        "(Alemania, población real, no proyectada; edad simple 85-99+ agregada a \"85 y más\").",
        fontsize=8, color=INK_MUTED, ha="left",
    )

    fig.tight_layout(rect=[0, 0.02, 1, 0.94])
    out_path = OUT_FIG / out_name
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Grafico guardado en:", out_path)


graficar([UMBRAL_VEJEZ], "05_piramide_chile_alemania_2024.png",
         "La línea roja marca el umbral de 65 años.")
graficar([UMBRAL_NINEZ, UMBRAL_VEJEZ], "06_piramide_chile_alemania_2024_tramos_edad.png",
         "Las líneas rojas marcan los límites de los tramos 0-14 / 15-64 / 65+.")

print(f"Chile: {total_cl:,} hab. | Alemania: {total_de:,} hab.".replace(",", "."))
