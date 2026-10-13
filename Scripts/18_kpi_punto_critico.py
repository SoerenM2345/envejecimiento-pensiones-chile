"""
Insumos del análisis "punto crítico" del KPI 1.2: ingreso por trabajador (lado ingreso) y costo por persona de 65+ (lado costo),
histórico y con los parámetros de la reforma. Los pesos reales son pesos de 2025 (IPC promedio anual).

Fuentes (Data raw/import_KPI1.2/, descargadas del sitio de la Superintendencia de Pensiones, del INE y del Banco Central):
  - 04A*.xls (+ 04A_descargas/ del script 15)  Nº de cotizantes e ingreso imponible promedio por tipo y sexo, mensual 2002-10 a 2026-08.
  - 32C*.xls, estadisticas (n).xls            Ingreso imponible promedio por región y AFP, cada diciembre 2010-2025 (se usa la fila Total).
  - 19B*.xls, estadisticas (n).xls            Nº de cotizantes por tramo de ingreso imponible (miles de $) y AFP, cada diciembre 2010-2025.
  - CL01,DF_YMEDIANOOCU_SEXO / DF_YMEDIOOCU_SEXO / DF_OCU_SEXO  INE: ingreso mediano y medio de los ocupados (ESI, anual, nominal)
                                              y ocupados (ENE, trimestre móvil; se usa octubre-diciembre, el período de la ESI).
  - F074IPCVARZZCM.xlsx                       Banco Central: IPC general, variación mensual (planilla mal formada: se lee el XML).
De Data processed/: pgu_pbs_aps_nacional_anual.csv, pgu_pbs_aps_region_trimestral.csv, proyeccion_envejecimiento_pais.csv,
proyeccion_pais_edad_sexo.csv.

Salidas (Data processed/):
  - sp_ingreso_imponible_nacional.csv   periodo, anio, mes, tipo, sexo, cotizantes, ingreso_promedio_nom   (mensual, 2002-10 a 2026-08)
  - sp_ingreso_imponible_region.csv     anio, region_id, ingreso_promedio_nom   (diciembre; Ñuble desde 2018)
  - sp_cotizantes_por_tramo.csv         anio, tramo_desde_miles, tramo_hasta_miles, cotizantes   (diciembre)
  - ine_ingresos_ocupados.csv           anio, region_id (0 = país), sexo, mediana_nom, media_nom, ocupados (octubre-diciembre)
  - ipc_anual.csv                       anio, ipc_prom, deflactor_2025
  - kpi_pc_nacional.csv                 una fila por año 2010-2025: el lado ingreso y el lado costo en pesos nominales y reales (2025)
  - kpi_pc_region.csv                   año x región 2010-2025: cotizantes, ingreso imponible, ocupados e ingreso de los ocupados,
                                        más la cuota regional del gasto de vejez del Pilar Solidario
  - kpi_pc_parametros_reforma.csv       calendario de la PGU de $250.000 (Ley 21.735) como factor de costo, 2025-2070

Notas de método:
  - Costo de vejez = total del Pilar Solidario - APS/PBS de invalidez (= PGU + APS vejez + PBS vejez); gasto anual nominal del informe OND, deflactado.
  - Mediana de los cotizantes: interpolación lineal dentro del tramo de ingreso imponible donde se acumula el 50 %.
    Es una aproximación (tramos de $20-50 mil); para el tramo abierto final se usa el límite inferior.
  - El IPC se encadena desde la variación mensual (redondeada a 1 decimal): sirve para razones entre años, no como nivel.
"""
import re
import zipfile
from html import unescape
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IMP = ROOT / "Data raw" / "import_KPI1.2"
OUT = ROOT / "Data processed"
OUT.mkdir(parents=True, exist_ok=True)

BASE_REAL = 2025
MESES = {m: i + 1 for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"])}
ROMANOS = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12,
           "R. METROP.": 13, "XIV": 14, "XV": 15, "XVI": 16}
PGU_FEB_2025, PGU_NUEVA = 224_004, 250_000  # Ley 21.735: monto de la PGU y monto al que sube


