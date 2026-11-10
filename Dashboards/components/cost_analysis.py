"""Motor del análisis del KPI 2.1 "costo real por adulto mayor" (sin Streamlit ni lectura de archivos).

Serie histórica (pesos reales de 2025, país):
  - Costo público = gasto del Gobierno Central en 'Edad avanzada' (DIPRES, COFOG 7102), repartido en
      PGU            (Pensión Garantizada Universal, desde 2022),
      PBS/APS vejez  (Pilar Solidario previo a la PGU y remanente),
      Resto          = Edad avanzada - PGU - PBS/APS (DIPRES no lo desglosa en la tabla usada: sistema antiguo y otros).
  - Beneficios de vejez = PGU + PBS vejez + APS vejez (promedio del año). Una persona podría tener más de uno: la
    cobertura es un tope superior.
  - Indicador principal: costo por persona 65+ como % del PIB per cápita (corriente / corriente: no depende del deflactor).
    El costo "real" usa el IPC (las pensiones se reajustan por IPC); el PIB real encadenado usa el deflactor del PIB, que subió
    mucho más (2016-2025: +68 % vs +51 % del IPC), por eso un índice "costo real vs PIB per cápita real" no es comparable.
  - Comparación con el ingreso: pago plano por ocupado (gasto / ocupados) frente al 10 % (cotización obligatoria para pensión) del
    ingreso mediano o promedio de los ocupados (INE, ESI); la base se elige con `base`.
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


def serie_historica(gasto: pd.DataFrame, pib: pd.DataFrame, pop: pd.DataFrame, nac: pd.DataFrame, pilar: pd.DataFrame,
                    base: str = "mediana") -> pd.DataFrame:
    """Una fila por año (pesos de 2025). gasto = gasto_proteccion_social.csv; pib = macro_pib_anual.csv;
    pop = proyeccion_envejecimiento_pais.csv; nac = kpi_pc_nacional.csv; pilar = pgu_pbs_aps_nacional_anual.csv.
    base = 'mediana' | 'promedio': ingreso de los ocupados usado en la comparación."""
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
    d["media_mensual"] = nac.loc[anios, "ing_ocupados_medio_real25"]
    d["ingreso_mensual"] = d["mediana_mensual" if base == "mediana" else "media_mensual"]
    d["ocupados"] = nac.loc[anios, "ocupados_ond"]
    d["defl_ipc"] = nac.loc[anios, "deflactor_2025"]                       # pesos de t -> pesos de 2025
    d["defl_pib"] = pib.loc[anios, "pib_corriente_mm"] / pib.loc[anios, "pib_real_mm_2018"]
    return _derivados(d)


def _derivados(d: pd.DataFrame) -> pd.DataFrame:
    """Comparación con el ingreso (columna `ingreso_mensual`, mediana o promedio de los ocupados): aporte anual del 10 % de un
    ocupado típico, ocupados necesarios, pago plano por ocupado y carga requerida (pago plano / ingreso)."""
    d["aporte_10"] = CARGA_MAX * MESES * d.ingreso_mensual
    d["razon_necesaria"] = d.costo_65 / d.aporte_10              # ocupados típicos al 10 % que cubrirían a una persona 65+
    d["ocupados_por_65"] = d.ocupados / d.pob_65
    d["pago_plano"] = d.gasto / d.ocupados / MESES                # pesos al mes que pagaría cada ocupado si el gasto se repartiera por igual
    d["carga_requerida"] = d.pago_plano / d.ingreso_mensual       # ... como fracción del ingreso típico
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
    d["ingreso_mensual"] = b.ingreso_mensual * pc
    d["costo_pct_pib_pc"] = d.pct_pib * d.pob_total / d.pob_65   # costo por persona 65+ como % del PIB per cápita
    d["ocupados"] = b.ocupados * d.pob_15_64 / b.pob_15_64
    return _derivados(d)


def _piezas_pilar(h: pd.DataFrame, pr: pd.DataFrame, a: int) -> tuple:
    """(costo del Pilar, personas 65+, beneficios por persona 65+, monto por beneficio) de un año: observado en `h` o escenario en `pr`.
    En el escenario la cobertura queda como en el último año observado y el monto por beneficio es lo que resta (incluye el alza de la PGU)."""
    ult = int(h.index.max())
    if a <= ult:
        r = h.loc[a]
        return float(r.pgu + r.pbs_aps), float(r.pob_65), float(r.cobertura), float(r.monto_por_beneficio)
    r, cob = pr.loc[a], float(h.loc[ult].cobertura)
    return float(r.pilar), float(r.pob_65), cob, float(r.pilar) / (float(r.pob_65) * cob)


PIEZAS_PILAR = (("pob_65", "Personas de 65+"), ("cobertura", "Beneficios por persona de 65+"), ("monto", "Monto por beneficio"))


def descomponer_pilar(h: pd.DataFrame, pr: pd.DataFrame, a0: int, a1: int) -> dict:
    """De qué se compone el cambio del costo del Pilar Solidario de vejez (PGU + pensiones solidarias) entre dos años:
    costo = personas de 65+ × beneficios por persona de 65+ (cobertura) × monto por beneficio. Descomposición logarítmica exacta: el aporte
    de cada pieza es (costo1 - costo0) x ln(razón de la pieza) / ln(costo1 / costo0), así que los aportes suman exactamente el cambio.
    h = serie_historica; pr = proyeccion (solo si a1 es posterior al último año observado). Devuelve costo0, costo1 y una lista de
    dicts (clave, nombre, razon, aporte en pesos, parte del cambio entre 0 y 1)."""
    p0, pob0, cob0, m0 = _piezas_pilar(h, pr, a0)
    p1, pob1, cob1, m1 = _piezas_pilar(h, pr, a1)
    razones = {"pob_65": pob1 / pob0, "cobertura": cob1 / cob0, "monto": m1 / m0}
    L = (p1 - p0) / np.log(p1 / p0)
    partes = [dict(clave=k, nombre=n, razon=razones[k], aporte=L * np.log(razones[k]), parte=L * np.log(razones[k]) / (p1 - p0)) for k, n in PIEZAS_PILAR]
    return dict(a0=a0, a1=a1, costo0=p0, costo1=p1, partes=partes)


def indices_costo(h: pd.DataFrame, pr: pd.DataFrame, a0: int, a1: int) -> pd.DataFrame:
    """Índice (a0 = 100) de lo que se compara en «qué sube más rápido»: costo del Pilar y sus tres piezas (monto por beneficio, personas de 65+ y
    cobertura = beneficios por persona de 65+; índice del costo = producto de los tres / 100², exacto) y el PIB real.
    Un período observado (a1 <= último año de `h`) usa el PIB real encadenado de `h`; uno futuro (a0 >= último año) usa solo el escenario `pr`,
    porque sus PIB están en precios distintos y no se pueden empalmar."""
    ult = int(h.index.max())
    futuro = a0 >= ult
    filas = {}
    for a in range(a0, a1 + 1):
        p, pob, cob, m = _piezas_pilar(h, pr, a)
        pib = float(pr.loc[a].gasto / (pr.loc[a].pct_pib / 100)) if futuro else float(h.loc[a].pib_pc_real * h.loc[a].pob_total)
        filas[a] = dict(pilar=p, monto=m, pob_65=pob, cobertura=cob, pib=pib)
    d = pd.DataFrame(filas).T
    return 100 * d / d.iloc[0]


RESTO_ESCENARIO = ("no", "constante", "crece")   # el «resto» no se proyecta: se omite o se agrega con un supuesto explícito


def gasto_total_vejez(h: pd.DataFrame, carga: pd.DataFrame, pilar: pd.DataFrame, pib: pd.DataFrame, nac: pd.DataFrame,
                      resto: str = "no") -> pd.DataFrame:
    """Costo total del Estado en la vejez: une el Pilar Solidario (KPI 2.1 y 2.2) con el gasto del Gobierno Central en «Edad avanzada».
    Una fila por año: observado (h, 2016-2025) y escenario (carga = financiamiento.proyeccion_carga, 2026 en adelante). Pesos reales de 2025.
      - pilar_vejez:      PGU + PBS/APS de vejez (la base de la descomposición del KPI 2.1; 6,25 billones en 2025).
      - pilar_invalidez:  PBS/APS de invalidez. No se suma al total: no se sabe si DIPRES lo cuenta en «Edad avanzada» (COFOG 7102) o en
                          «Enfermedad e incapacidad» (7101). Pilar total = vejez + invalidez = el 2,07 % del PIB del KPI 2.2.
      - resto:            «Edad avanzada» − Pilar de vejez (residual: sistema antiguo y otros, DIPRES no lo abre). En el escenario solo si
                          `resto` = 'constante' (total fijo) o 'crece' (con la población 65+), que son supuestos, no proyecciones.
      - aporte_fapp:      aporte del Estado al FAPP (Ley 21.735), solo escenario, lo que traiga `carga` (casilla del KPI 2.2).
      - total:            observado = «Edad avanzada» (DIPRES); escenario = Pilar de vejez + aporte FAPP (+ resto si se supone).
      - *_pct:            % del PIB. Observado: montos nominales / PIB corriente; escenario: monto real / PIB real de `carga` (mismo método del KPI 2.2).
    Precios: el gasto de DIPRES viene en pesos de 2025 de la propia DIPRES; el Pilar se deflacta con el IPC (kpi_pc_nacional). Los deflactores
    difieren a lo más 0,4 % (2016), así que el residual mezcla ambos dentro de ese margen; los % del PIB no dependen del deflactor."""
    assert resto in RESTO_ESCENARIO
    nom = pilar.pivot(index="anio", columns="tipo_beneficio", values="monto_nominal_mm")
    pibc = pib.set_index("anio").pib_corriente_mm
    dfl = nac.set_index("anio").deflactor_2025
    anios = list(h.index)
    o = pd.DataFrame(index=pd.Index(anios, name="anio"))
    o["pob_65"] = h.pob_65
    o["pilar_vejez"] = h.pgu + h.pbs_aps
    o["pilar_invalidez"] = (nom["PBS invalidez"] + nom["APS invalidez"]).reindex(anios) * dfl.reindex(anios) * 1e6
    o["resto"] = h.resto
    o["aporte_fapp"] = 0.0
    o["total"] = h.gasto
    o["total_pct"] = h.pct_pib
    vej_nom = h.pgu / h.defl_ipc + h.pbs_aps / h.defl_ipc            # pesos corrientes
    o["pilar_vejez_pct"] = 100 * vej_nom / (pibc.reindex(anios) * 1e6)
    o["pilar_invalidez_pct"] = 100 * (nom["PBS invalidez"] + nom["APS invalidez"]).reindex(anios) / pibc.reindex(anios)
    o["pilar_pct"] = o.pilar_vejez_pct + o.pilar_invalidez_pct
    o["resto_pct"] = o.total_pct - o.pilar_vejez_pct
    o["carga_pct"] = o.pilar_pct
    o["escenario"] = False
    b = h.loc[ANIO_BASE]
    c = carga[carga.index > ANIO_BASE]
    e = pd.DataFrame(index=c.index)
    e["pob_65"] = c.pob_65
    e["pilar_vejez"], e["pilar_invalidez"], e["aporte_fapp"] = c.pilar_vejez, c.pilar_invalidez, c.aporte_fapp
    e["resto"] = {"no": np.nan, "constante": b.resto, "crece": b.resto_65}[resto] * (c.pob_65 if resto == "crece" else 1.0)
    e["total"] = e.pilar_vejez + e.aporte_fapp + e.resto.fillna(0.0)
    for col in ("pilar_vejez", "pilar_invalidez", "resto", "aporte_fapp", "total"):
        e[f"{col}_pct"] = 100 * e[col] / c.pib_real25
    e["pilar_pct"], e["carga_pct"] = c.pilar_pct_pib, c.carga_pct_pib
    e["escenario"] = True
    d = pd.concat([o, e])
    d["costo_65"] = d.total / d.pob_65
    return d
