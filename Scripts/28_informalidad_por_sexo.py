"""
KPI 1.1, un descarte: ¿la brecha de informalidad entre mujeres y hombres se relaciona con la cobertura? No (n = 16). Ejecutar DESPUÉS de
Scripts/25_explorar_causas.py (usa kpi_cobertura_regiones.csv).

Fuentes:
  - Data raw/_external/ine_ene_regional/ene_regional_tasa_informal_por_sexo.csv   tasa de informalidad por trimestre móvil, región y sexo
        (INE, Encuesta Nacional de Empleo, serie INF_TOI_P2017, proyecciones base 2017). Se toma el trimestre nov-ene 2023-24 (código 2023-V12),
        el mismo de la informalidad del resto del KPI; el total coincide con `informalidad_ene` de kpi_cobertura_regiones.csv (se verifica).
  - Data processed/kpi_cobertura_regiones.csv   cobertura_2024, cotizantes, regiones prioritarias (prioridad_brecha_perdida)

Salidas (Data processed/):
  - kpi_cobertura_informalidad_sexo.csv          una fila por región (16): informalidad total, de hombres y de mujeres, brecha (mujeres − hombres,
        en puntos), cobertura 2024, cotizantes y su peso, y si es prioritaria
  - kpi_cobertura_informalidad_sexo_resumen.csv  indicador, valor: correlaciones (Pearson, valor p) de la informalidad por sexo y de la brecha con la
        cobertura, y el promedio de la brecha en las regiones prioritarias y en las demás
"""
from pathlib import Path

import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DP = ROOT / "Data processed"
CSV = ROOT / "Data raw" / "_external" / "ine_ene_regional" / "ene_regional_tasa_informal_por_sexo.csv"
SERIE, TRIMESTRE = "INF_TOI_P2017", "2023-V12"  # nov-ene 2023-24
ID_REGION = {"CHL%02d" % i: i for i in range(1, 17)}  # el código de la región termina en su número (CHL15 = Arica y Parinacota, CHL16 = Ñuble)
SEXO = {"_T": "informalidad", "M": "informalidad_hombres", "F": "informalidad_mujeres"}


def tabla() -> pd.DataFrame:
    raw = pd.read_csv(CSV, encoding="utf-8-sig")
    raw = raw[(raw.DTI_CL_INDICADOR == SERIE) & (raw.DTI_CL_TRIMESTRE_MOVIL == TRIMESTRE)]
    raw = raw.assign(region_id=raw.DTI_CL_REGION.map(ID_REGION | {"_T": 0}), col=raw.DTI_CL_SEXO.map(SEXO))
    inf = raw.pivot(index="region_id", columns="col", values="Value")
    reg = pd.read_csv(DP / "kpi_cobertura_regiones.csv").set_index("region_id")
    # el total debe ser la misma cifra que ya usa el KPI (otra descarga del mismo explorador del INE)
    assert (inf["informalidad"] - reg.loc[inf.index, "informalidad_ene"]).abs().max() < 0.001
    d = inf.loc[1:].join(reg[["region_nombre", "cobertura_2024", "cotizantes_ref", "peso_cotizantes_pct", "prioridad_brecha_perdida"]])
    d["brecha_mujeres_hombres"] = d.informalidad_mujeres - d.informalidad_hombres
    d["prioritaria"] = d.prioridad_brecha_perdida.notna()
    d = d.rename(columns={"cotizantes_ref": "cotizantes", "peso_cotizantes_pct": "share_cotizantes_pct"})
    assert len(d) == 16 and not d.drop(columns="prioridad_brecha_perdida").isna().any().any()
    return d.reset_index()[["region_id", "region_nombre", "informalidad", "informalidad_hombres", "informalidad_mujeres", "brecha_mujeres_hombres",
                            "cobertura_2024", "cotizantes", "share_cotizantes_pct", "prioritaria"]]


def main():
    d = tabla()
    filas = [{"indicador": "n", "valor": len(d)}]
    for col in ["informalidad", "informalidad_hombres", "informalidad_mujeres", "brecha_mujeres_hombres"]:
        r, p = stats.pearsonr(d[col], d.cobertura_2024)
        filas += [{"indicador": f"r_{col}", "valor": r}, {"indicador": f"p_{col}", "valor": p}]
    rho, p_rho = stats.spearmanr(d.brecha_mujeres_hombres, d.cobertura_2024)
    filas += [{"indicador": "rho_brecha_mujeres_hombres", "valor": rho}, {"indicador": "p_rho_brecha_mujeres_hombres", "valor": p_rho}]
    # sin Antofagasta y Atacama (las dos brechas más grandes): ¿depende la conclusión de ellas?
    sin = d[~d.region_id.isin(d.nlargest(2, "brecha_mujeres_hombres").region_id)]
    filas.append({"indicador": "r_brecha_sin_las_2_mayores", "valor": stats.pearsonr(sin.brecha_mujeres_hombres, sin.cobertura_2024)[0]})
    for col in ["brecha_mujeres_hombres", "informalidad_hombres", "informalidad_mujeres"]:
        filas += [{"indicador": f"{col}_prioritarias", "valor": d[d.prioritaria][col].mean()},
                  {"indicador": f"{col}_otras", "valor": d[~d.prioritaria][col].mean()}]
    resumen = pd.DataFrame(filas).round(4)
    d.round(4).to_csv(DP / "kpi_cobertura_informalidad_sexo.csv", index=False)
    resumen.to_csv(DP / "kpi_cobertura_informalidad_sexo_resumen.csv", index=False)
    print(resumen.to_string(index=False))
    print(d.sort_values("brecha_mujeres_hombres").round(1).to_string(index=False))


if __name__ == "__main__":
    main()
