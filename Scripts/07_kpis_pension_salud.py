"""
Calcula los KPIs "gold" que combinan Censo 2024 + proyecciones INE + datos de
pensiones (ver ../config/kpis.yaml para las definiciones formales):

  1. kpi_presion_previsional_region.csv  -> cobertura y razón de soporte por región
  2. kpi_presion_previsional_edad.csv    -> pensionados (sistema antiguo) vs
                                             cotizantes (AFP) por tramo de edad
  3. kpi_proyeccion_regional.csv         -> proyección regional 2024->2035->2050
                                             por reparto de tasas nacionales +
                                             índice de presión de salud
  4. kpi_urbanizacion_envejecimiento.csv -> comuna x pct_urbano x pct_65_mas
                                             + correlación
"""
import pandas as pd
import numpy as np
from pathlib import Path

DP = Path(__file__).resolve().parent.parent / "Data processed"

# =============================================================================
# 1) Presión previsional por región: cobertura y razón de soporte
# =============================================================================
print("1) kpi_presion_previsional_region.csv ...")
ind_region = pd.read_csv(DP / "indicadores_region.csv")
cot_region = pd.read_csv(DP / "cotizantes_por_region.csv")
cot_2025 = cot_region[(cot_region.anio == 2025) & cot_region.region_id.notna()][
    ["region_id", "cotizantes"]
]

reg = ind_region.rename(columns={"region": "region_id"}).merge(cot_2025, on="region_id", how="left")
reg["cobertura_previsional_pct"] = round(100 * reg["cotizantes"] / reg["pob_15_64"], 2)
reg["razon_soporte_previsional"] = round(reg["cotizantes"] / reg["pob_65_mas"], 2)
reg["adultos_mayores_por_cotizante"] = round(reg["pob_65_mas"] / reg["cotizantes"], 3)

out1 = reg[[
    "region_id", "region_nombre", "pob_total", "pob_15_64", "pob_65_mas", "cotizantes",
    "pct_65_mas", "cobertura_previsional_pct", "razon_soporte_previsional",
    "adultos_mayores_por_cotizante",
]].sort_values("razon_soporte_previsional")
out1.to_csv(DP / "kpi_presion_previsional_region.csv", index=False)
print(out1.to_string(index=False))
print(f"   Nacional: {reg['cotizantes'].sum()/reg['pob_65_mas'].sum():.2f} cotizantes por c/adulto mayor")

# =============================================================================
# 2) Sistema antiguo (pensionados IPS) vs sistema AFP (cotizantes), por edad
#    -- contexto historico, no es la razon de sostenibilidad del sistema AFP.
# =============================================================================
print("\n2) kpi_presion_previsional_edad.csv ...")
pens_edad = pd.read_csv(DP / "pensiones_pagadas_por_tramo_edad.csv")
pens_65mas = pens_edad[
    pens_edad.tramo_edad.isin(["+65 - 70", "+70 - 75", "+75 - 80", "+80 - 85",
                                "+85 - 90", "+90 - 95", "+95 - 100", "+100"])
]["numero_pensionados"].sum()

cot_edad = pd.read_csv(DP / "cotizantes_por_edad.csv")
cot_65mas_2025 = cot_edad[(cot_edad.anio == 2025) & (cot_edad.tramo_edad == "más de 65")]["cotizantes"].sum()
cot_total_2025 = cot_edad[(cot_edad.anio == 2025) & (cot_edad.tramo_edad == "Total")]["cotizantes"].sum()

out2 = pd.DataFrame([{
    "tramo": "65 y más",
    "pensionados_sistema_antiguo_jul2026": int(pens_65mas),
    "cotizantes_afp_2025": int(cot_65mas_2025),
    "pensionados_por_100_cotizantes": round(100 * pens_65mas / cot_65mas_2025, 1),
}, {
    "tramo": "Total país (todas las edades)",
    "pensionados_sistema_antiguo_jul2026": int(pens_edad[pens_edad.tramo_edad == "Total"]["numero_pensionados"].sum()),
    "cotizantes_afp_2025": int(cot_total_2025),
    "pensionados_por_100_cotizantes": round(100 * pens_edad[pens_edad.tramo_edad == "Total"]["numero_pensionados"].sum() / cot_total_2025, 1),
}])
out2.to_csv(DP / "kpi_presion_previsional_edad.csv", index=False)
print(out2.to_string(index=False))

