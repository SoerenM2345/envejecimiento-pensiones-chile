"""
KPI 1.1, causas de la cobertura por región: descomposición en factores y datos de la Encuesta Nacional de Empleo (ENE) y del Banco Central.

Es una exploración (sin regresión: con 16 regiones no alcanza). Ejecutar DESPUÉS de Scripts/24_cobertura_tendencia_causas.py, que
deja la tendencia, la prioridad y los factores del Censo; este script agrega los factores oficiales de la ENE y del PIB regional,
y recalcula cuáles se muestran.

Fuentes (Data raw/_external/ine_ene_regional/, bcentral_pib_regional/ y aafp_cobertura_regiones/, descargadas a mano del explorador de datos del INE y del Banco Central; los archivos tienen
nombres con código y se reconocen por su contenido, no por el nombre):
  - ENE, INE, «Nacional y regional, según sexo, trimestre móvil», proyecciones base 2017, ambos sexos, 2010 a mar-may 2024:
    ocupados, desocupados, ocupados informales (desde jul-sep 2017), tasa de ocupación informal, tasa de ocupación en el sector
    informal, tasa informal sin el sector agropecuario y tasa de tiempo parcial involuntario.
  - bcentral_pib_regional/CCNN2018_PIB_REGIONAL_T.xlsx, Banco Central: PIB trimestral por región, volumen encadenado, referencia 2018. Trae 15 regiones
    (falta Magallanes) y solo el total, no la actividad.
  - aafp_cobertura_regiones/Estudio-AAFP-cotizacion-previsional-por-regiones.pdf, Asociación de AFP (IPE N° 135): tabla de contraste de diciembre 2019 y 2024.
  - Data processed/cotizantes_por_region.csv (Superintendencia de Pensiones, cotizantes de diciembre) y la población del INE base 2017
    (Data raw/_external/ine_proyecciones_base2017/), con el mismo ajuste al Censo 2024 del script 24.

Descomposición (identidad exacta, por región y año; el trimestre móvil nov-ene es el que el INE llama «diciembre»):
    cobertura = (fuerza de trabajo / pob. 15-64) × (ocupados / fuerza de trabajo) × (cotizantes / ocupados)
                  participación                    empleo (1 − desocupación)        cotización de los ocupados
  La fuerza de trabajo incluye a las personas de 65+ que trabajan (la ENE mide desde los 15 años): la participación sobre 15-64 mezcla
  la participación y el envejecimiento, que se compensan (más mayores bajan la participación de 15+ y suben el cociente 15+/15-64).
  El Censo 2024 manda: la población 15-64 se lleva a su nivel con el factor de cada región (script 24). La ENE expande los ocupados con
  esa misma proyección 2017, así que ocupados y fuerza de trabajo se llevan con el MISMO factor (supuesto: la proyección se equivoca en
  la misma proporción en las personas y en los ocupados). Así el empleo no cambia (es un cociente) y los cotizantes, que son un
  registro administrativo, se comparan con ocupados al nivel del Censo.
  Los aportes en puntos se reparten con la media logarítmica (LMDI): suman exacto la diferencia de cobertura.
  Límite: la ENE del INE llega a mar-may 2024; diciembre de 2024 (el «hoy» de la descomposición) sale del anexo del estudio de la Asociación de AFP.
  Para 2025 no hay ocupados por región.

Salidas (Data processed/):
  - ene_region_anual.csv                   una fila por territorio y año (diciembre), con los datos de la ENE y el PIB
  - kpi_cobertura_factores_anual.csv       los factores de la descomposición por territorio y año
  - kpi_cobertura_descomposicion.csv       aporte de cada factor en puntos: nivel frente a Chile y cambios entre años
  - kpi_cobertura_contraste_aafp.csv       nuestras cifras de diciembre 2019 y 2024 junto a las del estudio de la AAFP
  - kpi_cobertura_test_asignacion.csv      participación de la Metropolitana en cotizantes, ocupados y población
  - kpi_cobertura_pendularidad.csv         ocupados que viven en una región y trabajan en otra (Censo 2024) y la cobertura si los cotizantes se contaran por lugar de trabajo
  - kpi_cobertura_siete_vs_chile.csv       las regiones prioritarias recomendadas juntas frente a Chile y frente a las demás (y docs/SIETE_VS_CHILE.md)
  - kpi_pc_escenarios_fijos.csv            los 6 escenarios fijos del KPI 1.2 (tope 10/11/12 %, cobertura que sigue cayendo, sin informalidad
                                           y mitad del camino); los calcula el dashboard con el motor de components/critical_point.py
  - kpi_cobertura_factores.csv y kpi_cobertura_regiones.csv: se les agregan los factores de la ENE y del PIB (idempotente)
"""
import importlib.util
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

ROOT = Path(__file__).resolve().parent.parent
DP = ROOT / "Data processed"
EXT = ROOT / "Data raw" / "_external"
ENE_DIR = EXT / "ine_ene_regional"
PIB_XLSX = EXT / "bcentral_pib_regional" / "CCNN2018_PIB_REGIONAL_T.xlsx"
CENSO = ROOT / "Data raw" / "personas_censo2024.csv"
NS = {"s": "urn:schemas-microsoft-com:office:spreadsheet"}

ANIOS = range(2010, 2025)  # diciembre de cada año (nov-ene): ENE hasta 2023 y, para 2024, el anexo del estudio de la Asociación de AFP
ID_BIOBIO_NUBLE = 816
FACTORES_DESC = ["participacion", "empleo", "cotizacion"]
NOMBRE_FACTOR = {
    "participacion": "Participación laboral (de 15 a 64 años)", "empleo": "Empleo (1 − desocupación)", "cotizacion": "Ocupados que cotizan",
}

# AAFP, Informe Previsional Económico N° 135 (mayo 2025), anexo p. 14 y gráficos p. 4-8: diciembre 2019 y diciembre 2024.
# Transcrito del PDF (Data raw/_external/aafp_cobertura_regiones/); orden de las regiones: 15, 1, 2, 3, 4, 5, 13, 6, 7, 16, 8, 9, 14, 10, 11, 12.
AAFP_ORDEN = [15, 1, 2, 3, 4, 5, 13, 6, 7, 16, 8, 9, 14, 10, 11, 12]
AAFP = pd.DataFrame({
    "region_id": AAFP_ORDEN,
    "ocupados_2019": [112880, 164390, 317037, 143918, 375059, 873469, 3974401, 464109, 535323, 233379, 702575, 450027, 198424, 417411, 59890, 93350],
    "ocupados_2024": [115220, 188980, 347573, 152052, 382046, 907774, 4139320, 467349, 535765, 224828, 725671, 440402, 191634, 417133, 59240, 99125],
    "desocupados_2024": [10131, 16612, 27629, 15475, 32416, 79965, 393492, 37209, 34674, 21834, 68902, 42586, 13978, 17888, 2579, 4062],
    "informales_2024": [34141, 55732, 65500, 44161, 117139, 274377, 938650, 133466, 163351, 77156, 187182, 162237, 62880, 112010, 19315, 20063],
    "desocupados_2019": [8159, 14176, 25902, 11939, 32544, 76622, 346836, 38986, 35460, 17724, 59158, 32093, 11616, 16168, 2168, 3493],
    "informales_2019": [40434, 48541, 74864, 39002, 130828, 252876, 1089269, 133041, 189283, 80911, 185423, 163069, 70070, 122635, 18433, 18169],
    "cobertura_ocupados_2019": [56.3, 59.6, 64.2, 63.5, 53.8, 59.1, 64.2, 62.7, 58.1, 52.6, 64.1, 52.0, 49.5, 60.1, 49.9, 64.1],
    "cobertura_ocupados_2024": [57.7, 58.2, 67.0, 65.6, 59.2, 58.7, 63.4, 70.2, 61.5, 57.2, 65.3, 55.7, 53.4, 63.7, 55.7, 62.7],
})


