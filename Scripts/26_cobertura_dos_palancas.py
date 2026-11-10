"""
KPI 1.1, síntesis de las causas: dos palancas (informalidad y participación laboral) explican casi toda la diferencia de cobertura
entre las 16 regiones. Ejecutar DESPUÉS de Scripts/25_explorar_causas.py (usa sus columnas de la ENE).

Modelo descriptivo (mínimos cuadrados, n = 16): cobertura 2024 = a + b·informalidad + c·participación. Con 16 regiones es una
asociación, no una causa: sirve para resumir, no para predecir. Se agregan las correlaciones parciales (controlando la informalidad)
de los demás factores candidatos, para mostrar que no aportan información propia.

Fuentes (Data processed/):
  - kpi_cobertura_regiones.csv        cobertura_2024 (cotizantes / pob. 15-64, Censo 2024), informalidad_ene y participacion_ene
                                      (ENE, nov-ene 2023-24), independientes y rama_A (Censo 2024), participacion_mujeres_censo
  - afiliados_por_region_edad.csv     afiliados a AFP por región y tramo de edad, diciembre 2024 (Superintendencia de Pensiones)
  - cotizantes_por_region.csv         cotizantes de diciembre 2024 por región
  - sp_ingreso_imponible_region.csv   ingreso imponible promedio 2024 por región

Salidas (Data processed/):
  - kpi_cobertura_dos_palancas.csv          una fila por región (16): cobertura, las dos palancas, cobertura esperada por el modelo,
        residuo, palanca(s) desfavorable(s) frente a Chile (al menos 1 punto peor), afiliados menores de 65, cotizantes y afiliados que no cotizan
  - kpi_cobertura_dos_palancas_modelo.csv   una fila por indicador: R² de cada modelo, coeficientes, valores p y correlaciones parciales

Nota: «afiliados que no cotizan» = afiliados de menos de 65 años − cotizantes (todas las edades; los cotizantes de 65+ son pocos,
así que la cifra es un mínimo). Se excluyen los afiliados de 65+ (en su mayoría pensionados) y los de edad sin información.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DP = ROOT / "Data processed"
FECHA_AFILIADOS, ANIO = "2024-12-01", 2024
PALANCAS = ["informalidad_ene", "participacion_ene"]
UMBRAL_PP = 1.0  # puntos frente a Chile para marcar una palanca como desfavorable
OTROS = {  # factor candidato -> nombre corto (correlación parcial con la cobertura, controlando la informalidad)
    "independientes": "Ocupados independientes",
    "rama_A": "Ocupados en agricultura y pesca",
    "participacion_mujeres_censo": "Participación laboral de las mujeres",
    "cotizantes_sobre_afiliados": "Cotizantes ÷ afiliados",
    "ingreso_imponible": "Ingreso imponible promedio",
}


def tabla_regional() -> tuple[pd.DataFrame, pd.Series]:
    reg = pd.read_csv(DP / "kpi_cobertura_regiones.csv")
    nac = reg[reg.region_id == 0].iloc[0]
    r = reg[reg.region_id > 0][["region_id", "region_nombre", "cobertura_2024", *PALANCAS, "independientes", "rama_A",
                                "participacion_mujeres_censo"]].copy()
    af = pd.read_csv(DP / "afiliados_por_region_edad.csv")
    af = af[(af.fecha == FECHA_AFILIADOS) & af.region_id.notna() & ~af.tramo_edad.isin(["65 y más", "S/I"])]
    cot = pd.read_csv(DP / "cotizantes_por_region.csv")
    cot = cot[(cot.anio == ANIO) & cot.region_id.notna()].set_index("region_id").cotizantes
    ing = pd.read_csv(DP / "sp_ingreso_imponible_region.csv")
    ing = ing[ing.anio == ANIO].set_index("region_id").ingreso_promedio_nom
    r["afiliados_menores_65"] = r.region_id.map(af.groupby("region_id").afiliados.sum())
    r["cotizantes"] = r.region_id.map(cot)
    r["afiliados_sin_cotizar"] = r.afiliados_menores_65 - r.cotizantes
    r["cotizantes_sobre_afiliados"] = 100 * r.cotizantes / r.afiliados_menores_65
    r["ingreso_imponible"] = r.region_id.map(ing)
    assert len(r) == 16 and not r.isna().any().any(), r[r.isna().any(axis=1)]
    return r, nac


def _residuo(y, x):
    X = sm.add_constant(x)
    return y - X @ np.linalg.lstsq(X, y, rcond=None)[0]


def main():
    r, nac = tabla_regional()
    filas = []
    m1 = sm.OLS(r.cobertura_2024, sm.add_constant(r[["informalidad_ene"]])).fit()
    m2 = sm.OLS(r.cobertura_2024, sm.add_constant(r[PALANCAS])).fit()
    filas += [{"indicador": "r2_solo_informalidad", "valor": m1.rsquared},
              {"indicador": "r2_dos_palancas", "valor": m2.rsquared},
              {"indicador": "r2_ajustado_dos_palancas", "valor": m2.rsquared_adj},
              {"indicador": "corr_entre_palancas", "valor": r[PALANCAS].corr().iloc[0, 1]},
              {"indicador": "n", "valor": len(r)}]
    for k in ["const", *PALANCAS]:
        filas += [{"indicador": f"coef_{k}", "valor": m2.params[k]}, {"indicador": f"p_{k}", "valor": m2.pvalues[k]}]
    e_cob = _residuo(r.cobertura_2024.values, r[["informalidad_ene"]].values)
    for k in OTROS:
        filas.append({"indicador": f"r_{k}", "valor": stats.pearsonr(r[k], r.cobertura_2024)[0]})
        filas.append({"indicador": f"r_parcial_{k}", "valor": np.corrcoef(e_cob, _residuo(r[k].values, r[["informalidad_ene"]].values))[0, 1]})
    modelo = pd.DataFrame(filas).round(4)

    r["cobertura_esperada"] = m2.fittedvalues.round(2)
    r["residuo"] = (r.cobertura_2024 - r.cobertura_esperada).round(2)
    # palanca desfavorable = al menos UMBRAL_PP puntos peor que Chile (diferencias menores están dentro del ruido de la encuesta)
    informal = r.informalidad_ene >= nac.informalidad_ene + UMBRAL_PP
    poca_part = r.participacion_ene <= nac.participacion_ene - UMBRAL_PP
    r["palanca"] = np.select([informal & poca_part, informal, poca_part], ["Ambas", "Informalidad", "Participación"], "Ninguna")
    r = r.drop(columns="ingreso_imponible").round(2)
    r.to_csv(DP / "kpi_cobertura_dos_palancas.csv", index=False)
    modelo.to_csv(DP / "kpi_cobertura_dos_palancas_modelo.csv", index=False)
    print(modelo.to_string(index=False))
    print(r.sort_values("residuo").to_string(index=False))


if __name__ == "__main__":
    main()
