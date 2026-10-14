"""Objetivo 2: controlar el costo por cliente. KPIs 2.1, 2.2 y 2.3."""
import pandas as pd
import streamlit as st
from utils import load_csv, load_geojson, kpi_card_row, PLOTLY_DL_CONFIG
from components.kpi_card import kpi_card
from components.cost_analysis import serie_historica, proyeccion
from components.financiamiento import peso_historico, proyeccion_carga, trayectoria_reserva, fuentes_pilar, dependencia_regional, proyeccion_sin_pension
from components.charts import cost_components_chart, beneficiaries_chart, cost_projection_chart, cost_per_person_chart, spending_vs_population_growth, spending_pct_pib, poverty_bars, region_choropleth
from components.charts import fiscal_weight_chart, financing_sources_chart, reserve_chart, fapp_flow_chart, fapp_schedule_chart, dependence_regions_chart

st.title("Objetivo 2: controlar el costo por cliente")
st.markdown("Optimizar la estructura de costos para absorber el crecimiento de cuentas inactivas y pensionadas sin perder rentabilidad.")


from components.charts import estilo_kpi as _estilo_2_1, cost_pct_pibpc_chart, burden_chart

ANIO_PGU = 2022  # entra en vigencia la Pensión Garantizada Universal (Ley 21.419, feb-2022)
ANIO_FIN_2_1 = 2050


def _g21(fig, alto=430):
    st.plotly_chart(_estilo_2_1(fig, alto), use_container_width=True, config=PLOTLY_DL_CONFIG, theme=None)


@st.cache_data
def serie_2_1(base: str = "mediana") -> pd.DataFrame:
    """Serie histórica 2016-2025 del KPI 2.1 con componentes, beneficiarios y comparación con el ingreso (base: mediana | promedio)."""
    return serie_historica(load_csv("gasto_proteccion_social.csv"), load_csv("macro_pib_anual.csv"),
                           load_csv("proyeccion_envejecimiento_pais.csv"), load_csv("kpi_pc_nacional.csv"),
                           load_csv("pgu_pbs_aps_nacional_anual.csv"), base)


@st.cache_data
def proyeccion_2_1(_h: pd.DataFrame, crec_pib: float, resto: str, pgu_250: bool, base: str = "mediana") -> pd.DataFrame:
    return proyeccion(_h, load_csv("proyeccion_envejecimiento_pais.csv"), load_csv("kpi_pc_parametros_reforma.csv"),
                      crec_pib, resto, pgu_250)


@st.cache_data
def ips_sistema_antiguo() -> tuple:
    """Pago anual (pesos) y número de pensionados de las ex cajas del IPS (mes de julio de 2026 x 12)."""
    c = load_csv("pensiones_pagadas_por_ex_caja.csv")
    c = c[c.ex_caja != "Total"]
    return float(c.monto_miles_pesos.sum() * 1e3 * 12), int(c.numero_pensionados.sum())


