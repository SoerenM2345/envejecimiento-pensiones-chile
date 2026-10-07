"""Fuentes de datos por KPI y limitaciones conocidas (diapositiva 18 + estado actual)."""
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

st.subheader("Diagnóstico general")
st.markdown(
    "| Dato | Fuente |\n|---|---|\n"
    "| Estructura etaria, pirámide Chile | INE, Censo 2024 (18.480.432 personas) |\n"
    "| Proyecciones 1992-2070 | INE, estimaciones y proyecciones de población base 2024 (nacional) |\n"
    "| Pirámide de Alemania | Destatis |\n"
    "| Cotizantes por región | Superintendencia de Pensiones |"
)

st.subheader("Limitaciones a tener presentes")
st.markdown(
    "- **Años distintos:** el Censo es 2024 y los cotizantes son de diciembre de 2025.\n"
    "- **Cotizantes sin región:** 13.914 cotizantes no tienen región informada y quedan fuera del cálculo regional.\n"
    "- **Proyección regional:** el INE aún no publica proyecciones regionales base 2024. La población 65+ por región "
    "en 2035 y 2050 usa un reparto de las tasas nacionales, no es oficial.\n"
    "- **Escenario de razón de soporte:** supone que la cobertura previsional 2025 se mantiene constante; no es un pronóstico.\n"
    "- **Edad no informada:** ~151 mil personas del Censo tienen la edad enmascarada y no entran en las pirámides.\n"
    "- **Pensiones pagadas (Superintendencia):** los archivos disponibles cubren solo el sistema antiguo (IPS), por lo que no "
    "equivalen a todas las pensiones."
)
st.caption("Detalle metodológico completo: `Data processed/README.md` y `config/kpis.yaml`.")
