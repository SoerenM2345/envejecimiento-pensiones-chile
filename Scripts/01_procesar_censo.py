"""
Procesa el CSV de microdatos del Censo 2024 (18.48M personas, ~2.4GB) con DuckDB
(streaming, sin cargar todo en RAM) y produce tablas agregadas listas para
analisis y dashboard:

  1. censo_comuna_edad_sexo.csv   -> poblacion por comuna x edad_quinquenal x sexo x area
  2. censo_region_edad_sexo.csv   -> poblacion por region x edad_quinquenal x sexo x area
  3. censo_pais_edad_simple.csv   -> poblacion por edad simple (0-85+) x sexo (piramide nacional)
  4. indicadores_comuna.csv       -> indicadores de envejecimiento por comuna (346/346)
  5. indicadores_region.csv       -> indicadores de envejecimiento por region

Nota de calidad de datos (importante):
  - `edad` (edad simple, 0-85 con 85 = "85 y mas") viene enmascarada (-66) para
    las 51 comunas bajo el umbral de poblacion definido por el INE para control
    de revelacion estadistica (`comuna_bajo_umbral = 1`), es decir, ~151k
    personas (0.82% del total nacional) en comunas pequenas/aisladas (islas,
    Aysen, Magallanes, etc.) no tienen edad exacta.
  - `edad_quinquenal` (tramos de 5 anios) SI esta disponible para el 100% de
    las 18.480.432 personas, incluidas esas 51 comunas. Como los quiebres de
    interes (0-14 / 15-64 / 65+ / 80+) caen justo en limites de quinquenio, se
    puede reconstruir esos grupos SIN perdida de precision usando
    edad_quinquenal. Por eso los indicadores de envejecimiento (tablas 1, 2, 4
    y 5) se calculan con edad_quinquenal y logran cobertura de 346/346 comunas
    y 16/16 regiones.
  - Solo la piramide nacional por edad simple (tabla 3, para el grafico de
    piramide con detalle anual) excluye esas ~151k personas por no tener edad
    exacta; se documenta como nota al pie donde se use.
"""
import duckdb
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "Data raw"
OUT = Path(__file__).resolve().parent.parent / "Data processed"
OUT.mkdir(parents=True, exist_ok=True)

CENSO_CSV = str(RAW / "personas_censo2024.csv")
LOOKUP_CSV = str(OUT / "region_comuna_lookup.csv")

con = duckdb.connect()
con.execute("SET threads TO 8")
con.execute("SET memory_limit='16GB'")

census = f"read_csv_auto('{CENSO_CSV}', delim=';')"
lookup = f"read_csv_auto('{LOOKUP_CSV}')"

# ---------------------------------------------------------------------------
# 1) Poblacion por comuna x edad_quinquenal x sexo x area (346/346 comunas)
# ---------------------------------------------------------------------------
print("1) Agregando por comuna x edad_quinquenal x sexo x area ...")
q1 = f"""
COPY (
    SELECT
        c.region,
        l.region_nombre_corto AS region_nombre,
        c.comuna,
        l.comuna_nombre,
        c.area,               -- 1 urbano, 2 rural
        c.sexo,                -- 1 hombre, 2 mujer
        c.edad_quinquenal,
        COUNT(*) AS poblacion
    FROM {census} c
    LEFT JOIN {lookup} l ON l.comuna_id = c.comuna
    GROUP BY 1,2,3,4,5,6,7
    ORDER BY 1,3,6,7
) TO '{OUT / "censo_comuna_edad_sexo.csv"}' (HEADER, DELIMITER ',')
"""
con.execute(q1)

