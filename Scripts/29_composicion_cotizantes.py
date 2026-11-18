"""
KPI 1.1, el estado actual: ¿cómo se reparten las personas de 15 a 64 años entre las que cotizan y las que no, y por qué no? Ejecutar DESPUÉS de
Scripts/25_explorar_causas.py (usa kpi_cobertura_factores_anual.csv y ene_region_anual.csv).

Los grupos son los mismos de la descomposición de la cobertura (participación × empleo × ocupados que cotizan), de modo que el gráfico y las
razones del resto del KPI usan las mismas piezas y suman lo mismo:
  - pieza 1 «Participación laboral»: fuera de la fuerza de trabajo (ni trabajan ni buscan) = población 15-64 − ocupados − desocupados
  - pieza 2 «Empleo»: desocupados
  - pieza 3 «Ocupados que cotizan»: cotizantes (dependientes; independientes y voluntarios) y ocupados que no cotizan, estos últimos separados en
        informales (ENE) y formales que no están en la estadística (honorarios, Capredena, Dipreca, cotizaciones declaradas y no pagadas)

Fuentes:
  - Data processed/kpi_cobertura_factores_anual.csv   Chile 2024: población 15-64, ocupados, desocupados y cotizantes con región (ya al nivel del Censo)
  - Data processed/ene_region_anual.csv               ocupados e informales de Chile 2024 (ENE, anexo del estudio de la Asociación de AFP); los informales se
        llevan al nivel del Censo con el mismo factor que los ocupados (ocupados del KPI ÷ ocupados de la ENE)
  - Data processed/cotizantes_por_tipo_sexo.csv       cotizantes de diciembre 2024 por tipo (Superintendencia de Pensiones); reparte los cotizantes con región
  - Data raw/personas_censo2024.csv                   categoría ocupacional del Censo (p40_cise_rec: 1 = independiente, 2 = asalariado, 3 = otras) de los ocupados

Supuestos (en docs/supuestos_y_limitaciones.md, sección 7): ningún ocupado informal figura entre los cotizantes; el código 1 de p40_cise_rec es «independiente»
(cuenta propia y empleadores), como ya lo usa el script 24; los ocupados y desocupados incluyen a los de 65 años o más, igual que la cobertura.

Por región (Chile y las 16 regiones) se usa la misma cuenta, con dos supuestos más: la Superintendencia no publica los cotizantes por tipo y región, así que
los independientes y voluntarios se reparten en cada región con la proporción del país (0,8 % de los cotizantes); y los informales de la ENE de cada región se
llevan al nivel del Censo con el factor de esa región. En O'Higgins los informales así llevados superan a los ocupados que no cotizan; se limitan a ellos
(los «formales fuera de la estadística» quedan en 0).

Salidas (Data processed/):
  - kpi_cobertura_composicion.csv            una fila por grupo: pieza, grupo, personas, % de la población 15-64 (Chile)
  - kpi_cobertura_composicion_region.csv     lo mismo para Chile (region_id 0) y las 16 regiones: region_id, region_nombre, pieza, grupo, personas, pct_15_64
  - kpi_cobertura_composicion_categoria.csv  ocupados (Censo) frente a cotizantes (Superintendencia) por tipo de trabajo: personas y %
"""
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DP = ROOT / "Data processed"
CENSO = ROOT / "Data raw" / "personas_censo2024.csv"
ANIO = 2024