def render_2_1():
    h = serie_2_1()
    pri, ult, hito = h.iloc[0], h.iloc[-1], h.loc[ANIO_PGU]
    a0, a1 = int(h.index[0]), int(h.index[-1])
    cagr = lambda col: 100 * ((ult[col] / hito[col]) ** (1 / (a1 - ANIO_PGU)) - 1)
    var_total = 100 * (ult.costo_65 / pri.costo_65 - 1)
    desde_hito = 100 * (ult.costo_65 / hito.costo_65 - 1)
    pico = int(h.costo_pct_pib_pc.idxmax())
    ipc = 100 * (h.defl_ipc.iloc[0] / h.defl_ipc.iloc[-1] - 1)
    defl_pib = 100 * (h.defl_pib.iloc[-1] / h.defl_pib.iloc[0] - 1)
    kpi_card_row([
        (f"Costo público por persona 65+ ({a1})", f"${ult.costo_65 / 1e6:.2f} millones",
         "Gasto del Gobierno Central en 'Edad avanzada' (pesos de 2025) dividido por la población de 65 años o más (INE)",
         ["Pensiones del sistema antiguo (IPS y ex cajas)", "Pensión Garantizada Universal (PGU)",
          "Pensiones básicas y aportes solidarios (PBS/APS)", "Clasificación funcional de DIPRES, código 7102",
          "En pesos de 2025; se divide por todas las personas 65+, reciban o no pensión del Estado",
          "No incluye las pensiones pagadas por las AFP"]),
        (f"Costo por persona 65+ / PIB per cápita ({a1})", f"{ult.costo_pct_pib_pc:.1f}%",
         f"Era {pri.costo_pct_pib_pc:.1f}% en {a0}; máximo {h.costo_pct_pib_pc.max():.1f}% en {pico}",
         ["Gasto en 'Edad avanzada' ÷ población 65+", "PIB ÷ población total, ambos a precios corrientes",
          "Esfuerzo fiscal por adulto mayor frente al ingreso medio del país", "Si baja, el gasto por persona crece más lento que la economía"]),
        (f"Desde {ANIO_PGU} (año de la PGU)", f"{desde_hito:+.0f}%",
         f"Variación real del costo por persona 65+ entre {ANIO_PGU} y {a1}",
         [f"Gasto real: {cagr('gasto'):+.1f}% al año", f"Población 65+: {cagr('pob_65'):+.1f}% al año",
          "Cada año hay más personas 65+ entre las que repartir el gasto"]),
    ])
    t1, t2, t3, t4, t5, t6 = st.tabs(["Evolución", "Qué lo explica", "Por beneficiario", "Frente al ingreso", "Proyección 2050", "Qué hacer"])
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            _g21(cost_per_person_chart(h.reset_index(), ANIO_PGU, "PGU"))
        with c2:
            _g21(cost_pct_pibpc_chart(h))
        st.markdown(f"**Lectura:** en pesos reales el costo por adulto mayor sube {var_total:.0f}% ({a0}-{a1}) por un salto único en {ANIO_PGU} (PGU) y desde entonces baja {-desde_hito:.0f}%; "
                    f"frente al PIB per cápita pasa de {pri.costo_pct_pib_pc:.1f}% a {ult.costo_pct_pib_pc:.1f}% (máximo {h.costo_pct_pib_pc.max():.1f}% en {pico}).")
        st.caption("\\* Derecha: precios corrientes a ambos lados, porque el costo real (IPC) y el PIB real (deflactor del PIB) no son comparables; detalle en «Método y fuentes».")
    with t2:
        c1, c2 = st.columns(2)
        with c1:
            _g21(cost_components_chart(h))
        with c2:
            _g21(spending_vs_population_growth(h.reset_index()))
        st.markdown(f"**Lectura:** el Pilar y la PGU suben de ${pri.pilar_65 / 1e6:.2f} a ${ult.pilar_65 / 1e6:.2f} millones por persona 65+, pero el resto de 'Edad avanzada' "
                    f"({100 * ult.resto / ult.gasto:.0f}% del gasto) baja ${(pri.resto_65 - ult.resto_65) / 1e6:.2f} millones: su gasto total casi no crece y la población 65+ sí.")
        st.caption("\\* Resto = Edad avanzada − PGU − PBS/APS de vejez; DIPRES no lo abre, así que no se sabe si su caída es cierre del sistema antiguo o recorte.")
    with t3:
        _g21(beneficiaries_chart(h))
        p0 = h.iloc[0]
        st.markdown(f"**Lectura:** la cobertura sube de {100 * p0.cobertura:.0f} a {100 * ult.cobertura:.0f} por cada 100 personas 65+ y el pago por beneficio de ${p0.monto_por_beneficio / 1e6:.2f} "
                    f"a ${ult.monto_por_beneficio / 1e6:.2f} millones (≈ ${ult.monto_por_beneficio / 12:,.0f} al mes), casi quieto desde {ANIO_PGU + 1}.")
        st.caption("\\* Solo Pilar Solidario y PGU de vejez; una persona puede tener más de un beneficio, así que la cobertura es un tope.")
    with t4:
        base = st.radio("Ingreso típico de los ocupados", ["mediana", "promedio"], horizontal=True,
                        help="Mediana: la mitad de los ocupados gana menos. Promedio: total de ingresos ÷ ocupados (más alto por los ingresos muy altos).")
        hb = serie_2_1(base)
        _g21(burden_chart(hb, base))
        u, p0 = hb.iloc[-1], hb.iloc[0]
        st.markdown(f"**Lectura:** repartido por igual, el gasto sería ${u.pago_plano:,.0f} al mes por ocupado: **{100 * u.carga_requerida:.0f}% del ingreso ({base})** frente al 10% de la cotización "
                    f"({100 * p0.carga_requerida:.0f}% en {a0}); harían falta {u.razon_necesaria:.1f} ocupados por persona 65+ y hay {u.ocupados_por_65:.1f}.")
        st.caption("\\* Escala de comparación, no un financiamiento real: el 10% va a cuentas individuales y estos gastos se pagan con impuestos generales.")
    with t5:
        c1, c2 = st.columns([2, 1])
        crec = c1.slider("Crecimiento real anual del PIB", 0.0, 4.0, 2.0, 0.5, format="%.1f%%") / 100
        resto = c2.radio("Resto de 'Edad avanzada'", ["Total constante", "Crece con la población 65+"],
                         help="Total constante: el sistema antiguo no crece. Crece: mismo gasto por persona 65+ que hoy.")
        pgu250 = st.checkbox("Incluir la PGU de $250.000 (Ley 21.735)", value=True)
        pr = proyeccion_2_1(hb, crec, "constante" if resto.startswith("Total") else "crece", pgu250, base)
        _g21(cost_projection_chart(hb, pr, base))
        f = pr.loc[ANIO_FIN_2_1]
        st.markdown(f"**Escenario {ANIO_FIN_2_1}:** gasto de {f.pct_pib:.1f}% del PIB (hoy {ult.pct_pib:.1f}%), {f.ocupados_por_65:.1f} ocupados por persona 65+ (hoy {ult.ocupados_por_65:.1f}) "
                    f"y un pago por ocupado de **{100 * f.carga_requerida:.0f}% del ingreso ({base})** (hoy {100 * hb.iloc[-1].carga_requerida:.0f}%).")
        st.caption("\\* Escenario, no pronóstico: el costo del Pilar por persona 65+ se mantiene en términos reales salvo el alza de la PGU.")
    with t6:
        _recomendaciones_2_1(h)
    ips, n_ips = ips_sistema_antiguo()
    with st.expander("Método y fuentes"):
        st.markdown(
            f"- **Fuentes:** gasto en 'Edad avanzada' (DIPRES, COFOG 7102, pesos de 2025); PGU, PBS y APS (Subsecretaría de Previsión Social); población INE base 2024; PIB (Banco Central); "
            f"ocupados (ENE) e ingreso de los ocupados (ESI) del INE.\n"
            f"- **Períodos:** gasto y PIB son flujos del año; la población 65+ y total, de mitad de año; ocupados e ingreso, de octubre-diciembre (desfase de unos 4 meses; "
            f"el efecto en los ocupados por persona 65+ es menor a 2%). El ingreso se pasa a pesos de 2025 con el IPC anual.\n"
            f"- **Precios:** el costo real usa el IPC (las pensiones se reajustan por IPC), que subió {ipc:.0f}% en {a0}-{a1}; el PIB real usa el deflactor del PIB, que subió {defl_pib:.0f}%. "
            f"Por eso el indicador principal usa precios corrientes en ambos lados.\n"
            f"- **Resto:** lo que queda de 'Edad avanzada' al restar PGU y PBS/APS; incluye el sistema antiguo y puede incluir pensiones a menores de 65. "
            f"El IPS paga ≈ ${ips / 1e12:.1f} billones al año a {f'{n_ips:,}'.replace(',', '.')} pensionados (julio 2026): solo una parte.\n"
            f"- **PGU 2022:** residual del total del Pilar (Total − PBS − APS); parte en febrero. La cobertura cuenta beneficios, no personas.\n"
            f"- **Proyección:** población INE; ocupados proporcionales a la población 15-64; el ingreso crece como el PIB per cápita; con la base «promedio» el pago por ocupado pesa menos porque el ingreso promedio es mayor que la mediana."
        )


