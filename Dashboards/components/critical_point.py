"""Motor del análisis "punto crítico" del KPI 1.2 (sin Streamlit ni lectura de archivos).

Compara dos masas de dinero, año a año y en pesos reales de 2025:
  - Costo   = costo del Pilar Solidario de vejez por persona de 65+  x  población de 65+.
  - Capacidad = carga máxima tolerable (% del sueldo)  x  ingreso por trabajador  x  trabajadores.
El punto crítico es el año en que la línea de costo cruza a la de capacidad. Equivale a que la razón de soporte
(trabajadores por persona de 65+) caiga bajo la razón de equilibrio R* = costo por 65+ / (ingreso anual por trabajador x carga máxima).

Dos bases de ingreso (se alternan con un interruptor):
  A "cotizantes": ingreso imponible (SP) x cotizantes: quienes hoy aportan al sistema. Los trabajadores son los cotizantes de
    diciembre con región (razón de soporte 2024 = 2,27, igual que la tarjeta); la masa es la anual de los 12 meses (no
    diciembre × 12, que la sobrestima 2-4 %): masa = trabajadores × ingreso anual × factor_masa (ver Scripts/18).
  B "ocupados":   ingreso de los ocupados (INE, ESI) x ocupados: la base si todos los que trabajan cotizaran.
Cada base admite promedio o mediana.

Población: el Censo 2024 manda (ver docs/DISCUSION_FUENTES.md). Para el país se usa la dinámica de las proyecciones INE llevada
al nivel del Censo (población INE x Censo 2024 / INE 2024); con `poblacion="ine"` se usa el nivel INE sin ajustar.
Proyección: población del INE reescalada (país) o del escenario regional ya existente (región); trabajadores = cobertura x población 15-64;
ingreso real crece a `crec_salarial`; el costo por persona de 65+ crece a `crec_costo` (la PGU se reajusta por IPC: 0 % real),
más la PGU de $250.000 de la Ley 21.735 si `pgu_250`.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

ANIO_BASE_PAIS = 2025      # último año con todos los datos (cotizantes, ingreso, costo)
ANIO_BASE_REGION = 2024    # año del Censo 2024: la población regional y todos los datos regionales coinciden en 2024
ANIOS_REGION = (2024, 2035, 2050)  # años con población regional (Censo 2024 y escenarios 2035 / 2050)
ANIO_FIN_PAIS = 2070
ANIO_FIN_REGION = 2050
MESES = 12


@dataclass(frozen=True)
class Escenario:
    base: str = "A"                 # "A" cotizantes (SP) | "B" ocupados (INE)
    estadistico: str = "promedio"   # "promedio" | "mediana"
    crec_salarial: float = 0.01     # crecimiento real anual del ingreso por trabajador
    crec_costo: float = 0.0         # crecimiento real anual del costo por persona de 65+
    carga_max: float = 0.10         # carga máxima tolerable: fracción del sueldo (10 % = la cotización obligatoria para pensión)
    cobertura_2050: float = 1.0     # trabajadores / población 15-64 en 2050 relativo a hoy (solo base A); 1 = constante
    pgu_250: bool = True            # incluir el aumento de la PGU a $250.000 (Ley 21.735)
    poblacion: str = "censo"        # "censo": población INE llevada al nivel del Censo 2024 (el Censo manda) | "ine": nivel INE


COLS_INGRESO = {  # (base, estadístico) -> columna de kpi_pc_nacional.csv / kpi_pc_region.csv (pesos de 2025, mensual)
    ("A", "promedio"): "ingreso_imponible_prom_real25",
    ("A", "mediana"): "ingreso_imponible_mediano_real25",
    ("B", "promedio"): "ing_ocupados_medio_real25",
    ("B", "mediana"): "ing_ocupados_mediano_real25",
}
COL_TRABAJADORES = {"A": "cotizantes_dic_con_region", "B": "ocupados_ond"}
NOMBRE_TRABAJADORES = {"A": "cotizantes", "B": "ocupados"}


def _factor_cobertura(anio, esc: Escenario, anio0):
    """Cobertura relativa a la del año base: lineal hasta `cobertura_2050` en 2050 y constante después. Solo base A."""
    if esc.base != "A":
        return 1.0
    return 1 + (esc.cobertura_2050 - 1) * np.clip((anio - anio0) / (2050 - anio0), 0, 1)


def _factor_pgu(anio, esc: Escenario, params: pd.DataFrame):
    if not esc.pgu_250:
        return 1.0
    p = params.set_index("anio").factor_costo_pgu
    return pd.Series(anio).map(p).fillna(1.0).values


def _derivados(d: pd.DataFrame, esc: Escenario) -> pd.DataFrame:
    """Columnas comunes: masas de dinero, carga requerida, razón de soporte y razón de equilibrio."""
    d["ingreso_anual_trab"] = d.ingreso_trab * MESES
    # factor_masa: lleva cotizantes de diciembre × ingreso × 12 a la masa anual de los 12 meses (base A; 1 en base B)
    d["masa_ingreso"] = d.trabajadores * d.ingreso_anual_trab * d.factor_masa  # CLP de 2025 al año
    d["capacidad"] = esc.carga_max * d.masa_ingreso
    d["costo_total"] = d.costo_65 * d.pob_65
    d["carga_requerida"] = d.costo_total / d.masa_ingreso                      # fracción del sueldo
    d["razon_soporte"] = d.trabajadores / d.pob_65
    d["razon_equilibrio"] = d.costo_65 / (d.ingreso_anual_trab * d.factor_masa * esc.carga_max)
    d["diferencia"] = d.capacidad - d.costo_total
    return d


def serie_pais(nac: pd.DataFrame, proy: pd.DataFrame, params: pd.DataFrame, esc: Escenario) -> pd.DataFrame:
    """País, 2010-2070. nac = kpi_pc_nacional.csv; proy = proyeccion_envejecimiento_pais.csv; params = kpi_pc_parametros_reforma.csv.
    Hasta 2025 son datos observados; desde 2026 es el escenario (columna `proyectado`)."""
    n = nac.set_index("anio")
    ing_col, trab_col = COLS_INGRESO[(esc.base, esc.estadistico)], COL_TRABAJADORES[esc.base]
    pr = proy.set_index("anio")
    anios = np.arange(int(n.index.min()), ANIO_FIN_PAIS + 1)
    d = pd.DataFrame({"anio": anios}).set_index("anio")
    f65, f1564 = (n.loc[ANIO_BASE_PAIS, "factor_censo_65"], n.loc[ANIO_BASE_PAIS, "factor_censo_15_64"]) if esc.poblacion == "censo" else (1.0, 1.0)
    d["pob_65"], d["pob_15_64"] = pr.pob_65_mas.reindex(anios) * f65, pr.pob_15_64.reindex(anios) * f1564
    t0 = ANIO_BASE_PAIS
    dt = (anios - t0).astype(float)  # float: con crec = 0 entero, 1 ** (exponente negativo) falla
    hist = anios <= t0
    d["trabajadores"] = np.where(hist, n[trab_col].reindex(anios),
                                 n.loc[t0, trab_col] * d.pob_15_64 / d.loc[t0, "pob_15_64"] * _factor_cobertura(anios, esc, t0))
    d["ingreso_trab"] = np.where(hist, n[ing_col].reindex(anios), n.loc[t0, ing_col] * (1 + esc.crec_salarial) ** dt)
    if esc.base == "A":  # en el escenario se mantiene el factor del año base
        d["factor_masa"] = np.where(hist, n.factor_masa_anual.reindex(anios), n.loc[t0, "factor_masa_anual"])
    else:
        d["factor_masa"] = 1.0
    costo_hist = n["costo_vejez_por_65_real25"] / f65  # el gasto es el mismo; con menos población 65+ cada persona cuesta más
    base_costo = costo_hist.loc[t0]
    d["costo_65"] = np.where(hist, costo_hist.reindex(anios),
                             base_costo * (1 + esc.crec_costo) ** dt * _factor_pgu(anios, esc, params))
    d["proyectado"] = ~hist
    d["ancla"] = d.index.isin(ANIOS_REGION)  # mismos años destacados que en la vista regional
    return _derivados(d.reset_index(), esc)


def _interpolar(anios, puntos: dict):
    xs = sorted(puntos)
    return np.interp(anios, xs, [puntos[x] for x in xs])


def datos_territorio(region_id: int, reg: pd.DataFrame, nac: pd.DataFrame, ind_region: pd.DataFrame, proy_reg: pd.DataFrame):
    """Valores de partida de una región en 2024 (Censo 2024 + diciembre 2024 + ESI 2024 + gasto de vejez 2024) y sus
    poblaciones 2035 / 2050 (escenario regional ya existente en kpi_proyeccion_regional.csv)."""
    r24 = reg[(reg.anio == ANIO_BASE_REGION) & (reg.region_id == region_id)].iloc[0]
    n24 = nac[nac.anio == ANIO_BASE_REGION].iloc[0]
    i = ind_region[ind_region.region == region_id].iloc[0]
    pr = proy_reg[proy_reg.region_id == region_id].set_index("anio")
    pob65 = {ANIO_BASE_REGION: float(i.pob_65_mas)}
    pob1564 = {ANIO_BASE_REGION: float(i.pob_15_64)}
    for a in (2035, 2050):  # índice de dependencia de vejez = 100 x 65+ / 15-64
        pob65[a] = float(pr.loc[a, "pob_65_mas_proy"])
        pob1564[a] = pob65[a] / (float(pr.loc[a, "indice_dependencia_vejez_proy"]) / 100)
    # ingreso mensual de los cotizantes: promedio SP regional; la mediana regional no existe (la SP publica tramos solo por AFP),
    # se estima como mediana nacional x (promedio regional / promedio nacional)
    escala = r24.ingreso_imponible_prom_real25 / n24.ingreso_imponible_prom_real25
    costo = r24.cuota_gasto_vejez * n24.costo_vejez_mm_real25 * 1e6 / pob65[ANIO_BASE_REGION]
    return dict(
        region_id=region_id, pob_65=pob65, pob_15_64=pob1564, costo_65=float(costo),
        cotizantes=float(r24.cotizantes_dic), ocupados=float(r24.ocupados_ond),
        ing_A_promedio=float(r24.ingreso_imponible_prom_real25), ing_A_mediana=float(n24.ingreso_imponible_mediano_real25 * escala),
        ing_B_promedio=float(r24.ing_ocupados_medio_real25), ing_B_mediana=float(r24.ing_ocupados_mediano_real25),
        factor_masa_A=float(n24.factor_estacional),  # los cotizantes regionales ya son con región: solo la estacionalidad nacional
    )


def comuna_desde_region(dr: dict, pob_65_comuna: float, pob_15_64_comuna: float) -> dict:
    """Aproximación comunal: la comuna hereda de su región la cobertura (trabajadores / pob. 15-64), el ingreso, el costo por
    persona de 65+ y el ritmo de cambio de la población; solo su estructura de edad de 2024 (Censo) es propia."""
    k65 = pob_65_comuna / dr["pob_65"][ANIO_BASE_REGION]
    k1564 = pob_15_64_comuna / dr["pob_15_64"][ANIO_BASE_REGION]
    out = dict(dr)
    out["pob_65"] = {a: v * k65 for a, v in dr["pob_65"].items()}
    out["pob_15_64"] = {a: v * k1564 for a, v in dr["pob_15_64"].items()}
    out["cotizantes"] = dr["cotizantes"] * k1564
    out["ocupados"] = dr["ocupados"] * k1564
    return out


def serie_territorio(dt: dict, params: pd.DataFrame, esc: Escenario) -> pd.DataFrame:
    """Región (o comuna), 2024-2050. 2024 es dato observado; 2035 y 2050 son los años con población regional del escenario
    (columna `ancla`); los años intermedios se interpolan linealmente."""
    anios = np.arange(ANIO_BASE_REGION, ANIO_FIN_REGION + 1)
    d = pd.DataFrame({"anio": anios})
    d["pob_65"] = _interpolar(anios, dt["pob_65"])
    d["pob_15_64"] = _interpolar(anios, dt["pob_15_64"])
    t0 = ANIO_BASE_REGION
    w0 = dt["cotizantes"] if esc.base == "A" else dt["ocupados"]
    d["trabajadores"] = w0 * d.pob_15_64 / dt["pob_15_64"][t0] * _factor_cobertura(anios, esc, t0)
    ing0 = dt[f"ing_{esc.base}_{esc.estadistico}"]
    d["ingreso_trab"] = ing0 * (1 + esc.crec_salarial) ** (anios - t0).astype(float)
    d["factor_masa"] = dt["factor_masa_A"] if esc.base == "A" else 1.0
    d["costo_65"] = dt["costo_65"] * (1 + esc.crec_costo) ** (anios - t0).astype(float) * _factor_pgu(anios, esc, params)
    d["proyectado"] = anios > t0
    d["ancla"] = np.isin(anios, ANIOS_REGION)
    return _derivados(d, esc)


def punto_critico(d: pd.DataFrame) -> dict:
    """Año en que el costo alcanza a la capacidad. Devuelve estado y año:
      'cruza'        el último paso de capacidad > costo a capacidad <= costo (anio_exacto interpolado dentro del año);
      'ya_superado'  el costo ya supera a la capacidad desde el primer año de la serie;
      'no_cruza'     la capacidad cubre el costo en toda la serie."""
    dif = d.diferencia.values
    if (dif > 0).all():
        return dict(estado="no_cruza", anio=None, anio_exacto=None)
    if (dif <= 0).all():
        return dict(estado="ya_superado", anio=int(d.anio.iloc[0]), anio_exacto=float(d.anio.iloc[0]))
    k = int(np.flatnonzero(dif > 0).max())  # último año con holgura
    if k == len(dif) - 1:
        return dict(estado="no_cruza", anio=None, anio_exacto=None)
    f = dif[k] / (dif[k] - dif[k + 1])
    return dict(estado="cruza", anio=int(d.anio.iloc[k + 1]), anio_exacto=float(d.anio.iloc[k] + f))


def colchon(d: pd.DataFrame, r_real: float) -> tuple:
    """Colchón acumulado: las holguras (capacidad - costo) desde el último año observado se ahorran a una rentabilidad real
    `r_real` y los déficits se pagan con ese ahorro: colchón_t = colchón_(t-1) x (1 + r) + diferencia_t. No es un dato ni una
    regla del sistema (el tope no se ahorra de verdad): muestra cuánto tiempo compraría el exceso de capacidad previo al cruce.
    Devuelve (serie del colchón, dict con estado y año):
      'se_agota'    primer año con colchón negativo (anio_exacto interpolado dentro del año);
      'sin_colchon' no hay holgura en el año de partida (el costo ya supera a la capacidad);
      'no_se_agota' el colchón se mantiene positivo hasta el final de la serie.
    El punto crítico (flujo anual) no depende de r: descontar costo y capacidad por el mismo factor no cambia dónde se cruzan."""
    desde = int(d.anio[~d.proyectado].max())
    fondo = pd.Series(np.nan, index=d.index)
    acum = 0.0
    for i in d.index[d.anio >= desde]:
        acum = acum * (1 + r_real) + d.loc[i, "diferencia"]
        fondo.loc[i] = acum
    f = fondo.dropna()
    if f.iloc[0] <= 0:
        return fondo, dict(estado="sin_colchon", anio=desde, anio_exacto=float(desde))
    neg = f[(f <= 0) & (f.index > f.index[0])]
    if neg.empty:
        return fondo, dict(estado="no_se_agota", anio=None, anio_exacto=None)
    j = neg.index[0]
    prev = f.index[list(f.index).index(j) - 1]
    frac = f.loc[prev] / (f.loc[prev] - f.loc[j])
    return fondo, dict(estado="se_agota", anio=int(d.loc[j, "anio"]), anio_exacto=float(d.loc[prev, "anio"] + frac))


def fila_anio(d: pd.DataFrame, anio: int) -> pd.Series:
    return d[d.anio == anio].iloc[0]
