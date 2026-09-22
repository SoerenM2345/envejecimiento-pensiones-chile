"""Propuestas de políticas de envejecimiento activo, priorizadas a partir de
una segmentación de comunas construida con los propios datos del proyecto
(no es una lista genérica: cada propuesta apunta a comunas/regiones concretas)."""
import pandas as pd
import plotly.express as px
import streamlit as st
from utils import load_csv, PLOTLY_LAYOUT, CATEGORICAL

st.set_page_config(page_title="Políticas de envejecimiento activo", page_icon="📋", layout="wide")
st.title("📋 Propuestas de políticas de envejecimiento activo")
st.caption("Segmentación construida a partir de indicadores_comuna.csv + kpi_ingreso_envejecimiento.csv — no es una lista genérica.")

ing = load_csv("kpi_ingreso_envejecimiento.csv").dropna(subset=["ingreso_per_capita_prom"])
ing = ing[ing.pob_total >= 1000].copy()

med_65 = ing["pct_65_mas"].median()
med_urb = ing["pct_urbano"].median()
med_ing = ing["ingreso_per_capita_prom"].median()

def clasifica(row):
    if row["pct_65_mas"] < med_65:
        return "Aún joven (bajo el promedio)"
    urbano = row["pct_urbano"] >= med_urb
    rico = row["ingreso_per_capita_prom"] >= med_ing
    if urbano and rico:
        return "Envejecimiento urbano acomodado"
    if urbano and not rico:
        return "Envejecimiento urbano vulnerable"
    if not urbano and rico:
        return "Envejecimiento rural con ingreso"
    return "Envejecimiento rural vulnerable"

ing["segmento"] = ing.apply(clasifica, axis=1)
orden_segmentos = ["Envejecimiento rural vulnerable", "Envejecimiento urbano vulnerable",
                    "Envejecimiento rural con ingreso", "Envejecimiento urbano acomodado", "Aún joven (bajo el promedio)"]

st.subheader("Segmentación de comunas envejecidas (pob≥1.000, n=" + str(len(ing)) + ")")
st.caption(f"Umbrales: % 65+ ≥ {med_65:.1f}% (mediana nacional de la muestra) · % urbano ≥ {med_urb:.0f}% · "
           f"ingreso per cápita ≥ ${med_ing:,.0f} (CASEN 2022)")

col1, col2 = st.columns([3, 2])
with col1:
    fig = px.scatter(
        ing, x="ingreso_per_capita_prom", y="pct_urbano", color="segmento",
        category_orders={"segmento": orden_segmentos}, color_discrete_sequence=CATEGORICAL,
        hover_name="comuna_nombre", size="pob_total", size_max=28,
        labels={"ingreso_per_capita_prom": "Ingreso per cápita ($)", "pct_urbano": "% urbano"},
    )
    fig.update_layout(**PLOTLY_LAYOUT, title="Mapa de segmentos (tamaño = población)")
    st.plotly_chart(fig, use_container_width=True)
with col2:
    conteo = ing["segmento"].value_counts().reindex(orden_segmentos).fillna(0).astype(int)
    st.dataframe(conteo.rename("N° comunas"), use_container_width=True)

st.divider()
st.header("Propuestas por segmento")

def top_comunas(segmento, n=6):
    sub = ing[ing.segmento == segmento].nlargest(n, "pct_65_mas")
    return ", ".join(f"{r.comuna_nombre} ({r.region_nombre_corto}, {r.pct_65_mas:.0f}%)" for r in sub.itertuples())

