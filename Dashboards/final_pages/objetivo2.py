"""Objetivo 2: controlar el costo por cliente. KPIs 2.1, 2.2 y 2.3."""
import pandas as pd
import streamlit as st
from utils import load_csv, load_geojson, kpi_card_row, PLOTLY_DL_CONFIG
from components.kpi_card import kpi_card
from components.charts import cost_vs_economy_index, spending_pct_pib, poverty_bars, region_choropleth

st.title("Objetivo 2: controlar el costo por cliente")
st.markdown("Optimizar la estructura de costos para absorber el crecimiento de cuentas inactivas y pensionadas sin perder rentabilidad.")


@st.cache_data
def serie_costo_vs_economia() -> pd.DataFrame:
    """Costo público real por persona 65+ (DIPRES 'Edad avanzada', pesos de 2025) y PIB per cápita real (Banco Central), base 2016 = 100."""
    gasto = load_csv("gasto_proteccion_social.csv")
    gasto = gasto[gasto.categoria == "Edad avanzada"].set_index("anio")
    pib = load_csv("macro_pib_anual.csv").set_index("anio")
    pob = load_csv("proyeccion_envejecimiento_pais.csv").set_index("anio")
    anios = [a for a in gasto.index if a in pib.index and a in pob.index]
    d = pd.DataFrame(index=anios)
    d["costo_65"] = gasto.loc[anios, "gasto_mm_2025"] * 1e6 / pob.loc[anios, "pob_65_mas"]
    d["pib_pc_real"] = pib.loc[anios, "pib_real_mm_2018"] * 1e6 / pob.loc[anios, "pob_total"]
    d["idx_costo_65"] = 100 * d.costo_65 / d.costo_65.iloc[0]
    d["idx_pib_pc"] = 100 * d.pib_pc_real / d.pib_pc_real.iloc[0]
    d.index.name = "anio"
    return d.reset_index()


def render_2_1():
    d = serie_costo_vs_economia()
    a0, a1 = int(d.anio.iloc[0]), int(d.anio.iloc[-1])
    ult, pri = d.iloc[-1], d.iloc[0]
    kpi_card_row([
        (f"Costo público por persona 65+ ({a1})", f"${ult.costo_65 / 1e6:.2f} millones", "Gasto del Gobierno Central en 'Edad avanzada' (pesos de 2025) / población 65+ (INE)"),
        (f"Variación real {a0}-{a1}", f"{ult.idx_costo_65 - 100:+.0f}%", "Costo real por persona 65+"),
        (f"PIB per cápita real {a0}-{a1}", f"{ult.idx_pib_pc - 100:+.0f}%", "Volumen encadenado (Banco Central) / población total (INE)"),
    ])
    st.plotly_chart(cost_vs_economy_index(d), use_container_width=True, config=PLOTLY_DL_CONFIG)
    mas_rapido = ult.idx_costo_65 > ult.idx_pib_pc
    st.markdown(
        f"**Lectura:** entre {a0} y {a1} el costo real por adulto mayor "
        f"{'creció más rápido' if mas_rapido else 'creció más lento'} que la economía por habitante "
        f"({ult.idx_costo_65 - 100:+.0f}% vs. {ult.idx_pib_pc - 100:+.0f}%)."
    )


def render_2_2():
    pil = load_csv("pgu_pbs_aps_nacional_anual.csv")
    pil = pil[(pil.tipo_beneficio == "Total")].set_index("anio")
    pib = load_csv("macro_pib_anual.csv").set_index("anio")
    gasto = load_csv("gasto_proteccion_social.csv")
    ea = gasto[gasto.categoria == "Edad avanzada"].set_index("anio")["pct_pib"]
    anios = [a for a in pil.index if a in pib.index]
    d = pd.DataFrame({"anio": anios})
    d["pilar_pct_pib"] = [100 * pil.loc[a, "monto_nominal_mm"] / pib.loc[a, "pib_corriente_mm"] for a in anios]
    d["edad_avanzada_pct_pib"] = [ea.get(a) for a in anios]
    ult = d.iloc[-1]
    kpi_card_row([
        (f"(PGU + pensión solidaria) / PIB ({int(ult.anio)})", f"{ult.pilar_pct_pib:.2f}%", "Total de beneficios pagados del Pilar Solidario y PGU (nominal) / PIB a precios corrientes"),
        (f"Gasto en edad avanzada / PIB ({int(ult.anio)})", f"{ult.edad_avanzada_pct_pib:.2f}%" if pd.notna(ult.edad_avanzada_pct_pib) else "n/d", "DIPRES, clasificación funcional del Gobierno Central"),
    ])
    st.plotly_chart(spending_pct_pib(d), use_container_width=True, config=PLOTLY_DL_CONFIG)
    st.markdown("**Ratio 2, (activos + reservas) / VP del déficit: pendiente.** Falta el valor presente del déficit proyectado; "
                "ver `docs/DATOS_ABIERTOS.md` para la alternativa propuesta.")


def render_2_3():
    p = load_csv("pobreza_65_region.csv")
    nac = p[p.region_id == 0].iloc[0]
    reg = p[p.region_id != 0].copy()
    mayor, menor = reg.sort_values("pct_pobreza_65").iloc[-1], reg.sort_values("pct_pobreza_65").iloc[0]
    kpi_card_row([
        ("Pobreza en personas 65+ (país)", f"{nac.pct_pobreza_65:.1f}%", f"IC 95%: {nac.ic95_inf:.1f}% a {nac.ic95_sup:.1f}%"),
        ("Pobreza en menores de 65 (país)", f"{nac.pct_pobreza_menores_65:.1f}%", "Para comparar: la vejez no es hoy el grupo más pobre"),
        ("Región con más pobreza 65+", mayor.region_nombre, f"{mayor.pct_pobreza_65:.1f}%"),
        ("Región con menos", menor.region_nombre, f"{menor.pct_pobreza_65:.1f}%"),
    ])
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(region_choropleth(reg, load_geojson("regiones_chile.geojson"), "pct_pobreza_65",
                                          "% de personas 65+ en pobreza", "Oranges"), use_container_width=True, config=PLOTLY_DL_CONFIG)
    with c2:
        st.plotly_chart(poverty_bars(reg, nac.pct_pobreza_65), use_container_width=True, config=PLOTLY_DL_CONFIG)
    st.caption("Las regiones pequeñas (Aysén, Magallanes, Tarapacá) tienen intervalos amplios: lea los rangos, no solo el orden.")


kpi_card("2.1", render_2_1)
kpi_card("2.2", render_2_2)
kpi_card("2.3", render_2_3)
