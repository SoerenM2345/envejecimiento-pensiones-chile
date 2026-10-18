"""Motor del análisis del KPI 2.2 "financiamiento dedicado" (sin Streamlit ni lectura de archivos).

Pregunta: ¿cuánto pesa el Pilar Solidario + PGU en el PIB, quién lo financia, y cuánto aguantan las reservas?

Peso fiscal (país, pesos reales de 2025):
  - Pilar = PGU + PBS/APS de vejez (proyectado como en el KPI 2.1: costo por persona 65+ constante en términos reales, más
    el alza de la PGU a $250.000 de la Ley 21.735, por la población 65+ del INE) + PBS/APS de invalidez (constante real).
  - Aporte del Estado al FAPP (Ley 21.735, millones de UTM por año desde 2028): costo nuevo, se suma a la carga.
  - % del PIB: el valor de 2025 es el del ratio 1 original (monto nominal / PIB corriente); los años siguientes escalan ese
    valor por el cambio del costo real y por el crecimiento real del PIB.

Reservas (stock al 31-dic-2025): cartera propia del FRP (sin los US$ 200 M ya transferidos al FAPP, para no contarlos dos veces)
y, opcional, los activos del FAPP. Se supone que la reserva rinde `r_real` y cubre un gasto elegido:
  - 'incremento': solo el alza del gasto sobre el peso que el Pilar tenía en 2025 (el PIB en pesos × 2,07 %);
  - 'total': todo el gasto del Pilar.
Saldo_t = Saldo_(t-1) × (1 + r) − gasto cubierto_t, desde 2026.
Ratio 2 «cobertura de reservas» = reserva al 31-dic-2025 / valor presente 2026-2050 del gasto cubierto, descontado a la misma tasa r
(alternativa al valor presente oficial del déficit, que no está publicado). Si es >= 1, la reserva alcanza hasta 2050; el año en
que el saldo pasa a negativo es el año de agotamiento. Supuestos (r, PIB, horizonte, aporte al FAPP): config/escenarios.yaml.
"""
import numpy as np
import pandas as pd

ANIO_BASE = 2025
ANIO_FIN = 2050
ANIO_PGU = 2022


def peso_historico(pilar: pd.DataFrame, pib: pd.DataFrame, gasto: pd.DataFrame) -> pd.DataFrame:
    """Ratio 1 original por año: Pilar 'Total' nominal / PIB corriente, y 'Edad avanzada' / PIB (DIPRES)."""
    pil = pilar[pilar.tipo_beneficio == "Total"].set_index("anio")
    pib = pib.set_index("anio")
    ea = gasto[gasto.categoria == "Edad avanzada"].set_index("anio").pct_pib
    anios = [a for a in pil.index if a in pib.index]
    d = pd.DataFrame({"anio": anios})
    d["pilar_pct_pib"] = [100 * pil.loc[a, "monto_nominal_mm"] / pib.loc[a, "pib_corriente_mm"] for a in anios]
    d["edad_avanzada_pct_pib"] = [ea.get(a) for a in anios]
    return d