# ───────────────────────── lectura de las tablas HTML (.xls) ─────────────────────────
def leer_html(path):
    """Devuelve (texto del título, filas) de una tabla HTML con extensión .xls (latin-1)."""
    t = Path(path).read_text(encoding="latin-1", errors="replace")
    filas = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S | re.I):
        celdas = [re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", c))).replace("\xa0", " ").strip()
                  for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)]
        filas.append(celdas)
    titulo = re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", t))).replace("\xa0", " ")
    return titulo, filas


def fecha_titulo(titulo):
    m = re.search(r"Al\s+\d+\s+de\s+(\w+)\s+de\s+(\d{4})", titulo)
    return (int(m.group(2)), MESES[m.group(1).lower()]) if m else (None, None)


def num(s):
    s = str(s).replace(".", "").replace(",", ".").strip()
    return float(s) if re.fullmatch(r"-?\d+(\.\d+)?", s) else np.nan


def archivos_sp():
    return sorted(list(IMP.glob("*.xls")) + list((IMP / "04A_descargas").glob("*.xls")))


# ───────────────────────── SP: 04A nacional mensual ─────────────────────────
def parse_04a(filas):
    out, tipo = [], None
    for f in filas:
        if len(f) < 3:
            continue
        et = f[0].upper().replace("Ú", "U")
        if et in ("DEPENDIENTES", "INDEPENDIENTES", "VOLUNTARIOS", "TOTAL"):
            tipo, sexo = et.capitalize(), "Ambos"
        elif et in ("MASCULINO", "FEMENINO", "S/I") and tipo:
            sexo = {"MASCULINO": "Hombres", "FEMENINO": "Mujeres", "S/I": "S/I"}[et]
        else:
            continue
        out.append(dict(tipo=tipo, sexo=sexo, cotizantes=num(f[1]), ingreso_promedio_nom=num(f[2])))
    return out


def sp_nacional():
    filas, vistos = [], set()
    for p in archivos_sp():
        titulo, rows = leer_html(p)
        if "COTIZANTES E INGRESO IMPONIBLE PROMEDIO POR TIPO Y SEXO" not in titulo.upper().replace("Ú", "U"):
            continue
        a, m = fecha_titulo(titulo)
        if (a, m) in vistos:
            continue
        vistos.add((a, m))
        for r in parse_04a(rows):
            filas.append(dict(periodo=f"{a}-{m:02d}", anio=a, mes=m, **r))
    d = pd.DataFrame(filas).sort_values(["periodo", "tipo", "sexo"]).reset_index(drop=True)
    tot = d[(d.tipo == "Total") & (d.sexo == "Ambos")]
    assert tot.periodo.nunique() == len(vistos), "faltan filas Total en algún 04A"
    meses = pd.period_range(tot.periodo.min(), tot.periodo.max(), freq="M").strftime("%Y-%m")
    faltan = sorted(set(meses) - set(tot.periodo))
    assert not faltan, f"meses sin 04A: {faltan} (corre Scripts/15_descargar_sp_ingreso_imponible.py)"
    d.to_csv(OUT / "sp_ingreso_imponible_nacional.csv", index=False)
    return d


# ───────────────────────── SP: ingreso imponible promedio por región (diciembre) ─────────────────────────
def sp_region():
    filas = {}
    for p in archivos_sp():
        titulo, rows = leer_html(p)
        if "INGRESO IMPONIBLE PROMEDIO POR REGI" not in titulo.upper().replace("Ó", "O").replace("REGIÓN", "REGION") \
                and "INGRESO IMPONIBLE PROMEDIO POR REGI" not in titulo.upper():
            continue
        a, m = fecha_titulo(titulo)
        cab = next(f for f in rows if f and f[0].strip().upper() == "I" and "II" in [c.strip().upper() for c in f])
        cab = [c.strip().upper() for c in cab]
        total = next(f for f in rows if f and f[0].strip().upper() == "TOTAL")
        vals = [num(x) for x in total[1:]]
        assert len(vals) == len(cab) + 1, f"{p.name}: {len(vals)} valores vs {len(cab)} regiones"
        for nombre, v in zip(cab, vals[1:]):
            rid = ROMANOS.get(nombre)
            if rid and not np.isnan(v) and v > 0:
                filas[(a, rid)] = v
    d = pd.DataFrame([dict(anio=a, region_id=r, ingreso_promedio_nom=v) for (a, r), v in sorted(filas.items())])
    assert d.anio.min() <= 2010 and d.anio.max() >= 2025, "faltan años en el ingreso imponible por región"
    d.to_csv(OUT / "sp_ingreso_imponible_region.csv", index=False)
    return d