# Total país del anexo (diciembre 2024): ocupados, desocupados, informales
AAFP_PAIS_2024 = dict(ocupados=9394112, desocupados=819433, informales=2467359)


def cargar_modulo(nombre_archivo: str):
    spec = importlib.util.spec_from_file_location("s24", Path(__file__).parent / nombre_archivo)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ───────────────────────────── ENE (explorador de datos del INE: XML de Excel 2003) ─────────────────────────────

def leer_filas(path: Path) -> list:
    """Filas de la primera hoja de una exportación SpreadsheetML; cada fila es una lista de textos (None si la celda no existe)."""
    hoja = ET.parse(path).getroot().find("s:Worksheet", NS)
    filas = []
    for row in hoja.findall(".//s:Row", NS):
        fila = []
        for c in row.findall("s:Cell", NS):
            idx = c.get("{%s}Index" % NS["s"])
            if idx:
                fila += [None] * (int(idx) - 1 - len(fila))
            d = c.find("s:Data", NS)
            fila.append(None if d is None else "".join(d.itertext()))
        filas.append(fila)
    return filas


def id_region(nombre: str) -> int:
    n = nombre.lower()
    for clave, i in [("total país", 0), ("nationwide", 0), ("arica", 15), ("tarapac", 1), ("antofagasta", 2), ("atacama", 3), ("coquimbo", 4),
                     ("valpara", 5), ("metropolitana", 13), ("o'higgins", 6), ("ohiggins", 6), ("libertador", 6), ("maule", 7), ("ñuble", 16), ("biob", 8), ("araucan", 9),
                     ("los ríos", 14), ("de los r", 14), ("los lagos", 10), ("ays", 11), ("magallanes", 12)]:
        if clave in n:
            return i
    raise ValueError(nombre)


def serie_regional(path: Path):
    """(clave, DataFrame trimestre × id de región) si el archivo es una serie por región de ambos sexos; si no, None."""
    filas = leer_filas(path)
    k = next(i for i, r in enumerate(filas) if r and r[0] and r[0][:2] == "20")
    cab = {r[0]: [x for x in r[1:] if x] for r in filas[:k] if r and r[0]}
    region = cab.get("Región") or cab.get("Region") or []
    sexo = cab.get("Sexo") or cab.get("Sex") or []
    if len(region) != 17 or sexo not in (["Ambos sexos"], ["Total"]):
        return None  # cortes por edad o nivel educacional, solo país: no sirven para comparar regiones
    titulo = filas[1][0].lower()
    indicador = " ".join(cab.get("Indicador") or cab.get("Indicator") or []).lower()
    clave = None
    if "ocupados informales" in titulo:
        clave = "informales"
    elif "excluyendo al sector agropecuario" in titulo:
        clave = "tasa_informal_sin_agro"
    elif "sector informal" in titulo:
        clave = "tasa_sector_informal"
    elif titulo.startswith("dataset: tasa de ocupación informal"):
        clave = "tasa_informal"
    elif "tiempo parcial involuntario" in titulo:
        clave = "tasa_parcial_involuntario"
    elif titulo.startswith("dataset: ocupados") and "ocupados (proyecciones" in indicador:
        clave = "ocupados"
    elif titulo.startswith("dataset: desocupados"):
        clave = "desocupados"
    if clave is None:
        return None
    datos = {r[0]: [float(r[3 + 2 * i]) if 3 + 2 * i < len(r) and r[3 + 2 * i] not in (None, "") else np.nan for i in range(17)]
             for r in filas[k:] if r and r[0] and r[0][:2] == "20"}
    return clave, pd.DataFrame(datos, index=[id_region(n) for n in region]).T


def ene_anual() -> pd.DataFrame:
    """Diciembre de cada año (trimestre nov-ene) por región: ocupados, desocupados, informales (personas) y tasas (%)."""
    series = {}
    for f in sorted(ENE_DIR.glob("*.xls")):
        r = serie_regional(f)
        if r and r[0] not in series:  # hay una copia en inglés de la tasa informal: vale la primera
            series[r[0]] = r[1]
    faltan = {"ocupados", "desocupados", "informales", "tasa_informal", "tasa_sector_informal", "tasa_informal_sin_agro",
              "tasa_parcial_involuntario"} - set(series)
    if faltan:
        raise SystemExit(f"faltan series de la ENE en {ENE_DIR}: {sorted(faltan)} (ver docs/EXPLORACION_COBERTURA.md)")
    filas = []
    for clave, d in series.items():
        d = d[[i.endswith(" nov-ene") for i in d.index]].copy()
        d.index = [int(i[:4]) for i in d.index]
        d = d.stack().rename(clave).reset_index()
        d.columns = ["anio", "territorio_id", clave]
        filas.append(d.set_index(["anio", "territorio_id"]))
    e = pd.concat(filas, axis=1).reset_index()
    for c in ("ocupados", "desocupados", "informales"):
        e[c] = e[c] * 1000  # el INE publica en miles de personas
    e = e.assign(fuente="ENE, INE (explorador de datos)")
    e = pd.concat([e, ene_2024_aafp()], ignore_index=True)
    return e[e.anio.isin(ANIOS) | e.anio.isin([2017, 2018])].sort_values(["territorio_id", "anio"]).reset_index(drop=True)


def ene_2024_aafp() -> pd.DataFrame:
    """Diciembre de 2024 (el último con ocupados y desocupados por región): el anexo del estudio de la Asociación de AFP, que trae la ENE
    del INE. El mismo anexo reproduce al decimal los datos de 2019 de las exportaciones del INE (contraste en kpi_cobertura_contraste_aafp.csv),
    así que es la misma serie. Solo ocupados, desocupados e informales; las demás columnas quedan vacías."""
    r = AAFP.set_index("region_id")
    filas = [dict(anio=2024, territorio_id=i, ocupados=float(r.loc[i, "ocupados_2024"]), desocupados=float(r.loc[i, "desocupados_2024"]),
                  informales=float(r.loc[i, "informales_2024"])) for i in r.index]
    filas.append(dict(anio=2024, territorio_id=0, **{k: float(x) for k, x in AAFP_PAIS_2024.items()}))
    d = pd.DataFrame(filas)
    d["tasa_informal"] = 100 * d.informales / d.ocupados
    return d.assign(fuente="Anexo del estudio de la Asociación de AFP (ENE, INE)")



def pib_anual() -> pd.DataFrame:
    """PIB anual por región (miles de millones de pesos encadenados, referencia 2018): suma de los 4 trimestres de los años completos."""
    x = pd.read_excel(PIB_XLSX, sheet_name="Cuadro", header=None)
    fechas = pd.to_datetime(x.iloc[2, 2:])
    filas = []
    for _, r in x.iloc[3:].iterrows():
        tid = id_region(str(r[1]))
        s = pd.Series(r[2:].astype(float).values, index=fechas)
        for a, g in s.groupby(s.index.year):
            if len(g) == 4:
                filas.append((tid, a, g.sum()))
    return pd.DataFrame(filas, columns=["territorio_id", "anio", "pib_mmm"])