# ---------------------------------------------------------------------------
# 2) Poblacion por region x edad_quinquenal x sexo x area
# ---------------------------------------------------------------------------
print("2) Agregando por region x edad_quinquenal x sexo x area ...")
q2 = f"""
COPY (
    SELECT
        c.region,
        l.region_nombre_corto AS region_nombre,
        c.area,
        c.sexo,
        c.edad_quinquenal,
        COUNT(*) AS poblacion
    FROM {census} c
    LEFT JOIN (SELECT DISTINCT region_id, region_nombre_corto FROM {lookup}) l
        ON l.region_id = c.region
    GROUP BY 1,2,3,4,5
    ORDER BY 1,4,5
) TO '{OUT / "censo_region_edad_sexo.csv"}' (HEADER, DELIMITER ',')
"""
con.execute(q2)

# ---------------------------------------------------------------------------
# 3) Piramide nacional por edad simple (0-85+) x sexo
#    (excluye ~151k personas de 51 comunas bajo umbral con edad enmascarada;
#     0.82% del total nacional -> ver docstring)
# ---------------------------------------------------------------------------
print("3) Agregando piramide nacional por edad simple ...")
q3 = f"""
COPY (
    SELECT edad, sexo, COUNT(*) AS poblacion
    FROM {census}
    WHERE edad >= 0
    GROUP BY 1,2
    ORDER BY 1,2
) TO '{OUT / "censo_pais_edad_simple.csv"}' (HEADER, DELIMITER ',')
"""
con.execute(q3)

# ---------------------------------------------------------------------------
# Bloque de grupos de edad reutilizado (a partir de edad_quinquenal, 100% cobertura)
#   0-14   : quinquenal in (0,5,10)
#   15-64  : quinquenal in (15..60)
#   65+    : quinquenal in (65,70,75,80,85)
#   80+    : quinquenal in (80,85)
#   mediana aproximada: interpolacion lineal sobre la distribucion acumulada
#   de quinquenios (punto medio de cada tramo, 85 tratado como 87.5)
# ---------------------------------------------------------------------------
EDAD_CASE = """
        SUM(CASE WHEN edad_quinquenal IN (0,5,10) THEN 1 ELSE 0 END) AS pob_0_14,
        SUM(CASE WHEN edad_quinquenal BETWEEN 15 AND 60 THEN 1 ELSE 0 END) AS pob_15_64,
        SUM(CASE WHEN edad_quinquenal >= 65 THEN 1 ELSE 0 END) AS pob_65_mas,
        SUM(CASE WHEN edad_quinquenal >= 80 THEN 1 ELSE 0 END) AS pob_80_mas,
"""