# ───────────────────────── SP: cotizantes por tramo de ingreso y mediana ─────────────────────────
def sp_tramos():
    filas = {}
    for p in archivos_sp():
        titulo, rows = leer_html(p)
        if "COTIZANTES POR INGRESO IMPONIBLE Y A.F.P" not in titulo.upper():
            continue
        a, m = fecha_titulo(titulo)
        for f in rows:
            g = re.match(r"^\+\s*(\d+)\s*(?:-\s*(\d+)|y\s*m[aá]s)?", f[0]) if f else None
            if not g or len(f) < 3:
                continue
            filas[(a, int(g.group(1)))] = (int(g.group(2)) if g.group(2) else np.nan, num(f[-1]))
    d = pd.DataFrame([dict(anio=a, tramo_desde_miles=lo, tramo_hasta_miles=hi, cotizantes=n)
                      for (a, lo), (hi, n) in sorted(filas.items())])
    d.to_csv(OUT / "sp_cotizantes_por_tramo.csv", index=False)
    return d


def mediana_tramos(g):
    """Mediana del ingreso imponible (en pesos) por interpolación lineal dentro del tramo."""
    g = g.sort_values("tramo_desde_miles")
    n = g.cotizantes.values
    acum = np.cumsum(n)
    k = int(np.searchsorted(acum, acum[-1] / 2))
    lo, hi = g.tramo_desde_miles.values[k], g.tramo_hasta_miles.values[k]
    if np.isnan(hi):
        return lo * 1000.0
    previo = acum[k - 1] if k else 0
    return (lo + (hi - lo) * (acum[-1] / 2 - previo) / n[k]) * 1000.0


# ───────────────────────── INE: ingresos de los ocupados (ESI) y ocupados (ENE) ─────────────────────────
def ine():
    def leer(patron):
        return pd.read_csv(next(IMP.glob(patron)), sep=";", dtype={"AREA_REF": str}, low_memory=False)

    med = leer("CL01,DF_YMEDIANOOCU_SEXO*A....csv")
    mea = leer("CL01,DF_YMEDIOOCU_SEXO*A....csv")
    ocu = leer("CL01,DF_OCU_SEXO*.csv")
    rid = lambda s: s.map(lambda x: 0 if x == "_T" else int(x))  # noqa: E731
    sx = {"AS": "Ambos", "F": "Mujeres", "M": "Hombres"}
    a = med[["AREA_REF", "SEXO", "TIME_PERIOD", "OBS_VALUE"]].rename(columns={"OBS_VALUE": "mediana_nom"})
    b = mea[["AREA_REF", "SEXO", "TIME_PERIOD", "OBS_VALUE"]].rename(columns={"OBS_VALUE": "media_nom"})
    d = a.merge(b, on=["AREA_REF", "SEXO", "TIME_PERIOD"], how="outer")
    d["anio"], d["region_id"], d["sexo"] = d.TIME_PERIOD.astype(int), rid(d.AREA_REF), d.SEXO.map(sx)
    o = ocu[ocu.TIME_PERIOD.str.contains(r"-10-01/P3M")].copy()  # trimestre octubre-diciembre
    o["anio"], o["region_id"], o["sexo"] = o.TIME_PERIOD.str[:4].astype(int), rid(o.AREA_REF), o.SEXO.map(sx)
    o = o[["anio", "region_id", "sexo", "OBS_VALUE"]].rename(columns={"OBS_VALUE": "ocupados"})
    d = d.drop(columns=["AREA_REF", "SEXO", "TIME_PERIOD"]).merge(o, on=["anio", "region_id", "sexo"], how="left")
    d = d.sort_values(["anio", "region_id", "sexo"]).reset_index(drop=True)
    d.to_csv(OUT / "ine_ingresos_ocupados.csv", index=False)
    return d


