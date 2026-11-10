"""
KPI 1.1: tendencia de la cobertura previsional por región (2002-2025) y causas posibles de que sea baja.

Pedido del profesor (2026-11): dónde es más baja o va bajando la cobertura (cotizantes / población 15-64), cuáles son las
regiones que más importan y qué puede explicarlo (desempleo, informalidad, industria dominante, migración).

Fuentes (Data raw/):
  - cotizantes_por_region.csv (Data processed/)       cotizantes de diciembre por región, Superintendencia de Pensiones, 1985-2025.
  - _external/ine_proyecciones_base2017/estimaciones-y-proyecciones-2002-2035-comunas.xlsx
        INE, estimaciones y proyecciones de población 2002-2035, base Censo 2017, por comuna, sexo y edad simple. Es lo único
        publicado con población regional año a año (la proyección regional base 2024 sale en el segundo semestre de 2026).
        Si falta el archivo, el script lo descarga de https://www.ine.gob.cl/docs/default-source/proyecciones-de-poblacion/
        cuadros-estadisticos/base-2017/estimaciones-y-proyecciones-2002-2035-comunas.xlsx (11 MB).
  - personas_censo2024.csv                              Censo 2024, microdatos: situación en la fuerza de trabajo, categoría en el
        empleo, rama de actividad, lugar de residencia hace 5 años, lugar de nacimiento, escolaridad.
  - Data processed/: indicadores_region.csv, kpi_pc_nacional.csv, kpi_cobertura_correlaciones_region.csv.

Después de este script hay que ejecutar Scripts/25_explorar_causas.py (descomposición y factores oficiales de la ENE).

Decisiones (ver docs/DISCUSION_FUENTES.md, filas 16-18):
  - El Censo 2024 manda: la población 15-64 de cada región es la del INE base 2017 multiplicada por
    (población 15-64 del Censo 2024 / INE base 2017 en 2024) de esa región, así la cobertura de 2024 coincide con la del KPI 1.1.
    Solo corrige el nivel: la dinámica 2010-2025 es la proyección del INE (no hay otra); 2018-2025 son proyecciones, no datos.
  - Cambios de regiones: antes de 2007 la Superintendencia publica Arica y Parinacota dentro de Tarapacá y Los Ríos dentro de Los Lagos;
    antes de 2018, Ñuble dentro de Biobío. Hay tres series fusionadas para 2002-2025 («Tarapacá y Arica y Parinacota» id 801,
    «Los Lagos y Los Ríos» id 810, «Biobío y Ñuble» id 816; numerador y denominador sumados) y las regiones separadas desde que existen.
  - País: la serie del KPI 1.2 (cotizantes con región / población 15-64 INE base 2024 al nivel del Censo).
  - Se descartó cotizantes / ocupados (ENE) como denominador: se rompe por la pandemia (2020-2022) y por la separación de Ñuble.
  - Códigos del Censo verificados contra las cifras agregadas oficiales del INE (Base_zona_localidad_CPV24): sit_fuerza_trabajo
    1 ocupado, 2 desocupado, 3 fuera de la fuerza de trabajo; p40_cise_rec 1 independiente, 2 dependiente, 3 no remunerado;
    p25_lug_nacimiento_rec 2 nacido en el extranjero; p24_lug_resid5 1 no había nacido, 2 misma comuna, 3 otra comuna,
    4 otro país (los tres primeros coinciden exacto con las cifras del INE; el de residencia hace 5 años es coherente pero no hay
    cifra agregada para contrastarlo).

Salidas (Data processed/):
  - kpi_cobertura_tendencia.csv   anio, territorio_id (0 país, 1-16 regiones, 801/810/816 series fusionadas), territorio, cotizantes,
                                  pob_15_64 (al nivel del Censo), cobertura_pct, y la misma cobertura con la proyección del INE sin
                                  ajustar (pob_15_64_proy, cobertura_sin_ajuste_pct)
  - kpi_cobertura_regiones.csv    una fila por región: cobertura 2019/2022/2024/2025, cambios en puntos, y con el año de referencia (ANIO_REF = 2024)
                                  cobertura_ref, cambio_2019_ref, cambio_2022_ref, peso en los cotizantes, brecha y las 4 listas prioritarias,
                                  y los factores del Censo 2024 (desocupación, independientes, ramas, migración, escolaridad)
  - kpi_cobertura_factores.csv    cada factor candidato con su correlación con la cobertura 2024 (16 regiones)
"""
import sys
import urllib.request
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