def _recomendaciones_2_1(h):
    """Tres lectores del KPI 2.1 con los supuestos de partida (PIB +2%, PGU de $250.000, ingreso mediano)."""
    pc = proyeccion_2_1(h, 0.02, "constante", True, "mediana")
    pg = proyeccion_2_1(h, 0.02, "crece", True, "mediana")
    u, a1 = h.iloc[-1], int(h.index[-1])
    nac = load_csv("kpi_pc_nacional.csv").set_index("anio").loc[a1]
    par = load_csv("kpi_pc_parametros_reforma.csv").set_index("anio")
    pib50 = pc.loc[ANIO_FIN_2_1, "gasto"] / (pc.loc[ANIO_FIN_2_1, "pct_pib"] / 100)
    dif = pg.loc[ANIO_FIN_2_1, "gasto"] - pc.loc[ANIO_FIN_2_1, "gasto"]
    anio28 = int(par.index[par.factor_costo_pgu >= par.factor_costo_pgu.max() - 1e-9][0])
    sube_pgu = u.pilar_65 * (par.loc[anio28, "factor_costo_pgu"] - 1) * pc.loc[anio28, "pob_65"]
    pgu_hoy, pgu_nueva = par.loc[a1, "pgu_monto_feb2025"], par.loc[a1, "pgu_monto_nuevo"]
    sin_cot = u.ocupados - nac.cotizantes_dic
    suma_cot = sin_cot * u.aporte_10
    bajo2 = pc.index[pc.ocupados_por_65 < 2]
    cobertura_10 = u.ocupados_por_65 / u.razon_necesaria
    st.markdown(
        "Cifras con los supuestos de partida (PIB +2%, PGU de $250.000, ingreso mediano de los ocupados).\n\n"
        f"**1. Hacienda / DIPRES (planificación fiscal).** El gasto en 'Edad avanzada' es {u.pct_pib:.1f}% del PIB en {a1}; en {ANIO_FIN_2_1} sería {pc.loc[ANIO_FIN_2_1].pct_pib:.1f}% si el resto "
        f"(sistema antiguo y otros, {100 * u.resto / u.gasto:.0f}% del gasto) se mantiene constante y {pg.loc[ANIO_FIN_2_1].pct_pib:.1f}% si crece con la población 65+: una diferencia de ${dif / 1e12:.1f} billones al año "
        f"({100 * dif / pib50:.1f} puntos del PIB). *Acción:* pedir a DIPRES que publique y proyecte 'Edad avanzada' por institución (IPS, Capredena, Dipreca, Pilar y PGU) antes de que la PGU llegue a $250.000 en {anio28}, "
        "porque el resto, que hoy no se puede abrir, decide si el gasto de 2050 sube o baja.\n\n"
        f"**2. Subsecretaría de Previsión Social (suficiencia de la PGU).** El pago por beneficio está casi quieto desde {ANIO_PGU + 1} (≈ ${u.monto_por_beneficio / 12:,.0f} al mes) y la cobertura llegó a {100 * u.cobertura:.0f} por cada 100 personas 65+. "
        f"La PGU de ${pgu_hoy:,.0f} equivale al {100 * pgu_hoy / u.mediana_mensual:.0f}% del ingreso mediano de los ocupados (${u.mediana_mensual:,.0f}); con $250.000 sería {100 * pgu_nueva / u.mediana_mensual:.0f}%, "
        f"y el Pilar cuesta ${sube_pgu / 1e12:.1f} billones más al año en {anio28}. *Acción:* fijar la meta de la PGU como porcentaje del ingreso mediano (hoy {100 * pgu_hoy / u.mediana_mensual:.0f}%) y revisarla cada año con la ESI, "
        "no solo con el IPC; mirar primero las regiones con más pobreza 65+ (KPI 2.3).\n\n"
        f"**3. Superintendencia de Pensiones y AFP (base cotizante).** Si todos los ocupados aportaran el 10% del ingreso mediano financiarían solo el {100 * cobertura_10:.0f}% del costo por persona 65+ ({u.ocupados_por_65:.1f} ocupados por persona 65+ frente a {u.razon_necesaria:.1f} necesarios), "
        f"y en {int(bajo2[0]) if len(bajo2) else 'más allá de ' + str(ANIO_FIN_2_1)} habría menos de 2. Hoy {sin_cot / 1e6:.1f} millones de ocupados no cotizan (cotizantes de diciembre: {nac.cotizantes_dic / 1e6:.1f} millones de {u.ocupados / 1e6:.1f} millones de ocupados); "
        f"si cotizaran el 10% de la mediana sumarían ${suma_cot / 1e12:.1f} billones al año a las cuentas individuales (equivale al {100 * suma_cot / u.gasto:.0f}% del gasto de {a1}). "
        "*Acción:* medir la afiliación de independientes y trabajadores informales con este mismo indicador (ocupados que cotizan / ocupados) y fijar una meta anual; es una palanca que no depende de impuestos. "
        "Distinto de 1 y 2: aquí no se mueve plata del Estado, se amplía la base que ahorra para su propia pensión."
    )


