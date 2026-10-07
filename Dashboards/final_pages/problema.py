"""Definición del problema (diapositivas 6-11): pirámides, Chile vs. Alemania, envejecimiento, pico de la población activa."""
import streamlit as st
from utils import load_csv, kpi_card_row, PLOTLY_DL_CONFIG
from components.charts import (pyramid_chile, pyramid_chile_vs_alemania, age_group_shares,
                               aging_share_series, working_age_peak)

st.title("Definición del problema")

reg = load_csv("indicadores_region.csv")
proy = load_csv("proyeccion_envejecimiento_pais.csv")
censo = load_csv("censo_pais_edad_simple.csv")
alemania = load_csv("alemania_piramide_edad_simple_2024.csv")

# --- 1. Chile ya no tiene forma de pirámide -------------------------------------
st.header("1. Chile ya no tiene forma de pirámide: envejece más rápido de lo que nace")
s24 = age_group_shares(reg)
p92 = proy[proy.anio == 1992].iloc[0]
col_fig, col_txt = st.columns([3, 2])
with col_fig:
    st.plotly_chart(pyramid_chile(censo), use_container_width=True, config=PLOTLY_DL_CONFIG)
with col_txt:
    st.markdown("**Chile 2024 (Censo)**")
    kpi_card_row([("0-14", f"{s24['pct_0_14']:.1f}%", None), ("15-64", f"{s24['pct_15_64']:.1f}%", None),
                  ("65+", f"{s24['pct_65_mas']:.1f}%", None)])
    st.markdown("**Chile 1992 (estimación INE)**")
    kpi_card_row([("0-14", f"{p92.pct_0_14:.1f}%", None), ("15-64", f"{100 - p92.pct_0_14 - p92.pct_65_mas:.1f}%", None),
                  ("65+", f"{p92.pct_65_mas:.1f}%", None)])
    st.caption("Barras por edad simple y sexo; tonos sólidos = 65 años y más (la línea roja marca los 65). "
               "El Censo agrupa los 85+ en una sola barra.")

# --- 2. Chile vs Alemania -------------------------------------------------------
st.header("2. Alemania es el espejo del Chile que viene")
st.plotly_chart(pyramid_chile_vs_alemania(censo, alemania), use_container_width=True, config=PLOTLY_DL_CONFIG)
st.markdown(
    "- Alemania muestra el punto de llegada; Chile sigue la misma trayectoria.\n"
    "- Menos población activa por cada adulto mayor implica menos soporte para el sistema previsional.\n"
    "- Esta presión demográfica recién comienza en Chile."
)
st.caption("Chile: Censo 2024 (la pirámide excluye ~151 mil personas con edad no informada, por eso su base es 18,33 millones "
           "y no 18,48). Alemania: Destatis, población 2024.")

# --- 3. Envejecimiento sostenido -------------------------------------------------
st.header("3. El envejecimiento se acelera de forma sostenida: de 14% a 43% hacia 2070")
st.plotly_chart(aging_share_series(proy), use_container_width=True, config=PLOTLY_DL_CONFIG)
st.caption("Fuente: INE, estimaciones y proyecciones de población 1992-2070 (base 2024). Punto rojo = Censo 2024.")

# --- 4. Pico de población en edad de trabajar -------------------------------------
st.header("4. En poco más de una década, la población en edad de trabajar comenzará a reducirse")
st.plotly_chart(working_age_peak(proy), use_container_width=True, config=PLOTLY_DL_CONFIG)
st.caption("Fuente: INE, proyecciones base 2024. Consecuencia: caída proyectada de los ingresos del sistema previsional.")

# --- 5. Por qué le importa a las AFP ----------------------------------------------
st.header("5. Por qué le importa a una AFP")
c1, c2 = st.columns(2)
with c1:
    st.subheader("Problema 1: caída de la población activa")
    st.markdown("Mayor carga para la población activa restante. **Menos cotizantes activos → menos comisión**, "
                "ya que la AFP solo cobra sobre el flujo activo.")
with c2:
    st.subheader("Problema 2: envejecimiento acelerado")
    st.markdown("Mayor costo y esfuerzo por una población 65+ creciente, con mayor esperanza de vida. "
                "**Más cuentas pasivas administradas sin comisión → sube el costo por cliente activo.**")

with st.expander("Modelo de negocio de la AFP y efecto de la Reforma 2025"):
    st.markdown(
        "**Ingreso = cotizantes activos × sueldo imponible × % comisión**\n\n"
        "- El 10% de ahorro obligatorio pertenece al trabajador; la AFP solo lo administra.\n"
        "- La comisión (tarifa adicional sobre el sueldo) es el ingreso real y se cobra solo sobre el flujo de cotizaciones activas.\n"
        "- Los nuevos ingresos vienen casi solo de traspasos entre AFP.\n\n"
        "**Reforma 2025:** solo parte de la nueva cotización llega a cuentas administradas por la AFP; el resto va al fondo "
        "estatal (FAPP) sin generar comisión. Licitación periódica de afiliados al menor postor y tope de participación "
        "de mercado por AFP; se suma además un gestor estatal como competidor."
    )
