"""Objetivo 2: controlar el costo por cliente. KPIs 2.1, 2.2 y 2.3."""
import pandas as pd
import streamlit as st
from utils import load_csv, load_geojson, kpi_card_row, PLOTLY_DL_CONFIG
from components.kpi_card import kpi_card
from components.charts import cost_per_person_chart, spending_vs_population_growth, spending_pct_pib, poverty_bars, region_choropleth

st.title("Objetivo 2: controlar el costo por cliente")
st.markdown("Optimizar la estructura de costos para absorber el crecimiento de cuentas inactivas y pensionadas sin perder rentabilidad.")


ANIO_PGU = 2022  # entra en vigencia la Pensión Garantizada Universal (Ley 21.419, feb-2022)


@st.cache_data
def serie_costo_vs_economia() -> pd.DataFrame:
    """Costo público real por persona 65+ (DIPRES 'Edad avanzada', pesos de 2025) y PIB per cápita real (Banco Central)."""
    gasto = load_csv("gasto_proteccion_social.csv")
    gasto = gasto[gasto.categoria == "Edad avanzada"].set_index("anio")
    pib = load_csv("macro_pib_anual.csv").set_index("anio")
    pob = load_csv("proyeccion_envejecimiento_pais.csv").set_index("anio")
    anios = [a for a in gasto.index if a in pib.index and a in pob.index]
    d = pd.DataFrame(index=anios)
    d["gasto"] = gasto.loc[anios, "gasto_mm_2025"] * 1e6
    d["pob_65"] = pob.loc[anios, "pob_65_mas"]
    d["costo_65"] = d.gasto / d.pob_65
    d["pib_pc_real"] = pib.loc[anios, "pib_real_mm_2018"] * 1e6 / pob.loc[anios, "pob_total"]
    d.index.name = "anio"
    return d.reset_index()


def render_2_1():
    d = serie_costo_vs_economia()
    pri, ult = d.iloc[0], d.iloc[-1]
    a0, a1 = int(pri.anio), int(ult.anio)
    hito = d[d.anio == ANIO_PGU].iloc[0]
    n = a1 - ANIO_PGU
    cagr = lambda col: 100 * ((ult[col] / hito[col]) ** (1 / n) - 1)
    var_total = 100 * (ult.costo_65 / pri.costo_65 - 1)
    var_pib = 100 * (ult.pib_pc_real / pri.pib_pc_real - 1)
    desde_hito = 100 * (ult.costo_65 / hito.costo_65 - 1)
    kpi_card_row([
        (f"Costo público por persona 65+ ({a1})", f"${ult.costo_65 / 1e6:.2f} millones",
         "Gasto del Gobierno Central en 'Edad avanzada' (pesos de 2025) dividido por la población de 65 años o más (INE)",
         ["Pensiones del sistema antiguo (IPS y ex cajas)", "Pensión Garantizada Universal (PGU)",
          "Pensiones básicas y aportes solidarios (PBS/APS)", "Clasificación funcional de DIPRES, código 7102",
          "En pesos de 2025; se divide por todas las personas 65+, reciban o no pensión del Estado",
          "No incluye las pensiones pagadas por las AFP"]),
        (f"Variación real {a0}-{a1}", f"{var_total:+.0f}%",
         f"Costo real por persona 65+ en {a1} frente a {a0}. PIB per cápita real en el mismo período: {var_pib:+.0f}%",
         [f"{a0}: ${pri.costo_65 / 1e6:.2f} millones; {a1}: ${ult.costo_65 / 1e6:.2f} millones",
          f"El PIB per cápita real subió {var_pib:+.0f}% (Banco Central, volumen encadenado / población INE)",
          f"Casi todo el aumento ocurre en {ANIO_PGU}, con la PGU"]),
        (f"Desde {ANIO_PGU} (año de la PGU)", f"{desde_hito:+.0f}%",
         f"Variación real del costo por persona 65+ entre {ANIO_PGU} y {a1}",
         [f"Gasto real: {cagr('gasto'):+.1f}% al año", f"Población 65+: {cagr('pob_65'):+.1f}% al año",
          "Cada año hay más personas 65+ entre las que repartir el gasto"]),
    ])
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(cost_per_person_chart(d, ANIO_PGU, "PGU"), use_container_width=True, config=PLOTLY_DL_CONFIG)
    with c2:
        st.plotly_chart(spending_vs_population_growth(d), use_container_width=True, config=PLOTLY_DL_CONFIG)
    st.markdown(
        f"**Lectura:** entre {a0} y {a1} el costo real por adulto mayor subió {var_total:.0f}%, algo más que el PIB per cápita "
        f"({var_pib:.0f}%), pero no es una tendencia: es un **salto único en {ANIO_PGU}** (la PGU) sobre una base plana. "
        f"Desde entonces el costo por persona **baja** ({desde_hito:+.0f}%): la población 65+ crece {cagr('pob_65'):.1f}% al año "
        f"y el gasto real solo {cagr('gasto'):.1f}%. El Estado gasta cada vez más en total, pero menos por persona."
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