# ───────────────────────────── población y descomposición ─────────────────────────────

def poblaciones(s24, ind: pd.DataFrame) -> dict:
    """Población INE base 2017 (15-64, 15+ y total) por región y año, y el factor del Censo 2024 (constante por región)."""
    d = pd.read_excel(s24.INE17)
    d.columns = [c.split("\n")[0] for c in d.columns]
    anios = [c for c in d.columns if c.startswith("Poblacion")]
    out = {}
    for nombre, cond in {"p1564": (d.Edad >= 15) & (d.Edad <= 64), "p15": d.Edad >= 15, "ptot": d.Edad >= 0}.items():
        g = d[cond].groupby("Region")[anios].sum()
        g.columns = [int(c.split()[-1]) for c in g.columns]
        out[nombre] = g
    out["escala"] = ind.pob_15_64 / out["p1564"][2024]  # Censo 2024 / proyección 2017 en 2024
    return out


def territorios(valores: dict, anio: int) -> pd.DataFrame:
    """Reúne las regiones en los territorios de la descomposición: 16 regiones, Biobío y Ñuble juntas y Chile (suma de las 16)."""
    filas = {}
    for r in range(1, 17):
        filas[r] = {k: v[r] for k, v in valores.items()}
    filas[ID_BIOBIO_NUBLE] = {k: v[8] + v[16] for k, v in valores.items()}
    filas[0] = {k: sum(v[r] for r in range(1, 17)) for k, v in valores.items()}
    return pd.DataFrame(filas).T.assign(anio=anio)


def factores_anuales(s24, ind, ene, pob) -> pd.DataFrame:
    nombres = {**ind.region_nombre.to_dict(), 0: "Chile", ID_BIOBIO_NUBLE: "Biobío y Ñuble"}
    c = pd.read_csv(DP / "cotizantes_por_region.csv")
    c = c[c.region_id.notna()].assign(region_id=lambda x: x.region_id.astype(int)).pivot(index="region_id", columns="anio", values="cotizantes")
    e = ene.set_index(["anio", "territorio_id"])
    esc = pob["escala"]
    filas = []
    for a in ANIOS:
        v = {  # todo al nivel del Censo 2024: cada región con su factor (cotizantes: registro administrativo, sin ajuste)
            "ocupados": {r: e.loc[(a, r), "ocupados"] * esc[r] for r in range(1, 17)},
            "desocupados": {r: e.loc[(a, r), "desocupados"] * esc[r] for r in range(1, 17)},
            "cotizantes": {r: (c.loc[r, a] if r in c.index and not np.isnan(c.loc[r, a]) else np.nan) for r in range(1, 17)},
            "p1564": {r: pob["p1564"].loc[r, a] * esc[r] for r in range(1, 17)},
            "p15": {r: pob["p15"].loc[r, a] * esc[r] for r in range(1, 17)},
        }
        if a < 2018:
            v["cotizantes"][8] = c.loc[8, a]  # hasta 2017 Biobío ya incluye a Ñuble
            v["cotizantes"][16] = 0.0
        filas.append(territorios(v, a))
    f = pd.concat(filas).reset_index(names="territorio_id")
    f["territorio"] = f.territorio_id.map(nombres)
    f["fuerza_trabajo"] = f.ocupados + f.desocupados
    f["cobertura_pct"] = 100 * f.cotizantes / f.p1564
    f["participacion"] = f.fuerza_trabajo / f.p1564
    f["empleo"] = f.ocupados / f.fuerza_trabajo
    f["cotizacion"] = f.cotizantes / f.ocupados
    f = f[~((f.anio < 2018) & f.territorio_id.isin([8, 16]))]  # hasta 2017 Biobío incluye a Ñuble: solo vale la serie conjunta
    ident = np.prod([f[k] for k in FACTORES_DESC], axis=0) * 100
    assert np.allclose(ident, f.cobertura_pct), "la descomposición no reproduce la cobertura"
    return f.reset_index(drop=True)


def media_log(a: float, b: float) -> float:
    return a if np.isclose(a, b) else (a - b) / (np.log(a) - np.log(b))


def descomposicion(f: pd.DataFrame, nivel_anio: int = 2024, cambios=((2019, 2024), (2023, 2024), (2010, 2019))) -> pd.DataFrame:
    """Aporte de cada factor a (a) la diferencia con Chile en un año y (b) el cambio entre años, en puntos (LMDI: suma exacta)."""
    g = f.set_index(["territorio_id", "anio"])
    filas = []
    for tid in f.territorio_id.unique():
        nombre = g.loc[(tid, nivel_anio if (tid, nivel_anio) in g.index else g.loc[tid].index[0]), "territorio"]
        comparaciones = []
        if tid != 0:
            comparaciones.append((f"Nivel frente a Chile en {nivel_anio}", g.loc[(tid, nivel_anio)], g.loc[(0, nivel_anio)]))
        for a0, a1 in cambios:
            if (tid, a0) in g.index and (tid, a1) in g.index:
                comparaciones.append((f"Cambio {a0}-{a1}", g.loc[(tid, a1)], g.loc[(tid, a0)]))
        for etiqueta, x, y in comparaciones:
            L = media_log(x.cobertura_pct, y.cobertura_pct)
            for k in FACTORES_DESC:
                filas.append((tid, nombre, etiqueta, k, NOMBRE_FACTOR[k], L * (np.log(x[k]) - np.log(y[k]))))
    return pd.DataFrame(filas, columns=["territorio_id", "territorio", "comparacion", "factor", "factor_nombre", "aporte_pp"])


# ───────────────────────────── contraste con la AAFP y prueba de asignación regional ─────────────────────────────

def contraste_aafp(f: pd.DataFrame, ene: pd.DataFrame, cot: pd.DataFrame) -> pd.DataFrame:
    e = ene.set_index(["anio", "territorio_id"])
    filas = []
    for r in AAFP.itertuples():
        o19 = e.loc[(2019, r.region_id), "ocupados"]
        c19 = cot.loc[r.region_id, 2019] if r.region_id not in (8, 16) else np.nan
        filas.append(dict(
            region_id=r.region_id, ocupados_ine_2019=o19, ocupados_aafp_2019=r.ocupados_2019, dif_ocupados_pct=100 * (o19 / r.ocupados_2019 - 1),
            desocupacion_ine_2019=100 * e.loc[(2019, r.region_id), "desocupados"] / (o19 + e.loc[(2019, r.region_id), "desocupados"]),
            desocupacion_aafp_2019=100 * r.desocupados_2019 / (r.ocupados_2019 + r.desocupados_2019),
            informalidad_ine_2019=e.loc[(2019, r.region_id), "tasa_informal"], informalidad_aafp_2019=100 * r.informales_2019 / r.ocupados_2019,
            cot_sobre_ocupados_2019=100 * cot.loc[r.region_id, 2019] / o19, cobertura_ocupados_aafp_2019=r.cobertura_ocupados_2019,
            cot_sobre_ocupados_2024_con_aafp=100 * cot.loc[r.region_id, 2024] / r.ocupados_2024, cobertura_ocupados_aafp_2024=r.cobertura_ocupados_2024,
        ))
    return pd.DataFrame(filas)


