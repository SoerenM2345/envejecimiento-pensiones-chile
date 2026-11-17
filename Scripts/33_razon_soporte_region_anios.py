"""
KPI 1.2: cotizantes por persona de 65+ de cada región en años pasados (2010, 2015, 2020), en 2024 y en el escenario regional (2035, 2050).

  - Cotizantes: diciembre, con región (cotizantes_por_region.csv, Superintendencia de Pensiones).
  - Población 65+ de los años pasados: INE base 2017 (única proyección regional año a año), llevada al nivel del Censo 2024 de cada región
    (el Censo manda): INE17(región, año) x Censo(región, 2024) / INE17(región, 2024). En 2024 coincide con razon_soporte_previsional
    de kpi_presion_previsional_region.csv.
  - Escenario 2035 y 2050: la misma regla que el gráfico regional del dashboard: cobertura 2024 constante / índice de dependencia de vejez
    del escenario regional (kpi_proyeccion_regional.csv).
  - Biobío y Ñuble: la Superintendencia las publica juntas hasta 2017, así que 2010 y 2015 son una sola razón para las dos
    (columna `fusionada` = True).

Genera Data processed/kpi_razon_soporte_region_anios.csv (region_id, region_nombre, anio, razon, tipo, fusionada).
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DP = ROOT / "Data processed"
INE17 = ROOT / "Data raw" / "_external" / "ine_proyecciones_base2017" / "estimaciones-y-proyecciones-2002-2035-comunas.xlsx"
ANIOS_PASADO = [2010, 2015, 2020]
ANIO_REF = 2024
BIOBIO, NUBLE = 8, 16

pres = pd.read_csv(DP / "kpi_presion_previsional_region.csv").set_index("region_id")
ind = pd.read_csv(DP / "indicadores_region.csv").set_index("region")
proy = pd.read_csv(DP / "kpi_proyeccion_regional.csv")

ine = pd.read_excel(INE17)
ine.columns = [c.split("\n")[0] for c in ine.columns]
cols = {int(c.split()[-1]): c for c in ine.columns if c.startswith("Poblacion")}
p65_ine = ine[ine.Edad >= 65].groupby("Region")[[cols[a] for a in ANIOS_PASADO + [ANIO_REF]]].sum()
p65_ine.columns = ANIOS_PASADO + [ANIO_REF]
p65 = p65_ine.mul(ind.pob_65_mas / p65_ine[ANIO_REF], axis=0)  # el Censo 2024 manda: se corrige el nivel de cada región

cot = pd.read_csv(DP / "cotizantes_por_region.csv")
cot = cot[cot.region_id.notna()].assign(region_id=lambda x: x.region_id.astype(int)).pivot(index="region_id", columns="anio", values="cotizantes")

filas = []
for rid in sorted(pres.index):
    nombre = pres.loc[rid, "region_nombre"]
    for a in ANIOS_PASADO + [ANIO_REF]:
        fusionada = rid in (BIOBIO, NUBLE) and a < 2018
        ids = [BIOBIO, NUBLE] if fusionada else [rid]
        filas.append((rid, nombre, a, cot.loc[ids, a].sum() / p65.loc[ids, a].sum(), "observado", fusionada))
    r = proy[proy.region_id == rid].set_index("anio")
    for a in (2035, 2050):
        filas.append((rid, nombre, a, pres.loc[rid, "cobertura_previsional_pct"] / r.loc[a, "indice_dependencia_vejez_proy"], "escenario", False))
out = pd.DataFrame(filas, columns=["region_id", "region_nombre", "anio", "razon", "tipo", "fusionada"])

ref = out[out.anio == ANIO_REF].set_index("region_id").razon
assert (ref - pres.razon_soporte_previsional).abs().max() < 0.01, (ref - pres.razon_soporte_previsional).abs().max()  # coincide con 1.2
out.round({"razon": 4}).to_csv(DP / "kpi_razon_soporte_region_anios.csv", index=False)
print(out.pivot(index="region_nombre", columns="anio", values="razon").round(2).to_string())