def proyeccion_carga(h: pd.DataFrame, pilar: pd.DataFrame, pib: pd.DataFrame, pop: pd.DataFrame, params: pd.DataFrame,
                     aporte_fapp: pd.DataFrame, crec_pib: float = 0.02, pgu_250: bool = True, con_fapp: bool = True,
                     anio_fin: int = ANIO_FIN) -> pd.DataFrame:
    """2025-anio_fin (config/escenarios.yaml: horizonte_proyeccion). h = cost_analysis.serie_historica; pilar = pgu_pbs_aps_nacional_anual; pib = macro_pib_anual;
    pop = proyeccion_envejecimiento_pais; params = kpi_pc_parametros_reforma; aporte_fapp = fapp_aporte_fiscal.
    Montos en pesos reales de 2025 (pesos, no millones). Columnas: pilar_vejez, pilar_invalidez, aporte_fapp, carga,
    pib_real25, pilar_pct_pib, carga_pct_pib, incremento (carga que excede el peso del Pilar de 2025)."""
    b = h.loc[ANIO_BASE]
    pop, fp = pop.set_index("anio"), params.set_index("anio").factor_costo_pgu
    nom = pilar[pilar.anio == ANIO_BASE].set_index("tipo_beneficio").monto_nominal_mm
    # deflactor 2025 = 1: el monto nominal de 2025 ya está en pesos de 2025
    invalidez = (nom["Total"] - nom.get("PGU", 0.0) - nom.get("PBS vejez", 0.0) - nom.get("APS vejez", 0.0)) * 1e6
    pib25 = pib.set_index("anio").loc[ANIO_BASE, "pib_corriente_mm"] * 1e6
    anios = np.arange(ANIO_BASE, anio_fin + 1)
    dt = anios - ANIO_BASE
    d = pd.DataFrame(index=pd.Index(anios, name="anio"))
    d["pob_65"] = pop.loc[anios, "pob_65_mas"].values
    factor = fp.reindex(anios).fillna(1.0).values if pgu_250 else 1.0
    d["pilar_vejez"] = b.pilar_65 * factor * d.pob_65
    d["pilar_invalidez"] = invalidez
    ap = aporte_fapp.set_index("anio").aporte_mm_2025 * 1e6
    d["aporte_fapp"] = ap.reindex(anios).fillna(0.0).values if con_fapp else 0.0
    d["pilar"] = d.pilar_vejez + d.pilar_invalidez
    d["carga"] = d.pilar + d.aporte_fapp
    d["pib_real25"] = pib25 * (1 + crec_pib) ** dt
    d["pilar_pct_pib"] = 100 * d.pilar / d.pib_real25
    # el valor de 2025 coincide con el ratio 1 original; el resto escala con el costo real y el PIB real
    ratio25 = d.pilar.iloc[0] / pib25
    d["incremento"] = (d.carga - ratio25 * d.pib_real25).clip(lower=0.0)
    d["carga_pct_pib"] = 100 * d.carga / d.pib_real25
    return d


def trayectoria_reserva(d: pd.DataFrame, reserva0: float, r_real: float = 0.025, cubre: str = "incremento") -> tuple[pd.DataFrame, dict]:
    """Aplica una reserva `reserva0` (pesos de 2025 al 31-dic-2025) al gasto de `d` (salida de proyeccion_carga).
    Devuelve (d con gasto_cubierto y saldo, resumen). cubre = 'incremento' | 'total'."""
    d = d.copy()
    base = d.incremento if cubre == "incremento" else d.carga
    d["gasto_cubierto"] = np.where(d.index > ANIO_BASE, base, 0.0)
    saldo = [reserva0]
    for a in d.index[1:]:
        saldo.append(saldo[-1] * (1 + r_real) - d.loc[a, "gasto_cubierto"])
    d["saldo"] = saldo
    t = (d.index - ANIO_BASE).values
    vp = float((d.gasto_cubierto.values / (1 + r_real) ** t).sum())
    agot = d.index[d.saldo < 0]
    gasto25 = d.loc[ANIO_BASE, "pilar"]
    res = dict(reserva0=reserva0, vp_gasto=vp, ratio_cobertura=reserva0 / vp if vp > 0 else float("inf"),
               anio_agotamiento=int(agot[0]) if len(agot) else None, anios_gasto_2025=reserva0 / gasto25)
    return d, res


def fuentes_pilar(frp: pd.DataFrame, nac: pd.DataFrame) -> pd.DataFrame:
    """Quién pagó el Pilar en 2022-2025: retiro del FRP (dólar promedio del año) frente al gasto total del Pilar, en pesos de 2025.
    frp = frp_reserva_anual.csv; nac = kpi_pc_nacional.csv (deflactor_2025)."""
    f = frp.dropna(subset=["retiros_mm", "pilar_total_mm"]).copy()
    dfl = nac.set_index("anio").deflactor_2025.reindex(f.anio).values
    f["retiros_real"] = f.retiros_mm.values * dfl * 1e6
    f["pilar_real"] = f.pilar_total_mm.values * dfl * 1e6
    f["pct_frp"] = 100 * f.retiros_real / f.pilar_real
    return f[["anio", "retiros_real", "pilar_real", "pct_frp"]].reset_index(drop=True)


TRIM_REGIONAL = "cuarto trimestre 2024"   # el cuarto trimestre de 2024 va con el Censo 2024 (misma fecha que el KPI 1.2 regional)
ANIO_REGIONAL = 2024
_VEJEZ = ["PGU contributiva", "PGU no contributiva", "APS vejez"]