def test_asignacion(f: pd.DataFrame, ene: pd.DataFrame, ind: pd.DataFrame) -> pd.DataFrame:
    """Paso 0: ¿la Metropolitana pesa en los cotizantes más que en los ocupados? (sin concluir más: ver docs/supuestos_y_limitaciones.md)."""
    g = f.set_index(["territorio_id", "anio"])
    c = pd.read_csv(DP / "cotizantes_por_region.csv")
    c = c[c.region_id.notna()].assign(region_id=lambda x: x.region_id.astype(int)).pivot(index="region_id", columns="anio", values="cotizantes")
    filas = []
    for a in (2010, 2015, 2019, 2023):
        tot_c = c.loc[1:16, a].sum()
        e = ene[(ene.anio == a) & (ene.territorio_id.between(1, 16))]
        filas.append(dict(
            fuente=f"diciembre {a}", cotizantes_pct=100 * c.loc[13, a] / tot_c,
            ocupados_ene_pct=100 * e[e.territorio_id == 13].ocupados.iloc[0] / e.ocupados.sum(),
            pob_15_64_pct=100 * g.loc[(13, a), "p1564"] / g.loc[(0, a), "p1564"]))
    con = duckdb.connect()
    cen = con.execute(f"""SELECT sum((region=13 AND sit_fuerza_trabajo=1)::int)*100.0/sum((sit_fuerza_trabajo=1)::int) o,
                                 sum((region=13 AND edad BETWEEN 15 AND 64)::int)*100.0/sum((edad BETWEEN 15 AND 64)::int) p
                          FROM read_csv_auto('{CENSO.as_posix()}', delim=';', sample_size=300000)""").df().iloc[0]
    filas.append(dict(fuente="Censo 2024 (abril)", cotizantes_pct=100 * c.loc[13, 2024] / c.loc[1:16, 2024].sum(),
                      ocupados_ene_pct=cen.o, pob_15_64_pct=cen.p))
    return pd.DataFrame(filas)


# ───────────────────────────── factores de la ENE y del PIB para la correlación con la cobertura ─────────────────────────────

def factores_ene_pib(ene, pib, pob, ind, f, censo_part_mujeres, extra) -> pd.DataFrame:
    """Un valor por territorio (0 = Chile, 1-16 = regiones) de cada factor oficial, medido en diciembre de 2023 (último diciembre con
    ENE); cambios 2019-2023. El PIB no tiene Chile ni Magallanes: quedan vacíos."""
    e = ene.set_index(["anio", "territorio_id"])
    ids = list(range(0, 17))
    p15 = lambda a: {**{r: pob["p15"][a][r] for r in range(1, 17)}, 0: pob["p15"][a].loc[1:16].sum()}  # noqa: E731
    desoc = lambda a, r: 100 * e.loc[(a, r), "desocupados"] / (e.loc[(a, r), "ocupados"] + e.loc[(a, r), "desocupados"])  # noqa: E731
    partic = lambda a, r: 100 * (e.loc[(a, r), "ocupados"] + e.loc[(a, r), "desocupados"]) / p15(a)[r]  # noqa: E731
    out = pd.DataFrame(index=ids)
    out["desocupacion_ene"] = [desoc(2023, r) for r in ids]
    out["informalidad_ene"] = [e.loc[(2023, r), "tasa_informal"] for r in ids]
    out["informalidad_sin_agro_ene"] = [e.loc[(2023, r), "tasa_informal_sin_agro"] for r in ids]
    out["sector_informal_ene"] = [e.loc[(2023, r), "tasa_sector_informal"] for r in ids]
    out["tiempo_parcial_ene"] = [e.loc[(2023, r), "tasa_parcial_involuntario"] for r in ids]
    out["participacion_ene"] = [partic(2023, r) for r in ids]
    out["participacion_mujeres_censo"] = [censo_part_mujeres[r] for r in ids]
    for c in extra.columns:
        out[c] = [extra.loc[r, c] for r in ids]
    pt = pob["ptot"].mul(pob["escala"], axis=0)  # población total al nivel del Censo (el mismo ajuste de la cobertura)
    pb = pib.pivot(index="territorio_id", columns="anio", values="pib_mmm")
    tiene = lambda r: r in pb.index and r != 0  # noqa: E731
    out["pib_per_capita"] = [1e3 * pb.loc[r, 2023] / pt.loc[r, 2023] if tiene(r) else np.nan for r in ids]  # millones de pesos por habitante
    out["pib_por_ocupado"] = [1e3 * pb.loc[r, 2023] / (e.loc[(2023, r), "ocupados"] * pob["escala"][r]) if tiene(r) else np.nan for r in ids]
    out["crecimiento_pib"] = [100 * ((pb.loc[r, 2023] / pb.loc[r, 2013]) ** (1 / 10) - 1) if tiene(r) else np.nan for r in ids]
    out["cambio_desocupacion"] = [desoc(2023, r) - desoc(2019, r) for r in ids]
    out["cambio_informalidad"] = [e.loc[(2023, r), "tasa_informal"] - e.loc[(2019, r), "tasa_informal"] for r in ids]
    out["cambio_participacion"] = [partic(2023, r) - partic(2019, r) for r in ids]
    g = f.set_index(["territorio_id", "anio"]).cobertura_pct
    out["_cambio_cobertura"] = [g[(r, 2023)] - g[(r, 2019)] for r in ids]
    return out


FACTORES_NUEVOS = {  # factor -> (nombre legible, hipótesis, fuente, ámbito, objetivo)
    "desocupacion_ene": ("Desocupación oficial (% de la fuerza de trabajo)", "Desempleo", "ENE (INE), dic. 2023", "regiones", "nivel"),
    "informalidad_ene": ("Ocupados informales (tasa oficial, %)", "Informalidad", "ENE (INE), dic. 2023", "regiones", "nivel"),
    "informalidad_sin_agro_ene": ("Ocupados informales sin agricultura (%)", "Informalidad", "ENE (INE), dic. 2023", "regiones", "nivel"),
    "sector_informal_ene": ("Ocupados en el sector informal (%)", "Informalidad", "ENE (INE), dic. 2023", "regiones", "nivel"),
    "tiempo_parcial_ene": ("Tiempo parcial involuntario (%)", "Otros", "ENE (INE), dic. 2023", "regiones", "nivel"),
    "participacion_ene": ("Participación laboral oficial (% de las personas de 15+)", "Otros", "ENE (INE), dic. 2023", "regiones", "nivel"),
    "participacion_mujeres_censo": ("Participación laboral de las mujeres (% de las de 15+)", "Otros", "Censo 2024", "regiones", "nivel"),
    "participacion_15_64_censo": ("Participación laboral de 15 a 64 años (sin el efecto de los mayores)", "Otros", "Censo 2024", "regiones", "nivel"),
    "indigena_pct": ("Población que se declara de un pueblo originario (%)", "Otros", "Censo 2024", "regiones", "nivel"),
    "rural_pct": ("Población rural (%)", "Otros", "Censo 2024", "regiones", "nivel"),
    "neto_pendular_pct": ("Saldo de pendulares entre regiones (% de los ocupados que viven allí)", "Medición", "Censo 2024", "regiones", "nivel"),
    "salida_pendular_pct": ("Ocupados que trabajan en otra región (%)", "Medición", "Censo 2024", "regiones", "nivel"),
    "pib_per_capita": ("PIB por habitante", "Otros", "Banco Central, 2023", "15 regiones (sin Magallanes)", "nivel"),
    "pib_por_ocupado": ("PIB por ocupado", "Otros", "Banco Central e INE, 2023", "15 regiones (sin Magallanes)", "nivel"),
    "crecimiento_pib": ("Crecimiento anual del PIB 2013-2023 (%)", "Otros", "Banco Central", "15 regiones (sin Magallanes)", "nivel"),
    "cambio_desocupacion": ("Cambio de la desocupación 2019-2023 (puntos)", "Desempleo", "ENE (INE)", "regiones", "cambio"),
    "cambio_informalidad": ("Cambio de la informalidad 2019-2023 (puntos)", "Informalidad", "ENE (INE)", "regiones", "cambio"),
    "cambio_participacion": ("Cambio de la participación 2019-2023 (puntos)", "Otros", "ENE (INE)", "regiones", "cambio"),
}
REPRESENTANTES = ["desocupacion_ene", "informalidad_ene", "migracion_interna_neta"]  # desempleo, informalidad, migración


