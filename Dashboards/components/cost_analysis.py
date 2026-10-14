"""Motor del análisis del KPI 2.1 "costo real por adulto mayor" (sin Streamlit ni lectura de archivos).

Serie histórica (pesos reales de 2025, país):
  - Costo público = gasto del Gobierno Central en 'Edad avanzada' (DIPRES, COFOG 7102), repartido en
      PGU            (Pensión Garantizada Universal, desde 2022),
      PBS/APS vejez  (Pilar Solidario previo a la PGU y remanente),
      Resto          = Edad avanzada - PGU - PBS/APS (DIPRES no lo desglosa en la tabla usada: sistema antiguo y otros).
  - Beneficios de vejez = PGU + PBS vejez + APS vejez (promedio del año). Una persona podría tener más de uno: la
    cobertura es un tope superior.
  - Comparación con el ingreso: 10 % (cotización obligatoria para pensión) del ingreso mediano de los ocupados (INE, ESI).
La PGU de 2022 no viene abierta en el cierre del Pilar Solidario: se obtiene como Total - (PBS + APS) y, antes de 2022, vale 0.

Proyección 2025-2050: población INE; el costo del Pilar por persona de 65+ se mantiene en términos reales salvo el alza de
la PGU a $250.000 (Ley 21.735); el 'Resto' queda constante en total (sistema antiguo que no crece) o crece con la población 65+;
el PIB real crece a `crec_pib` y el ingreso mediano real crece como el PIB per cápita.
"""
import numpy as np
import pandas as pd

CARGA_MAX = 0.10   # cotización obligatoria para pensión: 10 % del sueldo
MESES = 12
ANIO_PGU = 2022    # la PGU parte en febrero de 2022
ANIO_BASE = 2025
ANIO_FIN = 2050
_INVALIDEZ_Y_VEJEZ = ["APS invalidez", "APS vejez", "PBS invalidez", "PBS vejez"]


def _pilar_por_tipo(pilar: pd.DataFrame, col: str) -> pd.DataFrame:
    t = pilar.pivot(index="anio", columns="tipo_beneficio", values=col)
    resid = t["Total"] - t[_INVALIDEZ_Y_VEJEZ].sum(axis=1)
    t["PGU"] = t["PGU"].fillna(resid).where(t.index >= ANIO_PGU, 0.0)
    return t


def serie_historica(gasto: pd.DataFrame, pib: pd.DataFrame, pop: pd.DataFrame, nac: pd.DataFrame, pilar: pd.DataFrame) -> pd.DataFrame:
    """Una fila por año (pesos de 2025). gasto = gasto_proteccion_social.csv; pib = macro_pib_anual.csv;
    pop = proyeccion_envejecimiento_pais.csv; nac = kpi_pc_nacional.csv; pilar = pgu_pbs_aps_nacional_anual.csv."""
    ea = gasto[gasto.categoria == "Edad avanzada"].set_index("anio")
    pib, pop, nac = pib.set_index("anio"), pop.set_index("anio"), nac.set_index("anio")
    nom, nb = _pilar_por_tipo(pilar, "monto_nominal_mm"), _pilar_por_tipo(pilar, "n_promedio_beneficios")
    anios = [a for a in ea.index if a in pib.index and a in pop.index and a in nac.index and a in nom.index]
    d = pd.DataFrame(index=pd.Index(anios, name="anio"))
    dfl = nac.deflactor_2025.reindex(anios)
    d["pob_65"], d["pob_total"], d["pob_15_64"] = (pop.loc[anios, c] for c in ("pob_65_mas", "pob_total", "pob_15_64"))
    d["gasto"] = ea.loc[anios, "gasto_mm_2025"] * 1e6
    d["pct_pib"] = ea.loc[anios, "pct_pib"]
    d["pgu"] = nom.loc[anios, "PGU"] * dfl * 1e6
    d["pbs_aps"] = (nom.loc[anios, "PBS vejez"] + nom.loc[anios, "APS vejez"]) * dfl * 1e6
    d["resto"] = d.gasto - d.pgu - d.pbs_aps
    d["costo_65"] = d.gasto / d.pob_65
    for c in ("pgu", "pbs_aps", "resto"):
        d[f"{c}_65"] = d[c] / d.pob_65
    d["pilar_65"] = d.pgu_65 + d.pbs_aps_65
    d["beneficios"] = nb.loc[anios, "PGU"] + nb.loc[anios, "PBS vejez"] + nb.loc[anios, "APS vejez"]
    d["cobertura"] = d.beneficios / d.pob_65
    d["monto_por_beneficio"] = (d.pgu + d.pbs_aps) / d.beneficios
    d["pib_pc_real"] = pib.loc[anios, "pib_real_mm_2018"] * 1e6 / d.pob_total
    d["costo_pct_pib_pc"] = 100 * (ea.loc[anios, "gasto_corriente_mm"] * 1e6 / d.pob_65) / (pib.loc[anios, "pib_corriente_mm"] * 1e6 / d.pob_total)
    d["mediana_mensual"] = nac.loc[anios, "ing_ocupados_mediano_real25"]
    d["ocupados"] = nac.loc[anios, "ocupados_ond"]
    return _derivados(d)


def _derivados(d: pd.DataFrame) -> pd.DataFrame:
    """Comparación con el ingreso: aporte anual del 10 % de un ocupado mediano, trabajadores necesarios y carga requerida."""
    d["aporte_10"] = CARGA_MAX * MESES * d.mediana_mensual
    d["razon_necesaria"] = d.costo_65 / d.aporte_10              # ocupados medianos al 10 % que cubrirían a una persona 65+
    d["ocupados_por_65"] = d.ocupados / d.pob_65
    d["carga_requerida"] = d.gasto / (d.ocupados * MESES * d.mediana_mensual)   # fracción del sueldo mediano
    return d


def proyeccion(h: pd.DataFrame, pop: pd.DataFrame, params: pd.DataFrame, crec_pib: float = 0.02,
               resto: str = "constante", pgu_250: bool = True) -> pd.DataFrame:
    """2025-2050 a partir del último año de `h`. resto = 'constante' (total fijo) | 'crece' (con la población 65+)."""
    pop, fp = pop.set_index("anio"), params.set_index("anio").factor_costo_pgu
    b = h.loc[ANIO_BASE]
    anios = np.arange(ANIO_BASE, ANIO_FIN + 1)
    dt = anios - ANIO_BASE
    d = pd.DataFrame(index=pd.Index(anios, name="anio"))
    d["pob_65"], d["pob_total"], d["pob_15_64"] = (pop.loc[anios, c].values for c in ("pob_65_mas", "pob_total", "pob_15_64"))
    factor = fp.reindex(anios).fillna(1.0).values if pgu_250 else 1.0
    d["pilar"] = b.pilar_65 * factor * d.pob_65
    d["resto"] = b.resto if resto == "constante" else b.resto_65 * d.pob_65
    d["gasto"] = d.pilar + d.resto
    d["costo_65"] = d.gasto / d.pob_65
    d["pct_pib"] = b.pct_pib * (d.gasto / b.gasto) / (1 + crec_pib) ** dt
    pc = ((1 + crec_pib) ** dt) * (b.pob_total / d.pob_total)      # PIB per cápita real relativo a 2025
    d["mediana_mensual"] = b.mediana_mensual * pc
    d["ocupados"] = b.ocupados * d.pob_15_64 / b.pob_15_64
    return _derivados(d)