def dependencia_regional(trim: pd.DataFrame, pilar: pd.DataFrame, presion: pd.DataFrame, nac: pd.DataFrame) -> pd.DataFrame:
    """Por región (y Chile): quiénes dependen del Estado. trim = pgu_pbs_aps_region_trimestral; pilar = pgu_pbs_aps_nacional_anual;
    presion = kpi_presion_previsional_region (pob_65_mas Censo 2024, razon_soporte_previsional); nac = kpi_pc_nacional.
    - pct_sin_pension: PGU 'no contributiva' / toda la PGU (beneficiarios sin otra pensión propia).
    - beneficios_por_100: (PGU + APS vejez) por cada 100 personas 65+ (promedio mensual del trimestre).
    - peso_mes_por_65: pago mensual de vejez por persona 65+ en pesos de 2025. Los montos del informe regional no usan la misma base de
      pesos que el cierre anual; se usa solo la participación de cada región en el trimestre, aplicada al total anual nacional de 2024."""
    q = trim[(trim.trimestre == TRIM_REGIONAL) & (trim.sexo == "Total")]
    n = q.pivot(index="region_id", columns="tipo_beneficio", values="n_beneficiarios")
    m = q.pivot(index="region_id", columns="tipo_beneficio", values="monto_total_mm")
    nombre = q.drop_duplicates("region_id").set_index("region_id").region_nombre
    pr = presion.set_index("region_id")
    nom = pilar[pilar.anio == ANIO_REGIONAL].set_index("tipo_beneficio").monto_nominal_mm
    total_vejez = nom["PGU"] + nom.get("APS vejez", 0.0) + nom.get("PBS vejez", 0.0)
    dfl = nac.set_index("anio").deflactor_2025.loc[ANIO_REGIONAL]
    cuota = m[_VEJEZ].sum(axis=1) / m[_VEJEZ].sum().sum()
    r = pd.DataFrame({"region_nombre": nombre})
    r["pob_65"] = pr.pob_65_mas.reindex(r.index)
    r["n_sin_pension"] = n["PGU no contributiva"]
    r["pct_sin_pension"] = 100 * n["PGU no contributiva"] / (n["PGU contributiva"] + n["PGU no contributiva"])
    r["beneficios_por_100"] = 100 * n[_VEJEZ].sum(axis=1) / r.pob_65
    r["peso_mes_por_65"] = cuota * total_vejez * 1e6 * dfl / r.pob_65 / 12
    nc = m["PGU no contributiva"]
    pgu_nc_anual = nom["PGU"] * nc.sum() / (nc.sum() + m["PGU contributiva"].sum()) * 1e6 * dfl   # pesos de 2025, 2024
    r["costo_sin_pension"] = nc / nc.sum() * pgu_nc_anual
    r["razon_soporte"] = pr.razon_soporte_previsional.reindex(r.index)
    nac_row = dict(region_nombre="Chile", pob_65=r.pob_65.sum(), n_sin_pension=n["PGU no contributiva"].sum(),
                   pct_sin_pension=100 * n["PGU no contributiva"].sum() / (n["PGU contributiva"].sum() + n["PGU no contributiva"].sum()),
                   beneficios_por_100=100 * n[_VEJEZ].sum().sum() / r.pob_65.sum(),
                   peso_mes_por_65=total_vejez * 1e6 * dfl / r.pob_65.sum() / 12, razon_soporte=np.nan,
                   costo_sin_pension=pgu_nc_anual)
    return pd.concat([r.reset_index(), pd.DataFrame([{**nac_row, "region_id": 0}])], ignore_index=True)


def proyeccion_sin_pension(reg: pd.DataFrame, proy_reg: pd.DataFrame, anio: int) -> pd.DataFrame:
    """Escenario: personas sin pensión propia en `anio` (2035 o 2050) si cada región mantiene su tasa de 2024 (beneficiarios de la PGU
    sin otra pensión por persona 65+). proy_reg = kpi_proyeccion_regional (pob_65_mas_proy). Devuelve region_id, n_2024, n_anio."""
    q = proy_reg[proy_reg.anio == anio].set_index("region_id").pob_65_mas_proy
    r = reg[reg.region_id != 0].set_index("region_id")
    out = pd.DataFrame({"region_nombre": r.region_nombre, "n_2024": r.n_sin_pension})
    out["n_anio"] = r.n_sin_pension * q.reindex(r.index) / r.pob_65
    return out.reset_index()