# ───────────────────────── IPC (variación mensual -> índice -> deflactor) ─────────────────────────
def ipc():
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(IMP / "F074IPCVARZZCM.xlsx") as z:
        raiz = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))  # el libro apunta a otra hoja: los datos están en sheet1.xml
    filas = [[(c.find("x:v", ns).text if c.find("x:v", ns) is not None else "") for c in r.findall("x:c", ns)]
             for r in raiz.iter("{%s}row" % ns["x"])]
    fechas = next(f for f in filas if f and f[0].startswith("Descripción series"))[1:]
    valores = next(f for f in filas if f and f[0].startswith("IPC General"))[1:]
    s = pd.Series([float(v) if v not in ("", None) else np.nan for v in valores],
                  index=pd.to_datetime([f[:10] for f in fechas])).dropna()
    s = s[s.index >= "2008-12-01"]  # solo sirve la relación entre años recientes
    idx = 100 * (1 + s / 100).cumprod()
    anual = idx.groupby(idx.index.year).agg(["mean", "count"])
    anual = anual[anual["count"] == 12]
    d = pd.DataFrame({"anio": anual.index, "ipc_prom": anual["mean"].values})
    d["deflactor_2025"] = d.loc[d.anio == BASE_REAL, "ipc_prom"].iloc[0] / d.ipc_prom
    d.to_csv(OUT / "ipc_anual.csv", index=False)
    return d


# ───────────────────────── costo del Pilar Solidario de vejez ─────────────────────────
def costo_vejez(defl):
    n = pd.read_csv(OUT / "pgu_pbs_aps_nacional_anual.csv")
    tot = n[n.tipo_beneficio == "Total"].set_index("anio").monto_nominal_mm
    inv = n[n.tipo_beneficio.isin(["APS invalidez", "PBS invalidez"])].groupby("anio").monto_nominal_mm.sum().reindex(tot.index).fillna(0)
    # vejez = total - invalidez: robusto al 2022, cuando el informe no separa la fila PGU (PBS vejez pasó a PGU en febrero de 2022)
    d = pd.DataFrame({"costo_vejez_mm_nom": tot - inv, "costo_total_mm_nom": tot}).reset_index()
    d = d.merge(defl[["anio", "deflactor_2025"]], on="anio", how="left")
    d["costo_vejez_mm_real25"] = d.costo_vejez_mm_nom * d.deflactor_2025
    return d.drop(columns="deflactor_2025")


def cuota_regional():
    """Cuota de cada región en el gasto trimestral de vejez (PGU + APS vejez); 2024 = trimestre octubre-diciembre 2024."""
    r = pd.read_csv(OUT / "pgu_pbs_aps_region_trimestral.csv")
    r = r[(r.sexo == "Total") & r.tipo_beneficio.isin(["PGU no contributiva", "PGU contributiva", "APS vejez"])]
    anio = {"octubre 2023 a diciembre 2023": 2023, "cuarto trimestre 2024": 2024, "octubre 2025 a diciembre 2025": 2025}
    r = r.assign(anio=r.trimestre.map(anio)).dropna(subset=["anio"])
    g = r.groupby(["anio", "region_id"]).monto_total_mm.sum().reset_index()
    g["cuota_gasto_vejez"] = g.monto_total_mm / g.groupby("anio").monto_total_mm.transform("sum")
    assert g.groupby("anio").region_id.nunique().eq(16).all(), "faltan regiones en el gasto regional de vejez"
    g["anio"] = g.anio.astype(int)
    return g[["anio", "region_id", "cuota_gasto_vejez"]]