ROOT = Path(__file__).resolve().parent.parent
DP = ROOT / "Data processed"
INE17 = ROOT / "Data raw" / "_external" / "ine_proyecciones_base2017" / "estimaciones-y-proyecciones-2002-2035-comunas.xlsx"
URL_INE17 = ("https://www.ine.gob.cl/docs/default-source/proyecciones-de-poblacion/cuadros-estadisticos/base-2017/"
             "estimaciones-y-proyecciones-2002-2035-comunas.xlsx")
CENSO = ROOT / "Data raw" / "personas_censo2024.csv"

ANIOS = range(2002, 2026)
ID_BIOBIO_NUBLE = 816
FUSIONES = {  # id de la serie fusionada -> (nombre, regiones, primer año en que se publican por separado)
    801: ("Tarapacá y Arica y Parinacota", (1, 15), 2007),
    810: ("Los Lagos y Los Ríos", (10, 14), 2007),
    ID_BIOBIO_NUBLE: ("Biobío y Ñuble", (8, 16), 2018),
}
PARTICION = [2, 3, 4, 5, 6, 7, 9, 11, 12, 13, *FUSIONES]  # territorios sin solapamiento que suman el país en todos los años
SEPARADAS_DESDE = {1: 2007, 10: 2007, 8: 2018}  # región «grande» que hasta ese año incluye a la nueva en su numerador
N_PRIORIDAD = 5
# Año de referencia de todas las comparaciones del KPI 1.1 (barras, listas de regiones prioritarias, tabla y descomposición). 2024 es el año
# del Censo (la única población medida, no proyectada) y el último con ocupados por región; 2025 tiene cotizantes pero su población es una
# proyección y no hay empleo regional. Si se consiguen la ENE de 2025 y la proyección regional base 2024, basta cambiar esta constante.
ANIO_REF = 2024

RAMAS = {  # CAENES (CIIU rev. 4): letra -> nombre
    "A": "Agricultura, ganadería, silvicultura y pesca", "B": "Minería", "C": "Industria manufacturera", "F": "Construcción",
    "G": "Comercio", "H": "Transporte y almacenamiento", "I": "Alojamiento y comidas", "O": "Administración pública",
    "P": "Enseñanza", "Q": "Salud y asistencia social", "S": "Otros servicios", "T": "Hogares como empleadores",
}
RAMAS_INFORMALES = ["A", "F", "G", "I", "S", "T"]  # sectores donde la informalidad es más alta (proxy; la tasa oficial es de la ENE)