def participacion_mujeres() -> dict:
    con = duckdb.connect()
    d = con.execute(f"""SELECT coalesce(region, 0) region, sum((sit_fuerza_trabajo IN (1,2))::int)*100.0/sum((sit_fuerza_trabajo IN (1,2,3))::int) p
                        FROM read_csv_auto('{CENSO.as_posix()}', delim=';', sample_size=300000) WHERE sexo=2 AND edad>=15
                        GROUP BY GROUPING SETS ((region), ())""").df()
    return d.set_index("region").p.to_dict()


def pendularidad(ref: int = 2024) -> pd.DataFrame:
    """Ocupados que viven en una región y trabajan en otra (Censo 2024: p44_lug_trab = 3 «en otra comuna», con la comuna de destino en
    p44_lug_trab_esp; los códigos de lugar de trabajo se infieren, no hay diccionario en el proyecto). Una fila por región (1-16) con los que salen,
    los que entran y el saldo, y una sensibilidad a la regla de asignación que NO conocemos: si la Superintendencia contara a cada cotizante en la
    región del empleo y no en la de residencia, la cobertura de una región sería cotizantes ÷ (población 15-64 + saldo de pendulares)."""
    con = duckdb.connect()
    src = f"read_csv_auto('{CENSO.as_posix()}', delim=';', sample_size=300000)"
    res = con.execute(f"SELECT region, count(*) ocupados_residentes FROM {src} WHERE sit_fuerza_trabajo=1 GROUP BY 1").df().set_index("region")
    sal = con.execute(f"""SELECT region, floor(p44_lug_trab_esp/1000)::int destino, count(*) n FROM {src}
                          WHERE sit_fuerza_trabajo=1 AND p44_lug_trab=3 AND p44_lug_trab_esp>0 GROUP BY ALL""").df()
    sal = sal[sal.region != sal.destino]
    d = res.assign(salen=sal.groupby("region").n.sum(), entran=sal.groupby("destino").n.sum()).fillna(0)
    d["neto"] = d.entran - d.salen
    d["neto_pct"] = 100 * d.neto / d.ocupados_residentes
    d["salen_pct"] = 100 * d.salen / d.ocupados_residentes
    t = pd.read_csv(DP / "kpi_cobertura_tendencia.csv")
    t = t[(t.anio == ref) & t.territorio_id.between(1, 16)].set_index("territorio_id")
    d["cobertura_ref"] = t.cobertura_pct
    d["cobertura_si_lugar_de_trabajo"] = 100 * t.cotizantes / (t.pob_15_64 + d.neto)
    d["diferencia_puntos"] = d.cobertura_si_lugar_de_trabajo - d.cobertura_ref
    d.insert(0, "region_nombre", t.territorio)
    return d.reset_index(names="region_id")


def censo_extra(pend: pd.DataFrame) -> pd.DataFrame:
    """Factores del Censo 2024 que no estaban (0 = Chile, 1-16 = regiones): participación de 15 a 64 años, población que se declara de un
    pueblo originario, población rural y los pendulares entre regiones (neto y salida, en % de los ocupados que viven en la región)."""
    con = duckdb.connect()
    src = f"read_csv_auto('{CENSO.as_posix()}', delim=';', sample_size=300000)"
    a = con.execute(f"""SELECT coalesce(region, 0) region,
          sum((edad BETWEEN 15 AND 64 AND sit_fuerza_trabajo IN (1,2))::int)*100.0/sum((edad BETWEEN 15 AND 64)::int) participacion_15_64_censo,
          sum((p28_autoid_pueblo=1)::int)*100.0/sum((p28_autoid_pueblo IN (1,2))::int) indigena_pct,
          sum((area=2)::int)*100.0/count(*) rural_pct FROM {src} GROUP BY GROUPING SETS ((region), ())""").df().set_index("region")
    p = pend.set_index("region_id")
    a["neto_pendular_pct"] = p.neto_pct
    a["salida_pendular_pct"] = p.salen_pct
    a.loc[0, ["neto_pendular_pct", "salida_pendular_pct"]] = [0.0, 100 * p.salen.sum() / p.ocupados_residentes.sum()]
    return a.sort_index()


def actualizar_factores(nuevos: pd.DataFrame, cobertura_2024: pd.Series):
    """Agrega las columnas a kpi_cobertura_regiones.csv y las filas a kpi_cobertura_factores.csv (idempotente) y recalcula los mostrados."""
    cols = [k for k in FACTORES_NUEVOS]
    reg = pd.read_csv(DP / "kpi_cobertura_regiones.csv").drop(columns=[c for c in cols if c in pd.read_csv(DP / "kpi_cobertura_regiones.csv", nrows=1)], errors="ignore")
    reg = reg.merge(nuevos[cols].rename_axis("region_id").reset_index(), on="region_id", how="left")  # fila 0 = Chile
    reg.round(4).to_csv(DP / "kpi_cobertura_regiones.csv", index=False)

    fac = pd.read_csv(DP / "kpi_cobertura_factores.csv")
    fac = fac[~fac.factor.isin(cols)].copy()
    if "objetivo" not in fac:
        fac["objetivo"] = "nivel"
    filas = []
    for k, (nombre, hip, fuente, ambito, objetivo) in FACTORES_NUEVOS.items():
        y = cobertura_2024 if objetivo == "nivel" else nuevos["_cambio_cobertura"].loc[1:16]
        x = nuevos[k].loc[1:16]
        ok = x.notna() & y.notna()
        rp, p = pearsonr(x[ok], y[ok])
        rs, _ = spearmanr(x[ok], y[ok])
        filas.append(dict(factor=k, nombre=nombre, hipotesis=hip, fuente=fuente, ambito=ambito, n=int(ok.sum()), pearson_r=rp, pearson_p=p,
                          spearman_rho=rs, objetivo=objetivo))
    fac = pd.concat([fac.drop(columns=["ranking", "elegido"], errors="ignore"), pd.DataFrame(filas)], ignore_index=True)
    fac["hipotesis"] = fac.hipotesis.replace({"Informalidad (aproximación)": "Informalidad"})
    # Los que se muestran: la medida OFICIAL de cada hipótesis del profesor (desempleo e informalidad de la ENE, migración del Censo),
    # sea o no significativa (no se elige la que mejor calza); para la industria, la rama con mayor asociación entre las 12 probadas;
    # y para «1 o 2 más», las dos mejores de las demás con p < 0,05.
    nivel = fac[fac.objetivo == "nivel"].assign(abs_r=lambda d: d.pearson_r.abs()).sort_values("abs_r", ascending=False)
    elegidos = [*REPRESENTANTES, nivel[nivel.hipotesis == "Industria"].factor.iloc[0]]
    otros = nivel[nivel.hipotesis.isin(["Otros", "Educación"]) & (nivel.pearson_p < 0.05)].factor.head(2)
    fac["elegido"] = fac.factor.isin([*elegidos, *otros]) & (fac.objetivo == "nivel")
    fac = fac.assign(abs_r=fac.pearson_r.abs()).sort_values(["objetivo", "abs_r"], ascending=[False, False]).drop(columns="abs_r").reset_index(drop=True)
    fac["ranking"] = fac.groupby("objetivo").cumcount() + 1
    fac.round(4).to_csv(DP / "kpi_cobertura_factores.csv", index=False)
    return fac