# ───────────────────────── parámetros de la reforma (PGU $250.000) ─────────────────────────
def parametros_reforma(costo):
    """Factor de costo de la PGU de $250.000 con el calendario por edad de la Ley 21.735.

    sep-2025: 82+ · sep-2026: 75+ · sep-2027: 65+ (todos con $250.000). Se pondera por la fracción del año vigente y por la
    parte de los 65+ que cae en cada tramo de edad (proyección INE). El factor es relativo a 2025 (el costo base ya incluye
    la parte de 2025) y solo afecta a la parte PGU del gasto (cuota_pgu del costo de vejez 2025).
    """
    e = pd.read_csv(OUT / "proyeccion_pais_edad_sexo.csv")
    ecol = next(c for c in e.columns if c.lower().startswith("edad"))
    pcol = next(c for c in e.columns if c.lower().startswith("pob"))
    e = e[e[ecol] >= 65].groupby(["anio", ecol])[pcol].sum().reset_index()
    t = e.groupby("anio")[pcol].sum()
    s82 = e[e[ecol] >= 82].groupby("anio")[pcol].sum() / t
    s75 = e[e[ecol] >= 75].groupby("anio")[pcol].sum() / t
    d = pd.DataFrame({"anio": t.index, "share_82_mas": s82.values, "share_75_mas": s75.values})
    f = lambda a, b: a * 8 / 12 + b * 4 / 12  # noqa: E731  (enero-agosto con `a`, septiembre-diciembre con `b`)
    up = []
    for _, r in d.iterrows():
        y = r.anio
        up.append(0.0 if y < 2025 else f(0, r.share_82_mas) if y == 2025 else f(r.share_82_mas, r.share_75_mas) if y == 2026
                  else f(r.share_75_mas, 1.0) if y == 2027 else 1.0)
    d["fraccion_con_pgu_nueva"] = up
    u = PGU_NUEVA / PGU_FEB_2025 - 1
    c25 = costo[costo.anio == BASE_REAL].iloc[0]
    n = pd.read_csv(OUT / "pgu_pbs_aps_nacional_anual.csv")
    pgu25 = n[(n.anio == BASE_REAL) & (n.tipo_beneficio == "PGU")].monto_nominal_mm.iloc[0]
    cuota_pgu = pgu25 / c25.costo_vejez_mm_nom
    base = 1 + cuota_pgu * u * d.loc[d.anio == BASE_REAL, "fraccion_con_pgu_nueva"].iloc[0]
    d["factor_costo_pgu"] = (1 + cuota_pgu * u * d.fraccion_con_pgu_nueva) / base
    d.loc[d.anio < BASE_REAL, "factor_costo_pgu"] = 1.0
    d["pgu_monto_nuevo"], d["pgu_monto_feb2025"], d["cuota_pgu_en_costo_vejez"] = PGU_NUEVA, PGU_FEB_2025, cuota_pgu
    d = d[d.anio >= 2025].reset_index(drop=True)
    d.to_csv(OUT / "kpi_pc_parametros_reforma.csv", index=False)
    return d


