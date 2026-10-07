"""
Ingreso por comuna/región desde CASEN 2022 (única fuente de ingresos
disponible; el Censo es censo de derecho y NO pregunta ingresos).

Fuente: microdatos CASEN 2022 ya extraídos (columnas de ingreso, comuna,
región, factor de expansión `expc`) desde el repo público
bastianolea/casen_comparador_ingresos (GitHub), que a su vez viene del
Ministerio de Desarrollo Social. Se descarga una vez a
Data raw/development sources/casen_ingresos.parquet.

Advertencia metodológica: CASEN es una ENCUESTA muestral (n=202.231 personas
a nivel nacional), no un censo. A nivel comunal la muestra tiene entre 11 y
~8.000 casos por comuna (mediana ~298) — se reporta el tamaño de muestra
(`n_muestra`) en la salida para que comunas con muestra chica se interpreten
con cautela. Los promedios se calculan ponderados por el factor de expansión
`expc` (representan a la poblacion, no son promedios muestrales simples).

Salidas:
  - kpi_ingresos_comuna.csv   (335/346 comunas con dato CASEN)
  - kpi_ingresos_region.csv   (16/16 regiones)
  - kpi_ingreso_envejecimiento.csv (cruce con indicadores_comuna.csv + correlación)
"""
import unicodedata
import pandas as pd
import numpy as np
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "Data raw"
DP = Path(__file__).resolve().parent.parent / "Data processed"
EXT = RAW / "development sources"  # extracto CASEN 2022 de terceros: solo páginas dev (KPI 2.3 usa casen_2022.dta)
EXT.mkdir(exist_ok=True)

PARQUET_URL = "https://raw.githubusercontent.com/bastianolea/casen_comparador_ingresos/main/datos/casen_ingresos.parquet"
LOCAL = EXT / "casen_ingresos.parquet"
if not LOCAL.exists():
    import urllib.request
    urllib.request.urlretrieve(PARQUET_URL, LOCAL)

df = pd.read_parquet(LOCAL)


def normaliza(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.upper().replace("Ñ", "N").strip()


# el comparador ya reemplaza Ñ por N en algunos casos; normalizamos ambos lados
lookup = pd.read_csv(DP / "region_comuna_lookup.csv")
lookup["match_key"] = lookup["comuna_nombre"].apply(normaliza)
df["match_key"] = df["comuna"].apply(normaliza)

# --- correcciones manuales de nombres que no matchean por normalizacion simple
FIXES = {
    "AISEN": "AYSEN",
    "CALERA": "LA CALERA",
    "LLAILLAY": "LLAY LLAY",
    "COIHAIQUE": "COYHAIQUE",
}
df["match_key"] = df["match_key"].replace(FIXES)

# =============================================================================
# 1) Ingreso ponderado por comuna (per capita, ypc) y por hogar (ytotcorh)
# =============================================================================
def wavg(g, col):
    valid = g.dropna(subset=[col])
    if valid.empty:
        return np.nan
    return np.average(valid[col], weights=valid["expc"])


def safe_round(x):
    return round(x) if pd.notna(x) else np.nan


rows = []
for key, g in df.groupby("match_key"):
    rows.append({
        "match_key": key,
        "comuna_casen": g["comuna"].iloc[0],
        "region_casen": g["region"].iloc[0],
        "n_muestra": len(g),
        "ingreso_per_capita_prom": safe_round(wavg(g, "ypc")),
        "ingreso_hogar_prom": safe_round(wavg(g, "ytotcorh")),
    })
ing_comuna = pd.DataFrame(rows)

merged = lookup[["comuna_id", "comuna_nombre", "region_id", "region_nombre_corto", "match_key"]].merge(
    ing_comuna, on="match_key", how="left"
)
sin_match = merged[merged["ingreso_per_capita_prom"].isna()]
print(f"Comunas CASEN: {df['match_key'].nunique()} | comunas censo sin match de ingreso: {len(sin_match)}")
if len(sin_match):
    print("  ", sin_match["comuna_nombre"].tolist())

merged.drop(columns=["match_key"]).to_csv(DP / "kpi_ingresos_comuna.csv", index=False)

# =============================================================================
# 2) Ingreso ponderado por región (directo, sin problema de nombres)
# =============================================================================
rows = []
for reg, g in df.groupby("region"):
    rows.append({
        "region_casen": reg,
        "n_muestra": len(g),
        "ingreso_per_capita_prom": safe_round(wavg(g, "ypc")),
        "ingreso_hogar_prom": safe_round(wavg(g, "ytotcorh")),
    })
ing_region = pd.DataFrame(rows).sort_values("ingreso_per_capita_prom", ascending=False)
ing_region.to_csv(DP / "kpi_ingresos_region.csv", index=False)
print("\n=== Ingreso per cápita promedio por región (CASEN 2022) ===")
print(ing_region.to_string(index=False))

# =============================================================================
# 3) Cruce ingreso x envejecimiento (comuna) + correlacion
# =============================================================================
ind_comuna = pd.read_csv(DP / "indicadores_comuna.csv").rename(columns={"comuna": "comuna_id"})
cross = merged.drop(columns=["match_key"]).merge(
    ind_comuna[["comuna_id", "pob_total", "pct_65_mas", "pct_urbano", "indice_envejecimiento"]],
    on="comuna_id", how="inner",
)
cross_valid = cross.dropna(subset=["ingreso_per_capita_prom"])
cross_valid = cross_valid[cross_valid["pob_total"] >= 500]
pearson = cross_valid["ingreso_per_capita_prom"].corr(cross_valid["pct_65_mas"], method="pearson")
spearman = cross_valid["ingreso_per_capita_prom"].corr(cross_valid["pct_65_mas"], method="spearman")
cross.to_csv(DP / "kpi_ingreso_envejecimiento.csv", index=False)

print(f"\n=== Ingreso per cápita vs % 65+ (comuna, n={len(cross_valid)}, pob>=500) ===")
print(f"Pearson r = {pearson:.3f} | Spearman rho = {spearman:.3f}")
print("\nTop 5 comunas de MAYOR ingreso per cápita:")
print(cross_valid.nlargest(5, "ingreso_per_capita_prom")[["comuna_nombre", "region_nombre_corto", "ingreso_per_capita_prom", "pct_65_mas", "n_muestra"]].to_string(index=False))
print("\nTop 5 comunas de MENOR ingreso per cápita:")
print(cross_valid.nsmallest(5, "ingreso_per_capita_prom")[["comuna_nombre", "region_nombre_corto", "ingreso_per_capita_prom", "pct_65_mas", "n_muestra"]].to_string(index=False))

print("\nListo. Archivos escritos en:", DP)