st.markdown(f"""
### 🟥 Envejecimiento rural vulnerable
**Comunas ejemplo:** {top_comunas("Envejecimiento rural vulnerable")}

Alto % de 65+, baja urbanización, ingreso per cápita bajo el promedio. El patrón dominante es **éxodo de
población joven** hacia ciudades, dejando una población mayor con menos ingreso, más dispersión geográfica y
peor acceso a servicios.

- **Salud rural itinerante**: rondas médicas y geriátricas móviles (no solo postas fijas) con periodicidad
  garantizada, priorizando estas comunas en la red de Atención Primaria.
- **Conectividad y transporte**: subsidio a transporte rural para controles de salud y trámites de pensión
  (hoy la distancia es una barrera de acceso, no solo de ingreso).
- **Renta básica de cuidados** o refuerzo del Aporte Previsional Solidario/PGU con foco territorial en estas
  comunas, dado su bajo `razon_soporte_previsional` regional (ver página Pensiones y salud).
- **Programas "quedarse a cuidar"**: incentivos a cuidadores familiares que hoy migran, para reducir el
  abandono de adultos mayores solos.

### 🟧 Envejecimiento urbano vulnerable
**Comunas ejemplo:** {top_comunas("Envejecimiento urbano vulnerable")}

Alto % de 65+ en zonas urbanas de bajo ingreso — a diferencia del caso rural, aquí el desafío es **densidad sin
recursos**: mucha población mayor concentrada, pero con baja capacidad de pago para cuidados privados.

- **Centros diurnos comunales** (cuidado de día) financiados municipalmente vía Fondo Común Municipal
  reforzado, para liberar a cuidadores familiares que trabajan.
- **Vivienda adaptada**: subsidios de mejoramiento de vivienda (barandas, accesibilidad) en barrios con alta
  concentración de adultos mayores de bajos ingresos.
- **Prevención de aislamiento**: clubes de adultos mayores y voluntariado intergeneracional con financiamiento
  municipal, dado el mayor riesgo de soledad en departamentos/viviendas urbanas pequeñas.

### 🟨 Envejecimiento rural con ingreso
**Comunas ejemplo:** {top_comunas("Envejecimiento rural con ingreso")}

Zonas rurales/agrícolas o turísticas con envejecimiento alto pero ingreso per cápita sobre la mediana (ej. zonas
vitivinícolas, agroexportadoras o balnearios de segunda vivienda).

- **Envejecimiento activo productivo**: programas de turismo rural y economía local liderados por adultos
  mayores (activos, con base económica, pero en riesgo de pérdida de roles sociales al jubilarse del agro).
- **Telemedicina especializada**: aquí el ingreso permite conectividad; priorizar telemedicina geriátrica
  antes que infraestructura física nueva.

### 🟩 Envejecimiento urbano acomodado
**Comunas ejemplo:** {top_comunas("Envejecimiento urbano acomodado")}

Comunas de altos ingresos (ej. barrio alto de Santiago) con % 65+ igual o mayor que comunas pobres —
**envejecimiento "in situ"**: la población envejece en el mismo lugar, sin presión de vivienda ni de ingreso, pero
con riesgos propios (soledad en adultos mayores solos con recursos, sobre-uso de salud privada sin coordinación
con la red pública que igual los atenderá en la vejez extrema).

- **Envejecimiento activo con enfoque social, no asistencial**: programas de voluntariado, mentoría
  intergeneracional y participación cívica (la necesidad aquí no es económica sino de propósito y red social).
- **Coordinación público-privada de salud geriátrica**: estas comunas concentran demanda de salud compleja
  (ver el índice de demanda de salud) que eventualmente presiona también la red pública regional.
""")

st.divider()
st.header("Propuestas a nivel región (sostenibilidad del sistema)")
pres = load_csv("kpi_presion_previsional_region.csv").sort_values("razon_soporte_previsional")
peor3 = pres.head(3)["region_nombre"].tolist()
demanda = load_csv("kpi_indice_demanda_salud_region.csv").sort_values("indice_demanda_salud", ascending=False)
top3_salud = demanda.head(3)["region_nombre"].tolist()

st.markdown(f"""
- **Focalización territorial del gasto en PGU/pensiones solidarias**: {", ".join(peor3)} tienen la menor razón
  de soporte previsional (menos cotizantes activos por cada adulto mayor) — son las regiones donde el gasto
  fiscal en pensiones no contributivas crecerá más rápido relativo a su base de cotizantes local.
- **Inversión anticipada en salud geriátrica**: {", ".join(top3_salud)} encabezan el índice de demanda de
  salud (mayor % actual de 65+/80+ *y* mayor velocidad de envejecimiento proyectada a 2035) — son las
  candidatas naturales para priorizar camas geriátricas, especialistas y Centros de Salud Familiar con
  módulo del adulto mayor antes de que la demanda madure.
- **Formalización laboral regional**: la cobertura previsional (% de 15-64 años que cotiza) varía de ~39% a
  ~55% entre regiones (página Pensiones y salud) — cerrar esa brecha en las regiones de menor cobertura
  amplía la base de cotizantes futuros más rápido que cualquier ajuste paramétrico del sistema.
- **Envejecimiento activo en zonas mineras jóvenes (Antofagasta, Tarapacá)**: hoy son las regiones más
  jóvenes del país, pero envejecerán con el tiempo sobre una base económica distinta (alta dependencia del
  ciclo minero) — planificar ahora infraestructura de cuidados evita el rezago que hoy enfrentan Valparaíso/Ñuble.
""")

st.caption("Metodología de segmentación: split por mediana en % urbano e ingreso per cápita CASEN 2022, "
           "cruzado con % 65+ sobre la mediana nacional. Es una heurística simple y transparente, no un "
           "modelo de clustering — reproducible en el Explorador de datos filtrando kpi_ingreso_envejecimiento.csv.")