# factor -> (nombre legible, hipótesis del profesor, fuente, ámbito)
FACTORES = {
    "ingreso_per_capita_prom": ("Ingreso per cápita", "Otros", "CASEN 2022", "regiones"),
    "pct_pobreza_65": ("Pobreza en personas de 65+", "Otros", "CASEN 2022", "regiones"),
    "pct_urbano": ("Población urbana", "Otros", "Censo 2024", "país y regiones"),
    "pct_65_mas": ("Personas de 65+ (% de la población)", "Otros", "Censo 2024", "país y regiones"),
    "desocupacion": ("Desocupación (% de la fuerza de trabajo)", "Desempleo", "Censo 2024", "país y regiones"),
    "participacion": ("Participación laboral (% de las personas de 15+)", "Otros", "Censo 2024", "país y regiones"),
    "independientes": ("Ocupados independientes (%)", "Informalidad (aproximación)", "Censo 2024", "país y regiones"),
    "sectores_informales": ("Ocupados en sectores de alta informalidad (%)", "Informalidad (aproximación)", "Censo 2024", "país y regiones"),
    "escolaridad_25mas": ("Años de escolaridad (25+)", "Educación", "Censo 2024", "país y regiones"),
    "migracion_interna_neta": ("Migración interna neta en 5 años (por 1.000 habitantes)", "Migración", "Censo 2024", "regiones"),
    "llegada_reciente_ext": ("Llegados del extranjero en 5 años (%)", "Migración", "Censo 2024", "país y regiones"),
    "inmigrantes": ("Nacidos en el extranjero (%)", "Migración", "Censo 2024", "país y regiones"),
}
FACTORES |= {f"rama_{L}": (f"Ocupados en {n.lower()} (%)", "Industria", "Censo 2024", "país y regiones") for L, n in RAMAS.items()}


def asegurar_ine17():
    if INE17.exists():
        return
    INE17.parent.mkdir(parents=True, exist_ok=True)
    print("descargando", URL_INE17)
    req = urllib.request.Request(URL_INE17, headers={"User-Agent": "Mozilla/5.0"})
    INE17.write_bytes(urllib.request.urlopen(req, timeout=180).read())


def poblacion_15_64_ine17() -> pd.DataFrame:
    """Población de 15 a 64 años por región (filas) y año (columnas), INE base 2017, 2002-2035."""
    d = pd.read_excel(INE17)
    d.columns = [c.split("\n")[0] for c in d.columns]
    anios = [c for c in d.columns if c.startswith("Poblacion")]
    d = d[(d.Edad >= 15) & (d.Edad <= 64)].groupby("Region")[anios].sum()
    d.columns = [int(c.split()[-1]) for c in d.columns]
    return d


def tendencia(nombres: pd.Series, ind: pd.DataFrame) -> pd.DataFrame:
    p_raw = poblacion_15_64_ine17()
    censo = ind.pob_15_64
    p = p_raw.mul(censo / p_raw[2024], axis=0)  # el Censo 2024 manda: se corrige el nivel de cada región
    c = pd.read_csv(DP / "cotizantes_por_region.csv")
    c = c[c.region_id.notna()].assign(region_id=lambda x: x.region_id.astype(int)).pivot(index="region_id", columns="anio", values="cotizantes")
    filas = []
    for r in p.index:
        for a in ANIOS:
            if a < SEPARADAS_DESDE.get(r, 0):
                continue  # hasta ese año los cotizantes de la región incluyen a la nueva: solo sirve la serie fusionada
            if r in c.index and a in c.columns and not np.isnan(c.loc[r, a]):
                filas.append((a, r, nombres[r], c.loc[r, a], p.loc[r, a], p_raw.loc[r, a]))
    for tid, (nombre, regs, desde) in FUSIONES.items():
        for a in ANIOS:
            cot = sum(c.loc[r, a] for r in regs if not np.isnan(c.loc[r, a]))  # antes de «desde», la región nueva ya viene dentro de la grande
            filas.append((a, tid, nombre, cot, sum(p.loc[r, a] for r in regs), sum(p_raw.loc[r, a] for r in regs)))
    t = pd.DataFrame(filas, columns=["anio", "territorio_id", "territorio", "cotizantes", "pob_15_64", "pob_15_64_proy"])
    # país: la serie del KPI 1.2 (misma que la tarjeta de razón de soporte) desde 2010; antes de 2010 la suma de las regiones,
    # empalmada con la serie del KPI en 2010 (la diferencia entre ambas es de 0,2 puntos)
    n = pd.read_csv(DP / "kpi_pc_nacional.csv").set_index("anio")
    suma = t[t.territorio_id.isin(PARTICION)].groupby("anio")[["cotizantes", "pob_15_64", "pob_15_64_proy"]].sum()
    pais = pd.DataFrame({"anio": list(ANIOS), "territorio_id": 0, "territorio": "Chile"})
    pais["cotizantes"] = [suma.loc[a, "cotizantes"] for a in ANIOS]
    ajuste = (n.loc[2010, "cotizantes_dic_con_region"] / (n.loc[2010, "pob_15_64_ine"] * n.loc[2010, "factor_censo_15_64"])) / (suma.loc[2010, "cotizantes"] / suma.loc[2010, "pob_15_64"])
    pais["pob_15_64"] = [n.loc[a, "pob_15_64_ine"] * n.loc[a, "factor_censo_15_64"] if a >= 2010 else suma.loc[a, "pob_15_64"] / ajuste for a in ANIOS]
    pais["pob_15_64_proy"] = [n.loc[a, "pob_15_64_ine"] if a >= 2010 else suma.loc[a, "pob_15_64_proy"] / ajuste for a in ANIOS]
    t = pd.concat([pais, t], ignore_index=True)
    t["cobertura_pct"] = 100 * t.cotizantes / t.pob_15_64
    t["cobertura_sin_ajuste_pct"] = 100 * t.cotizantes / t.pob_15_64_proy
    return t.sort_values(["territorio_id", "anio"]).reset_index(drop=True)