def escenarios_fijos_kpi12(ene: pd.DataFrame) -> pd.DataFrame:
    """Parámetros de los 6 escenarios fijos del KPI 1.2 (país). Todo lo demás, como en config/escenarios.yaml.
      - Tope de carga 10, 11 y 12 %: la cobertura queda como hoy.
      - Cobertura que sigue cayendo: la pendiente de la cobertura de Chile 2022-2025 (ajuste lineal, 4 años) se prolonga hasta 2050 y después
        queda constante (así es el motor: tramo lineal hasta `cobertura_2050`).
      - Sin informalidad: los ocupados informales de hoy (ENE, diciembre 2023, llevados al nivel del Censo con el factor de la población)
        pasan a cotizar desde 2026: cotizantes × (1 + informales ÷ cotizantes). Supone el mismo ingreso imponible promedio y que los informales no
        están hoy entre los cotizantes; es el techo teórico, no una proyección.
      - Mitad del camino: la mitad de ese aumento."""
    n = pd.read_csv(DP / "kpi_pc_nacional.csv").set_index("anio")
    cob = 100 * n.cotizantes_dic_con_region / (n.pob_15_64_ine * n.factor_censo_15_64)
    pend = float(np.polyfit(np.arange(2022, 2026), cob.loc[2022:2025].to_numpy(), 1)[0])  # puntos de cobertura por año
    cob_2050 = 1 + pend * (2050 - 2025) / float(cob[2025])
    inf = float(ene[(ene.territorio_id == 0) & (ene.anio == 2023)].informales.iloc[0]) * float(n.loc[2023, "factor_censo_15_64"])
    salto = 1 + inf / float(n.loc[2023, "cotizantes_dic_con_region"])
    filas = [
        ("tope_10", "Tope de carga 10 % (base)", "Tope de carga", 0.10, 1.0, 1.0, "La cotización obligatoria para pensión; la cobertura queda como hoy"),
        ("tope_11", "Tope de carga 11 %", "Tope de carga", 0.11, 1.0, 1.0, "El sistema tolera 11 % del sueldo; la cobertura queda como hoy"),
        ("tope_12", "Tope de carga 12 %", "Tope de carga", 0.12, 1.0, 1.0, "El sistema tolera 12 % del sueldo; la cobertura queda como hoy"),
        ("cobertura_cae", "Cobertura sigue cayendo", "Cobertura", 0.10, cob_2050, 1.0,
         f"La cobertura baja {abs(pend):.2f} puntos por año (tendencia 2022-2025, ajuste lineal) hasta 2050, de {cob[2025]:.1f} % a {cob[2025] + pend * 25:.1f} %"),
        ("sin_informalidad", "Sin informalidad", "Cobertura", 0.10, 1.0, salto,
         f"Todos los informales de hoy cotizan desde 2026: {inf / 1e6:.2f} millones más sobre {n.loc[2023, 'cotizantes_dic_con_region'] / 1e6:.2f} millones de cotizantes (+{100 * (salto - 1):.0f} %)"),
        ("mitad_informalidad", "Mitad del camino", "Cobertura", 0.10, 1.0, 1 + (salto - 1) / 2,
         f"La mitad de los informales de hoy cotiza desde 2026 (+{50 * (salto - 1):.0f} % de cotizantes)"),
    ]
    return pd.DataFrame(filas, columns=["clave", "nombre", "grupo", "carga_max", "cobertura_2050", "cobertura_salto", "descripcion"]).assign(
        orden=lambda d: range(1, len(d) + 1), pendiente_pp_anio=pend, informales_censo=inf)


def _piezas(g: dict) -> dict:
    ft = g["O"] + g["D"]
    return dict(participacion=ft / g["P"], empleo=g["O"] / ft, cotizacion=g["C"] / g["O"], cobertura=100 * g["C"] / g["P"])


def _aporte(a: dict, b: dict) -> dict:
    """Aporte en puntos de cada pieza a la diferencia de cobertura a - b (media logarítmica: suman exacto)."""
    L = media_log(a["cobertura"], b["cobertura"])
    return {k: L * (np.log(a[k]) - np.log(b[k])) for k in FACTORES_DESC}


