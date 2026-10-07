"""Objetivo 1: retener y ampliar la base activa. KPIs 1.1, 1.2, 1.3."""
import pandas as pd
import streamlit as st
from utils import load_csv, load_geojson, kpi_card_row, BLUE, ORANGE, PLOTLY_DL_CONFIG
from components.kpi_card import kpi_card
from components.charts import region_choropleth, region_bars, support_ratio_projection

st.title("Objetivo 1: retener y ampliar la base activa")
st.markdown("Aumentar y retener la base de cotizantes activos por región, para sostener el ingreso por comisión pese al envejecimiento.")

pres = load_csv("kpi_presion_previsional_region.csv")
nac_cobertura = 100 * pres["cotizantes"].sum() / pres["pob_15_64"].sum()
nac_soporte = pres["cotizantes"].sum() / pres["pob_65_mas"].sum()


def render_1_1():
    kpi_card_row([
        ("Cobertura nacional", f"{nac_cobertura:.1f}%", "Cotizantes 2025 / población 15-64"),
        ("Región con mayor cobertura", pres.sort_values("cobertura_previsional_pct").iloc[-1]["region_nombre"],
         f"{pres['cobertura_previsional_pct'].max():.1f}%"),
        ("Región con menor cobertura", pres.sort_values("cobertura_previsional_pct").iloc[0]["region_nombre"],
         f"{pres['cobertura_previsional_pct'].min():.1f}%"),
    ])
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(region_choropleth(pres, load_geojson("regiones_chile.geojson"), "cobertura_previsional_pct",
                                          "Cobertura previsional (%)"), use_container_width=True, config=PLOTLY_DL_CONFIG)
    with c2:
        st.plotly_chart(region_bars(pres, "cobertura_previsional_pct", "Cobertura previsional (% de 15-64 que cotiza)",
                                    nac_cobertura, ".1f", ORANGE), use_container_width=True, config=PLOTLY_DL_CONFIG)


def render_1_2():
    kpi_card_row([
        ("Cotizantes por adulto mayor (país)", f"{nac_soporte:.2f}", "Cotizantes 2025 / población 65+ (Censo 2024)"),
        ("Región más presionada", pres.sort_values("razon_soporte_previsional").iloc[0]["region_nombre"],
         f"{pres['razon_soporte_previsional'].min():.2f}"),
        ("Región menos presionada", pres.sort_values("razon_soporte_previsional").iloc[-1]["region_nombre"],
         f"{pres['razon_soporte_previsional'].max():.2f}"),
    ])
    st.plotly_chart(region_bars(pres, "razon_soporte_previsional", "Razón de soporte: cotizantes por adulto mayor",
                                nac_soporte, ".2f", BLUE), use_container_width=True, config=PLOTLY_DL_CONFIG)

    st.markdown("**Escenario 2035 / 2050 (cobertura previsional 2025 constante)**")
    proy_pais = load_csv("proyeccion_envejecimiento_pais.csv").set_index("anio")
    proy_reg = load_csv("kpi_proyeccion_regional.csv")
    opciones = ["País"] + sorted(pres["region_nombre"])
    sel = st.selectbox("Territorio", opciones)
    if sel == "País":
        base = proy_pais.loc[2024, "pob_15_64"] / proy_pais.loc[2024, "pob_65_mas"]
        filas = pd.DataFrame([{"anio": a, "razon": nac_soporte * (proy_pais.loc[a, "pob_15_64"] / proy_pais.loc[a, "pob_65_mas"]) / base}
                              for a in (2030, 2035, 2040, 2050, 2060, 2070)])
        fig = support_ratio_projection(nac_soporte, filas, "Chile")
    else:
        fila = pres[pres.region_nombre == sel].iloc[0]
        r = proy_reg[proy_reg.region_nombre == sel]
        # razón = cobertura × pob15-64 / pob65+ = cobertura / índice de dependencia de vejez
        filas = pd.DataFrame({"anio": r.anio, "razon": fila.cobertura_previsional_pct / r.indice_dependencia_vejez_proy})
        fig = support_ratio_projection(fila.razon_soporte_previsional, filas, sel)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DL_CONFIG)


kpi_card("1.1", render_1_1)
kpi_card("1.2", render_1_2)
kpi_card("1.3")