def factores_censo() -> pd.DataFrame:
    """Factores por región del Censo 2024 (todas las personas de la región, sin ponderar; el Censo es un conteo)."""
    con = duckdb.connect()
    src = f"read_csv_auto('{CENSO.as_posix()}', delim=';', sample_size=300000)"
    b = con.execute(f"""
        SELECT region, count(*) pob,
          sum((sit_fuerza_trabajo=1)::int) ocup, sum((sit_fuerza_trabajo=2)::int) desoc, sum((sit_fuerza_trabajo=3)::int) fuera,
          sum((p40_cise_rec=1)::int) indep, sum((p40_cise_rec IN (1,2,3))::int) con_cise,
          sum((p25_lug_nacimiento_rec=2)::int) nac_ext,
          sum((p24_lug_resid5=4)::int) llega_ext, sum((p24_lug_resid5 IN (2,3,4))::int) pob5,
          sum((p24_lug_resid5=3 AND floor(p24_lug_resid5_esp/1000)<>region)::int) entra,
          avg(CASE WHEN edad>=25 AND escolaridad>=0 THEN escolaridad END) escol25
        FROM {src} GROUP BY 1 ORDER BY 1""").df().set_index("region")
    sale = con.execute(f"""
        SELECT floor(p24_lug_resid5_esp/1000)::int region, count(*) sale FROM {src}
        WHERE p24_lug_resid5=3 AND floor(p24_lug_resid5_esp/1000)<>region GROUP BY 1""").df().set_index("region")
    ramas = con.execute(f"""SELECT region, cod_caenes, count(*) n FROM {src} WHERE cod_caenes IS NOT NULL GROUP BY 1,2""").df()
    cnt = ramas.pivot(index="region", columns="cod_caenes", values="n").fillna(0)
    b = b.join(sale).fillna({"sale": 0})
    escol_pais = np.average(b.escol25, weights=b["pob"])  # promedio ponderado por población
    b.loc[0] = b.sum()  # fila 0 = Chile (suma de las regiones; la migración interna entre regiones suma cero por construcción)
    b.loc[0, "escol25"] = escol_pais
    cnt.loc[0] = cnt.sum()
    sh = 100 * cnt.div(cnt.sum(axis=1), axis=0)
    f = pd.DataFrame(index=b.index)
    f["desocupacion"] = 100 * b.desoc / (b.ocup + b.desoc)
    f["participacion"] = 100 * (b.ocup + b.desoc) / (b.ocup + b.desoc + b.fuera)
    f["independientes"] = 100 * b.indep / b.con_cise
    f["sectores_informales"] = sh[RAMAS_INFORMALES].sum(axis=1)
    f["escolaridad_25mas"] = b.escol25
    f["migracion_interna_neta"] = 1000 * (b.entra - b.sale) / b.pob5
    f["llegada_reciente_ext"] = 100 * b.llega_ext / b.pob5
    f["inmigrantes"] = 100 * b.nac_ext / b["pob"]
    for L in RAMAS:
        f[f"rama_{L}"] = sh[L]
    # industria dominante (mayor peso) y especializada (mayor cociente de localización frente al país, entre ramas con >= 3 % nacional)
    nac = sh.loc[0]
    f["rama_dominante"] = sh.idxmax(axis=1).map(lambda L: RAMAS.get(L, L))
    cl = sh.div(nac, axis=1)[[L for L in sh.columns if nac[L] >= 3]]
    f["rama_especializada"] = cl.idxmax(axis=1).map(lambda L: RAMAS.get(L, L))
    f["rama_especializada_indice"] = cl.max(axis=1)
    f.loc[0, ["rama_especializada", "rama_especializada_indice"]] = [None, np.nan]  # el país no se especializa frente a sí mismo
    return f