def resumen_grupo(f: pd.DataFrame, ene: pd.DataFrame, ind: pd.DataFrame) -> pd.DataFrame:
    """Las regiones prioritarias recomendadas (columna `prioridad` de kpi_cobertura_regiones.csv) juntas, frente a Chile y frente a las demás.
    Siempre agregados, no promedios simples: cada indicador se pondera con lo que corresponde (cotizantes ÷ población de las regiones sumadas;
    tasas de empleo con los ocupados o la fuerza de trabajo; el resto con la población). «Chile» es la suma de las 16 regiones, igual que en la
    descomposición. Devuelve una fila por indicador con las columnas siete, chile, otras, diferencia."""
    reg = pd.read_csv(DP / "kpi_cobertura_regiones.csv")
    reg = reg[reg.region_id > 0].set_index("region_id")
    sel = list(reg[reg.prioridad.notna()].index)
    otros = [i for i in reg.index if i not in sel]
    grupos = {"siete": sel, "chile": list(reg.index), "otras": otros}
    filas = []

    def fila(seccion, indicador, unidad, valores, pond):
        filas.append(dict(seccion=seccion, indicador=indicador, unidad=unidad, **valores, ponderacion=pond))

    # 1. nivel y cambio de la cobertura (suma de cotizantes ÷ suma de población, por año)
    t = pd.read_csv(DP / "kpi_cobertura_tendencia.csv")
    t = t[t.territorio_id.between(1, 16)]

    def cob(ids, a):
        g = t[(t.anio == a) & t.territorio_id.isin(ids)]
        return 100 * g.cotizantes.sum() / g.pob_15_64.sum(), g.cotizantes.sum(), g.pob_15_64.sum()

    ref = int(reg.anio_ref.iloc[0])
    fila("Cobertura", f"Cobertura {ref}", "% de 15-64", {k: cob(v, ref)[0] for k, v in grupos.items()}, "cotizantes ÷ población 15-64 de las regiones sumadas")
    for a0 in (2019, 2022):
        fila("Cobertura", f"Cambio desde {a0}", "puntos", {k: cob(v, ref)[0] - cob(v, a0)[0] for k, v in grupos.items()}, "cobertura del grupo en {} menos en {}".format(ref, a0))
    fila("Cobertura", "Cotizantes desde 2022", "personas", {k: cob(v, ref)[1] - cob(v, 2022)[1] for k, v in grupos.items()}, "suma de las regiones")
    fila("Cobertura", "Cotizantes desde 2022", "%", {k: 100 * (cob(v, ref)[1] / cob(v, 2022)[1] - 1) for k, v in grupos.items()}, "suma de las regiones")
    fila("Peso", "Parte de la población de 15 a 64 años", "%", {k: 100 * cob(v, ref)[2] / cob(grupos["chile"], ref)[2] for k, v in grupos.items()}, "Censo 2024")
    fila("Peso", "Parte de los cotizantes", "%", {k: 100 * cob(v, ref)[1] / cob(grupos["chile"], ref)[1] for k, v in grupos.items()}, "suma de las regiones")
    brecha = {k: float(reg.loc[v, "brecha_cotizantes"].sum()) for k, v in grupos.items()}
    fila("Peso", "Brecha de cotizantes frente a Chile", "personas", {**brecha, "chile": np.nan}, "suma de las brechas regionales (solo regiones bajo el promedio)")

    # 2. descomposición: de dónde viene la diferencia con Chile, el grupo entero como un solo territorio
    g = f.set_index(["territorio_id", "anio"])

    def agregado(ids, a):
        x = g.loc[[(i, a) for i in ids]]
        return _piezas(dict(C=x.cotizantes.sum(), O=x.ocupados.sum(), D=x.desocupados.sum(), P=x.p1564.sum()))

    ch = agregado(grupos["chile"], ref)
    for k, nom in (("participacion", "Participación laboral (de 15 a 64 años)"), ("empleo", "Empleo (1 − desocupación)"), ("cotizacion", "Ocupados que cotizan")):
        fila("Diferencia con Chile", nom, "puntos", {"siete": _aporte(agregado(sel, ref), ch)[k], "chile": 0.0, "otras": _aporte(agregado(otros, ref), ch)[k]}, "descomposición exacta del grupo como un solo territorio")
    ap = {k: sum(_aporte(agregado(v, ref), ch).values()) for k, v in (("siete", sel), ("otras", otros))}
    fila("Diferencia con Chile", "Diferencia total", "puntos", {"siete": ap["siete"], "chile": 0.0, "otras": ap["otras"]}, "suma de las tres piezas")
    for a0 in (2019,):
        for k, nom in (("participacion", "Participación laboral"), ("empleo", "Empleo"), ("cotizacion", "Ocupados que cotizan")):
            vals = {c: _aporte(agregado(v, ref), agregado(v, a0))[k] for c, v in grupos.items()}
            fila(f"Cambio {a0}-{ref}", nom, "puntos", vals, "descomposición del cambio de cada grupo")

    # 3. el resto de los indicadores: tasas ponderadas
    e23 = ene[(ene.anio == 2023)].set_index("territorio_id")
    pesos = {"ocupados 2023": e23.ocupados, "fuerza de trabajo 2023": e23.ocupados + e23.desocupados,
             "población total": ind.pob_total, "población 15-64": ind.pob_15_64, "personas de 65+": ind.pob_65_mas}
    pen = pd.read_csv(DP / "kpi_cobertura_pendularidad.csv").set_index("region_id")
    pesos["ocupados que viven en la región"] = pen.ocupados_residentes
    tabla = [("Informalidad (tasa oficial, ENE dic. 2023)", "informalidad_ene", "%", "ocupados 2023"),
             ("Desocupación (ENE dic. 2023)", "desocupacion_ene", "%", "fuerza de trabajo 2023"),
             ("Participación laboral de 15 a 64 años (Censo 2024)", "participacion_15_64_censo", "%", "población 15-64"),
             ("Participación laboral de las mujeres de 15+ (Censo 2024)", "participacion_mujeres_censo", "%", "población 15-64"),
             ("Ocupados independientes (Censo 2024)", "independientes", "%", "ocupados 2023"),
             ("Ingreso per cápita (CASEN 2022)", "ingreso_per_capita_prom", "$ al mes", "población total"),
             ("Pobreza en personas de 65+ (CASEN 2022)", "pct_pobreza_65", "%", "personas de 65+"),
             ("Personas de 65+ (Censo 2024)", "pct_65_mas", "% de la población", "población total"),
             ("Población urbana (Censo 2024)", "pct_urbano", "%", "población total"),
             ("Migración interna neta en 5 años (Censo 2024)", "migracion_interna_neta", "por 1.000 habitantes", "población total"),
             ("Ocupados que trabajan en otra región (Censo 2024)", "salida_pendular_pct", "%", "ocupados que viven en la región")]
    for nombre, col, unidad, pond in tabla:
        w = pesos[pond]
        fila("Otros indicadores", nombre, unidad, {k: float(np.average(reg.loc[v, col], weights=w.reindex(v))) for k, v in grupos.items()}, f"promedio ponderado por {pond}")
    r = pd.DataFrame(filas)
    r["dif_siete_chile"] = r.siete - r.chile
    r.attrs["regiones"] = [(int(i), reg.loc[i, "region_nombre"]) for i in sel]
    return r


