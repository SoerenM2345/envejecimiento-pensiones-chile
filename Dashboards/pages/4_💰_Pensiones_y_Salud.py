"""Presión sobre pensiones y salud: cobertura previsional, razón de soporte,
proyección regional 2024→2035→2050 e índice de demanda de salud."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils import load_csv, kpi_card_row, CATEGORICAL, PLOTLY_LAYOUT, RED, INK_MUTED, PLOTLY_DL_CONFIG

st.set_page_config(page_title="Pensiones y salud", page_icon="💰", layout="wide")
st.title("💰 Presión sobre pensiones y salud")

pres = load_csv("kpi_presion_previsional_region.csv").sort_values("razon_soporte_previsional")
edad_kpi = load_csv("kpi_presion_previsional_edad.csv")
proy_reg = load_csv("kpi_proyeccion_regional.csv")
demanda = load_csv("kpi_indice_demanda_salud_region.csv")

nacional_soporte = pres["cotizantes"].sum() / pres["pob_65_mas"].sum()
nacional_cobertura = 100 * pres["cotizantes"].sum() / pres["pob_15_64"].sum()

kpi_card_row([
    ("Cotizantes por adulto mayor (país)", f"{nacional_soporte:.2f}", "Cotizantes AFP 2025 / población 65+ (Censo 2024)"),
    ("Cobertura previsional (país)", f"{nacional_cobertura:.1f}%", "Cotizantes 2025 / población 15-64"),
    ("Región más presionada", pres.iloc[0]["region_nombre"], f"{pres.iloc[0]['razon_soporte_previsional']:.2f} cotizantes/adulto mayor"),
    ("Región menos presionada", pres.iloc[-1]["region_nombre"], f"{pres.iloc[-1]['razon_soporte_previsional']:.2f} cotizantes/adulto mayor"),
])

st.divider()
col1, col2 = st.columns(2)
with col1:
    fig = px.bar(pres, x="razon_soporte_previsional", y="region_nombre", orientation="h",
                 color_discrete_sequence=[CATEGORICAL[0]],
                 labels={"razon_soporte_previsional": "Cotizantes por adulto mayor", "region_nombre": ""})
    fig.add_vline(x=nacional_soporte, line_dash="dash", line_color="#52514e",
                  annotation_text=f"País: {nacional_soporte:.2f}", annotation_position="top")
    fig.update_layout(**PLOTLY_LAYOUT, title="Razón de soporte previsional por región")
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DL_CONFIG)
    st.caption("Cotizantes AFP 2025 por cada persona de 65+ (Censo 2024). A menor valor, mayor presión sobre el sistema en esa región.")

with col2:
    pres2 = pres.sort_values("cobertura_previsional_pct")
    fig = px.bar(pres2, x="cobertura_previsional_pct", y="region_nombre", orientation="h",
                 color_discrete_sequence=[CATEGORICAL[1]],
                 labels={"cobertura_previsional_pct": "% de 15-64 años que cotiza", "region_nombre": ""})
    fig.add_vline(x=nacional_cobertura, line_dash="dash", line_color="#52514e",
                  annotation_text=f"País: {nacional_cobertura:.1f}%", annotation_position="top")
    fig.update_layout(**PLOTLY_LAYOUT, title="Cobertura previsional por región")
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DL_CONFIG)
    st.caption("Cotizantes 2025 sobre población en edad de trabajar (15-64, Censo 2024). El resto está fuera del sistema activo (informalidad, cesantía, inactividad).")

st.divider()
st.subheader("Proyección regional 2024 → 2035 → 2050 (método de reparto de tasas nacionales)")
st.caption("Aproximación: se aplica a cada región la tasa de crecimiento que el INE proyecta a nivel nacional por grupo etario, "
           "partiendo de su estructura real del Censo 2024. No es una proyección oficial INE por región (el INE aún no la publica en base 2024).")

regiones_todas = sorted(proy_reg["region_nombre"].unique())
default_sel = demanda.sort_values("indice_demanda_salud", ascending=False)["region_nombre"].head(5).tolist()
sel_regiones = st.multiselect("Regiones a comparar (recomendado: máx. 5-6 para legibilidad)", regiones_todas, default=default_sel)

ind_region = load_csv("indicadores_region.csv")
base2024 = ind_region[["region_nombre", "pct_65_mas"]].rename(columns={"pct_65_mas": "pct_65_mas_proy"})
base2024["anio"] = 2024
serie = load_csv("kpi_proyeccion_regional.csv")[["anio", "region_nombre", "pct_65_mas_proy"]]
serie_completa = pd.concat([base2024, serie])

if sel_regiones:
    plot_df = serie_completa[serie_completa.region_nombre.isin(sel_regiones)]
    fig = px.line(plot_df.sort_values("anio"), x="anio", y="pct_65_mas_proy", color="region_nombre",
                  markers=True, color_discrete_sequence=CATEGORICAL,
                  labels={"pct_65_mas_proy": "% población 65+", "anio": "Año", "region_nombre": "Región"})
    fig.update_layout(**PLOTLY_LAYOUT, title="Evolución proyectada de % 65+ por región")
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DL_CONFIG)
else:
    st.info("Elige al menos una región.")

st.divider()
st.subheader("Valparaíso vs. país: el envejecimiento avanza más rápido en la región")
st.caption(
    "Línea gris: índice de envejecimiento nacional 1992-2070 (INE, proyección base 2024 — ver también página "
    "Pirámides), ya en franca aceleración. Puntos rojos: Valparaíso, con su valor real 2024 (Censo) y su "
    "proyección 2035/2050 por reparto de tasas nacionales (misma aproximación de la sección anterior; no es una "
    "proyección oficial INE por región). Valparaíso ya parte más envejecida que el país (98.6 vs 80.0 en 2024) y "
    "la brecha se mantiene hacia 2035/2050 — mientras tanto, la región ya muestra solo 1.71 cotizantes por cada "
    "adulto mayor (gráfico de razón de soporte, arriba): menos personas activas sosteniendo a más adultos mayores."
)

proy_pais_full = load_csv("proyeccion_envejecimiento_pais.csv")
valpo_2024_idx = float(ind_region.loc[ind_region.region_nombre == "Valparaíso", "indice_envejecimiento"].iloc[0])
valpo_proy_idx = proy_reg.loc[proy_reg.region_nombre == "Valparaíso", ["anio", "indice_envejecimiento_proy"]]
valpo_serie = pd.concat([
    pd.DataFrame([{"anio": 2024, "indice_envejecimiento": valpo_2024_idx}]),
    valpo_proy_idx.rename(columns={"indice_envejecimiento_proy": "indice_envejecimiento"}),
]).sort_values("anio")

fig_val = go.Figure()
fig_val.add_trace(go.Scatter(
    x=proy_pais_full["anio"], y=proy_pais_full["indice_envejecimiento"], mode="lines",
    name="Chile (país)", line=dict(color=INK_MUTED, width=2),
    hovertemplate="Año %{x:.0f}<br>País: %{y:.0f} mayores por c/100 niños<extra></extra>",
))
fig_val.add_trace(go.Scatter(
    x=valpo_serie["anio"], y=valpo_serie["indice_envejecimiento"], mode="lines+markers",
    name="Valparaíso", line=dict(color=RED, width=3), marker=dict(size=9, color=RED),
    hovertemplate="Año %{x:.0f}<br>Valparaíso: %{y:.0f} mayores por c/100 niños<extra></extra>",
))
fig_val.update_layout(
    **PLOTLY_LAYOUT,
    title="Índice de envejecimiento: Valparaíso vs. Chile",
)
fig_val.update_xaxes(title_text="Año")
fig_val.update_yaxes(title_text="Mayores de 65 por c/100 niños de 0-14")
st.plotly_chart(fig_val, use_container_width=True, config=PLOTLY_DL_CONFIG)

st.divider()
st.subheader("Índice de presión potencial sobre salud (proxy demográfico)")
st.caption("Suma de puntajes estandarizados: % 65+ actual + % 80+ actual + velocidad de envejecimiento 2024→2035. "
           "No usa datos de uso real de servicios de salud (no hay archivo DEIS/MINSAL disponible) — es un indicador de demanda potencial, no de oferta ni utilización.")
fig = px.bar(demanda.sort_values("indice_demanda_salud"), x="indice_demanda_salud", y="region_nombre", orientation="h",
             color="indice_demanda_salud", color_continuous_scale="Blues",
             labels={"indice_demanda_salud": "Índice (score-z)", "region_nombre": ""})
fig.update_layout(**PLOTLY_LAYOUT, title="Índice de demanda de salud por envejecimiento", coloraxis_showscale=False)
st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DL_CONFIG)

st.divider()
st.subheader("⚠️ Contexto: sistema antiguo (IPS) vs sistema AFP")
st.warning(
    "Los datos de **pago de pensiones** (Superintendencia de Pensiones, corte julio 2026) cubren únicamente el "
    "**sistema de reparto anterior a 1981** (ex-cajas como Empart, Servicio de Seguro Social, Empleados Públicos), "
    "administrado hoy por el IPS. Es una cohorte en extinción, **no equivalente** a 'todos los adultos mayores con pensión' "
    "(no incluye AFP ni Pensión Garantizada Universal)."
)
st.dataframe(edad_kpi, hide_index=True, use_container_width=True)
