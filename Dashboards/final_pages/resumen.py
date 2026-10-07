"""Resumen: el problema en cuatro cifras (modo final)."""
import streamlit as st
from utils import load_csv, kpi_card_row
from components.charts import age_group_shares

st.title("Envejecimiento demográfico y sostenibilidad de las pensiones")
st.caption("Desafío 1 · Herramientas de Análisis y Visualización de Datos · USM")

reg = load_csv("indicadores_region.csv")
proy = load_csv("proyeccion_envejecimiento_pais.csv")
pres = load_csv("kpi_presion_previsional_region.csv")
alemania = load_csv("alemania_piramide_edad_simple_2024.csv")

shares = age_group_shares(reg)
pct_2070 = proy.loc[proy.anio == 2070, "pct_65_mas"].iloc[0]
peak_year = int(proy.loc[proy.pob_15_64.idxmax(), "anio"])
soporte = pres["cotizantes"].sum() / pres["pob_65_mas"].sum()
pct_65_de = 100 * alemania.loc[alemania.edad >= 65, "poblacion"].sum() / alemania["poblacion"].sum()

st.markdown("### Chile envejece más rápido de lo que nace")
kpi_card_row([
    ("Población 65+ hoy (Censo 2024)", f"{shares['pct_65_mas']:.1f}%", "Era 6,6% en 1992"),
    ("Población 65+ en 2070", f"{pct_2070:.0f}%", "Proyección INE base 2024"),
    ("Pico de población en edad de trabajar", str(peak_year), "Desde ahí la población de 15-64 años decrece de forma permanente"),
    ("Cotizantes por adulto mayor", f"{soporte:.2f}", "Cotizantes AFP 2025 / población 65+ (Censo 2024)"),
])
st.caption(f"Alemania ya está en {pct_65_de:.1f}% de población 65+ (2024): es el espejo del Chile que viene.")

st.divider()
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Qué le pasa a una AFP")
    st.markdown(
        "- **Ingreso = cotizantes activos × sueldo imponible × % comisión.** La AFP solo cobra sobre el flujo activo.\n"
        "- Menos cotizantes activos → menos comisión.\n"
        "- Más cuentas pasivas (inactivas y pensionadas) → sube el costo por cliente activo.\n"
        "- La Reforma 2025 suma un gestor estatal como competidor."
    )
with col2:
    st.markdown("#### Cómo está organizado este dashboard")
    st.markdown(
        "- **Problema:** pirámides, Chile vs. Alemania, envejecimiento 1992-2070 y pico de la población activa.\n"
        "- **Objetivo 1, retener y ampliar la base activa:** KPIs 1.1, 1.2 y 1.3.\n"
        "- **Objetivo 2, controlar el costo por cliente:** KPIs 2.1, 2.2 y 2.3.\n"
        "- **Fuentes y método:** de dónde sale cada cifra y sus límites."
    )