# ---------------------------------------------------------------------------
# 4) Indicadores de envejecimiento por comuna (346/346)
# ---------------------------------------------------------------------------
print("4) Calculando indicadores de envejecimiento por comuna (346/346) ...")
q4 = f"""
COPY (
    WITH agg AS (
        SELECT
            comuna,
            ANY_VALUE(region) AS region,
            COUNT(*) AS pob_total,
            {EDAD_CASE}
            SUM(CASE WHEN area = 1 THEN 1 ELSE 0 END) AS pob_urbana,
            MEDIAN(CASE WHEN edad >= 0 THEN edad END) AS edad_mediana_exacta,
            -- mediana aproximada desde quinquenios (fallback, siempre disponible)
            MEDIAN(CASE edad_quinquenal
                WHEN 0 THEN 2 WHEN 5 THEN 7 WHEN 10 THEN 12 WHEN 15 THEN 17
                WHEN 20 THEN 22 WHEN 25 THEN 27 WHEN 30 THEN 32 WHEN 35 THEN 37
                WHEN 40 THEN 42 WHEN 45 THEN 47 WHEN 50 THEN 52 WHEN 55 THEN 57
                WHEN 60 THEN 62 WHEN 65 THEN 67 WHEN 70 THEN 72 WHEN 75 THEN 77
                WHEN 80 THEN 82 ELSE 87.5 END) AS edad_mediana_aprox,
            MAX(CASE WHEN edad < 0 THEN 1 ELSE 0 END) AS tiene_edad_enmascarada
        FROM {census} c
        GROUP BY comuna
    )
    SELECT
        a.region,
        l.region_nombre_corto AS region_nombre,
        a.comuna,
        l.comuna_nombre,
        a.pob_total,
        a.pob_0_14,
        a.pob_15_64,
        a.pob_65_mas,
        a.pob_80_mas,
        COALESCE(a.edad_mediana_exacta, a.edad_mediana_aprox) AS edad_mediana,
        (a.tiene_edad_enmascarada = 1) AS edad_mediana_es_aproximada,
        ROUND(100.0 * a.pob_65_mas / a.pob_total, 2) AS pct_65_mas,
        ROUND(100.0 * a.pob_0_14 / a.pob_total, 2) AS pct_0_14,
        ROUND(100.0 * a.pob_80_mas / a.pob_total, 2) AS pct_80_mas,
        ROUND(100.0 * a.pob_65_mas / NULLIF(a.pob_0_14,0), 2) AS indice_envejecimiento,
        ROUND(100.0 * (a.pob_0_14 + a.pob_65_mas) / NULLIF(a.pob_15_64,0), 2) AS indice_dependencia_total,
        ROUND(100.0 * a.pob_65_mas / NULLIF(a.pob_15_64,0), 2) AS indice_dependencia_vejez,
        ROUND(100.0 * a.pob_urbana / a.pob_total, 2) AS pct_urbano
    FROM agg a
    LEFT JOIN {lookup} l ON l.comuna_id = a.comuna
    ORDER BY pct_65_mas DESC
) TO '{OUT / "indicadores_comuna.csv"}' (HEADER, DELIMITER ',')
"""
con.execute(q4)

# ---------------------------------------------------------------------------
# 5) Indicadores de envejecimiento por region (16/16, edad exacta disponible
#    en las 16 regiones ya que ninguna region completa esta bajo el umbral)
# ---------------------------------------------------------------------------
print("5) Calculando indicadores de envejecimiento por region ...")
q5 = f"""
COPY (
    WITH agg AS (
        SELECT
            region,
            COUNT(*) AS pob_total,
            {EDAD_CASE}
            SUM(CASE WHEN area = 1 THEN 1 ELSE 0 END) AS pob_urbana,
            MEDIAN(CASE WHEN edad >= 0 THEN edad END) AS edad_mediana
        FROM {census} c
        GROUP BY region
    )
    SELECT
        a.region,
        l.region_nombre_corto AS region_nombre,
        a.pob_total,
        a.pob_0_14,
        a.pob_15_64,
        a.pob_65_mas,
        a.pob_80_mas,
        a.edad_mediana,
        ROUND(100.0 * a.pob_65_mas / a.pob_total, 2) AS pct_65_mas,
        ROUND(100.0 * a.pob_0_14 / a.pob_total, 2) AS pct_0_14,
        ROUND(100.0 * a.pob_80_mas / a.pob_total, 2) AS pct_80_mas,
        ROUND(100.0 * a.pob_65_mas / NULLIF(a.pob_0_14,0), 2) AS indice_envejecimiento,
        ROUND(100.0 * (a.pob_0_14 + a.pob_65_mas) / NULLIF(a.pob_15_64,0), 2) AS indice_dependencia_total,
        ROUND(100.0 * a.pob_65_mas / NULLIF(a.pob_15_64,0), 2) AS indice_dependencia_vejez,
        ROUND(100.0 * a.pob_urbana / a.pob_total, 2) AS pct_urbano
    FROM agg a
    LEFT JOIN (SELECT DISTINCT region_id, region_nombre_corto FROM {lookup}) l
        ON l.region_id = a.region
    ORDER BY pct_65_mas DESC
) TO '{OUT / "indicadores_region.csv"}' (HEADER, DELIMITER ',')
"""
con.execute(q5)

print("Listo. Archivos escritos en:", OUT)