# =============================================================================
# 3) Proyeccion regional por reparto de tasas nacionales (shift-share) +
#    indice de presion de salud
# =============================================================================
print("\n3) kpi_proyeccion_regional.csv ...")
proy_pais = pd.read_csv(DP / "proyeccion_envejecimiento_pais.csv").set_index("anio")

def tasa_crecimiento(grupo_col, anio_base, anio_destino):
    return proy_pais.loc[anio_destino, grupo_col] / proy_pais.loc[anio_base, grupo_col]

filas = []
for anio_destino in (2035, 2050):
    r15 = tasa_crecimiento("pob_0_14", 2024, anio_destino)
    r1564 = tasa_crecimiento("pob_15_64", 2024, anio_destino)
    r65 = tasa_crecimiento("pob_65_mas", 2024, anio_destino)
    r80 = tasa_crecimiento("pob_80_mas", 2024, anio_destino)
    for _, row in ind_region.iterrows():
        p0_14 = row["pob_0_14"] * r15
        p15_64 = row["pob_15_64"] * r1564
        p65 = row["pob_65_mas"] * r65
        p80 = row["pob_80_mas"] * r80
        ptot = p0_14 + p15_64 + p65
        filas.append({
            "anio": anio_destino,
            "region_id": row["region"],
            "region_nombre": row["region_nombre"],
            "pob_total_proy": round(ptot),
            "pob_65_mas_proy": round(p65),
            "pob_80_mas_proy": round(p80),
            "pct_65_mas_proy": round(100 * p65 / ptot, 2),
            "pct_80_mas_proy": round(100 * p80 / ptot, 2),
        })
proy_regional = pd.DataFrame(filas)

# indice de presion de salud (2035): z(pct_65_mas 2024) + z(pct_80_mas 2024) + z(delta pct_65_mas 2024->2035)
base = ind_region.rename(columns={"region": "region_id"})[["region_id", "region_nombre", "pct_65_mas", "pct_80_mas"]]
p2035 = proy_regional[proy_regional.anio == 2035][["region_id", "pct_65_mas_proy"]]
comb = base.merge(p2035, on="region_id")
comb["delta_pct_65_mas_2024_2035"] = comb["pct_65_mas_proy"] - comb["pct_65_mas"]

def zscore(s):
    return (s - s.mean()) / s.std(ddof=0)

comb["indice_demanda_salud"] = round(
    zscore(comb["pct_65_mas"]) + zscore(comb["pct_80_mas"]) + zscore(comb["delta_pct_65_mas_2024_2035"]), 3
)
comb = comb.sort_values("indice_demanda_salud", ascending=False)
comb.to_csv(DP / "kpi_indice_demanda_salud_region.csv", index=False)
proy_regional.to_csv(DP / "kpi_proyeccion_regional.csv", index=False)

print(proy_regional[proy_regional.anio == 2035].sort_values("pct_65_mas_proy", ascending=False).to_string(index=False))
print("\nÍndice de presión de salud (top 5):")
print(comb.head(5)[["region_nombre", "pct_65_mas", "pct_80_mas", "delta_pct_65_mas_2024_2035", "indice_demanda_salud"]].to_string(index=False))

# =============================================================================
# 4) Urbanizacion vs envejecimiento (comuna)
# =============================================================================
print("\n4) kpi_urbanizacion_envejecimiento.csv ...")
ind_comuna = pd.read_csv(DP / "indicadores_comuna.csv")
sub = ind_comuna[ind_comuna.pob_total >= 500].copy()  # evita ruido de comunas minusculas
pearson = sub["pct_urbano"].corr(sub["pct_65_mas"], method="pearson")
spearman = sub["pct_urbano"].corr(sub["pct_65_mas"], method="spearman")
sub[["region_nombre", "comuna_nombre", "pob_total", "pct_urbano", "pct_65_mas"]].to_csv(
    DP / "kpi_urbanizacion_envejecimiento.csv", index=False
)
print(f"   Pearson r = {pearson:.3f} | Spearman rho = {spearman:.3f} (n={len(sub)} comunas, pob>=500)")

print("\nListo. KPIs escritos en:", DP)