@st.cache_data
def proyeccion_2_2(_h: pd.DataFrame, crec_pib: float, pgu_250: bool, con_fapp: bool) -> pd.DataFrame:
    return proyeccion_carga(_h, load_csv("pgu_pbs_aps_nacional_anual.csv"), load_csv("macro_pib_anual.csv"),
                            load_csv("proyeccion_envejecimiento_pais.csv"), load_csv("kpi_pc_parametros_reforma.csv"),
                            load_csv("fapp_aporte_fiscal.csv"), crec_pib, pgu_250, con_fapp)


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
    st.markdown("**Ratio 2 con el valor presente del déficit oficial: sigue pendiente.** Falta ese valor presente (ver `docs/DATOS_ABIERTOS.md`). "
                "Mientras tanto, abajo se calcula una alternativa con datos oficiales: cuánto del gasto que sube cubren las reservas (FRP y FAPP).")
    st.divider()
    st.markdown("#### Profundización: ¿quién financia el Pilar y cuánto aguantan las reservas?")
    _profundizacion_2_2()


def _profundizacion_2_2():
    h = serie_2_1()
    frp, fb, ap = load_csv("frp_reserva_anual.csv"), load_csv("fapp_balance.csv"), load_csv("fapp_aporte_fiscal.csv")
    nac = load_csv("kpi_pc_nacional.csv")
    c1, c2, c3 = st.columns([2, 2, 2])
    crec = c1.slider("Crecimiento real anual del PIB", 0.0, 4.0, 2.0, 0.5, format="%.1f%%", key="k22_pib",
                     help="Mismo supuesto de partida que el KPI 2.1. Un PIB que crece más reduce el peso del Pilar en el PIB.") / 100
    pgu250 = c2.checkbox("Incluir la PGU de $250.000 (Ley 21.735)", value=True, key="k22_pgu")
    con_fapp = c3.checkbox("Sumar el aporte del Estado al FAPP (Ley 21.735)", value=True, key="k22_fapp",
                           help="Desde 2028 la ley obliga al Estado a aportar al Fondo Autónomo de Protección Previsional (Seguro Social): "
                                "2,2 millones de UTM al año, hasta 15 millones desde 2037.")
    p = proyeccion_2_2(h, crec, pgu250, con_fapp)
    t1, t2, t3, t4, t5 = st.tabs(["Peso fiscal 2050", "Quién lo financia", "Reservas", "FAPP hoy", "Dónde"])

    with t1:
        hist = peso_historico(load_csv("pgu_pbs_aps_nacional_anual.csv"), load_csv("macro_pib_anual.csv"), load_csv("gasto_proteccion_social.csv"))
        st.plotly_chart(fiscal_weight_chart(hist, p, con_fapp), use_container_width=True, config=PLOTLY_DL_CONFIG)
        b, a37, f = p.loc[2025], p.loc[2037], p.loc[2050]
        pico = p.pilar_pct_pib.idxmax()
        kpi_card_row([
            ("Pilar + PGU, 2025", f"{b.pilar_pct_pib:.2f}% del PIB", "Ratio 1 del KPI: el mismo valor del gráfico de arriba"),
            (f"Pilar + PGU, {pico}", f"{p.loc[pico].pilar_pct_pib:.2f}% del PIB", f"Año de mayor peso del Pilar en el escenario; +{p.loc[pico].pilar_pct_pib - b.pilar_pct_pib:.2f} puntos del PIB sobre 2025"),
            ("Con aporte al FAPP, 2037", f"{a37.carga_pct_pib:.2f}% del PIB", "Pilar + aporte del Estado al FAPP; 15 millones de UTM al año desde 2037"),
            ("Carga 2050", f"{f.carga_pct_pib:.2f}% del PIB", f"Equivale a ${f.carga / 1e12:.1f} billones al año, en pesos de 2025 (2025: ${b.carga / 1e12:.1f} billones)"),
        ])
        st.markdown(
            f"**Lectura:** el Pilar Solidario y la PGU pesan {b.pilar_pct_pib:.2f}% del PIB en 2025 y llegan a {p.loc[pico].pilar_pct_pib:.2f}% en {pico}: "
            f"entre 2025 y 2030 sube {p.loc[2030].pilar_pct_pib - b.pilar_pct_pib:+.2f} puntos del PIB (el alza de la PGU a $250.000 y el envejecimiento) y entre 2030 y 2050 {f.pilar_pct_pib - p.loc[2030].pilar_pct_pib:+.2f} puntos. "
            + (f"El aporte del Estado al FAPP suma {100 * (a37.carga - a37.pilar) / a37.pib_real25:.2f}% del PIB desde 2037 "
               f"(${(a37.carga - a37.pilar) / 1e12:.2f} billones al año), de modo que la carga total de la reforma llega a {a37.carga_pct_pib:.2f}% del PIB en 2037. "
               if con_fapp else "")
            + f"La carga en 2050 es {f.carga_pct_pib:.2f}% del PIB."
        )
        st.caption("Observado 2009-2025 (sólido): monto nominal pagado del Pilar (incluye invalidez) / PIB corriente, del mismo año. Escenario (punteado): "
                   "población 65+ INE base 2024; el costo por persona 65+ se mantiene en términos reales salvo el alza de la PGU; invalidez constante en términos reales; "
                   "el aporte al FAPP está en UTM (ley) y se pasa a pesos de 2025 con la UTM promedio de 2025. No incluye el sistema antiguo ni el resto de la reforma.")

    with t2:
        fu = fuentes_pilar(frp, nac)
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(financing_sources_chart(fu), use_container_width=True, config=PLOTLY_DL_CONFIG)
        with g2:
            st.plotly_chart(fapp_schedule_chart(proyeccion_2_2(h, crec, pgu250, True)), use_container_width=True, config=PLOTLY_DL_CONFIG)
        u = fu.iloc[-1]
        f1 = frp.set_index("anio").loc[2025]
        st.markdown(
            f"**Lectura:** en {int(u.anio)} el retiro del Fondo de Reserva de Pensiones (US${f1.retiros_musd:,.0f} millones, ${u.retiros_real / 1e12:.2f} billones) "
            f"financió solo el **{u.pct_frp:.1f}%** del Pilar Solidario y la PGU (${u.pilar_real / 1e12:.2f} billones; {f1.retiros_pct_pib:.2f}% del PIB): "
            f"el {100 - u.pct_frp:.1f}% restante sale del presupuesto general. Esa proporción se mueve poco: entre {fu.pct_frp.min():.1f}% y {fu.pct_frp.max():.1f}% en {int(fu.anio.min())}-{int(fu.anio.max())}. "
            f"El único financiamiento dedicado nuevo es el aporte del Estado al FAPP, que por ley parte en 2028 con ${ap.aporte_mm_2025.iloc[0] / 1e6:.2f} billones "
            f"y llega a ${ap.aporte_mm_2025.max() / 1e6:.2f} billones al año desde 2037, y va al Seguro Social, no al Pilar."
        )
        st.caption("Retiros del FRP: informe mensual de DIPRES (julio 2026), en US$, pasados a pesos con el dólar observado promedio de cada año (SII) y a pesos de 2025 con el IPC. "
                   "Los retiros de 2020-2021 (US$ 1.576 y 2.960 millones) se omiten por no ser comparables. Gasto del Pilar: nominal del año, incluye invalidez.")

    with t3:
        k1, k2, k3 = st.columns(3)
        res_in = k1.radio("Reservas incluidas", ["Solo FRP", "FRP + activos del FAPP"], key="k22_res",
                          help="El FRP está pensado para complementar las pensiones garantizadas por el Estado. Los activos del FAPP están destinados por ley al Seguro Social, "
                               "no al Pilar; se pueden sumar para ver el máximo.")
        cubre_in = k2.radio("Qué gasto cubren", ["Solo el alza sobre el peso de 2025", "Todo el gasto del Pilar"], key="k22_cubre",
                            help="Alza: lo que el Pilar (y el aporte al FAPP) gasta por encima de mantener el 2,07% del PIB de 2025. Todo: el gasto completo.")
        r_real = k3.slider("Rentabilidad real de la reserva", 0.0, 5.0, 2.5, 0.5, format="%.1f%%", key="k22_r",
                           help="2,5% real al año: es la tasa de 2,53% real que DIPRES fijó para el préstamo del FRP al FAPP (Resolución Exenta 646 de 2025). Es también la tasa de descuento del valor presente.") / 100
        reserva0 = frp.set_index("anio").loc[2025, "cartera_propia_mm"] * 1e6
        if res_in.startswith("FRP +"):
            reserva0 += fb[fb.cierre == "2025-12-31"].activos_mm.iloc[0] * 1e6
        cubre = "incremento" if cubre_in.startswith("Solo") else "total"
        dr, res = trayectoria_reserva(p, reserva0, r_real, cubre)
        st.plotly_chart(reserve_chart(dr, res, cubre), use_container_width=True, config=PLOTLY_DL_CONFIG)
        agot = res["anio_agotamiento"]
        kpi_card_row([
            ("Reserva al 31-dic-2025", f"${reserva0 / 1e12:.1f} billones", "FRP: US$10.091 millones × dólar de cierre $911,18" + (" + activos del FAPP" if res_in.startswith("FRP +") else ""),
             ["Cartera propia del FRP, sin los US$ 200 millones ya transferidos al FAPP", f"Equivale a {res['anios_gasto_2025']:.1f} años del gasto de 2025 del Pilar"]),
            ("Ratio 2: reservas / VP del gasto", f"{100 * res['ratio_cobertura']:.0f}%", f"Valor presente 2026-2050 del gasto que cubre: ${res['vp_gasto'] / 1e12:.0f} billones (tasa {100 * r_real:.1f}% real)",
             ["100% o más: la reserva alcanza hasta 2050", "Ratio alternativo al VP del déficit oficial, que no está publicado"]),
            ("Año en que se agota", str(agot) if agot else "No antes de 2051", "Primer año con saldo negativo"),
        ])
        st.markdown(
            f"**Lectura:** la reserva de ${reserva0 / 1e12:.1f} billones equivale a {res['anios_gasto_2025']:.1f} años del gasto del Pilar de 2025. "
            + (f"Si solo cubre el alza del gasto sobre el peso de 2025 (hasta ${dr.gasto_cubierto.max() / 1e12:.1f} billones al año), alcanza hasta **{agot}** y cubre el {100 * res['ratio_cobertura']:.0f}% del valor presente de ese gasto. "
               if cubre == "incremento" and agot else "")
            + (f"Si tuviera que financiar todo el gasto del Pilar se agotaría en **{agot}**: es un amortiguador, no un financiamiento. " if cubre == "total" and agot else "")
            + ("La reserva alcanza hasta 2050 con estos supuestos. " if not agot else "")
            + "Más allá de ese año, el alza tiene que financiarse con impuestos."
        )
        st.caption("Stock al 31-dic-2025 (FRP en US$ × dólar del último día hábil, validado contra DIPRES) frente al gasto de 2025 y su proyección: todo en pesos de 2025. "
                   "Es un ejercicio de cobertura, no un plan de retiros: los retiros reales del FRP los fija la ley y Hacienda, y no se modelan las reglas de reposición.")

    with t4:
        b6 = fb[fb.cierre == "2026-06-30"].reset_index(drop=True)
        b5 = fb[fb.cierre == "2025-12-31"].iloc[0]
        r6 = b6.iloc[0]
        meses = 6
        quema = (r6.beneficios_periodo_mm - r6.cotizaciones_periodo_mm) / meses
        tope_musd = 700
        tc = frp.set_index("anio").loc[2025, "tc_cierre"]
        g1, g2 = st.columns([3, 2])
        with g1:
            st.plotly_chart(fapp_flow_chart(b6), use_container_width=True, config=PLOTLY_DL_CONFIG)
        with g2:
            st.metric("Patrimonio del FAPP, 31-dic-2025", f"${b5.patrimonio_mm / 1e6:.2f} billones")
            st.metric("Patrimonio del FAPP, 30-jun-2026", f"${r6.patrimonio_mm / 1e6:.3f} billones",
                      help="Activos menos lo que el FAPP debe al FRP")
            st.metric("Cotizaciones / beneficios, ene-jun 2026", f"{100 * r6.cotizaciones_periodo_mm / r6.beneficios_periodo_mm:.0f}%")
        st.markdown(
            f"**Lectura:** en el primer semestre de 2026 el FAPP pagó ${r6.beneficios_periodo_mm / 1e6:.2f} billones en beneficios y recibió ${r6.cotizaciones_periodo_mm / 1e6:.2f} billones en cotizaciones "
            f"({100 * r6.cotizaciones_periodo_mm / r6.beneficios_periodo_mm:.0f}%). Su patrimonio bajó de ${b5.patrimonio_mm / 1e6:.2f} a ${r6.patrimonio_mm / 1e6:.3f} billones: "
            f"los activos (${r6.activos_mm / 1e6:.2f} billones) casi son todos el préstamo del FRP (${r6.deuda_frp_mm / 1e6:.2f} billones). Al ritmo del semestre el FAPP gasta ${quema / 1e3:.0f} mil millones al mes "
            f"más de lo que recibe, así que el patrimonio equivale a {r6.patrimonio_mm / quema:.1f} meses de ese déficit y los activos a {r6.activos_mm / quema:.1f}. "
            f"Quedan hasta US${tope_musd} millones autorizados del FRP (≈ ${tope_musd * tc / 1e6:.2f} billones, {tope_musd * tc / quema:.0f} meses a ese ritmo). "
            "La brecha es transitoria por diseño: según el calendario de DIPRES la cotización al Seguro Social sube de 0,9% a 3,4% de la masa imponible en septiembre de 2026 y llega a 4,0% en septiembre de 2027."
        )
        st.caption("Estados financieros del FAPP al 31-dic-2025 (5 meses de operación) y al 30-jun-2026 (interinos). Esta pestaña usa el último dato disponible (junio de 2026), seis meses después del resto del KPI. "
                   "Faltan los estados de julio a septiembre de 2026 para ver si el déficit se cerró con la nueva tasa. Tasas de cotización y límite del FRP: nota técnica DIPRES 2025/47.")

    with t5:
        reg = dependencia_regional(load_csv("pgu_pbs_aps_region_trimestral.csv"), load_csv("pgu_pbs_aps_nacional_anual.csv"),
                                   load_csv("kpi_presion_previsional_region.csv"), nac)
        nacr, rr = reg[reg.region_id == 0].iloc[0], reg[reg.region_id != 0]
        alta, baja = rr.sort_values("pct_sin_pension").iloc[-1], rr.sort_values("pct_sin_pension").iloc[0]
        corr = rr.pct_sin_pension.corr(rr.razon_soporte)
        pib24 = load_csv("macro_pib_anual.csv").set_index("anio").loc[2024, "pib_corriente_mm"] * 1e6
        proy_reg = load_csv("kpi_proyeccion_regional.csv")
        n35, n50 = (proyeccion_sin_pension(reg, proy_reg, a).n_anio.sum() for a in (2035, 2050))
        kpi_card_row([
            ("Sin pensión propia, 2024", f"{nacr.n_sin_pension / 1000:,.0f} mil personas", "Beneficiarios de la PGU no contributiva, promedio mensual del 4.º trimestre de 2024"),
            ("PGU que les paga el Estado", f"${nacr.costo_sin_pension / 1e12:.2f} billones al año", f"Equivale a {100 * nacr.costo_sin_pension / pib24:.2f}% del PIB de 2024, en pesos de 2025",
             ["Cuota del 4.º trimestre de 2024 de la PGU no contributiva aplicada a la PGU de 2024", "Con la PGU de $250.000 el monto por persona sube"]),
            ("Escenario 2035", f"{n35 / 1000:,.0f} mil personas", f"Con la tasa de cada región de 2024 constante; {n35 / nacr.n_sin_pension:.1f} veces las de 2024"),
            ("Escenario 2050", f"{n50 / 1000:,.0f} mil personas", f"{n50 / nacr.n_sin_pension:.1f} veces las de 2024"),
        ])
        g1, g2 = st.columns([3, 2])
        with g1:
            st.plotly_chart(dependence_regions_chart(rr, nacr.pct_sin_pension), use_container_width=True, config=PLOTLY_DL_CONFIG)
        with g2:
            tabla = rr.sort_values("pct_sin_pension", ascending=False)[["region_nombre", "pct_sin_pension", "beneficios_por_100", "peso_mes_por_65", "razon_soporte"]].rename(columns={
                "region_nombre": "Región", "pct_sin_pension": "% sin pensión propia", "beneficios_por_100": "Beneficios por 100 de 65+",
                "peso_mes_por_65": "$ al mes por persona 65+", "razon_soporte": "Cotizantes por 65+"})
            st.dataframe(tabla, hide_index=True, use_container_width=True,
                         column_config={"% sin pensión propia": st.column_config.NumberColumn(format="%.1f"), "Beneficios por 100 de 65+": st.column_config.NumberColumn(format="%.0f"),
                                        "$ al mes por persona 65+": st.column_config.NumberColumn(format="$%,.0f"), "Cotizantes por 65+": st.column_config.NumberColumn(format="%.2f")})
        st.markdown(
            f"**Lectura:** {nacr.pct_sin_pension:.0f}% de los beneficiarios de la PGU no recibe otra pensión ({nacr.n_sin_pension / 1000:,.0f} mil personas, ${nacr.costo_sin_pension / 1e12:.2f} billones al año); en {alta.region_nombre} son {alta.pct_sin_pension:.0f}% y en {baja.region_nombre} {baja.pct_sin_pension:.0f}%. "
            f"Las regiones con más cotizantes por persona 65+ dependen menos del Estado (correlación {corr:.2f} entre el % sin pensión propia y los cotizantes por 65+, 16 regiones): "
            f"donde el sistema contributivo llegó menos, el Pilar paga más de la pensión. El pago mensual por persona 65+ varía poco entre regiones (${rr.peso_mes_por_65.min():,.0f} a ${rr.peso_mes_por_65.max():,.0f}); "
            "lo que cambia es de quién depende la pensión. Si cada región mantiene su tasa, serían "
            f"{n35 / 1000:,.0f} mil personas en 2035 y {n50 / 1000:,.0f} mil en 2050."
        )
        st.caption("Cuarto trimestre de 2024 (informe del Pilar Solidario, promedio mensual) frente a la población 65+ del Censo 2024 y a los cotizantes de diciembre de 2024. "
                   "«Sin pensión propia» = beneficiarios de la PGU no contributiva / toda la PGU. Los montos regionales usan la participación de cada región en el trimestre aplicada al total anual de 2024. "
                   "Escenario 2035 y 2050: tasa regional de 2024 constante sobre la población 65+ regional del KPI 1.2 (reparto de tasas nacionales, no proyección oficial); no modela la reforma.")

    with st.expander("Qué se desprende para cada actor"):
        _recomendaciones_2_2(h, frp, fb, nac)


