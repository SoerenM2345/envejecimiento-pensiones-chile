"""
KPI 1.1, cierre: ¿qué puede hacer una administradora de fondos de pensiones frente a la cobertura estancada y qué le corresponde al Estado? Una fila por palanca,
con a cuántas personas alcanza (de las piezas de la cobertura), quién actúa y con qué respaldo. Ejecutar DESPUÉS de Scripts/29_composicion_cotizantes.py.

Qué es dato y qué es juicio (columna `respaldo`):
  - «Ley» = lo dice la Nota Técnica de la Ley 21.735 (Data raw/_external/ley_21735/): Sistema Único de Cobranza (sección 3.1.4, desde el 1 de junio de 2026 y financiado
    por las administradoras), Seguro de Lagunas Previsionales ampliado (sección 5, desde el 1 de mayo de 2025), honorarios e independientes (sección 6).
  - «Propuesta del gremio» = documentos de la Asociación de AFP: Hoja de Ruta 555 (agosto de 2023: más cotización, edad de jubilación) y Mesa de Formalidad Laboral
    con la CPC y la ASECH (15 medidas contra la informalidad, 2024). Se cita que existen y qué proponen; no se evalúa su efecto.
  - «Juicio del equipo» = el alcance de la administradora y el impacto son una valoración nuestra, no una estimación: no hay medición del efecto de estas palancas.
Las personas vienen de kpi_cobertura_composicion*.csv (diciembre de 2024, Censo 2024) y NO se suman: los grupos se superponen (parte de los informales son
independientes) y las palancas de retención se miden sobre los cotizantes de hoy.

Salida (Data processed/): kpi_cobertura_palancas.csv  orden, efecto, palanca, que_es, actor, alcance_afp, grupo, personas, pieza, impacto, respaldo, fuente
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DP = ROOT / "Data processed"
NT = "Nota Técnica Ley 21.735 (Subsecretaría de Previsión Social, agosto de 2025)"


def palancas() -> pd.DataFrame:
    g = pd.read_csv(DP / "kpi_cobertura_composicion.csv").set_index("grupo").personas
    c = pd.read_csv(DP / "kpi_cobertura_composicion_categoria.csv")
    ind_ocupados = float(c[(c.tipo == "Independientes") & c.universo.str.startswith("Ocupados")].personas.iloc[0])
    ind_cotizan = float(c[(c.tipo == "Independientes") & c.universo.str.startswith("Cotizantes")].personas.iloc[0])
    cotizan = float(g["Cotizan: dependientes"] + g["Cotizan: independientes y voluntarios"])
    fuera = float(g["Buscan trabajo (desocupados)"] + g["Ni trabajan ni buscan"])
    filas = [
        ("Suma personas", "Más empleo y más participación laboral",
         "Que más personas trabajen o busquen trabajo: crecimiento, empleo, cuidado infantil, educación", "Estado y mercado laboral", "Ninguno",
         "Buscan trabajo + ni trabajan ni buscan", fuera, "Participación laboral y empleo", "Alto", "Juicio del equipo",
         "Descomposición de la cobertura del KPI 1.1 (piezas 1 y 2)"),
        ("Suma personas", "Cotización de los independientes",
         "Honorarios: la cotización será obligatoria al Seguro Social tras la gradualidad de la Ley 21.133 (año tributario 2028), con una ley pendiente. "
         "Sin boletas: cotización voluntaria simplificada desde agosto de 2025. La administradora puede facilitar el pago y comunicar; el gremio propone hacerla obligatoria",
         "Estado (ley); la administradora, de forma indirecta", "Indirecto",
         "Independientes que no figuran entre los cotizantes", ind_ocupados - ind_cotizan, "Ocupados que cotizan", "Alto", "Ley",
         f"{NT}, sección 6; Asociación de AFP, Mesa de Formalidad Laboral (2024)"),
        ("Suma personas", "Formalizar el empleo",
         "Menos informalidad: facilitar la contratación formal, compatibilizar la Pensión Garantizada Universal y los subsidios con la formalidad, más fiscalización "
         "(15 medidas de la Mesa de Formalidad Laboral de la Asociación de AFP, la CPC y la ASECH)",
         "Estado y empleadores; la administradora, con propuestas y capacitación", "Indirecto",
         "Ocupados informales (se superponen con los independientes)", float(g["No cotizan: ocupados informales"]), "Ocupados que cotizan", "Alto",
         "Propuesta del gremio", "Asociación de AFP, Propuestas Mesa de Formalidad Laboral 2024"),
        ("Suma personas", "Cobrar las cotizaciones declaradas y no pagadas",
         "Desde el 1 de junio de 2026 rige un Sistema Único de Cobranza de Cotizaciones que financian las administradoras; las cotizaciones cobradas vuelven a contar como pagadas",
         "Las administradoras", "Directo",
         "Ocupados formales fuera de la estadística (mezcla honorarios, Capredena, Dipreca y cotizaciones impagas)",
         float(g["No cotizan: ocupados formales fuera de la estadística"]), "Ocupados que cotizan", "Bajo", "Ley", f"{NT}, sección 3.1.4"),
        ("Protege lo que ya hay", "Avisar y cubrir las lagunas",
         "Avisar a los afiliados cuando se interrumpen las cotizaciones (cambio de trabajo, cesantía) y usar el Seguro de Lagunas Previsionales, ampliado desde el 1 de mayo de 2025 "
         "a todos los beneficiarios del Seguro de Cesantía. Cuida la densidad de quienes ya cotizan, no agrega personas",
         "Las administradoras", "Directo", "Cotizantes de hoy", cotizan, "Ocupados que cotizan", "Medio", "Juicio del equipo",
         f"{NT}, sección 5 (el seguro); los avisos son una posible acción, no una práctica comprobada"),
        ("Protege lo que ya hay", "Más cotización y edad de jubilación",
         "Hoja de Ruta 555 de la Asociación de AFP (agosto de 2023): resolver las lagunas, subir la tasa de cotización e incentivar postergar la jubilación. "
         "Sube el monto de la pensión, no la cantidad de cotizantes",
         "Estado (ley); la administradora, con propuestas", "Indirecto", "Cotizantes de hoy", cotizan, "Monto de la pensión", "Bajo",
         "Propuesta del gremio", "Asociación de AFP, Hoja de Ruta 555 (2023)"),
    ]
    d = pd.DataFrame(filas, columns=["efecto", "palanca", "que_es", "actor", "alcance_afp", "grupo", "personas", "pieza", "impacto", "respaldo", "fuente"])
    d.insert(0, "orden", range(1, len(d) + 1))
    assert d.personas.gt(0).all() and d.alcance_afp.isin(["Directo", "Indirecto", "Ninguno"]).all()
    return d


def main():
    d = palancas()
    d.round(1).to_csv(DP / "kpi_cobertura_palancas.csv", index=False)
    print(d[["orden", "efecto", "palanca", "alcance_afp", "personas", "impacto", "respaldo"]].to_string(index=False))


if __name__ == "__main__":
    main()
