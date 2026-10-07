"""
KPI 2.3: pobreza por ingresos en personas de 65+ por región, con CASEN 2022 completa.

Fuente: Data raw/_external/casen2022/casen_2022.dta (Ministerio de Desarrollo Social; no versionado, 501 MB).
Variables: edad, region, pobreza (1 = pobre extremo, 2 = pobre no extremo, 3 = no pobre), expr (factor de expansión
regional, el correcto para estimaciones por región según la Nota de uso), varstrat y varunit (estratos y conglomerados).

Método: proporción ponderada con expr; error estándar por linealización de Taylor con el diseño (estratos varstrat,
conglomerados varunit), estimando el dominio (65+ en la región) sobre toda la muestra. IC 95% = p ± 1,96 EE.

Metodología: la variable `pobreza` de esta base ya está recalculada con la metodología 2024 del Ministerio (nueva canasta
básica, escala de equivalencia y línea única urbano/rural; ver Valor_CBA_y_LPs_25.12.pdf). Con ella la pobreza por ingresos de
2022 es 20,5% (con la metodología anterior eran 6,5%) y la de 2024 es 17,3%. Por eso las cifras de este KPI no se comparan con
las publicadas en 2023.

Validación: la pobreza por ingresos de TODAS las personas, a nivel país, debe dar ≈ 20,5% (cifra oficial de 2022 con metodología 2024).

Salida (Data processed/): pobreza_65_region.csv
  region_id (0 = Chile), region_nombre, n_muestra_65, pob_65_expandida, pct_pobreza_65 (extrema + no extrema),
  pct_pobreza_extrema_65, ee, ic95_inf, ic95_sup, pct_pobreza_menores_65 (contraste)
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DTA = ROOT / "Data raw" / "_external" / "casen2022" / "casen_2022.dta"
OUT = ROOT / "Data processed"
COLS = ["edad", "region", "pobreza", "expr", "varstrat", "varunit"]


def prop_y_ee(df, y, dominio):
    """Proporción ponderada de `y` (0/1) en `dominio` (máscara booleana sobre df) y su EE por linealización."""
    w = df["expr"].to_numpy(dtype=float)
    m = dominio.to_numpy()
    W = (w * m).sum()
    if W == 0:
        return np.nan, np.nan
    p = (w * m * y).sum() / W
    z = m * w * (y - p) / W
    tot = pd.DataFrame({"h": df["varstrat"].to_numpy(), "c": df["varunit"].to_numpy(), "z": z}).groupby(["h", "c"]).z.sum().reset_index()
    var = 0.0
    for _, g in tot.groupby("h"):
        n = len(g)
        if n > 1:
            var += n / (n - 1) * ((g.z - g.z.mean()) ** 2).sum()
    return p, float(np.sqrt(var))


def main():
    from pandas.io.stata import StataReader
    with StataReader(DTA) as r:
        etiquetas = r.value_labels()
    print("etiquetas pobreza:", etiquetas.get("pobreza"))
    df = pd.read_stata(DTA, columns=COLS, convert_categoricals=False)
    print("filas:", len(df), "| valores de pobreza:", sorted(df.pobreza.dropna().unique()))
    df = df.dropna(subset=["pobreza", "edad", "region", "expr"]).copy()

    pobre = df["pobreza"].isin([1, 2]).astype(float).to_numpy()
    extrema = (df["pobreza"] == 1).astype(float).to_numpy()
    p_pais, ee_pais = prop_y_ee(df, pobre, pd.Series(True, index=df.index))
    print(f"VALIDACIÓN pobreza por ingresos, todas las edades, país: {100 * p_pais:.2f}% (±{196 * ee_pais:.2f}) | oficial 2022 con metodología 2024 = 20,5%")
    assert 19.8 < 100 * p_pais < 21.2, "no coincide con la cifra oficial: revisar codificación de pobreza o factor de expansión"

    nombres = pd.read_csv(ROOT / "Data processed" / "kpi_presion_previsional_region.csv").set_index("region_id")["region_nombre"].to_dict()
    nombres[0] = "Chile"
    filas = []
    for rid in [0] + sorted(df["region"].unique().astype(int)):
        en_region = pd.Series(True, index=df.index) if rid == 0 else (df["region"] == rid)
        dom65 = en_region & (df["edad"] >= 65)
        dom_menor = en_region & (df["edad"] < 65)
        p, ee = prop_y_ee(df, pobre, dom65)
        pe, _ = prop_y_ee(df, extrema, dom65)
        pm, _ = prop_y_ee(df, pobre, dom_menor)
        filas.append(dict(
            region_id=rid, region_nombre=nombres.get(rid, str(rid)), n_muestra_65=int(dom65.sum()),
            pob_65_expandida=float(df.loc[dom65, "expr"].sum()),
            pct_pobreza_65=100 * p, pct_pobreza_extrema_65=100 * pe, ee=100 * ee,
            ic95_inf=max(0.0, 100 * (p - 1.96 * ee)), ic95_sup=100 * (p + 1.96 * ee),
            pct_pobreza_menores_65=100 * pm,
        ))
    res = pd.DataFrame(filas)
    res.to_csv(OUT / "pobreza_65_region.csv", index=False)
    print(res.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