def main():
    asegurar_ine17()
    ind = pd.read_csv(DP / "indicadores_region.csv").set_index("region")
    nombres = ind.region_nombre
    t = tendencia(nombres, ind)
    t.round(4).to_csv(DP / "kpi_cobertura_tendencia.csv", index=False)

    cob = t.pivot(index="territorio_id", columns="anio", values="cobertura_pct")
    r = pd.DataFrame(index=ind.index)
    r["region_nombre"] = nombres
    r["pob_15_64"] = ind.pob_15_64
    for a in (2010, 2019, 2022, 2024, 2025):
        r[f"cobertura_{a}"] = cob[a].reindex(r.index)
    r["cobertura_2010"] = r.cobertura_2010.where(~r.index.isin([8, 16]))  # Biobío y Ñuble separados solo desde 2018
    cotz = t.pivot(index="territorio_id", columns="anio", values="cotizantes")
    r["anio_ref"] = ANIO_REF
    r["cobertura_ref"] = cob[ANIO_REF].reindex(r.index)
    r["cambio_2019_ref"] = r.cobertura_ref - r.cobertura_2019
    r["cambio_2022_ref"] = r.cobertura_ref - r.cobertura_2022
    r["peso_cotizantes_pct"] = 100 * cotz[ANIO_REF].reindex(r.index) / cotz.loc[0, ANIO_REF]  # parte de los cotizantes del país (con región)
    r["cambio_2010_2025"] = r.cobertura_2025 - r.cobertura_2010
    r["cambio_2019_2025"] = r.cobertura_2025 - r.cobertura_2019
    r["cambio_2022_2025"] = r.cobertura_2025 - r.cobertura_2022
    nac25 = cob.loc[0, 2025]
    nac_ref = cob.loc[0, ANIO_REF]
    # brecha de cotizantes: cuántos cotizantes más habría si la región alcanzara la cobertura del país (pesa tanto el nivel como el tamaño)
    r["brecha_cotizantes"] = (nac_ref - r.cobertura_ref).clip(lower=0) / 100 * r.pob_15_64
    top = lambda rank: rank.where(rank <= N_PRIORIDAD)  # noqa: E731
    # cuatro listas de las 5 regiones «más importantes» (el dashboard deja elegir; ver docs/SHORTLIST_REGIONES.md)
    r["prioridad_brecha"] = top(r.brecha_cotizantes.rank(ascending=False, method="first"))  # nivel × tamaño
    r["prioridad_caida"] = top(r.cambio_2022_ref.rank(method="first"))  # caída de la cobertura desde 2022 (puntos), la más fuerte primero
    r["prioridad_peso"] = top(r.peso_cotizantes_pct.rank(ascending=False, method="first"))  # parte de los cotizantes del país
    cae = (r.brecha_cotizantes > 0) & (r.cambio_2022_ref < 0)  # bajo el promedio de Chile y bajando
    r["prioridad_brecha_caida"] = top((r.brecha_cotizantes + 1e9 * cae).rank(ascending=False, method="first"))  # primero las que caen, por brecha
    r["prioridad"] = r.prioridad_brecha_caida  # la recomendada: la que muestra el dashboard por defecto
    f = factores_censo()
    cor = pd.read_csv(DP / "kpi_cobertura_correlaciones_region.csv").set_index("region_id")
    for c in ("ingreso_per_capita_prom", "pct_pobreza_65", "pct_urbano", "pct_65_mas"):
        f[c] = cor[c]
        f.loc[0, c] = np.average(cor[c], weights=ind.pob_total.reindex(cor.index))  # Chile: promedio ponderado por población
    f_regiones = f.drop(index=0)
    f_pais = f.loc[[0]].assign(region_nombre="Chile", pob_15_64=ind.pob_15_64.sum(), cobertura_2025=nac25, cobertura_ref=nac_ref, anio_ref=ANIO_REF)
    r = r.join(f_regiones)
    r = pd.concat([f_pais, r])
    r.index.name = "region_id"
    r.round(4).reset_index().to_csv(DP / "kpi_cobertura_regiones.csv", index=False)
    f = f_regiones

    filas = []
    y = cor.cobertura_previsional_pct.reindex(f.index)
    for k, (nombre, hip, fuente, ambito) in FACTORES.items():
        x = f[k]
        rp, p = pearsonr(x, y)
        rs, _ = spearmanr(x, y)
        filas.append(dict(factor=k, nombre=nombre, hipotesis=hip, fuente=fuente, ambito=ambito, n=len(x), pearson_r=rp, pearson_p=p, spearman_rho=rs))
    fac = pd.DataFrame(filas)
    fac["abs_r"] = fac.pearson_r.abs()
    fac = fac.sort_values("abs_r", ascending=False).reset_index(drop=True)
    fac["ranking"] = fac.index + 1
    # los 5 factores que se muestran: la mejor medida de cada hipótesis del profesor (desempleo, informalidad, industria, migración)
    # más la mejor de las otras; solo con p < 0,05 (con 16 regiones y 30 factores probados, algunos saldrán por azar: ver docs)
    mejor = fac[fac.pearson_p < 0.05].groupby("hipotesis").head(1)
    fac["elegido"] = fac.factor.isin(mejor.factor) & fac.hipotesis.isin(["Desempleo", "Informalidad (aproximación)", "Industria", "Migración", "Otros"])
    fac.drop(columns="abs_r").round(4).to_csv(DP / "kpi_cobertura_factores.csv", index=False)

    p = lambda v: f"{v:.1f}".replace(".", ",")  # noqa: E731
    print(f"cobertura del país 2010 / 2019 / 2022 / 2025: {p(cob.loc[0, 2010])} / {p(cob.loc[0, 2019])} / {p(cob.loc[0, 2022])} / {p(cob.loc[0, 2025])}")
    print("prioridad (bajo el promedio de Chile y cayendo desde 2022, por brecha de cotizantes):")
    print(r[r.prioridad.notna()].sort_values("prioridad")[["region_nombre", "cobertura_ref", "cambio_2019_ref", "cambio_2022_ref", "brecha_cotizantes"]]
          .round(1).to_string())
    print("factores con mayor correlación con la cobertura 2024:")
    print(fac[["nombre", "hipotesis", "pearson_r", "pearson_p", "elegido"]].head(12).round(2).to_string(index=False))
    print("factores elegidos:", list(fac[fac.elegido].nombre))


if __name__ == "__main__":
    sys.exit(main())
