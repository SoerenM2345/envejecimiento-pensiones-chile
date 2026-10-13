"""Objetivo 1: retener y ampliar la base activa. KPIs 1.1, 1.2, 1.3."""
import pandas as pd
import streamlit as st
from utils import load_csv, load_geojson, kpi_card_row, BLUE, ORANGE, PLOTLY_DL_CONFIG
from components.kpi_card import kpi_card
from components.charts import (region_choropleth, region_bars, support_ratio_projection, commissionable_flow_bars,
                               commissionable_share_line)

st.title("Objetivo 1: retener y ampliar la base activa")
st.markdown("Aumentar y retener la base de cotizantes activos por región, para sostener el ingreso por comisión pese al envejecimiento.")

pres = load_csv("kpi_presion_previsional_region.csv")
nac_cobertura = 100 * pres["cotizantes_2024"].sum() / pres["pob_15_64"].sum()
nac_soporte = pres["cotizantes"].sum() / pres["pob_65_mas"].sum()


def render_1_1():
    kpi_card_row([
        ("Cobertura nacional", f"{nac_cobertura:.1f}%", "Cotizantes 2024 / población 15-64 (Censo 2024)"),
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
        # (cobertura con cotizantes 2025, igual que la razón actual; la columna cobertura_previsional_pct es 2024, KPI 1.1)
        cobertura_2025 = 100 * fila.cotizantes / fila.pob_15_64
        filas = pd.DataFrame({"anio": r.anio, "razon": cobertura_2025 / r.indice_dependencia_vejez_proy})
        fig = support_ratio_projection(fila.razon_soporte_previsional, filas, sel)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DL_CONFIG)


def render_1_3():
    flujo = load_csv("kpi_flujo_comisionable.csv")
    real = flujo[flujo.tipo == "real"].sort_values("anio")
    esc = flujo[flujo.tipo == "escenario"].set_index("anio")
    r25 = real.iloc[-1]
    a_meta = 2033
    e33 = esc.loc[a_meta]
    minimo = esc.kpi_1_3_pct.idxmin()
    kpi_card_row([
        (f"Flujo comisionable {int(r25.anio)} (real)", f"{r25.kpi_1_3_pct:.1f}%", "Cuentas individuales / flujo total"),
        (f"Flujo comisionable {a_meta} (escenario)", f"{e33.kpi_1_3_pct:.1f}%", "Cotización del empleador completa (8,5%)"),
        (f"Variación {int(r25.anio)}-{a_meta}", f"{e33.kpi_1_3_pct - r25.kpi_1_3_pct:+.1f} pp",
         f"Mínimo del escenario: {esc.kpi_1_3_pct.min():.1f}% en {minimo}"),
    ])
    c1, c2 = st.columns([2, 3])
    with c1:
        st.plotly_chart(commissionable_flow_bars(real), use_container_width=True, config=PLOTLY_DL_CONFIG, theme=None)
    with c2:
        st.plotly_chart(commissionable_share_line(flujo), use_container_width=True, config=PLOTLY_DL_CONFIG, theme=None)
    st.markdown(
        f"El dinero previsional crece, pero una parte menor pasa por la base comisionable de las AFP: del "
        f"**{r25.kpi_1_3_pct:.1f}%** en {int(r25.anio)} baja a **{esc.kpi_1_3_pct.min():.1f}%** en {minimo} "
        f"(entra el Seguro Social) y solo se recupera en parte, a **{e33.kpi_1_3_pct:.1f}%** en {a_meta}, "
        "cuando sube la parte del empleador que va a la cuenta individual."
    )
    st.caption("Escenario, no pronóstico: cobertura y beneficio real constantes, población INE. Tasas del empleador según la "
               "Nota Técnica de la Ley 21.735 (Tabla 1). Desde agosto 2026 el 2,5% del Seguro Social incluye el SIS, que antes "
               "el empleador pagaba aparte (1,88%) y no se contaba en el flujo.")


kpi_card("1.1", render_1_1)
kpi_card("1.2", render_1_2)
kpi_card("1.3", render_1_3)
