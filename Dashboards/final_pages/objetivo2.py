"""Objetivo 2: controlar el costo por cliente. KPIs 2.1, 2.2 y 2.3."""
import pandas as pd
import streamlit as st
from utils import load_csv, load_geojson, kpi_card_row, PLOTLY_DL_CONFIG
from components.kpi_card import kpi_card
from components.cost_analysis import serie_historica, proyeccion
from components.charts import cost_components_chart, beneficiaries_chart, income_comparison_chart, cost_projection_chart, cost_per_person_chart, spending_vs_population_growth, spending_pct_pib, poverty_bars, region_choropleth

st.title("Objetivo 2: controlar el costo por cliente")
st.markdown("Optimizar la estructura de costos para absorber el crecimiento de cuentas inactivas y pensionadas sin perder rentabilidad.")


ANIO_PGU = 2022  # entra en vigencia la Pensión Garantizada Universal (Ley 21.419, feb-2022)
ANIO_FIN_2_1 = 2050


@st.cache_data
def serie_2_1() -> pd.DataFrame:
    """Serie histórica 2016-2025 del KPI 2.1 con componentes, beneficiarios y comparación con el ingreso."""
    return serie_historica(load_csv("gasto_proteccion_social.csv"), load_csv("macro_pib_anual.csv"),
                           load_csv("proyeccion_envejecimiento_pais.csv"), load_csv("kpi_pc_nacional.csv"),
                           load_csv("pgu_pbs_aps_nacional_anual.csv"))