def _recomendaciones_2_2(h, frp, fb, nac):
    base = proyeccion_2_2(h, 0.02, True, True)
    reserva0 = frp.set_index("anio").loc[2025, "cartera_propia_mm"] * 1e6
    dr, res = trayectoria_reserva(base, reserva0, 0.025, "incremento")
    u = fuentes_pilar(frp, nac).iloc[-1]
    pico = base.pilar_pct_pib.idxmax()
    r6 = fb[fb.cierre == "2026-06-30"].iloc[0]
    quema = (r6.beneficios_periodo_mm - r6.cotizaciones_periodo_mm) / 6
    reg = dependencia_regional(load_csv("pgu_pbs_aps_region_trimestral.csv"), load_csv("pgu_pbs_aps_nacional_anual.csv"),
                               load_csv("kpi_presion_previsional_region.csv"), nac)
    rr = reg[reg.region_id != 0].sort_values("pct_sin_pension", ascending=False)
    top = rr.head(3)
    pgu_nc = int(round(reg[reg.region_id == 0].iloc[0].n_sin_pension, -3))
    n35 = proyeccion_sin_pension(reg, load_csv("kpi_proyeccion_regional.csv"), 2035).n_anio.sum()
    st.markdown(
        "Cifras con los supuestos de partida (PIB +2%, PGU de $250.000, aporte al FAPP, reserva = FRP, rentabilidad real 2,5%).\n\n"
        f"**1. Hacienda / DIPRES (planificación fiscal).** El Pilar pasa de {base.pilar_pct_pib.iloc[0]:.2f}% del PIB en 2025 a {base.loc[pico].pilar_pct_pib:.2f}% en {pico}; con el aporte al FAPP la carga llega a {base.loc[2037].carga_pct_pib:.2f}% en 2037. "
        f"El FRP financia solo el {u.pct_frp:.1f}% del gasto del Pilar y, usado para cubrir el alza sobre el peso de 2025, se agota en {res['anio_agotamiento']} (cubre {100 * res['ratio_cobertura']:.0f}% del valor presente de ese alza). "
        f"*Acción:* tener definida antes de {res['anio_agotamiento'] - 3} la fuente permanente (impuestos) para un alza de hasta {(base.carga_pct_pib.max() - base.pilar_pct_pib.iloc[0]):.1f} puntos del PIB (${(base.carga - base.pilar_pct_pib.iloc[0] / 100 * base.pib_real25).max() / 1e12:.1f} billones al año), y no contar el FRP como fuente de régimen.\n\n"
        f"**2. Consejo Directivo del FAPP y Hacienda (administración del FRP).** En enero-junio de 2026 las cotizaciones cubrieron {100 * r6.cotizaciones_periodo_mm / r6.beneficios_periodo_mm:.0f}% de los beneficios; el patrimonio quedó en ${r6.patrimonio_mm / 1e6:.3f} billones, {r6.patrimonio_mm / quema:.1f} meses del déficit semestral. "
        "*Acción:* programar los tramos del FRP (hasta US$ 700 millones, de US$ 100 millones cada uno) según el patrimonio mensual, y revisar los estados de julio a septiembre de 2026 (aún no están en este análisis) para confirmar que el déficit se cerró con la tasa de 3,4% (septiembre de 2026); "
        "si el patrimonio vuelve a bajar de 3 meses de déficit antes de septiembre de 2027 (cuando la tasa llega a 4,0%), pedir el siguiente tramo.\n\n"
        f"**3. AFP y Superintendencia de Pensiones (cobertura contributiva).** {pgu_nc:,} personas (28% de los beneficiarios de la PGU) no tienen pensión propia y el Estado les paga ${reg[reg.region_id == 0].iloc[0].costo_sin_pension / 1e12:.2f} billones al año; "
        f"en {top.iloc[0].region_nombre} ({top.iloc[0].pct_sin_pension:.0f}%), {top.iloc[1].region_nombre} ({top.iloc[1].pct_sin_pension:.0f}%) y {top.iloc[2].region_nombre} ({top.iloc[2].pct_sin_pension:.0f}%) superan por mucho el 23% de Tarapacá o Magallanes. "
        f"Con las tasas de hoy serían {n35 / 1000:,.0f} mil personas en 2035 ({n35 / reg[reg.region_id == 0].iloc[0].n_sin_pension:.1f} veces las de 2024). "
        f"*Acción:* concentrar las campañas de afiliación de independientes y de ahorro voluntario en esas tres regiones (juntas: {top.n_sin_pension.sum() / 1000:,.0f} mil personas hoy), con la meta de llevar su tasa a la mediana de las regiones ({rr.pct_sin_pension.median():.0f}%) antes de 2035; medirlo cada informe trimestral con este mismo indicador. "
        "Distinto de las acciones 1 y 2: aquí no se mueve plata del Estado, se busca que menos personas lleguen a los 65 años sin pensión."
    )


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
