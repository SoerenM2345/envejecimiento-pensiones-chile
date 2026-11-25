"""KPI 1.1, selección de las regiones críticas con dos preguntas (reemplaza la regla de rangos de docs/SHORTLIST_REGIONES.md).

La regla (sin el factor «nivel», que es redundante: las regiones de menor nivel ya son las de mayor brecha):
  Pregunta 1 (tendencia): ¿qué territorios perdieron puestos en el ranking de cobertura desde 2007?
      Ranking de los 15 territorios (Biobío y Ñuble unidos, como en kpi_cobertura_tendencia.csv), 1 = mayor cobertura, diciembre de
      2007 y de 2024. puestos_perdidos = puesto_2024 − puesto_2007 (positivo = perdió puestos). Entra si perdió puestos Y su cobertura
      2024 está bajo la de Chile. 2007 es el año de partida porque la serie salta entre 2006 y 2007 (documentado, sin explicación).
  Pregunta 2 (brecha): ¿dónde faltan más cotizantes?
      16 regiones, 2024. brecha = (cobertura de Chile − cobertura de la región) / 100 × población de 15 a 64 años, solo regiones bajo
      Chile. Se ordena de mayor a menor y entran todas hasta que la participación acumulada llega al 80 %, incluida la que la cruza.
  Selección = unión de ambas respuestas. Columna `motivo` ∈ {brecha, tendencia, ambas, ninguna}.

Salidas (Data processed/):
  - kpi_seleccion_dos_preguntas.csv   formato largo, columna `section`:
        chile          cobertura de Chile 2007 y 2024 (cambio en puntos y en %)
        ranking        un territorio por fila: puestos 2007 y 2024, puestos perdidos, cobertura, cambio, si entra por tendencia
        gap            una región bajo Chile por fila: brecha en personas, participación y acumulada, si entra por brecha
        selection      las 16 regiones: motivo de selección, brecha, población
        decomposition  las 8 regiones elegidas: aporte de cada etapa en puntos (media logarítmica) y en personas
  - kpi_seleccion_sensibilidad.csv    año de partida 2007…2018 × corte 70/80/90 %: regiones, número, % de la brecha y % de la población
La sensibilidad se informa; la regla principal no se ajusta a ella.

Uso: "Data raw/.venv/bin/python" Scripts/35_seleccion_dos_preguntas.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DP = ROOT / "Data processed"

ANIO_PARTIDA = 2007
ANIO_FINAL = 2024
CORTE = 0.80
ID_CHILE = 0
ID_BIOBIO, ID_NUBLE, ID_BIOBIO_NUBLE = 8, 16, 816
IDS_AGREGADOS = {801, 810}            # «Tarapacá y Arica y Parinacota» y «Los Lagos y Los Ríos»: agregados de apoyo, no son territorios del ranking
PRIMER_ANIO_16_REGIONES = 2018        # desde 2018 Biobío y Ñuble son dos regiones separadas
FACTORES = ["cotizacion", "participacion", "empleo"]


def territorios_del_ranking(tend: pd.DataFrame, anio: int) -> pd.DataFrame:
    """Territorios que entran al ranking de un año: 15 hasta 2017 (Biobío y Ñuble unidos), 16 desde 2018. Sin Chile ni agregados de apoyo."""
    d = tend[(tend.anio == anio) & (tend.territorio_id != ID_CHILE) & (~tend.territorio_id.isin(IDS_AGREGADOS))]
    if anio >= PRIMER_ANIO_16_REGIONES:
        d = d[d.territorio_id != ID_BIOBIO_NUBLE]
    else:
        d = d[~d.territorio_id.isin([ID_BIOBIO, ID_NUBLE])]
    return d


def ranking(tend: pd.DataFrame, partida: int, final: int = ANIO_FINAL) -> pd.DataFrame:
    """Puestos en `partida` y en `final` (1 = mayor cobertura) dentro del mismo universo de territorios que el año de partida."""
    a = territorios_del_ranking(tend, partida)
    ids = set(a.territorio_id)
    b = tend[(tend.anio == final) & (tend.territorio_id.isin(ids))]
    r = a[["territorio_id", "territorio", "cobertura_pct"]].rename(columns={"cobertura_pct": "cov_partida"}).merge(
        b[["territorio_id", "cobertura_pct"]].rename(columns={"cobertura_pct": "cov_final"}), on="territorio_id")
    r["puesto_partida"] = r.cov_partida.rank(ascending=False, method="min").astype(int)
    r["puesto_final"] = r.cov_final.rank(ascending=False, method="min").astype(int)
    r["puestos_perdidos"] = r.puesto_final - r.puesto_partida
    chile_f = float(tend[(tend.anio == final) & (tend.territorio_id == ID_CHILE)].cobertura_pct.iloc[0])
    r["bajo_chile"] = r.cov_final < chile_f
    r["entra_tendencia"] = (r.puestos_perdidos > 0) & r.bajo_chile
    r["cambio_pp"] = r.cov_final - r.cov_partida
    r["cambio_pct"] = r.cov_final / r.cov_partida * 100 - 100
    return r.sort_values("puesto_final").reset_index(drop=True)


def brecha(reg: pd.DataFrame, chile_cov: float) -> pd.DataFrame:
    """Brecha de cotizantes de las regiones bajo Chile (16 regiones; la fila 0 es Chile) con participación y acumulada."""
    d = reg[reg.region_id != ID_CHILE][["region_id", "region_nombre", "pob_15_64", "cobertura_ref"]].copy()
    d["brecha"] = np.where(d.cobertura_ref < chile_cov, (chile_cov - d.cobertura_ref) / 100 * d.pob_15_64, 0.0)
    g = d[d.brecha > 0].sort_values("brecha", ascending=False).reset_index(drop=True)
    g["participacion"] = g.brecha / g.brecha.sum()
    g["acumulada"] = g.participacion.cumsum()
    return g


def entran_por_brecha(g: pd.DataFrame, corte: float) -> set:
    """Regiones hasta que la acumulada llega al corte, incluida la que lo cruza (con tolerancia para el borde exacto)."""
    previa = g.acumulada.shift(1, fill_value=0.0)
    return set(g.loc[previa < corte - 1e-9, "region_id"])


def regiones_por_tendencia(r: pd.DataFrame) -> set:
    """Pasa de territorios a regiones: «Biobío y Ñuble» (816) vale por las dos regiones."""
    out = set()
    for tid in r.loc[r.entra_tendencia, "territorio_id"]:
        out |= {ID_BIOBIO, ID_NUBLE} if tid == ID_BIOBIO_NUBLE else {int(tid)}
    return out


def seleccion(tend: pd.DataFrame, reg: pd.DataFrame, partida: int = ANIO_PARTIDA, corte: float = CORTE):
    chile_cov = float(reg.loc[reg.region_id == ID_CHILE, "cobertura_ref"].iloc[0])
    r = ranking(tend, partida)
    g = brecha(reg, chile_cov)
    por_t, por_b = regiones_por_tendencia(r), entran_por_brecha(g, corte)
    return r, g, por_t, por_b, chile_cov


def motivo(rid: int, por_t: set, por_b: set) -> str:
    return "ambas" if rid in por_t and rid in por_b else "brecha" if rid in por_b else "tendencia" if rid in por_t else "ninguna"


def descomposicion(reg: pd.DataFrame, ids: list) -> pd.DataFrame:
    """Aporte de cada etapa (participación, empleo, cotización) a la diferencia con Chile en 2024, en puntos (media logarítmica,
    Scripts/25_explorar_causas.py) y en personas (puntos / 100 × población de 15 a 64 años). Los tres suman exacto la diferencia."""
    f = pd.read_csv(DP / "kpi_cobertura_factores_anual.csv")
    f = f[f.anio == ANIO_FINAL].set_index("territorio_id")
    ch = f.loc[ID_CHILE]
    filas = []
    for rid in ids:
        x = f.loc[rid]
        L = (x.cobertura_pct - ch.cobertura_pct) / np.log(x.cobertura_pct / ch.cobertura_pct)  # media logarítmica de las dos coberturas
        aporte = {k: L * np.log(x[k] / ch[k]) for k in ("participacion", "empleo", "cotizacion")}
        pob = float(reg.loc[reg.region_id == rid, "pob_15_64"].iloc[0])
        fila = dict(section="decomposition", id=rid, name=x.territorio, pop_15_64=pob, total_pp=x.cobertura_pct - ch.cobertura_pct)
        for k, v in aporte.items():
            fila[f"{k}_pp"] = v
            fila[f"{k}_people"] = v / 100 * pob
            fila[f"{k}_level"] = x[k] * 100
            fila[f"{k}_level_chile"] = ch[k] * 100
        fila["cov_region"], fila["cov_chile"] = x.cobertura_pct, ch.cobertura_pct
        filas.append(fila)
    return pd.DataFrame(filas)


def main():
    tend = pd.read_csv(DP / "kpi_cobertura_tendencia.csv")
    reg = pd.read_csv(DP / "kpi_cobertura_regiones.csv")
    r, g, por_t, por_b, chile_cov = seleccion(tend, reg)
    union = por_t | por_b
    pob_16 = float(reg.loc[reg.region_id != ID_CHILE, "pob_15_64"].sum())
    brecha_total = float(g.brecha.sum())

    # ---- Chile
    c07 = float(tend[(tend.anio == ANIO_PARTIDA) & (tend.territorio_id == ID_CHILE)].cobertura_pct.iloc[0])
    filas = [dict(section="chile", name="Chile", cov_start=c07, cov_end=chile_cov, change_pp=chile_cov - c07, change_pct=chile_cov / c07 * 100 - 100,
                  year_start=ANIO_PARTIDA, year_end=ANIO_FINAL)]
    # ---- ranking (15 territorios)
    for _, x in r.iterrows():
        filas.append(dict(section="ranking", id=int(x.territorio_id), name=x.territorio, rank_start=x.puesto_partida, rank_end=x.puesto_final,
                          places_lost=x.puestos_perdidos, cov_start=x.cov_partida, cov_end=x.cov_final, change_pp=x.cambio_pp, change_pct=x.cambio_pct,
                          below_chile=bool(x.bajo_chile), by_trend=bool(x.entra_tendencia), year_start=ANIO_PARTIDA, year_end=ANIO_FINAL))
    # ---- brecha (regiones bajo Chile)
    for i, x in g.iterrows():
        filas.append(dict(section="gap", id=int(x.region_id), name=x.region_nombre, pop_15_64=x.pob_15_64, cov_end=x.cobertura_ref, gap_people=x.brecha,
                          gap_share=x.participacion, gap_cum_share=x.acumulada, gap_order=i + 1, by_gap=int(x.region_id) in por_b))
    # ---- selección (16 regiones)
    brecha_reg = g.set_index("region_id").brecha
    for _, x in reg[reg.region_id != ID_CHILE].sort_values("region_id").iterrows():
        rid = int(x.region_id)
        filas.append(dict(section="selection", id=rid, name=x.region_nombre, pop_15_64=x.pob_15_64, gap_people=float(brecha_reg.get(rid, 0.0)),
                          by_trend=rid in por_t, by_gap=rid in por_b, selected=rid in union, motivo=motivo(rid, por_t, por_b)))
    # ---- descomposición de las elegidas (orden: mayor diferencia total primero)
    d = descomposicion(reg, sorted(union))
    d = d.assign(order=d.total_pp.abs().rank(ascending=False, method="first").astype(int)).sort_values("order")
    filas += d.to_dict("records")
    out = pd.DataFrame(filas)
    cols = ["section", "id", "name", "year_start", "year_end", "rank_start", "rank_end", "places_lost", "cov_start", "cov_end", "change_pp", "change_pct",
            "below_chile", "by_trend", "by_gap", "selected", "motivo", "pop_15_64", "gap_people", "gap_share", "gap_cum_share", "gap_order", "order",
            "total_pp", "participacion_pp", "empleo_pp", "cotizacion_pp", "participacion_people", "empleo_people", "cotizacion_people",
            "participacion_level", "empleo_level", "cotizacion_level", "participacion_level_chile", "empleo_level_chile", "cotizacion_level_chile",
            "cov_region", "cov_chile"]
    out[cols].to_csv(DP / "kpi_seleccion_dos_preguntas.csv", index=False, float_format="%.6f")

    # ---- sensibilidad: año de partida × corte
    sens = []
    for anio in range(2007, 2019):
        for corte in (0.70, 0.80, 0.90):
            r_, g_, t_, b_, _ = seleccion(tend, reg, anio, corte)
            u = t_ | b_
            nombres = reg.set_index("region_id").region_nombre
            sens.append(dict(start_year=anio, cutoff=corte, n_territories=len(r_), regions="; ".join(nombres[sorted(u)]), n_regions=len(u),
                             by_trend="; ".join(nombres[sorted(t_)]), by_gap="; ".join(nombres[sorted(b_)]),
                             gap_share=float(g_.loc[g_.region_id.isin(u), "brecha"].sum() / g_.brecha.sum()),
                             pop_share=float(reg.loc[reg.region_id.isin(u), "pob_15_64"].sum() / pob_16)))
    pd.DataFrame(sens).to_csv(DP / "kpi_seleccion_sensibilidad.csv", index=False, float_format="%.6f")

    # ---- resumen en consola
    nombres = reg.set_index("region_id").region_nombre
    print(f"Chile {c07:.1f} → {chile_cov:.1f}: {chile_cov - c07:+.1f} puntos, {chile_cov / c07 * 100 - 100:+.1f} %")
    print(r[["territorio", "puesto_partida", "puesto_final", "puestos_perdidos", "cov_partida", "cov_final", "cambio_pp", "cambio_pct", "entra_tendencia"]]
          .round(2).to_string(index=False))
    print(g[["region_nombre", "brecha", "acumulada"]].round(3).to_string(index=False))
    print("Por tendencia:", sorted(nombres[sorted(por_t)]), "| por brecha:", sorted(nombres[sorted(por_b)]))
    print(f"Unión ({len(union)}): {sorted(nombres[sorted(union)])}")
    print(f"Brecha de la unión: {g.loc[g.region_id.isin(union), 'brecha'].sum():,.0f} de {brecha_total:,.0f} = "
          f"{g.loc[g.region_id.isin(union), 'brecha'].sum() / brecha_total * 100:.2f} %; población 15-64: "
          f"{reg.loc[reg.region_id.isin(union), 'pob_15_64'].sum() / pob_16 * 100:.2f} % de {pob_16:,.0f}")
    tot = {k: d[f"{k}_people"].sum() for k in ("cotizacion", "participacion", "empleo")}
    print({k: (round(v), round(v / sum(tot.values()) * 100, 2)) for k, v in tot.items()}, round(sum(tot.values())))


if __name__ == "__main__":
    main()