def composicion(territorio_id: int = 0) -> pd.DataFrame:
    f = pd.read_csv(DP / "kpi_cobertura_factores_anual.csv")
    f = f[(f.territorio_id == territorio_id) & (f.anio == ANIO)].iloc[0]
    ene = pd.read_csv(DP / "ene_region_anual.csv")
    ene = ene[(ene.territorio_id == territorio_id) & (ene.anio == ANIO)].iloc[0]
    tipo = pd.read_csv(DP / "cotizantes_por_tipo_sexo.csv")
    tipo = tipo[(tipo.anio == ANIO) & (tipo.sexo == "Total")].set_index("tipo").cotizantes
    assert tipo["Dependientes"] + tipo["Independientes"] + tipo["Afiliados voluntarios"] == tipo["Total"]

    cot = float(f.cotizantes)  # cotizantes con región, los de la cobertura del KPI
    dep = cot * tipo["Dependientes"] / tipo["Total"]  # los 56 mil sin región se reparten en la misma proporción
    ind = cot - dep
    informales = float(ene.informales) * float(f.ocupados) / float(ene.ocupados)  # al nivel del Censo
    sin_cotizar = float(f.ocupados) - cot
    if informales >= sin_cotizar:  # solo ocurre en O'Higgins (la encuesta y el Censo no cuadran en una región); en las demás y en Chile los informales caben
        assert territorio_id != 0
        print(f"Aviso: en la región {territorio_id} los informales ({informales:,.0f}) superan a los ocupados que no cotizan ({sin_cotizar:,.0f}); se limitan a estos")
        informales = sin_cotizar
    assert 0 < informales <= sin_cotizar
    filas = [
        (3, "Cotizan: dependientes", dep),
        (3, "Cotizan: independientes y voluntarios", ind),
        (3, "No cotizan: ocupados informales", informales),
        (3, "No cotizan: ocupados formales fuera de la estadística", sin_cotizar - informales),
        (2, "Buscan trabajo (desocupados)", float(f.desocupados)),
        (1, "Ni trabajan ni buscan", float(f.p1564) - float(f.ocupados) - float(f.desocupados)),
    ]
    d = pd.DataFrame(filas, columns=["pieza", "grupo", "personas"])
    d["pct_15_64"] = 100 * d.personas / float(f.p1564)
    assert abs(d.personas.sum() - float(f.p1564)) < 1 and abs(d.pct_15_64.sum() - 100) < 1e-6
    assert abs(d[d.grupo.str.startswith("Cotizan")].pct_15_64.sum() - float(f.cobertura_pct)) < 1e-6  # la misma cobertura del KPI
    return d


def categoria() -> pd.DataFrame:
    n = duckdb.connect().execute(f"""
        SELECT p40_cise_rec c, count(*) n FROM read_csv_auto('{CENSO.as_posix()}', delim=';', sample_size=300000)
        WHERE sit_fuerza_trabajo = 1 AND p40_cise_rec IN (1, 2, 3) GROUP BY 1""").df().set_index("c").n
    tipo = pd.read_csv(DP / "cotizantes_por_tipo_sexo.csv")
    tipo = tipo[(tipo.anio == ANIO) & (tipo.sexo == "Total")].set_index("tipo").cotizantes
    ind_cot = float(tipo["Independientes"] + tipo["Afiliados voluntarios"])
    filas = [
        ("Ocupados (Censo 2024)", "Independientes", float(n[1])),
        ("Ocupados (Censo 2024)", "Dependientes y otros", float(n[2] + n[3])),
        ("Cotizantes (Superintendencia, dic-2024)", "Independientes", ind_cot),
        ("Cotizantes (Superintendencia, dic-2024)", "Dependientes y otros", float(tipo["Dependientes"])),
    ]
    d = pd.DataFrame(filas, columns=["universo", "tipo", "personas"])
    d["pct"] = 100 * d.personas / d.groupby("universo").personas.transform("sum")
    return d


def composicion_regiones() -> pd.DataFrame:
    nombres = pd.read_csv(DP / "kpi_cobertura_regiones.csv").set_index("region_id").region_nombre
    filas = [composicion(rid).assign(region_id=rid, region_nombre=nombres[rid]) for rid in range(0, 17)]
    return pd.concat(filas, ignore_index=True)[["region_id", "region_nombre", "pieza", "grupo", "personas", "pct_15_64"]]


def main():
    d, c = composicion(), categoria()
    d.round(4).to_csv(DP / "kpi_cobertura_composicion.csv", index=False)
    composicion_regiones().round(4).to_csv(DP / "kpi_cobertura_composicion_region.csv", index=False)
    c.round(4).to_csv(DP / "kpi_cobertura_composicion_categoria.csv", index=False)
    print(d.round(1).to_string(index=False))
    print(c.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