def escribir_doc_siete(r: pd.DataFrame, ruta: Path):
    """docs/SIETE_VS_CHILE.md: las tablas de resumen_grupo con una lectura que se arma con los mismos números."""
    nombres = ", ".join(n for _, n in r.attrs["regiones"])
    n = len(r.attrs["regiones"])
    num = lambda v, d=1: "—" if pd.isna(v) else f"{v:,.{d}f}".replace(",", "§").replace(".", ",").replace("§", ".").replace("-", "−")  # noqa: E731
    sg = lambda v, d=1: "—" if pd.isna(v) else ("+" if v >= 0 else "−") + num(abs(v), d)  # noqa: E731
    cab = f"| Indicador | Las {n} juntas | Chile | Las otras {16 - n} | Las {n} menos Chile | Cómo se calcula |\n|---|---|---|---|---|---|\n"
    def tabla(seccion, signo=False, dec=1):
        x = r[r.seccion == seccion]
        filas = []
        for q in x.itertuples():
            d = 0 if q.unidad == "personas" or q.unidad == "$ al mes" else dec
            f_ = sg if signo or q.unidad in ("puntos",) else num
            dif = "—" if (q.seccion == "Peso" or q.unidad == "personas") else sg(q.dif_siete_chile, d)  # restar sumas o partes no significa nada
            filas.append(f"| {q.indicador} ({q.unidad}) | {f_(q.siete, d)} | {f_(q.chile, d)} | {f_(q.otras, d)} | {dif} | {q.ponderacion} |")
        return cab + "\n".join(filas)
    v = lambda ind, col="siete": float(r[r.indicador == ind][col].iloc[0])  # noqa: E731
    sec = lambda s_, i_: float(r[(r.seccion == s_) & (r.indicador == i_)].siete.iloc[0])  # noqa: E731
    ref = [q for q in r.indicador if q.startswith("Cobertura 20")][0]
    texto = f"""# Las {n} regiones prioritarias frente al promedio de Chile

Documento generado por `Scripts/25_explorar_causas.py` (`Data processed/kpi_cobertura_siete_vs_chile.csv`); se rehace solo cada vez que se corre el script. Regiones: **{nombres}**.

**Cómo leer los promedios.** Son **agregados**, no promedios simples de tasas: la cobertura de «las {n} juntas» es la suma de sus cotizantes dividida por la suma de su población de 15 a 64 años; las tasas de empleo se ponderan con los ocupados o la fuerza de trabajo, y el resto con la población. «Chile» es la suma de las 16 regiones (igual que en la descomposición del dashboard) y «las otras {16 - n}» son las regiones no seleccionadas. Así el promedio de las {n} se compara de igual a igual con el del país.

## 1. Nivel y cambio de la cobertura

{tabla("Cobertura")}

Las {n} regiones juntas tienen una cobertura de **{num(v(ref))} %**, frente a {num(v(ref, 'chile'))} % de Chile y {num(v(ref, 'otras'))} % de las otras {16 - n}: **{num(abs(v(ref) - v(ref, 'chile')))} puntos bajo el país**. Desde 2019 subieron {num(v("Cambio desde 2019"))} puntos (Chile: {num(v("Cambio desde 2019", "chile"))}); desde 2022 {sg(v("Cambio desde 2022"))} (Chile: {sg(v("Cambio desde 2022", "chile"))}), y su cantidad de cotizantes cambió {sg(r[(r.indicador == "Cotizantes desde 2022") & (r.unidad == "%")].siete.iloc[0])} % frente a {sg(r[(r.indicador == "Cotizantes desde 2022") & (r.unidad == "%")].chile.iloc[0])} % del país.

**Dos lecturas honestas.** (1) La brecha de las {n} con el país es sobre todo de **nivel**, no de caída reciente: desde 2022 su cobertura cae casi igual que la del resto ({sg(v("Cambio desde 2022"))} puntos frente a {sg(v("Cambio desde 2022", "otras"))}); lo que sí es peor es la pérdida de cotizantes en personas ({sg(r[(r.indicador == "Cotizantes desde 2022") & (r.unidad == "%")].siete.iloc[0])} % frente a {sg(r[(r.indicador == "Cotizantes desde 2022") & (r.unidad == "%")].otras.iloc[0])} % en las otras {16 - n}). (2) Desde 2019 el grupo mejoró más que el país ({sg(v("Cambio desde 2019"))} frente a {sg(v("Cambio desde 2019", "chile"))} puntos): la distancia con Chile se achicó {num(v("Cambio desde 2019") - v("Cambio desde 2019", "chile"))} puntos, aunque sigue en {num(abs(v(ref) - v(ref, "chile")))}.

## 2. Cuánto pesan

{tabla("Peso")}

## 3. De dónde viene la diferencia con Chile (las {n} juntas como un solo territorio)

{tabla("Diferencia con Chile", signo=True)}

La diferencia total de las {n} con el país es de **{sg(v("Diferencia total"))} puntos**; de ellos, {sg(v("Ocupados que cotizan"))} vienen de que menos ocupados cotizan, {sg(v("Participación laboral (de 15 a 64 años)"))} de la participación laboral y {sg(v("Empleo (1 − desocupación)"))} del desempleo. Las otras {16 - n} regiones, en cambio, están {sg(v("Diferencia total", "otras"))} puntos respecto del país (sobre el promedio).

## 4. Cómo cambió la cobertura desde 2019, por pieza

{tabla("Cambio 2019-" + ref.split()[-1])}

## 5. El resto de los indicadores

{tabla("Otros indicadores")}

## Límites

- Los promedios ocultan diferencias entre las regiones del grupo (La Araucanía y Los Ríos tienen la cotización mucho más baja que Biobío, por ejemplo); el detalle por región está en `docs/ANALISIS_SIETE_REGIONES.md` y en el dashboard.
- La descomposición del grupo trata a las {n} regiones como un solo territorio: es exacta, pero sus piezas no son el promedio de las piezas de cada región.
- Las tasas de la ENE son de diciembre de 2023; la desocupación y la informalidad de 2024 no están por región en los archivos bajados (solo en el anexo del estudio de la Asociación de AFP).
- Todo es asociación y aritmética, no causa; con 16 regiones no hay regresión.
"""
    ruta.write_text(texto)


def main():
    s24 = cargar_modulo("24_cobertura_tendencia_causas.py")
    s24.asegurar_ine17()
    ind = pd.read_csv(DP / "indicadores_region.csv").set_index("region")
    ene = ene_anual()
    ene.round(4).to_csv(DP / "ene_region_anual.csv", index=False)
    pib = pib_anual()
    pob = poblaciones(s24, ind)
    f = factores_anuales(s24, ind, ene, pob)
    f.round(6).to_csv(DP / "kpi_cobertura_factores_anual.csv", index=False)
    d = descomposicion(f)
    d.round(4).to_csv(DP / "kpi_cobertura_descomposicion.csv", index=False)

    cot = pd.read_csv(DP / "cotizantes_por_region.csv")
    cot = cot[cot.region_id.notna()].assign(region_id=lambda x: x.region_id.astype(int)).pivot(index="region_id", columns="anio", values="cotizantes")
    # el estudio de la AAFP separa Biobío y Ñuble en 2019: el cotizante de Biobío incluye a Ñuble hasta 2017, pero en 2019 ya están separados
    contr = contraste_aafp(f, ene.assign(ocupados=ene.ocupados), cot)
    contr.round(2).to_csv(DP / "kpi_cobertura_contraste_aafp.csv", index=False)
    ta = test_asignacion(f, ene, ind)
    ta.round(2).to_csv(DP / "kpi_cobertura_test_asignacion.csv", index=False)
    esc = escenarios_fijos_kpi12(ene)
    esc.round(6).to_csv(DP / "kpi_pc_escenarios_fijos.csv", index=False)

    pend = pendularidad()
    pend.round(3).to_csv(DP / "kpi_cobertura_pendularidad.csv", index=False)
    nuevos = factores_ene_pib(ene, pib, pob, ind, f, participacion_mujeres(), censo_extra(pend))
    reg24 = pd.read_csv(DP / "kpi_cobertura_correlaciones_region.csv").set_index("region_id")
    fac = actualizar_factores(nuevos, reg24.cobertura_previsional_pct.reindex(range(1, 17)))
    sv = resumen_grupo(f, ene, ind)
    sv.round(4).to_csv(DP / "kpi_cobertura_siete_vs_chile.csv", index=False)
    escribir_doc_siete(sv, ROOT / "docs" / "SIETE_VS_CHILE.md")
    pib.round(3).to_csv(DP / "pib_regional_anual.csv", index=False)

    print("escenarios fijos del KPI 1.2:"); print(esc[["clave", "carga_max", "cobertura_2050", "cobertura_salto"]].round(3).to_string(index=False))
    print("test de asignación regional (participación de la Metropolitana, %):")
    print(ta.round(1).to_string(index=False))
    print("contraste con la AAFP (ocupados INE vs AAFP dic. 2019, diferencia %):", contr.dif_ocupados_pct.abs().max().round(2), "máx.")
    print("cotizantes / ocupados 2019, nuestra vs AAFP (diferencia en puntos, máx.):",
          (contr.cot_sobre_ocupados_2019 - contr.cobertura_ocupados_aafp_2019).abs().max().round(1))
    print("factores nuevos (nivel):")
    print(fac[fac.factor.isin(FACTORES_NUEVOS)][["nombre", "objetivo", "n", "pearson_r", "pearson_p", "elegido"]].round(2).to_string(index=False))
    print("mostrados:", list(fac[fac.elegido].nombre))
    print("descomposición, 5 prioritarias vs Chile (nivel 2024):")
    print(d[(d.comparacion.str.startswith("Nivel")) & d.territorio_id.isin([9, 5, 8, 4, 16, 816])]
          .pivot(index="territorio", columns="factor_nombre", values="aporte_pp").round(1).to_string())


if __name__ == "__main__":
    sys.exit(main())
