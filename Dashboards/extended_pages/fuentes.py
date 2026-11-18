"""Fuentes de datos por KPI, cómo se combinan y limitaciones conocidas (diapositiva 18 + estado actual)."""
import pandas as pd
import streamlit as st
from components.kpi_card import load_presentation_kpis, STATUS_LABEL

st.title("Fuentes y método")

st.subheader("Fuentes por KPI")
rows = []
for k in load_presentation_kpis().values():
    icon, status_text = STATUS_LABEL[k["status"]]
    rows.append({
        "KPI": f"{k['id']} {k['nombre']}",
        "Estado": f"{icon} {status_text}",
        "Fuente(s)": "; ".join(k["fuente"]) if k.get("fuente") else "; ".join(k.get("datos_faltantes", [])),
    })
st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

st.subheader("Todas las fuentes: qué se tomó y dónde se ve")
FUENTES = [
    ("INE, Censo 2024 (microdatos de personas)", "Población por edad, sexo y región; 15-64 y 65+; ocupación y empleo",
     "Problema; cobertura y razón de soporte; causas de la cobertura",
     "Abril de 2024: es el año de referencia y manda sobre otras fuentes de población. Edad en tramos de 5 años (la edad exacta está enmascarada en 51 comunas)"),
    ("INE, estimaciones y proyecciones 1992-2070 (base 2024, país)", "Población por edad y sexo, año a año",
     "Pico de población en edad de trabajar; 65+ hasta 2070; escenarios de razón de soporte y de costo",
     "Población al 30 de junio. Se usa su variación en el tiempo, llevada al nivel del Censo"),
    ("INE, proyecciones 2002-2035 por comuna (base 2017)", "Población 15-64 por región, año a año",
     "Cobertura por región desde 2002", "Solo aporta la dinámica; el nivel es el del Censo 2024"),
    ("INE, Encuesta Nacional de Empleo (regional)", "Ocupados, desocupados e informalidad por región y sexo",
     "Por qué cotizan menos en unas regiones", "Diciembre 2024 (trimestre nov-ene 2024-25), del anexo del estudio de la Asociación de AFP; las exportaciones del INE llegan a mar-may 2024 (por sexo: nov-ene 2023-24)"),
    ("INE, Encuesta Suplementaria de Ingresos y empleo", "Ingreso mediano y número de ocupados",
     "Costo por ocupado frente al 10 % del ingreso", "Ingreso nominal anual, llevado a pesos de 2025; ocupados de octubre-diciembre"),
    ("Superintendencia de Pensiones, cotizantes por región", "Cotizantes de cada diciembre, 1985-2025",
     "Cobertura y razón de soporte", "Diciembre de 2024 (56.094 sin región); 2025 solo en las series"),
    ("Superintendencia de Pensiones, cuadros 04A y 32C", "Cotizantes e ingreso imponible mensual (2002-2026) y por región",
     "Capacidad de pago del punto crítico", "Masa imponible = suma de los 12 meses; pesos de 2025"),
    ("Superintendencia de Pensiones, Fichas Estadísticas Previsionales 136-159", "Cotizantes e ingreso promedio, ene-2024 a dic-2025",
     "Flujo comisionable (KPI 1.3)", "Aporte del trabajador estimado: cotizantes × ingreso × 10 %"),
    ("Superintendencia de Pensiones, pensiones pagadas (julio 2026)", "Pensionados y monto de las ex cajas del IPS",
     "Parte del costo por persona de 65+ que no es Pilar Solidario", "Solo el sistema antiguo; sin leyes de reparación"),
    ("Subsecretaría de Previsión Social, Pilar Solidario (informes de oct-dic 2023, 2024 y 2025) y Nota Técnica Ley 21.735",
     "Pensión Garantizada Universal, pensiones básicas y aportes solidarios; calendario de la reforma",
     "Costo del Pilar; sin pensión propia por región; aporte del Estado al fondo del Seguro Social",
     "Gasto nominal anual, llevado a pesos de 2025; región: promedio del cuarto trimestre de 2024"),
    ("DIPRES, finanzas públicas 2016-2025, informe del Fondo de Reserva de Pensiones y nota técnica del fondo del Seguro Social",
     "Gasto «Edad avanzada»; retiros y saldo del Fondo de Reserva", "Costo por persona de 65+; peso en el PIB; agotamiento de la reserva",
     "Gasto del Gobierno Central, clasificación funcional 7102; saldo al 31-12-2025"),
    ("Banco Central, PIB anual (referencia 2018) e IPC", "PIB corriente; variación mensual del IPC",
     "Peso en el PIB; pesos de 2025", "IPC con un decimal: sirve para razones entre años, no como nivel"),
    ("Fondo Autónomo de Protección Previsional, estados financieros", "Cotizaciones recibidas y beneficios pagados",
     "Flujo comisionable; caja del primer semestre de 2026", "Estados al 31-12-2025 y al 30-06-2026 (revisión limitada); cifras transcritas del PDF"),
    ("Servicio de Impuestos Internos, UTM y dólar observado", "Valor de la UTM 2025; dólar promedio y de cierre",
     "Aporte del Estado en pesos; retiros y reserva del Fondo de Reserva en pesos", "Promedio de los meses; leído de la página web (no hay copia en el repositorio)"),
    ("CASEN 2022, Ministerio de Desarrollo Social", "Pobreza por ingresos de 65+; ingreso per cápita",
     "Pobreza en la vejez; ingreso y cobertura", "Pobreza con el factor de expansión regional; ingreso con el factor comunal de un extracto de terceros"),
    ("Asociación de AFP, Informe Previsional Económico 135", "Ocupados, desocupados e informales de diciembre de 2024",
     "Descomposición de la brecha de cobertura; informalidad y desocupación de 2024 en las causas", "Cifras transcritas a mano del anexo del PDF (96 valores revisados); reproduce al decimal la ENE del INE de 2019"),
    ("Superintendencia de Pensiones, costos de administración de los fondos (informes 2016-2025)", "Ingresos por comisiones, gastos y ganancia del sistema y de cada administradora",
     "Costos y economía de las administradoras", "Cada informe en pesos de su diciembre; el gasto se compara con las comisiones del mismo año"),
    ("Destatis (Alemania)", "Población por edad y sexo 2024", "Comparación de pirámides", "Variante 0 (datos observados), año 2024"),
]
st.dataframe(pd.DataFrame(FUENTES, columns=["Fuente", "Qué se tomó", "Dónde se ve", "Cómo se tomó"]), hide_index=True, use_container_width=True)