@st.cache_data
def proyeccion_2_1(_h: pd.DataFrame, crec_pib: float, resto: str, pgu_250: bool) -> pd.DataFrame:
    return proyeccion(_h, load_csv("proyeccion_envejecimiento_pais.csv"), load_csv("kpi_pc_parametros_reforma.csv"),
                      crec_pib, resto, pgu_250)


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
    h = serie_2_1()
    t1, t2, t3, t4, t5 = st.tabs(["Evolución", "Qué lo explica", "Por beneficiario", "Frente al ingreso", "Proyección 2050"])
    with t1:
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
    with t2:
        st.plotly_chart(cost_components_chart(h), use_container_width=True, config=PLOTLY_DL_CONFIG)
        u, i = h.iloc[-1], h.loc[ANIO_PGU]
        d0 = h.iloc[0]
        st.markdown(
            f"**Lectura:** entre {a0} y {a1} el Pilar Solidario y la PGU suben de ${d0.pilar_65 / 1e6:.2f} a ${u.pilar_65 / 1e6:.2f} millones por persona 65+ "
            f"(+${(u.pilar_65 - d0.pilar_65) / 1e6:.2f}), pero el resto de 'Edad avanzada' ({100 * u.resto / u.gasto:.0f}% del gasto de {a1}) baja "
            f"${(d0.resto_65 - u.resto_65) / 1e6:.2f} millones: su gasto total casi no crece mientras la población 65+ sí. El neto es el +${(u.costo_65 - d0.costo_65) / 1e6:.2f} millones de "
            f"{var_total:+.0f}%. Desde {ANIO_PGU} el resto cae de ${i.resto_65 / 1e6:.2f} a ${u.resto_65 / 1e6:.2f} millones por persona y eso empuja a la baja el costo total por persona."
        )
        st.caption("DIPRES no abre 'Edad avanzada' en la tabla usada: el resto se calcula restando PGU y PBS/APS de vejez (Subsecretaría de Previsión Social). "
                   "La PGU de 2022 es un residual del total del Pilar y parte en febrero, por eso es parcial ese año.")
    with t3:
        st.plotly_chart(beneficiaries_chart(h), use_container_width=True, config=PLOTLY_DL_CONFIG)
        u, p0 = h.iloc[-1], h.iloc[0]
        st.markdown(
            f"**Lectura:** la cobertura sube de {100 * p0.cobertura:.0f} a {100 * u.cobertura:.0f} beneficios por cada 100 personas 65+ y el pago anual por "
            f"beneficio pasa de ${p0.monto_por_beneficio / 1e6:.2f} a ${u.monto_por_beneficio / 1e6:.2f} millones (≈ ${u.monto_por_beneficio / 12:,.0f} al mes). "
            f"Hasta {ANIO_PGU} subieron las dos cosas (la PGU reemplaza a la PBS/APS de vejez con un monto mayor); desde {ANIO_PGU + 1} el monto por beneficio "
            "está casi quieto y lo que sube es **cuántos reciben**."
        )
        st.caption("Solo cuenta lo que paga el Pilar Solidario y la PGU (vejez); no incluye el resto de 'Edad avanzada'. "
                   "Una persona puede tener más de un beneficio, así que la cobertura es un tope superior.")
    with t4:
        st.plotly_chart(income_comparison_chart(h), use_container_width=True, config=PLOTLY_DL_CONFIG)
        u = h.iloc[-1]
        st.markdown(
            f"**Lectura:** en {a1} cada persona 65+ cuesta {u.costo_pct_pib_pc:.0f}% del PIB per cápita. El 10% (la cotización obligatoria) del ingreso mediano "
            f"de un ocupado (${u.mediana_mensual:,.0f} al mes) son ${u.aporte_10 / 1e6:.2f} millones al año: harían falta **{u.razon_necesaria:.1f} ocupados** "
            f"con ese aporte por cada persona 65+, y hay **{u.ocupados_por_65:.1f}**. Para cubrir el gasto con los ocupados actuales haría falta "
            f"**{100 * u.carga_requerida:.0f}% del sueldo mediano**, casi el doble del 10%."
        )
        st.caption("Es una escala de comparación, no un financiamiento real: el 10% va a las cuentas individuales de pensión y estos gastos se pagan con impuestos generales. "
                   "Ingreso mediano de los ocupados: INE, Encuesta Suplementaria de Ingresos, en pesos de 2025. El análisis de punto crítico (KPI 1.2) usa el mismo cálculo solo para PGU y pensiones solidarias.")
    with t5:
        c1, c2 = st.columns([2, 1])
        crec = c1.slider("Crecimiento real anual del PIB", 0.0, 4.0, 2.0, 0.5, format="%.1f%%") / 100
        resto = c2.radio("Resto de 'Edad avanzada'", ["Total constante", "Crece con la población 65+"],
                         help="Total constante: el sistema antiguo no crece. Crece: mismo gasto por persona 65+ que hoy.")
        pgu250 = st.checkbox("Incluir la PGU de $250.000 (Ley 21.735)", value=True)
        pr = proyeccion_2_1(h, crec, "constante" if resto.startswith("Total") else "crece", pgu250)
        st.plotly_chart(cost_projection_chart(h, pr), use_container_width=True, config=PLOTLY_DL_CONFIG)
        f = pr.loc[ANIO_FIN_2_1]
        st.markdown(
            f"**Escenario {ANIO_FIN_2_1}:** el gasto en edad avanzada sería {f.pct_pib:.1f}% del PIB (hoy {h.pct_pib.iloc[-1]:.1f}%), el costo por persona 65+ "
            f"${f.costo_65 / 1e6:.2f} millones (hoy ${h.costo_65.iloc[-1] / 1e6:.2f}) y habría {f.ocupados_por_65:.1f} ocupados por persona 65+ (hoy {h.ocupados_por_65.iloc[-1]:.1f}). "
            f"Cubrirlo con los ocupados exigiría **{100 * f.carga_requerida:.0f}% del sueldo mediano** (hoy {100 * h.carga_requerida.iloc[-1]:.0f}%)."
        )
        st.caption("Escenario, no pronóstico: población INE base 2024; el costo del Pilar por persona 65+ se mantiene en términos reales "
                   "(la PGU se reajusta por IPC) salvo el alza de la PGU; ocupados proporcionales a la población 15-64; ingreso mediano crece como el PIB per cápita.")


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
        (f"(PGU + pensión solidaria) / PIB ({int(ult.anio)})", f"{ult.pilar_pct_pib:.2f}%", "Total de beneficios pagados del Pilar Solidario y PGU (nominal) / PIB a precios corrientes",
         ["PGU", "Pensión Básica Solidaria (PBS)", "Aporte Previsional Solidario (APS)", "Incluye invalidez además de vejez", "No incluye el sistema antiguo"]),
        (f"Gasto en edad avanzada / PIB ({int(ult.anio)})", f"{ult.edad_avanzada_pct_pib:.2f}%" if pd.notna(ult.edad_avanzada_pct_pib) else "n/d", "DIPRES, clasificación funcional del Gobierno Central",
         ["Gasto del Gobierno Central, código 7102 «Edad avanzada»", "Incluye PGU, PBS/APS y sistema antiguo", "Dividido por el PIB a precios corrientes"]),
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
        ("Pobreza en personas 65+ (país)", f"{nac.pct_pobreza_65:.1f}%", f"IC 95%: {nac.ic95_inf:.1f}% a {nac.ic95_sup:.1f}%",
         ["Personas 65+ bajo la línea de pobreza por ingresos", "CASEN 2022, metodología 2024 del Ministerio", "IC 95%: rango probable por ser una encuesta"]),
        ("Pobreza en menores de 65 (país)", f"{nac.pct_pobreza_menores_65:.1f}%", "Para comparar: la vejez no es hoy el grupo más pobre",
         ["Mismo indicador para menores de 65", "CASEN 2022"]),
        ("Región con más pobreza 65+", mayor.region_nombre, f"{mayor.pct_pobreza_65:.1f}%",
         ["Pobreza 65+ por región", "Regiones pequeñas tienen intervalos amplios"]),
        ("Región con menos", menor.region_nombre, f"{menor.pct_pobreza_65:.1f}%",
         ["Pobreza 65+ por región", "Regiones pequeñas tienen intervalos amplios"]),
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
