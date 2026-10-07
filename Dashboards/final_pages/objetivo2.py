"""Objetivo 2: controlar el costo por cliente. KPIs 2.1, 2.2, 2.3 (aún sin datos: ver config/kpis.yaml)."""
import streamlit as st
from components.kpi_card import kpi_card

st.title("Objetivo 2: controlar el costo por cliente")
st.markdown("Optimizar la estructura de costos para absorber el crecimiento de cuentas inactivas y pensionadas sin perder rentabilidad.")

kpi_card("2.1")
kpi_card("2.2")
kpi_card("2.3")
