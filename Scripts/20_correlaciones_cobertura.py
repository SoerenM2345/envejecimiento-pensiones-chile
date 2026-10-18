"""
KPI 1.1 (diagnóstico): correlaciones de la cobertura previsional regional con ingreso, pobreza 65+, urbanización y
envejecimiento. Insumo de las dos analíticas de la tarjeta 1.1 (dispersión con regresión y matriz de riesgo).

Fuentes (Data processed/):
  - kpi_presion_previsional_region.csv  cotizantes_2024, pob_15_64, cobertura_previsional_pct (cotizantes 2024 / Censo 2024,
                                        la misma base que la tarjeta 1.1; script 07)
  - kpi_ingresos_region.csv             ingreso_per_capita_prom, CASEN 2022 (script 08). Trae el nombre largo de la región
                                        ('region_casen'): se une por un mapeo explícito a region_id, no por similitud de texto
  - indicadores_region.csv              pct_65_mas, pct_urbano, Censo 2024 (script 01)
  - pobreza_65_region.csv               pct_pobreza_65, CASEN 2022 (script 14); se excluye region_id 0 (Chile)

Salidas (Data processed/):
  - kpi_cobertura_correlaciones_region.csv   una fila por región (16): region_id, region_nombre, cotizantes, pob_15_64,
        cobertura_previsional_pct, share_cotizantes_pct (% del total de cotizantes con región), ingreso_per_capita_prom,
        pct_65_mas, pct_urbano, pct_pobreza_65
  - kpi_cobertura_correlaciones_resumen.csv  una fila por variable: variable, n, pearson_r, pearson_p, spearman_rho, spearman_p
  - kpi_pobreza_cobertura_region.csv         KPI 2.3 diagnóstico (16 filas): region_id, region_nombre, cobertura_previsional_pct,
        pct_pobreza_65, ic95_inf, ic95_sup, n_pobres_65 (pob. 65+ expandida CASEN × %), share_pobres_pct

Notas: n = 16 regiones, correlación no implica causalidad. Los cotizantes sin región informada quedan fuera.
"""
from pathlib import Path

import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DP = ROOT / "Data processed"

# nombre de región en CASEN 2022 -> código oficial de región
CASEN_A_REGION_ID = {
    "Región de Tarapacá": 1,
    "Región de Antofagasta": 2,
    "Región de Atacama": 3,
    "Región de Coquimbo": 4,
    "Región de Valparaíso": 5,
    "Región del Libertador Gral. Bernardo O'Higgins": 6,
    "Región del Maule": 7,
    "Región del Biobío": 8,
    "Región de La Araucanía": 9,
    "Región de Los Lagos": 10,
    "Región de Aysén del Gral. Carlos Ibáñez del Campo": 11,
    "Región de Magallanes y de la Antártica Chilena": 12,
    "Región Metropolitana de Santiago": 13,
    "Región de Los Ríos": 14,
    "Región de Arica y Parinacota": 15,
    "Región de Ñuble": 16,
}
VARIABLES = [  # (columna, nombre corto en el resumen)
    ("ingreso_per_capita_prom", "ingreso"),
    ("pct_pobreza_65", "pobreza_65"),
    ("pct_urbano", "urbano"),
    ("pct_65_mas", "pct_65_mas"),
]

# =============================================================================
# 1) Tabla regional
# =============================================================================
print("1) kpi_cobertura_correlaciones_region.csv ...")
pres = pd.read_csv(DP / "kpi_presion_previsional_region.csv")
reg = pres[["region_id", "region_nombre", "cotizantes_2024", "pob_15_64", "cobertura_previsional_pct"]].rename(
    columns={"cotizantes_2024": "cotizantes"})
reg["share_cotizantes_pct"] = round(100 * reg.cotizantes / reg.cotizantes.sum(), 2)

ing = pd.read_csv(DP / "kpi_ingresos_region.csv")
sin_mapeo = set(ing.region_casen) - set(CASEN_A_REGION_ID)
assert not sin_mapeo, f"regiones CASEN sin mapeo: {sin_mapeo}"
ing["region_id"] = ing.region_casen.map(CASEN_A_REGION_ID)

ind = pd.read_csv(DP / "indicadores_region.csv").rename(columns={"region": "region_id"})
pob = pd.read_csv(DP / "pobreza_65_region.csv")
pob = pob[pob.region_id != 0]

reg = (reg.merge(ing[["region_id", "ingreso_per_capita_prom"]], on="region_id", how="left")
          .merge(ind[["region_id", "pct_65_mas", "pct_urbano"]], on="region_id", how="left")
          .merge(pob[["region_id", "pct_pobreza_65"]], on="region_id", how="left")
          .sort_values("region_id"))
assert len(reg) == 16 and reg.region_id.is_unique, "se esperan 16 regiones"
assert not reg.isna().any().any(), f"valores faltantes:\n{reg[reg.isna().any(axis=1)]}"

reg.to_csv(DP / "kpi_cobertura_correlaciones_region.csv", index=False)
print(reg.to_string(index=False))

# =============================================================================
# 2) Correlaciones con la cobertura
# =============================================================================
print("\n2) kpi_cobertura_correlaciones_resumen.csv ...")
filas = []
for col, nombre in VARIABLES:
    r, p_r = stats.pearsonr(reg[col], reg.cobertura_previsional_pct)
    rho, p_rho = stats.spearmanr(reg[col], reg.cobertura_previsional_pct)
    filas.append({"variable": nombre, "n": len(reg), "pearson_r": round(r, 3), "pearson_p": round(p_r, 4),
                  "spearman_rho": round(rho, 3), "spearman_p": round(p_rho, 4)})
res = pd.DataFrame(filas)
res.to_csv(DP / "kpi_cobertura_correlaciones_resumen.csv", index=False)
print(res.to_string(index=False))

# =============================================================================
# 3) KPI 2.3: pobreza 65+ frente a cobertura (misma correlación que 'pobreza_65' del resumen)
# =============================================================================
print("\n3) kpi_pobreza_cobertura_region.csv ...")
pc = reg[["region_id", "region_nombre", "cobertura_previsional_pct", "pct_pobreza_65"]].merge(
    pob[["region_id", "ic95_inf", "ic95_sup", "pob_65_expandida"]], on="region_id")
pc["n_pobres_65"] = (pc.pob_65_expandida * pc.pct_pobreza_65 / 100).round(0)
pc["share_pobres_pct"] = round(100 * pc.n_pobres_65 / pc.n_pobres_65.sum(), 2)
pc = pc.drop(columns="pob_65_expandida")
assert len(pc) == 16 and not pc.isna().any().any()
pc.to_csv(DP / "kpi_pobreza_cobertura_region.csv", index=False)
print(pc.sort_values("pct_pobreza_65", ascending=False).round(2).to_string(index=False))