# ───────────────────────── tablas finales ─────────────────────────
def main():
    nac = sp_nacional()
    reg = sp_region()
    tramos = sp_tramos()
    ing = ine()
    defl = ipc()
    costo = costo_vejez(defl)

    # --- nacional ---
    dic = nac[(nac.mes == 12) & (nac.tipo == "Total") & (nac.sexo == "Ambos")][["anio", "cotizantes", "ingreso_promedio_nom"]]
    dic = dic.rename(columns={"cotizantes": "cotizantes_dic", "ingreso_promedio_nom": "ingreso_imponible_prom_nom"})
    med = tramos.groupby("anio").apply(mediana_tramos, include_groups=False).rename("ingreso_imponible_mediano_nom").reset_index()
    ine_n = ing[(ing.region_id == 0) & (ing.sexo == "Ambos")][["anio", "mediana_nom", "media_nom", "ocupados"]].rename(
        columns={"mediana_nom": "ing_ocupados_mediano_nom", "media_nom": "ing_ocupados_medio_nom", "ocupados": "ocupados_ond"})
    pais = pd.read_csv(OUT / "proyeccion_envejecimiento_pais.csv")[["anio", "pob_15_64", "pob_65_mas"]]
    d = dic.merge(med, on="anio", how="left").merge(ine_n, on="anio", how="left").merge(defl, on="anio", how="left")
    d = d.merge(costo, on="anio", how="left").merge(pais.rename(columns={"pob_15_64": "pob_15_64_ine", "pob_65_mas": "pob_65_mas_ine"}),
                                                    on="anio", how="left")
    d = d[(d.anio >= 2010) & (d.anio <= 2025)].copy()
    for c in ["ingreso_imponible_prom", "ingreso_imponible_mediano", "ing_ocupados_mediano", "ing_ocupados_medio"]:
        d[c + "_real25"] = d[c + "_nom"] * d.deflactor_2025
    d["costo_vejez_por_65_real25"] = d.costo_vejez_mm_real25 * 1e6 / d.pob_65_mas_ine
    d.to_csv(OUT / "kpi_pc_nacional.csv", index=False)

    # --- regional ---
    cot = pd.read_csv(OUT / "cotizantes_por_region.csv")
    cot = cot[cot.region_id.notna()].assign(region_id=lambda x: x.region_id.astype(int))[["anio", "region_id", "cotizantes"]]
    cot = cot.rename(columns={"cotizantes": "cotizantes_dic"})
    r = reg.rename(columns={"ingreso_promedio_nom": "ingreso_imponible_prom_nom"}).merge(cot, on=["anio", "region_id"], how="outer")
    i = ing[(ing.region_id > 0) & (ing.sexo == "Ambos")][["anio", "region_id", "mediana_nom", "media_nom", "ocupados"]].rename(
        columns={"mediana_nom": "ing_ocupados_mediano_nom", "media_nom": "ing_ocupados_medio_nom", "ocupados": "ocupados_ond"})
    r = r.merge(i, on=["anio", "region_id"], how="outer").merge(defl[["anio", "deflactor_2025"]], on="anio", how="left")
    r = r.merge(cuota_regional(), on=["anio", "region_id"], how="left")
    r = r[(r.anio >= 2010) & (r.anio <= 2025)]
    # Ñuble se separó de Biobío en 2018: antes de eso el ingreso imponible regional de Ñuble se aproxima con el de Biobío
    biob = r[r.region_id == 8].set_index("anio").ingreso_imponible_prom_nom
    falta = (r.region_id == 16) & r.ingreso_imponible_prom_nom.isna()
    r.loc[falta, "ingreso_imponible_prom_nom"] = r.loc[falta, "anio"].map(biob)
    r["ingreso_imponible_aprox_biobio"] = falta
    for c in ["ingreso_imponible_prom", "ing_ocupados_mediano", "ing_ocupados_medio"]:
        r[c + "_real25"] = r[c + "_nom"] * r.deflactor_2025
    r = r.sort_values(["anio", "region_id"]).reset_index(drop=True)
    r.to_csv(OUT / "kpi_pc_region.csv", index=False)

    params = parametros_reforma(costo)

    # --- resumen en pantalla ---
    p = lambda x: f"{x:,.0f}".replace(",", ".")  # noqa: E731
    print("nacional 2025:", {k: (p(v) if isinstance(v, (int, float, np.floating)) else v)
                             for k, v in d[d.anio == 2025].iloc[0].items() if k in
                             ["cotizantes_dic", "ingreso_imponible_prom_nom", "ingreso_imponible_mediano_nom", "ing_ocupados_mediano_nom",
                              "ocupados_ond", "costo_vejez_mm_real25", "pob_65_mas_ine", "costo_vejez_por_65_real25"]})
    print("mediana de los cotizantes (nom) 2010/2020/2025:", [p(d.loc[d.anio == y, "ingreso_imponible_mediano_nom"].iloc[0]) for y in (2010, 2020, 2025)])
    print("factor PGU 250k:", params[["anio", "factor_costo_pgu"]].iloc[[0, 1, 2, 3, 5]].round(3).values.tolist())
    print("filas:", len(nac), len(reg), len(tramos), len(ing), len(defl), len(d), len(r))


if __name__ == "__main__":
    main()