st.subheader("Cómo se combinan las fuentes")
st.markdown(
    "- **El Censo 2024 manda.** Si otra fuente choca con él, se usa el Censo; la otra fuente solo aporta cómo cambian las cosas en el tiempo, multiplicada por (Censo 2024 / fuente 2024). "
    "Por eso las proyecciones del INE, que corrigen el subconteo del censo (+7,5 % en 65+), no cambian el nivel de las cifras.\n"
    "- **Año de referencia 2024:** cotizantes e ingreso imponible de diciembre de 2024 y gasto de 2024; 2025 aparece en las series. Regla: todo lo que compara territorios o se cruza con el Censo es de 2024; las series y la proyección del país llegan hasta 2025 y se marcan.\n"
    "- **Pesos de 2025:** todo monto de distintos años se lleva a pesos de 2025 con el IPC promedio anual; el peso en el PIB usa precios corrientes de cada año.\n"
    "- Cada choque entre fuentes, con la decisión y su efecto en los resultados, está anotado en `docs/DISCUSION_FUENTES.md`."
)

st.subheader("Limitaciones a tener presentes")
st.markdown(
    "- **Años de los cotizantes:** la cobertura (KPI 1.1) y la razón de soporte (KPI 1.2) usan cotizantes de diciembre de 2024, mismo año que el Censo 2024; los de 2025 (más recientes) quedan a 20 meses del Censo y no se mezclan con su población. El análisis del punto crítico usa 2025 como año de partida del país (con las proyecciones INE de ese año) y 2024 para regiones y comunas; toda comparación entre territorios, incluida Chile, es de 2024. Con 2024 como partida del país el punto crítico sigue en 2038 (2037,5 en lugar de 2037,7), así que la diferencia no cambia el resultado.\n"
    "- **Cotizantes sin región:** 56.094 cotizantes en 2024 y 13.914 en 2025 no tienen región informada y quedan fuera del cálculo regional.\n"
    "- **Proyección regional:** el INE aún no publica proyecciones regionales base 2024. La población 65+ por región "
    "en 2035 y 2050 usa un reparto de las tasas nacionales, no es oficial.\n"
    "- **Cobertura año a año:** la población regional de 2002 a 2025 viene de las proyecciones base 2017, llevadas al nivel del Censo; 2018-2025 son proyecciones, no datos. "
    "La serie del país entre 2002 y 2009 es la suma de las regiones y queda hasta 0,2 puntos sobre la serie oficial que se usa desde 2010.\n"
    "- **Causas de la cobertura:** son correlaciones entre 16 regiones, no causas. La informalidad es de diciembre 2024 (nov-ene 2024-25, del anexo del estudio de la Asociación de AFP, el mismo mes de los cotizantes): r = −0,80; con diciembre 2023 era −0,83 y con mar-may 2024 −0,85, así que el resultado es estable.\n"
    "- **Ingreso de la CASEN:** es una encuesta, y el extracto con comuna es de terceros (sus ingresos son idénticos a los de la base oficial). "
    "Ponderado con el factor comunal, el ingreso regional queda hasta 4,7 % bajo el calculado con el factor regional; la correlación con la cobertura pasa de 0,77 a 0,78.\n"
    "- **Escenario de razón de soporte:** supone que la cobertura previsional se mantiene constante; no es un pronóstico.\n"
    "- **Edad no informada:** ~151 mil personas del Censo tienen la edad enmascarada y no entran en las pirámides.\n"
    "- **Pensiones pagadas (Superintendencia):** los archivos disponibles cubren solo el sistema antiguo (IPS), por lo que no "
    "equivalen a todas las pensiones.\n"
    "- **Cifras transcritas a mano:** los PDF del Fondo Autónomo de Protección Previsional, del Fondo de Reserva de Pensiones y del estudio de la Asociación de AFP, y el dólar y la UTM del SII, no tienen lector automático; se revisaron contra el original (ver abajo)."
)

st.subheader("Revisión contra las fuentes originales")
st.markdown(
    "El 16 de noviembre de 2026 se recalcularon, desde los archivos originales y sin usar los scripts del proyecto, más de 1.200 valores de los gráficos "
    "(pirámides, regiones, series 2002-2025, costos, financiamiento, pobreza). No hay diferencias de datos: las que quedan son decisiones de método y están en las limitaciones de arriba. "
    "Detalle por fuente en `docs/AUDITORIA_FUENTES.md`."
)
st.caption("Metodología completa de cada indicador: `Data processed/README.md` y `config/kpis.yaml`.")
