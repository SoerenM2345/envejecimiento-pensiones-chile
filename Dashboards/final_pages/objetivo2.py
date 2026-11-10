"""Objetivo 2: anticipar la presión fiscal del envejecimiento. KPIs 2.1, 2.2 y 2.3."""
import pandas as pd
import streamlit as st
from utils import cargar_escenarios, es_cl, load_csv, load_geojson, kpi_card_row, PLOTLY_DL_CONFIG, subtitulo_visible
from components.kpi_card import kpi_card
from components.cost_analysis import serie_historica, proyeccion, descomponer_pilar, indices_costo, gasto_total_vejez
from components.financiamiento import peso_historico, proyeccion_carga, trayectoria_reserva, fuentes_pilar, dependencia_regional, proyeccion_sin_pension
from components.charts import mostrar, cost_components_chart, beneficiaries_chart, cost_projection_chart, cost_per_person_chart, spending_vs_population_growth, spending_pct_pib, poverty_bars, poverty_people_bars, region_choropleth
from components.charts import cost_index_chart, cost_drivers_chart, num_cl, estilo_kpi, poverty_coverage_scatter, fiscal_weight_chart, financing_sources_chart, reserve_chart, fapp_flow_chart, fapp_schedule_chart, dependence_regions_chart

TITULO_OBJETIVO_2 = "Objetivo 2: anticipar la presión fiscal del envejecimiento"  # igual que config/kpis.yaml e Inicio.py
st.title(TITULO_OBJETIVO_2)
st.markdown("La carga del envejecimiento sobre el Estado crece y sus reservas son mínimas: eso genera presión para desviar cotizaciones "
            "de las cuentas individuales (KPI 1.3). Medimos cuánto cuesta, quién lo financia y dónde está el límite social.")


from components.charts import estilo_kpi as _estilo_2_1, cost_pct_pibpc_chart, burden_chart, total_cost_chart
from components.charts import afp_cost_ratio_chart, afp_waterfall_chart, afp_sales_it_chart, afp_by_firm_chart, afp_stress_chart
from components import afp_economia as afe

ANIO_BASE_COSTO = 2025
ANIO_PGU = 2022  # entra en vigencia la Pensión Garantizada Universal (Ley 21.419, feb-2022)
ANIO_FIN_2_1 = 2050


def _g21(fig, alto=430):
    mostrar(_estilo_2_1(fig, alto))


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
    """Pago anual (pesos), número de pensionados de las ex cajas del IPS (julio de 2026 x 12) y % del pago a menores de 65."""
    c = load_csv("pensiones_pagadas_por_ex_caja.csv")
    c = c[c.ex_caja != "Total"]
    e = load_csv("pensiones_pagadas_por_tramo_edad.csv")
    e = e[~e.tramo_edad.isin(["Total", "Sin información"])]
    menores = e[~e.tramo_edad.str.startswith(("+65", "+7", "+8", "+9", "+100"))]
    return float(c.monto_miles_pesos.sum() * 1e3 * 12), int(c.numero_pensionados.sum()), 100 * menores.monto_miles_pesos.sum() / e.monto_miles_pesos.sum()


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
    render_2_1_total(h)
    render_2_1_por_que(h)
    st.divider()
    st.markdown("#### Detalle del costo por persona de 65+")
    t1, t2, t3, t4, t5, t6 = st.tabs(["Evolución", "Qué lo explica", "Por beneficiario", "Frente al ingreso", "Proyección 2050", "Qué hacer"])
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            _g21(cost_per_person_chart(h.reset_index(), ANIO_PGU, "Pensión Garantizada Universal"))
        with c2:
            _g21(cost_pct_pibpc_chart(h))
        pob = load_csv("proyeccion_envejecimiento_pais.csv").set_index("anio").pob_65_mas
        crece_65 = 100 * (pob.loc[a1] / pob.loc[ANIO_PGU] - 1)
        if desde_hito < 0 and ult.costo_pct_pib_pc < pri.costo_pct_pib_pc:
            _texto(f"**Lectura:** el costo por persona 65+ está controlado ({desde_hito:.0f}% desde {ANIO_PGU}; {ult.costo_pct_pib_pc:.1f}% del PIB per cápita "
                   f"vs. {pri.costo_pct_pib_pc:.1f}% en {a0}). La presión no viene del costo por persona sino del número de personas 65+, "
                   f"que crece {crece_65:.0f}% en el mismo período.")
            if ult.resto / ult.gasto < hito.resto / hito.gasto:  # el sistema antiguo pesa cada vez menos en el gasto
                _texto("Parte de la baja se explica por el sistema antiguo (IPS), cuyos pensionados disminuyen; no es solo eficiencia "
                       f"(su parte del gasto baja de {100 * hito.resto / hito.gasto:.0f}% en {ANIO_PGU} a {100 * ult.resto / ult.gasto:.0f}% en {a1}).")
        else:
            _texto(f"**Lectura:** en pesos reales el costo por adulto mayor cambia {var_total:+.0f}% ({a0}-{a1}) y {desde_hito:+.0f}% desde {ANIO_PGU} (PGU); "
                   f"frente al PIB per cápita pasa de {pri.costo_pct_pib_pc:.1f}% a {ult.costo_pct_pib_pc:.1f}%; las personas 65+ crecen {crece_65:.0f}% desde {ANIO_PGU}.")
        st.caption("\\* Derecha: precios corrientes a ambos lados, porque el costo real (IPC) y el PIB real (deflactor del PIB) no son comparables; detalle en «Método y fuentes».")
    with t2:
        c1, c2 = st.columns(2)
        with c1:
            _g21(cost_components_chart(h))
        with c2:
            _g21(spending_vs_population_growth(h.reset_index()))
        _texto(f"**Lectura:** el Pilar y la PGU suben de ${pri.pilar_65 / 1e6:.2f} a ${ult.pilar_65 / 1e6:.2f} millones por persona 65+, pero el resto de 'Edad avanzada' "
                    f"({100 * ult.resto / ult.gasto:.0f}% del gasto) baja ${(pri.resto_65 - ult.resto_65) / 1e6:.2f} millones: su gasto total casi no crece y la población 65+ sí.")
        st.caption("\\* Resto = Edad avanzada − PGU − PBS/APS de vejez; DIPRES no lo abre, así que no se sabe si su caída es cierre del sistema antiguo o recorte.")
    with t3:
        _g21(beneficiaries_chart(h))
        p0 = h.iloc[0]
        _texto(f"**Lectura:** la cobertura sube de {100 * p0.cobertura:.0f} a {100 * ult.cobertura:.0f} por cada 100 personas 65+ y el pago por beneficio de ${p0.monto_por_beneficio / 1e6:.2f} "
                    f"a ${ult.monto_por_beneficio / 1e6:.2f} millones (≈ ${ult.monto_por_beneficio / 12:,.0f} al mes), casi quieto desde {ANIO_PGU + 1}.")
        st.caption("\\* Solo Pilar Solidario y PGU de vejez; una persona puede tener más de un beneficio, así que la cobertura es un tope.")
    with t4:
        base = st.radio("Ingreso típico de los ocupados", ["mediana", "promedio"], horizontal=True,
                        help="Mediana: la mitad de los ocupados gana menos. Promedio: total de ingresos ÷ ocupados (más alto por los ingresos muy altos).")
        hb = serie_2_1(base)
        _g21(burden_chart(hb, base))
        u, p0 = hb.iloc[-1], hb.iloc[0]
        _texto(f"**Lectura:** repartido por igual, el gasto sería ${u.pago_plano:,.0f} al mes por ocupado: **{100 * u.carga_requerida:.0f}% del ingreso ({base})** frente al 10% de la cotización "
                    f"({100 * p0.carga_requerida:.0f}% en {a0}); harían falta {u.razon_necesaria:.1f} ocupados por persona 65+ y hay {u.ocupados_por_65:.1f}.")
        st.caption("\\* Escala de comparación, no un financiamiento real: el 10% va a cuentas individuales y estos gastos se pagan con impuestos generales.")
    with t5:
        c1, c2 = st.columns([2, 1])
        crec = c1.slider("Crecimiento real anual del PIB", 0.0, 4.0, 100 * cargar_escenarios()["crecimiento_pib_real"], 0.5,
                         format="%.1f%%") / 100
        resto = c2.radio("Resto de 'Edad avanzada'", ["Total constante", "Crece con la población 65+"],
                         help="Total constante: el sistema antiguo no crece. Crece: mismo gasto por persona 65+ que hoy.")
        pgu250 = st.checkbox("Incluir la PGU de $250.000 (Ley 21.735)", value=cargar_escenarios()["pgu_250"])
        pr = proyeccion_2_1(hb, crec, "constante" if resto.startswith("Total") else "crece", pgu250, base)
        _g21(cost_projection_chart(hb, pr, base))
        f = pr.loc[ANIO_FIN_2_1]
        _texto(f"**Escenario {ANIO_FIN_2_1}:** gasto de {f.pct_pib:.1f}% del PIB (hoy {ult.pct_pib:.1f}%), {f.ocupados_por_65:.1f} ocupados por persona 65+ (hoy {ult.ocupados_por_65:.1f}) "
                    f"y un pago por ocupado de **{100 * f.carga_requerida:.0f}% del ingreso ({base})** (hoy {100 * hb.iloc[-1].carga_requerida:.0f}%).")
    with t6:
        _recomendaciones_2_1(h)
    ips, n_ips, ips_men65 = ips_sistema_antiguo()
    with st.expander("Método y fuentes"):
        st.markdown(
            f"- **Fuentes:** gasto en 'Edad avanzada' (DIPRES, COFOG 7102, pesos de 2025); PGU, PBS y APS (Subsecretaría de Previsión Social); población INE base 2024; PIB (Banco Central); "
            f"ocupados (ENE) e ingreso de los ocupados (ESI) del INE.\n"
            f"- **Períodos:** gasto y PIB son flujos del año; la población 65+ y total, de mitad de año; ocupados e ingreso, de octubre-diciembre (desfase de unos 4 meses; "
            f"el efecto en los ocupados por persona 65+ es menor a 2%). El ingreso se pasa a pesos de 2025 con el IPC anual.\n"
            f"- **Precios:** el costo real usa el IPC (las pensiones se reajustan por IPC), que subió {ipc:.0f}% en {a0}-{a1}; el PIB real usa el deflactor del PIB, que subió {defl_pib:.0f}%. "
            f"Por eso el indicador principal usa precios corrientes en ambos lados.\n"
            f"- **Resto:** lo que queda de 'Edad avanzada' al restar PGU y PBS/APS; incluye el sistema antiguo. "
            f"El IPS paga ≈ ${ips / 1e12:.1f} billones al año a {f'{n_ips:,}'.replace(',', '.')} pensionados (julio 2026), solo una parte del resto, y solo {ips_men65:.0f}% de ese pago va a menores de 65; "
            f"Capredena y Dipreca no se pueden ver con estos datos.\n"
            f"- **PGU 2022:** residual del total del Pilar (Total − PBS − APS); parte en febrero. La cobertura cuenta beneficios, no personas.\n"
            f"- **Proyección:** población INE; ocupados proporcionales a la población 15-64; el ingreso crece como el PIB per cápita; con la base «promedio» el pago por ocupado pesa menos porque el ingreso promedio es mayor que la mediana."
        )


RESTO_OPCIONES = {"No mostrar (no se proyecta)": "no", "Supuesto: total constante": "constante", "Supuesto: crece con la población 65+": "crece"}


def render_2_1_total(h: pd.DataFrame):
    """Costo total del Estado en la vejez: une el Pilar Solidario (KPI 2.1 y 2.2) y el gasto en «Edad avanzada» (DIPRES)."""
    cfg = cargar_escenarios()
    ult = int(h.index[-1])
    st.markdown("#### ¿Cuánto cuesta en total la vejez al Estado?")
    c1, c2, c3 = st.columns([2, 2, 2])
    per = c1.radio("Período", [f"{h.index[0]}-{ult} (observado)", f"{ult}-{ANIO_FIN_2_1} (escenario)"], horizontal=True, key="c21_total_periodo")
    futuro = "escenario" in per
    con_fapp = c2.checkbox("Con aporte al FAPP (Ley 21.735)", value=cfg["aporte_fapp"], key="c21_total_fapp", disabled=not futuro,
                           help="El mismo aporte del Estado al Fondo Autónomo de Protección Previsional que el KPI 2.2 (desde 2028).")
    resto = RESTO_OPCIONES[c3.radio("Resto de «Edad avanzada» en el escenario", list(RESTO_OPCIONES), key="c21_total_resto", disabled=not futuro,
                                    help="DIPRES no abre el resto (sistema antiguo y otros) y el modelo no lo proyecta: se omite o se agrega con un supuesto explícito.")]
    carga = proyeccion_2_2(h, cfg["crecimiento_pib_real"], cfg["pgu_250"], con_fapp)
    d = gasto_total_vejez(h, carga, load_csv("pgu_pbs_aps_nacional_anual.csv"), load_csv("macro_pib_anual.csv"), load_csv("kpi_pc_nacional.csv"),
                          resto if futuro else "no")
    par = load_csv("kpi_pc_parametros_reforma.csv").set_index("anio")
    anio_pgu = int(par.index[par.factor_costo_pgu >= par.factor_costo_pgu.max() - 1e-9][0])
    anio_fapp = int(load_csv("fapp_aporte_fiscal.csv").anio.min())
    frp0 = load_csv("frp_reserva_anual.csv").set_index("anio").loc[ult, "cartera_propia_mm"] * 1e6
    _, res = trayectoria_reserva(carga, frp0, cfg["rentabilidad_real_reservas"]["base"], "incremento")
    hitos = [(ANIO_PGU, "PGU (Ley 21.419, feb. 2022)"), (ult, "Ley 21.735")]
    hitos += ([(anio_pgu, "PGU de $250.000 para todos y aporte al FAPP")] if anio_pgu == anio_fapp else
              [(anio_pgu, "PGU de $250.000 para todos"), (anio_fapp, "Aporte al FAPP")])
    if res["anio_agotamiento"]:
        hitos.append((res["anio_agotamiento"], "Se agota el FRP (KPI 2.2)"))
    dv = d[d.escenario] if futuro else d[~d.escenario]
    if futuro:
        dv = pd.concat([d.loc[[ult]].assign(resto=d.loc[ult, "resto"] if resto != "no" else float("nan"),
                                            resto_pct=d.loc[ult, "resto_pct"] if resto != "no" else float("nan"),
                                            carga_pct=d.loc[ult, "pilar_pct"]), dv])
    mostrar(estilo_kpi(total_cost_chart(dv, futuro, hitos), 680))
    o = d[~d.escenario]
    p0, u = o.iloc[0], o.iloc[-1]
    a0 = int(o.index[0])
    k = lambda a, b: 100 * (b / a - 1)  # noqa: E731
    kpi_card_row([
        (f"Gasto del Estado en la vejez ({ult})", f"${u.total / 1e12:.1f} billones", f"{u.total_pct:.2f}% del PIB; {k(p0.total, u.total):+.0f}% real desde {a0}",
         ["Gasto del Gobierno Central en «Edad avanzada» (DIPRES, COFOG 7102), pesos de 2025",
          f"Pilar Solidario de vejez: ${u.pilar_vejez / 1e12:.2f} billones; resto (sistema antiguo y otros): ${u.resto / 1e12:.2f} billones",
          f"Aparte, Pilar de invalidez: ${u.pilar_invalidez / 1e12:.2f} billones (no sumado)"]),
        (f"Costo por persona 65+ ({ult})", f"${u.costo_65 / 1e6:.2f} millones", f"{k(p0.costo_65, u.costo_65):+.0f}% real desde {a0}",
         ["El mismo indicador de la tarjeta de arriba", "Gasto en «Edad avanzada» ÷ personas de 65+ (INE)"]),
        (f"Personas de 65+ ({ult})", f"{u.pob_65 / 1e6:.2f} millones", f"{k(p0.pob_65, u.pob_65):+.0f}% desde {a0}",
         ["Proyecciones de población del INE, base 2024"]),
    ])
    g, pob, cpp = u.total / p0.total, u.pob_65 / p0.pob_65, u.costo_65 / p0.costo_65
    h22 = o.loc[ANIO_PGU]
    if not futuro:
        subtitulo_visible(f"Qué muestra: el gasto total del Estado en la vejez ({a0}-{ult}), separado en el Pilar Solidario de vejez y el resto de «Edad avanzada» "
                          f"(sobre todo el sistema antiguo, calculado como residual); abajo, lo mismo en % del PIB. El Pilar de invalidez va aparte.")
        _texto(f"**Lectura:** el gasto total se multiplicó por {g:.2f} entre {a0} y {ult}: las personas de 65+ por {pob:.2f} y el costo por persona por {cpp:.2f} "
               f"({pob:.2f} × {cpp:.2f} = {g:.2f}). Desde {ANIO_PGU} el costo por persona cambió {k(h22.costo_65, u.costo_65):+.0f}% y las personas de 65+ "
               f"{k(h22.pob_65, u.pob_65):+.0f}%: **el alza del total viene de cuántas personas mayores hay, no de que cada una cueste más**. "
               f"Dentro del total sí hay un cambio: el Pilar Solidario sube de {100 * p0.pilar_vejez / p0.total:.0f}% a {100 * u.pilar_vejez / u.total:.0f}% del gasto "
               f"(su monto por beneficio se duplicó, ver abajo) mientras el sistema antiguo se achica.")
    else:
        f, b = carga.loc[ANIO_FIN_2_1], carga.loc[ult]
        cg = "carga_pct_pib" if con_fapp else "pilar_pct_pib"
        pico = int(carga[cg].idxmax())
        subtitulo_visible(f"Qué muestra: el escenario {ult}-{ANIO_FIN_2_1} de lo que el modelo proyecta, el Pilar Solidario de vejez"
                          + (" y el aporte al FAPP" if con_fapp else "") + "; el Pilar de invalidez queda constante en pesos reales. "
                          + ("El resto de «Edad avanzada» no se proyecta: se omite." if resto == "no" else
                             f"El resto de «Edad avanzada» es un supuesto ({'total constante' if resto == 'constante' else 'mismo gasto por persona de 65+ que hoy'}), no una proyección."))
        _texto(f"**Lectura:** el Pilar (vejez + invalidez{' + aporte al FAPP' if con_fapp else ''}) pasa de {b[cg]:.2f}% del PIB en {ult} a {carga.loc[pico, cg]:.2f}% en {pico} "
               f"y {f[cg]:.2f}% en {ANIO_FIN_2_1}, las mismas cifras del KPI 2.2. Las personas de 65+ se multiplican por {f.pob_65 / b.pob_65:.2f} y el costo del Pilar de vejez "
               f"por persona de 65+ por {(f.pilar_vejez / f.pob_65) / (b.pilar_vejez / b.pob_65):.2f} (solo la PGU de $250.000): otra vez, el motor es la demografía."
               + (f" Con el supuesto para el resto, «Edad avanzada» llegaría a {d.loc[ANIO_FIN_2_1, 'pilar_vejez_pct'] + d.loc[ANIO_FIN_2_1, 'resto_pct']:.2f}% del PIB en {ANIO_FIN_2_1}." if resto != "no" else ""))
    _nota(f"\\* «Resto» = «Edad avanzada» − Pilar Solidario de vejez: es un residual, DIPRES no lo abre (sistema antiguo del IPS, Capredena, Dipreca y otros). "
          f"El Pilar total ({u.pilar_pct:.2f}% del PIB en {ult}, KPI 2.2) incluye invalidez; la descomposición del KPI 2.1 usa solo vejez (${u.pilar_vejez / 1e12:.2f} billones). "
          f"Escenario: PIB +{cfg['crecimiento_pib_real']:.0%} real al año, PGU de $250.000 y cobertura constante (config/escenarios.yaml); no es un pronóstico.")
    gps = load_csv("gasto_proteccion_social.csv")
    ei = float(gps[(gps.categoria == "Enfermedad e incapacidad") & (gps.anio == ult)].gasto_mm_2025.iloc[0]) * 1e6
    with st.expander("Método y fuentes del costo total"):
        _texto(
            f"- **Series:** «Edad avanzada» del Gobierno Central (DIPRES, Estadísticas de las Finanzas Públicas, clasificación funcional COFOG 7102), en pesos de 2025 de la propia DIPRES y en % del PIB; "
            f"PGU, PBS y APS de vejez e invalidez (Subsecretaría de Previsión Social, cierre anual), en pesos nominales llevados a pesos de 2025 con el IPC; personas de 65+ (INE, proyecciones base 2024); "
            f"PIB a precios corrientes (Banco Central).\n"
            f"- **Pilar de vejez vs. Pilar total:** en {ult} el Pilar de vejez (PGU + PBS/APS de vejez) cuesta ${u.pilar_vejez / 1e12:.2f} billones y el de invalidez ${u.pilar_invalidez / 1e12:.2f} billones; "
            f"juntos, ${(u.pilar_vejez + u.pilar_invalidez) / 1e12:.2f} billones = {u.pilar_pct:.2f}% del PIB (ratio 1 del KPI 2.2). La descomposición «¿por qué suben los costos?» usa solo vejez.\n"
            f"- **Invalidez aparte:** no se suma al total porque no se sabe si DIPRES la registra en «Edad avanzada» (7102) o en «Enfermedad e incapacidad» (7101); "
            f"esta última suma ${ei / 1e12:.2f} billones en {ult}, menos que el Pilar de invalidez, así que no puede estar entero ahí. Hay que preguntarlo a DIPRES.\n"
            f"- **Resto:** residual de «Edad avanzada» menos el Pilar de vejez. DIPRES usa su propio deflactor y el Pilar el IPC; difieren a lo más 0,4% (en {a0}), "
            f"así que el residual en pesos reales tiene ese margen. Los % del PIB no dependen del deflactor (nominal ÷ PIB corriente).\n"
            f"- **Escenario:** el mismo motor del KPI 2.2 (costo del Pilar de vejez por persona de 65+ constante en términos reales, más la PGU de $250.000 por la población 65+ del INE; "
            f"invalidez constante; aporte al FAPP según la ley). El resto no se proyecta; si se elige un supuesto, se dibuja como tal.\n"
            f"- **Agotamiento del FRP:** {res['anio_agotamiento'] or 'no antes de ' + str(ANIO_FIN_2_1 + 1)}, con la reserva cubriendo solo el alza sobre el peso de {ult} y "
            f"{100 * cfg['rentabilidad_real_reservas']['base']:.1f}% real (KPI 2.2).\n"
            f"- **Precios en otros gráficos:** el costo por persona 65+ frente al PIB per cápita usa precios corrientes a ambos lados; no se mezcla con estas series reales.")


PERIODOS_COSTO = (("2016 → 2021", 2016, 2021), ("2021 → 2025", 2021, 2025), ("2025 → 2050 (escenario)", 2025, 2050))


def render_2_1_por_que(h: pd.DataFrame):
    """Costos como problema nacional (punto 3 del profesor): qué sube más rápido y por qué, con las tres piezas exactas del costo del Pilar."""
    cfg = cargar_escenarios()
    pr = proyeccion_2_1(h, cfg["crecimiento_pib_real"], "constante", cfg["pgu_250"], "mediana")
    ult = int(h.index[-1])
    st.markdown("#### ¿Por qué suben los costos?")
    st.markdown("El Pilar Solidario de vejez (la Pensión Garantizada Universal y las pensiones solidarias, que paga el Estado con impuestos) cuesta "
                "**personas de 65+ × cuántas reciben beneficio × cuánto recibe cada beneficio**. Es una multiplicación exacta, así que se puede ver cuál de las tres "
                "piezas explica el alza: la demografía (las personas de 65+) o las decisiones de política (a cuántas se llega y con cuánto).")
    st.markdown("##### 1. ¿Qué sube más rápido?")
    per = st.radio("Período", [f"{h.index[0]}-{ult} (observado)", f"{ult}-{ANIO_FIN_2_1} (escenario)"], horizontal=True, key="c21_periodo")
    futuro = "escenario" in per
    a0, a1 = (ult, ANIO_FIN_2_1) if futuro else (int(h.index[0]), ult)
    idx = indices_costo(h, pr, a0, a1)
    mostrar(estilo_kpi(cost_index_chart(idx, futuro), 520))
    v = lambda c: idx[c].iloc[-1] / 100  # noqa: E731
    subtitulo_visible(f"Qué muestra: cuánto creció cada cosa desde {a0} (= 100); lo que queda más arriba creció más rápido. Entre {a0} y {a1} el costo del Pilar se multiplica por {v('pilar'):.1f}, "
                      f"el monto por beneficio por {v('monto'):.1f}, las personas de 65+ por {v('pob_65'):.1f} y la economía (PIB real) por {v('pib'):.1f}. "
                      + ("Por eso el costo pesa cada vez más frente a la economía." if v("pilar") > v("pib") else "El costo crece menos que la economía."))
    st.markdown("##### 2. ¿De dónde viene el aumento?")
    descs = [(et, descomponer_pilar(h, pr, x0, x1)) for et, x0, x1 in PERIODOS_COSTO]
    mostrar(estilo_kpi(cost_drivers_chart(descs), 400))
    pp = lambda d, k: 100 * next(p["parte"] for p in d["partes"] if p["clave"] == k)  # noqa: E731
    d0, d1, d2 = (d for _, d in descs)
    subtitulo_visible(f"Qué muestra: de cada 100 pesos que sube el costo del Pilar, cuántos vienen de cada pieza. Hasta 2021 el monto por beneficio explica {pp(d0, 'monto'):.0f}; "
                      f"con la PGU (2022) la cobertura pasa a {pp(d1, 'cobertura'):.0f} y el monto a {pp(d1, 'monto'):.0f}; hacia 2050 las personas de 65+ explican {pp(d2, 'pob_65'):.0f} "
                      f"(escenario con la cobertura de {ult} constante). El motor pasa de la política a la demografía.")
    st.markdown("##### 3. Las razones una por una (resumen)")
    par = load_csv("kpi_pc_parametros_reforma.csv").set_index("anio")
    anio28 = int(par.index[par.factor_costo_pgu >= par.factor_costo_pgu.max() - 1e-9][0])
    p0, pf = h.iloc[0], h.iloc[-1]
    g_resto = 100 * ((pf.resto / p0.resto) ** (1 / (ult - h.index[0])) - 1)
    g_pib = 100 * (((pf.pib_pc_real * pf.pob_total) / (p0.pib_pc_real * p0.pob_total)) ** (1 / (ult - h.index[0])) - 1)
    pc = lambda d, k: f"{pp(d, k):.0f} %"  # noqa: E731
    filas = [
        ("Más personas de 65+ (envejecimiento)", "Personas de 65+", pc(d0, "pob_65"), pc(d1, "pob_65"), pc(d2, "pob_65"),
         f"De {p0.pob_65 / 1e6:.1f} a {pf.pob_65 / 1e6:.1f} millones entre {h.index[0]} y {ult}, y a {pr.loc[ANIO_FIN_2_1].pob_65 / 1e6:.1f} millones en {ANIO_FIN_2_1} (INE). Es la pieza que no depende de decisiones."),
        ("Más personas reciben el beneficio", "Beneficios por persona de 65+", pc(d0, "cobertura"), pc(d1, "cobertura"), pc(d2, "cobertura"),
         f"De {100 * p0.cobertura:.0f} a {100 * pf.cobertura:.0f} beneficios por cada 100 personas de 65+. La Pensión Garantizada Universal (Ley 21.419, desde febrero de {ANIO_PGU}) llegó a más gente. "
         f"En el escenario se supone constante."),
        ("Cada beneficio paga más", "Monto por beneficio", pc(d0, "monto"), pc(d1, "monto"), pc(d2, "monto"),
         f"El pago anual real por beneficio pasa de ${p0.monto_por_beneficio / 1e6:.2f} a ${pf.monto_por_beneficio / 1e6:.2f} millones. "
         f"La PGU de $250.000 (Ley 21.735) suma otro {100 * (par.factor_costo_pgu.max() - 1):.0f} % hasta {anio28} (escenario)."),
        ("Menos trabajadores por persona de 65+", "No cambia el costo: cambia quién lo paga", "—", "—", "—",
         f"Ocupados por persona de 65+: {pf.ocupados_por_65:.1f} en {ult} y {pr.loc[ANIO_FIN_2_1].ocupados_por_65:.1f} en {ANIO_FIN_2_1} (escenario). El mismo costo recae en menos personas: ver el KPI 1.2."),
        ("Sistema antiguo y otros («resto»)", "Fuera del Pilar", "—", "—", "—",
         f"Crece {g_resto:.1f} % al año en pesos reales ({h.index[0]}-{ult}), menos que el PIB ({g_pib:.1f} %): no empuja el alza. DIPRES no lo abre."),
    ]
    tabla = pd.DataFrame(filas, columns=["Posible razón", "En qué pieza cae", f"{PERIODOS_COSTO[0][0]}", f"{PERIODOS_COSTO[1][0]}", f"{PERIODOS_COSTO[2][0]}", "Trasfondo"])
    tabla["Trasfondo"] = tabla["Trasfondo"].map(lambda x: es_cl(x).replace("$", "\\$"))  # coma decimal; sin que el «$» se lea como fórmula
    st.table(tabla.set_index("Posible razón"))
    _nota("Las tres columnas de períodos son el % del aumento del costo del Pilar que aporta cada pieza (los gráficos de arriba). "
          f"Fuente: DIPRES (Estadísticas de las Finanzas Públicas), Subsecretaría de Previsión Social (PGU, PBS y APS), INE (población base 2024), pesos reales de {ANIO_BASE_COSTO}. "
          f"Escenario hasta {ANIO_FIN_2_1}: PIB +{cfg['crecimiento_pib_real']:.0%} al año, PGU de $250.000 y cobertura constante; no es un pronóstico. "
          "La cobertura cuenta beneficios, no personas (una persona puede tener más de uno), y el «Total» del Pilar incluye invalidez además de vejez. "
          "El gasto en «Edad avanzada» incluye el sistema antiguo, que DIPRES no abre: por eso la descomposición es del Pilar y no de todo el gasto. "
          "Cuánto pesa en el PIB: KPI 2.2. Hasta cuándo alcanza lo que aportan los cotizantes: KPI 1.2.")


def _recomendaciones_2_1(h):
    """Lectores del KPI 2.1 con los supuestos de partida de config/escenarios.yaml; la AFP primero."""
    cfg = cargar_escenarios()
    pc = proyeccion_2_1(h, cfg["crecimiento_pib_real"], "constante", cfg["pgu_250"], "mediana")
    pg = proyeccion_2_1(h, cfg["crecimiento_pib_real"], "crece", cfg["pgu_250"], "mediana")
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
    cob = load_csv("kpi_cobertura_correlaciones_region.csv").sort_values("cobertura_previsional_pct").head(3)
    _texto(
        f"Cifras con los supuestos de partida de config/escenarios.yaml (PIB +{cfg['crecimiento_pib_real']:.0%}, PGU de $250.000, ingreso mediano de los ocupados).\n\n"
        f"**1. AFP (base cotizante).** Hoy {sin_cot / 1e6:.1f} millones de ocupados no cotizan (cotizantes de diciembre: {nac.cotizantes_dic / 1e6:.1f} millones de "
        f"{u.ocupados / 1e6:.1f} millones de ocupados). Si cotizaran el 10% del ingreso mediano sumarían ${suma_cot / 1e12:.1f} billones al año a las cuentas "
        f"individuales (equivale al {100 * suma_cot / u.gasto:.0f}% del gasto de {a1}): es la base comisionable que se puede ganar. Las regiones con menor cobertura son "
        + ", ".join(f"{r.region_nombre} ({r.cobertura_previsional_pct:.1f}%)" for r in cob.itertuples())
        + ". *Acción:* fijar una meta anual de afiliación de independientes e informales, empezando por esas regiones, y medirla con el "
        "mismo indicador (ocupados que cotizan / ocupados). No depende de impuestos: amplía la base que ahorra para su propia pensión y le baja presión "
        "al Pilar.\n\n"
        "**Contexto: Estado**\n\n"
        f"**2. Hacienda / DIPRES (planificación fiscal).** El gasto en 'Edad avanzada' es {u.pct_pib:.1f}% del PIB en {a1}; en {ANIO_FIN_2_1} sería {pc.loc[ANIO_FIN_2_1].pct_pib:.1f}% si el resto "
        f"(sistema antiguo y otros, {100 * u.resto / u.gasto:.0f}% del gasto) se mantiene constante y {pg.loc[ANIO_FIN_2_1].pct_pib:.1f}% si crece con la población 65+: una diferencia de ${dif / 1e12:.1f} billones al año "
        f"({100 * dif / pib50:.1f} puntos del PIB). Si todos los ocupados aportaran el 10% del ingreso mediano financiarían solo el {100 * cobertura_10:.0f}% del costo por persona 65+ "
        f"({u.ocupados_por_65:.1f} ocupados por persona 65+ frente a {u.razon_necesaria:.1f} necesarios), y en {int(bajo2[0]) if len(bajo2) else 'más allá de ' + str(ANIO_FIN_2_1)} habría menos de 2. "
        f"*Acción:* pedir a DIPRES que publique y proyecte 'Edad avanzada' por institución (IPS, Capredena, Dipreca, Pilar y PGU) antes de que la PGU llegue a $250.000 en {anio28}.\n\n"
        f"**3. Subsecretaría de Previsión Social (suficiencia de la PGU).** El pago por beneficio está casi quieto desde {ANIO_PGU + 1} (≈ ${u.monto_por_beneficio / 12:,.0f} al mes) y la cobertura llegó a {100 * u.cobertura:.0f} por cada 100 personas 65+. "
        f"La PGU de ${pgu_hoy:,.0f} equivale al {100 * pgu_hoy / u.mediana_mensual:.0f}% del ingreso mediano de los ocupados (${u.mediana_mensual:,.0f}); con $250.000 sería {100 * pgu_nueva / u.mediana_mensual:.0f}%, "
        f"y el Pilar cuesta ${sube_pgu / 1e12:.1f} billones más al año en {anio28}. *Acción:* fijar la meta de la PGU como porcentaje del ingreso mediano y revisarla cada año con la ESI; "
        "mirar primero las regiones con más pobreza 65+ (KPI 2.3)."
    )


@st.cache_data
def proyeccion_2_2(_h: pd.DataFrame, crec_pib: float, pgu_250: bool, con_fapp: bool) -> pd.DataFrame:
    return proyeccion_carga(_h, load_csv("pgu_pbs_aps_nacional_anual.csv"), load_csv("macro_pib_anual.csv"),
                            load_csv("proyeccion_envejecimiento_pais.csv"), load_csv("kpi_pc_parametros_reforma.csv"),
                            load_csv("fapp_aporte_fiscal.csv"), crec_pib, pgu_250, con_fapp,
                            cargar_escenarios()["horizonte_proyeccion"])


def _texto(t):
    """st.markdown con coma decimal (es-CL) y sin confundir los pares de «$» con fórmulas."""
    st.markdown(es_cl(t).replace("$", "\\$"))


def _nota(t):
    st.caption(es_cl(t).replace("$", "\\$"))


def _caja(clave, titulo, formula, numeros, defecto=True):
    """Caja del panel de fórmulas: casilla para mostrar u ocultar la línea, fórmula en símbolos y las cifras del año base."""
    with st.container(border=True):
        ver = st.checkbox(titulo, value=defecto, key=clave)
        st.markdown(f"`{formula}`")
        _nota(numeros)
    return ver


def _grafico(fig, alto=460, leyenda_y=None):
    """Mismo estilo de texto que los KPIs 1.2 y 1.3 (texto negro, leyenda abajo)."""
    estilo_kpi(fig, alto)
    if leyenda_y is not None:
        fig.update_layout(legend_y=leyenda_y)
    mostrar(fig)


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
    _grafico(spending_pct_pib(d), 420)
    cfg = cargar_escenarios()
    base = proyeccion_2_2(serie_2_1(), cfg["crecimiento_pib_real"], cfg["pgu_250"], cfg["aporte_fapp"])
    frp0 = load_csv("frp_reserva_anual.csv").set_index("anio").loc[2025, "cartera_propia_mm"] * 1e6
    _, res0 = trayectoria_reserva(base, frp0, cfg["rentabilidad_real_reservas"]["base"], "incremento")
    pico0 = base.pilar_pct_pib.idxmax()
    agota = f"se agotan en {res0['anio_agotamiento']}" if res0["anio_agotamiento"] else f"alcanzan hasta {base.index.max()}"
    _texto(f"**Lectura:** la carga sube de {base.pilar_pct_pib.iloc[0]:.2f}% a {base.loc[pico0].pilar_pct_pib:.2f}% del PIB hasta {pico0} "
           f"(+{base.loc[pico0].pilar_pct_pib - base.pilar_pct_pib.iloc[0]:.2f} pp; incluye invalidez, el punto crítico del KPI 1.2 usa solo vejez): "
           f"es moderada, pero se financia con impuestos generales y las reservas (FRP) cubren solo {100 * res0['ratio_cobertura']:.0f}% del valor "
           f"presente del alza y {agota}.")
    _nota("\\* Ratio 2 = cobertura de reservas (pestaña «Reservas»): el valor presente oficial del déficit no está publicado, así que se "
          "compara la reserva con el valor presente del alza del gasto sobre el peso de 2025.")
    _texto("#### ¿Quién financia el Pilar y cuánto aguantan las reservas?")
    _profundizacion_2_2()


def _profundizacion_2_2():
    h = serie_2_1()
    frp, fb, ap = load_csv("frp_reserva_anual.csv"), load_csv("fapp_balance.csv"), load_csv("fapp_aporte_fiscal.csv")
    nac = load_csv("kpi_pc_nacional.csv")
    c1, c2, c3 = st.columns([2, 2, 2])
    crec = c1.slider("Crecimiento real anual del PIB", 0.0, 4.0, 100 * cargar_escenarios()["crecimiento_pib_real"], 0.5,
                     format="%.1f%%", key="k22_pib",
                     help="Mismo supuesto de partida que el KPI 2.1. Un PIB que crece más reduce el peso del Pilar en el PIB.") / 100
    cfg = cargar_escenarios()
    pgu250 = c2.checkbox("Incluir la PGU de $250.000 (Ley 21.735)", value=cfg["pgu_250"], key="k22_pgu")
    con_fapp = c3.checkbox("Sumar el aporte al FAPP (Ley 21.735)", value=cfg["aporte_fapp"], key="k22_fapp",
                           help="Desde 2028 la ley obliga al Estado a aportar al Fondo Autónomo de Protección Previsional (Seguro Social): "
                                "2,2 millones de UTM al año, hasta 15 millones desde 2037.")
    p = proyeccion_2_2(h, crec, pgu250, con_fapp)
    t1, t2, t3, t4, t5 = st.tabs(["Peso fiscal 2050", "Quién lo financia", "Reservas", "FAPP hoy", "Dónde"])

    with t1:
        hist = peso_historico(load_csv("pgu_pbs_aps_nacional_anual.csv"), load_csv("macro_pib_anual.csv"), load_csv("gasto_proteccion_social.csv"))
        b, a37, f = p.loc[2025], p.loc[2037], p.loc[2050]
        utm = ap.utm_pesos_2025.iloc[0]
        cg, cp = st.columns([3, 1])
        with cp:
            v_obs = _caja("k22_v_obs", "Observado", "Pilar / PIB = (PGU + PBS/APS) / PIB",
                          f"2025: ${b.pilar / 1e12:.2f} ÷ ${b.pib_real25 / 1e12:.1f} billones → {b.pilar_pct_pib:.2f}%")
            v_esc = _caja("k22_v_esc", "Escenario del Pilar", "c₆₅ × f(PGU) × P₆₅₊ / PIB",
                          f"2037: ${a37.pilar / 1e12:.2f} ÷ ${a37.pib_real25 / 1e12:.0f} billones → {a37.pilar_pct_pib:.2f}%")
            v_fapp = _caja("k22_v_fapp", "Con aporte al FAPP", "(Pilar + UTM × valor UTM) / PIB",
                           f"2037: ${a37.pilar / 1e12:.2f} + {ap.millones_utm.max():.0f} M UTM × ${utm:,.0f} → ${a37.carga / 1e12:.2f} billones = {a37.carga_pct_pib:.2f}%") if con_fapp else False
        with cg:
            _grafico(fiscal_weight_chart(hist, p, con_fapp, (v_obs, v_esc, v_fapp)), 560)
        pico = p.pilar_pct_pib.idxmax()
        fin = int(p.index.max())
        kpi_card_row([
            ("Pilar + PGU, 2025 (real)", f"{b.pilar_pct_pib:.2f}%", "% del PIB. Ratio 1 del KPI: el mismo valor del gráfico de arriba"),
            (f"Pilar + PGU, {pico} (escenario)", f"{p.loc[pico].pilar_pct_pib:.2f}%",
             f"% del PIB en el año de mayor peso del Pilar; +{p.loc[pico].pilar_pct_pib - b.pilar_pct_pib:.2f} puntos del PIB sobre 2025"),
            (f"Pilar + PGU, {fin} (escenario)", f"{p.loc[fin].pilar_pct_pib:.2f}%",
             f"% del PIB; equivale a ${p.loc[fin].pilar / 1e12:.1f} billones al año en pesos de 2025 (2025: ${b.pilar / 1e12:.1f} billones)"),
            (f"Con aporte FAPP, {pico} (escenario)", f"{p.loc[pico].carga_pct_pib:.2f}%" if con_fapp else "sin aporte",
             "% del PIB: Pilar + aporte del Estado al FAPP (Ley 21.735)" if con_fapp else "Casilla del aporte al FAPP desmarcada"),
        ])
        _texto(f"**Lectura:** el Pilar pasa de {b.pilar_pct_pib:.2f}% del PIB en 2025 a {p.loc[pico].pilar_pct_pib:.2f}% en {pico}"
                    + (f"; con el aporte al FAPP, la carga llega a {p.loc[pico].carga_pct_pib:.2f}% ese año." if con_fapp else "."))
        _nota("\\* Sólido: observado. Punteado: escenario. Franja: aporte del Estado al FAPP.")

    with t2:
        fu = fuentes_pilar(frp, nac)
        g1, g2 = st.columns(2)
        with g1:
            _grafico(financing_sources_chart(fu), 420)
        with g2:
            _grafico(fapp_schedule_chart(proyeccion_2_2(h, crec, pgu250, True)), 420)
        u = fu.iloc[-1]
        f1 = frp.set_index("anio").loc[2025]
        _texto(f"**Lectura:** en {int(u.anio)} el retiro del FRP (US${f1.retiros_musd:,.0f} millones) financió el **{u.pct_frp:.1f}%** del Pilar (${u.pilar_real / 1e12:.2f} billones); "
                    f"el {100 - u.pct_frp:.1f}% sale del presupuesto general. El aporte del Estado al FAPP llega a ${ap.aporte_mm_2025.max() / 1e6:.2f} billones al año desde 2037 y va al Seguro Social, no al Pilar.")
        _nota("\\* Bajo cada año: parte del Pilar que financió el FRP. Pesos de 2025.")

    with t3:
        k1, k2, k3 = st.columns(3)
        res_in = k1.radio("Reservas incluidas", ["Solo FRP", "FRP + activos del FAPP"], key="k22_res",
                          help="El FRP está pensado para complementar las pensiones garantizadas por el Estado. Los activos del FAPP están destinados por ley al Seguro Social, "
                               "no al Pilar; se pueden sumar para ver el máximo.")
        cubre_in = k2.radio("Qué gasto cubren", ["Solo el alza sobre el peso de 2025", "Todo el gasto del Pilar"], key="k22_cubre",
                            help="Alza: lo que el Pilar (y el aporte al FAPP) gasta por encima de mantener el 2,07% del PIB de 2025. Todo: el gasto completo.")
        r_real = k3.slider("Rentabilidad real de la reserva", 0.0, 5.0, 100 * cfg["rentabilidad_real_reservas"]["base"], 0.5,
                           format="%.1f%%", key="k22_r",
                           help="2,5% real al año: es la tasa de 2,53% real que DIPRES fijó para el préstamo del FRP al FAPP (Resolución Exenta 646 de 2025). Es también la tasa de descuento del valor presente.") / 100
        reserva0 = frp.set_index("anio").loc[2025, "cartera_propia_mm"] * 1e6
        if res_in.startswith("FRP +"):
            reserva0 += fb[fb.cierre == "2025-12-31"].activos_mm.iloc[0] * 1e6
        cubre = "incremento" if cubre_in.startswith("Solo") else "total"
        dr, res = trayectoria_reserva(p, reserva0, r_real, cubre)
        a37r = dr.loc[2037]
        base_pct = dr.pilar_pct_pib.iloc[0]
        cg, cp = st.columns([3, 1])
        with cp:
            v_gas = _caja("k22_v_gas", "Gasto cubierto", "G = max(0, C − p₂₅ × PIB)" if cubre == "incremento" else "G = C (todo el gasto)",
                          (f"2037: ${a37r.carga / 1e12:.2f} − {base_pct:.2f}% × ${a37r.pib_real25 / 1e12:.0f} → ${a37r.gasto_cubierto / 1e12:.2f} billones"
                           if cubre == "incremento" else f"2037: C = ${a37r.carga / 1e12:.2f} billones"))
            v_sal = _caja("k22_v_sal", "Saldo de la reserva", "S = S₋₁ × (1 + r) − G",
                          f"2026: ${reserva0 / 1e12:.1f} × {num_cl(1 + r_real, 3)} − ${dr.loc[2026].gasto_cubierto / 1e12:.2f} → ${dr.loc[2026].saldo / 1e12:.1f} billones")
        with cg:
            _grafico(reserve_chart(dr, res, cubre, (v_gas, v_sal)), 480, leyenda_y=-0.3)
        agot = res["anio_agotamiento"]
        kpi_card_row([
            ("Reserva al 31-dic-2025", f"${reserva0 / 1e12:.1f} billones", "FRP: US$10.091 millones × dólar de cierre $911,18" + (" + activos del FAPP" if res_in.startswith("FRP +") else ""),
             ["Cartera propia del FRP, sin los US$ 200 millones ya transferidos al FAPP", f"Equivale a {res['anios_gasto_2025']:.1f} años del gasto de 2025 del Pilar"]),
            ("Ratio 2: cobertura de reservas (escenario)", f"{100 * res['ratio_cobertura']:.0f}%",
             f"Reserva / valor presente {p.index.min() + 1}-{p.index.max()} del gasto que cubre: ${res['vp_gasto'] / 1e12:.0f} billones (tasa {100 * r_real:.1f}% real)",
             ["100% o más: la reserva alcanza hasta el horizonte", "Alternativa al valor presente oficial del déficit, que no está publicado",
              f"PIB +{crec:.1%} real, PGU $250.000: {'sí' if pgu250 else 'no'}, aporte al FAPP: {'sí' if con_fapp else 'no'} (config/escenarios.yaml)".replace(".", ",")]),
            ("Año en que se agota (escenario)", str(agot) if agot else f"No antes de {p.index.max() + 1}", "Primer año con saldo negativo"),
        ])
        _texto(f"**Lectura:** la reserva equivale a {res['anios_gasto_2025']:.1f} años del gasto del Pilar de 2025; "
                    + (f"cubre {'el alza' if cubre == 'incremento' else 'todo el gasto'} hasta **{agot}** ({100 * res['ratio_cobertura']:.0f}% de su valor presente)." if agot else "alcanza hasta 2050 con estos supuestos."))
        _nota("\\* Estrella: año en que el saldo pasa a negativo. Fondo gris: escenario. Es un ejercicio de cobertura, no un plan de retiros.")
        with st.expander("Sensibilidad a la rentabilidad real (solo FRP, cubre el alza, supuestos de config/escenarios.yaml)"):
            sens = load_csv("kpi_2_2_sensibilidad.csv")
            st.dataframe(pd.DataFrame({
                "Rentabilidad real": [f"{100 * r:.1f}%".replace(".", ",") + (" (base)" if b else "") for r, b in zip(sens.rentabilidad_real, sens.es_base)],
                "VP del gasto cubierto (billones)": sens.vp_gasto_billones.round(1),
                "Cobertura de reservas": [f"{c:.1f}%".replace(".", ",") for c in sens.cobertura_pct],
                "Año en que se agota": [str(int(a)) if pd.notna(a) else "no se agota" for a in sens.anio_agotamiento],
            }), hide_index=True, use_container_width=True)
            _nota("Más rentabilidad baja el valor presente del gasto y sube la cobertura, pero el año de agotamiento casi no se mueve: "
                  "el alza del gasto crece más rápido que lo que rinde la reserva. Lo calcula Scripts/23_kpi_2_2_sensibilidad.py.")

    with t4:
        b6 = fb[fb.cierre == "2026-06-30"].reset_index(drop=True)
        b5 = fb[fb.cierre == "2025-12-31"].iloc[0]
        r6 = b6.iloc[0]
        quema = (r6.beneficios_periodo_mm - r6.cotizaciones_periodo_mm) / 6
        g1, g2 = st.columns([3, 2])
        with g1:
            _grafico(fapp_flow_chart(b6), 420)
        with g2:
            st.metric("Patrimonio del FAPP, 31-dic-2025", es_cl(f"${b5.patrimonio_mm / 1e6:.2f} billones"))
            st.metric("Patrimonio del FAPP, 30-jun-2026", es_cl(f"${num_cl(r6.patrimonio_mm / 1e6, 3)} billones"), help="Activos menos lo que el FAPP debe al FRP")
            st.metric("Cotizaciones / beneficios, ene-jun 2026", es_cl(f"{100 * r6.cotizaciones_periodo_mm / r6.beneficios_periodo_mm:.0f}%"))
        _texto(f"**Lectura:** en ene-jun 2026 las cotizaciones cubrieron {100 * r6.cotizaciones_periodo_mm / r6.beneficios_periodo_mm:.0f}% de los beneficios y el patrimonio quedó en "
                    f"{r6.patrimonio_mm / quema:.1f} meses de ese déficit; quedan hasta US$700 millones autorizados del FRP.")
        _nota("\\* Último dato disponible: 30-jun-2026, seis meses después del resto del KPI. Detalle de la brecha en «Método y fuentes».")

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
            ("Sin pensión propia, 2024", f"{nacr.n_sin_pension / 1000:,.0f} mil", "Beneficiarios de la PGU no contributiva, promedio mensual del 4.º trimestre de 2024"),
            ("PGU: billones de $ al año", f"{nacr.costo_sin_pension / 1e12:.2f}", f"Equivale a {100 * nacr.costo_sin_pension / pib24:.2f}% del PIB de 2024, en pesos de 2025",
             ["Cuota del 4.º trimestre de 2024 de la PGU no contributiva aplicada a la PGU de 2024", "Con la PGU de $250.000 el monto por persona sube"]),
            ("Sin pensión propia, 2035 (escenario)", f"{n35 / 1000:,.0f} mil", f"Con la tasa de cada región de 2024 constante; {n35 / nacr.n_sin_pension:.1f} veces las de 2024",
             ["Supuesto: cada región mantiene su tasa de 2024 (PGU no contributiva por persona 65+)",
              "Población 65+ regional = reparto de tasas nacionales (INE no publica proyección regional base 2024)"]),
            ("Sin pensión propia, 2050 (escenario)", f"{n50 / 1000:,.0f} mil", f"{n50 / nacr.n_sin_pension:.1f} veces las de 2024",
             ["Mismo supuesto que 2035"]),
        ])
        _grafico(dependence_regions_chart(rr, nacr.pct_sin_pension), 520)
        _texto(f"**Lectura:** {nacr.pct_sin_pension:.0f}% de los beneficiarios de la PGU no tiene otra pensión; en {alta.region_nombre} son {alta.pct_sin_pension:.0f}% y en {baja.region_nombre} {baja.pct_sin_pension:.0f}% "
                    f"(correlación {corr:.2f} con los cotizantes por persona 65+).")
        _nota("\\* 4.º trimestre de 2024 con el Censo 2024. Escenario 2035 y 2050: tasa regional de 2024 constante.")

    with st.expander("Método y fuentes"):
        _nota("**Fechas.** Todo se ancla en 2025: Pilar y PIB son flujos de 2025; las reservas son saldos al 31-dic-2025; el retiro del FRP usa el dólar promedio del año y los saldos el dólar del último día hábil "
                   "(30-dic-2025, SII; coincide con el que implica la tabla de activos en dólares de DIPRES). La pestaña «FAPP hoy» usa junio de 2026. Lo regional va con el Censo 2024 (4.º trimestre de 2024).")
        _nota("**Observado y escenario.** 2009-2025: monto nominal pagado del Pilar (incluye invalidez) / PIB corriente del mismo año. Escenario: población 65+ INE base 2024; costo por persona 65+ constante en términos reales "
                   "salvo la PGU de $250.000; invalidez constante en términos reales; el aporte al FAPP está en UTM y se pasa a pesos de 2025 con la UTM promedio de 2025 ($68.640). No incluye el sistema antiguo.")
        _nota("**FAPP, brecha del primer semestre de 2026.** Es transitoria por diseño: según el calendario de DIPRES la cotización al Seguro Social sube de 0,9% a 3,4% de la masa imponible en septiembre de 2026 y llega a 4,0% en septiembre de 2027; el patrimonio es los activos menos lo que el FAPP debe al FRP.")
        _nota("**Reservas.** Cartera propia del FRP (US$ 10.313 M de valor de mercado menos US$ 222 M ya transferidos al FAPP) a la rentabilidad real elegida; cubre el gasto elegido desde 2026. "
                   "Ratio 2 «cobertura de reservas» = reserva / valor presente de ese gasto a la misma tasa (alternativa al valor presente oficial del déficit, no publicado); supuestos en config/escenarios.yaml. El FRP es para pensiones garantizadas; los activos del FAPP son del Seguro Social. No se modelan las reglas de retiro ni de reposición.")
        _nota("**Sensibilidad.** El primer aporte al FAPP es 2028 en la tabla de la Subsecretaría y 2027 en el texto de DIPRES: adelantarlo mueve el agotamiento de 2033 a 2032. "
                   "Usar el dólar promedio en vez del de cierre sube la reserva 4,4% y no cambia el año.")
        _nota("**Fuentes.** FRP: informe mensual de DIPRES (julio 2026). FAPP: estados financieros al 31-dic-2025 y 30-jun-2026. Aporte por ley: Tabla 2 de la Ley 21.735 (Subsecretaría de Previsión Social). "
                   "UTM y dólar: SII. Pilar: informes del Pilar Solidario. Los retiros del FRP de 2020 y 2021 no se desglosan y no se usan. Montos regionales: solo la participación de cada región en el trimestre, aplicada al total anual de 2024.")
    with st.expander("Qué se desprende para cada actor"):
        _recomendaciones_2_2(h, frp, fb, nac)


def _recomendaciones_2_2(h, frp, fb, nac):
    cfg = cargar_escenarios()
    r_base = cfg["rentabilidad_real_reservas"]["base"]
    base = proyeccion_2_2(h, cfg["crecimiento_pib_real"], cfg["pgu_250"], cfg["aporte_fapp"])
    reserva0 = frp.set_index("anio").loc[2025, "cartera_propia_mm"] * 1e6
    dr, res = trayectoria_reserva(base, reserva0, r_base, "incremento")
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
    _texto(
        f"Cifras con los supuestos de partida de config/escenarios.yaml (PIB +{cfg['crecimiento_pib_real']:.0%}, PGU de $250.000, aporte al FAPP, "
        f"reserva = FRP, rentabilidad real {str(round(100 * r_base, 1)).replace('.', ',')}%).\n\n"
        f"**1. AFP (base cotizante).** {pgu_nc:,} personas ({reg[reg.region_id == 0].iloc[0].pct_sin_pension:.0f}% de los beneficiarios de la PGU) no tienen pensión propia y el Estado les paga ${reg[reg.region_id == 0].iloc[0].costo_sin_pension / 1e12:.2f} billones al año; "
        f"en {top.iloc[0].region_nombre} ({top.iloc[0].pct_sin_pension:.0f}%), {top.iloc[1].region_nombre} ({top.iloc[1].pct_sin_pension:.0f}%) y {top.iloc[2].region_nombre} ({top.iloc[2].pct_sin_pension:.0f}%) superan por mucho el {rr.iloc[-1].pct_sin_pension:.0f}% de {rr.iloc[-2].region_nombre} o {rr.iloc[-1].region_nombre}. "
        f"En el escenario con las tasas de hoy serían {n35 / 1000:,.0f} mil personas en 2035 ({n35 / reg[reg.region_id == 0].iloc[0].n_sin_pension:.1f} veces las de 2024). "
        f"*Acción:* campaña de la AFP para independientes y de ahorro previsional voluntario (APV) en esas tres regiones (juntas: {top.n_sin_pension.sum() / 1000:,.0f} mil personas hoy), con la meta de llevar su tasa a la mediana de las regiones ({rr.pct_sin_pension.median():.0f}%) antes de 2035; medirlo cada informe trimestral con este mismo indicador. "
        "Para la AFP es base nueva: más cotizantes hoy y menos personas que llegan a los 65 años sin pensión.\n\n"
        "**Contexto: Estado**\n\n"
        f"**2. Hacienda / DIPRES (planificación fiscal).** El Pilar pasa de {base.pilar_pct_pib.iloc[0]:.2f}% del PIB en 2025 a {base.loc[pico].pilar_pct_pib:.2f}% en {pico}; con el aporte al FAPP la carga llega a {base.loc[2037].carga_pct_pib:.2f}% en 2037. "
        f"El FRP financia solo el {u.pct_frp:.1f}% del gasto del Pilar y, usado para cubrir el alza sobre el peso de 2025, se agota en {res['anio_agotamiento']} (cubre {100 * res['ratio_cobertura']:.0f}% del valor presente de ese alza). "
        f"*Acción:* tener definida antes de {res['anio_agotamiento'] - 3} la fuente permanente (impuestos) para un alza de hasta {(base.carga_pct_pib.max() - base.pilar_pct_pib.iloc[0]):.1f} puntos del PIB (${(base.carga - base.pilar_pct_pib.iloc[0] / 100 * base.pib_real25).max() / 1e12:.1f} billones al año), y no contar el FRP como fuente de régimen.\n\n"
        f"**3. Consejo Directivo del FAPP y Hacienda (administración del FRP).** En enero-junio de 2026 las cotizaciones cubrieron {100 * r6.cotizaciones_periodo_mm / r6.beneficios_periodo_mm:.0f}% de los beneficios; el patrimonio quedó en ${num_cl(r6.patrimonio_mm / 1e6, 3)} billones, {r6.patrimonio_mm / quema:.1f} meses del déficit semestral. "
        "*Acción:* programar los tramos del FRP (hasta US$ 700 millones, de US$ 100 millones cada uno) según el patrimonio mensual, y revisar los estados de julio a septiembre de 2026 (aún no están en este análisis) para confirmar que el déficit se cerró con la tasa de 3,4% (septiembre de 2026); "
        "si el patrimonio vuelve a bajar de 3 meses de déficit antes de septiembre de 2027 (cuando la tasa llega a 4,0%), pedir el siguiente tramo."
    )


UMBRAL_IC_PP = 2.5  # media amplitud del IC 95% (puntos porcentuales) desde la que se avisa que el intervalo es amplio


def render_2_3():
    p = load_csv("pobreza_65_region.csv")
    nac = p[p.region_id == 0].iloc[0]
    reg = p[p.region_id != 0].copy()
    reg["n_pobres"] = reg.pob_65_expandida * reg.pct_pobreza_65 / 100
    mayor, menor = reg.sort_values("pct_pobreza_65").iloc[-1], reg.sort_values("pct_pobreza_65").iloc[0]
    n_pobres, n_extremos = nac.pob_65_expandida * nac.pct_pobreza_65 / 100, nac.pob_65_expandida * nac.pct_pobreza_extrema_65 / 100
    kpi_card_row([
        ("Pobreza en personas 65+ (país)", f"{nac.pct_pobreza_65:.1f}%", f"IC 95%: {nac.ic95_inf:.1f}% a {nac.ic95_sup:.1f}%",
         ["Personas 65+ bajo la línea de pobreza por ingresos", "CASEN 2022, metodología 2024 del Ministerio", "IC 95%: rango probable por ser una encuesta"]),
        ("Personas 65+ en pobreza", f"{n_pobres / 1000:,.0f} mil", f"{n_extremos / 1000:,.0f} mil en pobreza extrema ({nac.pct_pobreza_extrema_65:.1f}%)",
         ["Porcentaje de pobreza × población 65+ expandida de la CASEN 2022", f"Población 65+ de la encuesta: {nac.pob_65_expandida / 1e6:.2f} millones", "Pobreza extrema = ingreso bajo la línea de pobreza extrema"]),
        ("Pobreza en menores de 65 (país)", f"{nac.pct_pobreza_menores_65:.1f}%", "Para comparar: la vejez no es hoy el grupo más pobre",
         ["Mismo indicador para menores de 65", "CASEN 2022"]),
        ("Región con más pobreza 65+", mayor.region_nombre, f"{mayor.pct_pobreza_65:.1f}%",
         ["Pobreza 65+ por región", "Regiones pequeñas tienen intervalos amplios"]),
        ("Región con menos", menor.region_nombre, f"{menor.pct_pobreza_65:.1f}%",
         ["Pobreza 65+ por región", "Regiones pequeñas tienen intervalos amplios"]),
    ])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div style='height:5.2rem'></div>", unsafe_allow_html=True)  # alinea el mapa con las barras (que llevan el selector arriba)
        _grafico(region_choropleth(reg, load_geojson("regiones_chile.geojson"), "pct_pobreza_65", "% de personas 65+ en pobreza", "Oranges"), 520)
    with c2:
        vista_reg = st.radio("Vista por región", ["Porcentaje (relativo)", "Personas (mismo orden)"], horizontal=True, key="s23_vista_region")
        _grafico(poverty_bars(reg, nac.pct_pobreza_65) if vista_reg == "Porcentaje (relativo)" else poverty_people_bars(reg, nac.pct_pobreza_65), 520)
    sobre = reg[reg.ic95_inf > nac.ic95_sup]            # regiones cuyo intervalo queda por encima del intervalo del país
    mas_gente = reg.sort_values("n_pobres").iloc[-1]
    top3 = reg.sort_values("pct_pobreza_65", ascending=False).head(3)
    regiones_top = ", ".join(r.region_nombre for r in top3.itertuples())
    if nac.pct_pobreza_65 < nac.pct_pobreza_menores_65:
        _texto(f"**Lectura:** la pobreza 65+ ({nac.pct_pobreza_65:.1f}%) es menor que la de los menores de 65 ({nac.pct_pobreza_menores_65:.1f}%): la PGU protege. "
               f"Recortarla sin compensación aumentaría la pobreza, sobre todo en {regiones_top}. "
               f"Por número, {mas_gente.region_nombre} reúne más personas ({mas_gente.n_pobres / 1000:,.0f} mil, {100 * mas_gente.n_pobres / n_pobres:.0f}% del total).")
    else:
        _texto(f"**Lectura:** la pobreza 65+ ({nac.pct_pobreza_65:.1f}%) no es menor que la de los menores de 65 ({nac.pct_pobreza_menores_65:.1f}%): la PGU no alcanza "
               f"a proteger a la vejez; las tasas más altas están en {regiones_top}.")
    # intervalos amplios: media amplitud del IC 95% sobre UMBRAL_IC_PP puntos (se determina con los datos)
    amplios = reg[(reg.ic95_sup - reg.ic95_inf) / 2 > UMBRAL_IC_PP].sort_values("pct_pobreza_65", ascending=False)
    if len(amplios):
        _nota(f"\\* Intervalos amplios (± más de {UMBRAL_IC_PP:.1f} pp) en " + ", ".join(amplios.region_nombre)
              + ": lea los rangos, no solo el orden.")

    # --- diagnóstico: pobreza 65+ frente a la cobertura de hoy ---
    _texto("#### ¿Por qué hay más pobreza 65+ en unas regiones?")
    pc = load_csv("kpi_pobreza_cobertura_region.csv")
    rc = load_csv("kpi_cobertura_correlaciones_resumen.csv").set_index("variable").loc["pobreza_65"]
    _grafico(poverty_coverage_scatter(pc, rc.pearson_r, rc.spearman_rho, int(rc.n)), 520)
    _texto(f"**Lectura:** las regiones con menor cobertura tienen más pobreza en la vejez (r = {rc.pearson_r:.2f}, p = {num_cl(rc.pearson_p, 3)}): "
           "la base cotizante de hoy define la presión sobre la PGU de mañana (ver KPI 1.1).")
    _nota(f"Correlación no implica causalidad; n = {int(rc.n)}; CASEN 2022 con IC amplios en regiones pequeñas. Cobertura: cotizantes 2024 / población 15-64 (Censo 2024).")
    with st.expander("Qué se desprende para cada actor"):
        a, b = sobre.sort_values("pct_pobreza_65", ascending=False), reg.sort_values("n_pobres", ascending=False).head(3)
        cob_nac = load_csv("kpi_presion_previsional_region.csv")
        cob_nac = 100 * cob_nac.cotizantes_2024.sum() / cob_nac.pob_15_64.sum()
        foco = pc[(pc.pct_pobreza_65 > nac.pct_pobreza_65) & (pc.cobertura_previsional_pct < cob_nac)].sort_values("pct_pobreza_65", ascending=False)
        _texto(
            f"**1. AFP (base cotizante).** Menor cobertura hoy es más pobreza 65+ mañana (r = {rc.pearson_r:.2f} entre regiones). {len(foco)} regiones tienen a la vez "
            f"pobreza 65+ sobre el país ({nac.pct_pobreza_65:.1f}%) y cobertura bajo el país ({cob_nac:.1f}%): "
            + ", ".join(f"{r.region_nombre} ({r.pct_pobreza_65:.1f}% / {r.cobertura_previsional_pct:.1f}%)" for r in foco.itertuples())
            + ". *Acción:* afiliación en las regiones con alta pobreza 65+ y baja cobertura, con foco en independientes e informales; "
            "cada cotizante nuevo es base comisionable hoy y menos presión sobre la PGU mañana. Entre paréntesis: pobreza 65+ / cobertura.\n\n"
            "**Contexto: Estado**")
        _texto(
            f"**2. Hacienda y la Dipres (costo de las pensiones garantizadas).** Con las pensiones actuales, la pobreza en la vejez ({nac.pct_pobreza_65:.1f}%) queda por debajo de la de los menores de 65 ({nac.pct_pobreza_menores_65:.1f}%), "
            f"pero {n_extremos / 1000:,.0f} mil personas 65+ siguen en pobreza extrema. *Acción:* medir cualquier ahorro en el Pilar (reajuste, focalización) por su efecto sobre esas personas antes de aplicarlo; "
            "este indicador es el contrapeso de los KPIs 2.1 y 2.2.\n\n"
            f"**3. Subsecretaría de Previsión Social y municipios (focalización).** Hay dos criterios distintos: la tasa y el número. Por tasa, {len(a)} regiones superan con claridad al país "
            f"({', '.join(f'{r.region_nombre} {r.pct_pobreza_65:.0f}%' for r in a.itertuples())}: juntas {a.n_pobres.sum() / 1000:,.0f} mil personas); por número, "
            f"{', '.join(f'{r.region_nombre} ({r.n_pobres / 1000:,.0f} mil)' for r in b.itertuples())} suman {b.n_pobres.sum() / 1000:,.0f} mil. "
            "*Acción:* las campañas de acceso a la PGU y al APS por tasa van a las primeras; la atención por volumen a las segundas. Distinto de la acción 2: aquí no se mueve el gasto total, se elige dónde llegar.")
    with st.expander("Método y fuentes"):
        st.caption("**Cifra.** Proporción ponderada de personas 65+ con ingreso bajo la línea de pobreza (extrema o no) en la CASEN 2022 completa; intervalo del 95% con el diseño de la encuesta "
                   "(estratos y conglomerados). «Personas» = porcentaje × población 65+ expandida de la propia encuesta.")
        st.caption("**Fechas.** Todo sale de la misma encuesta (terreno 2022): numerador y denominador comparten período. No se mezcla con el Censo 2024 ni con otros años; "
                   "por eso las personas en pobreza no calzan con la población 65+ del Censo (KPI 1.2).")
        st.caption("**Metodología.** La base ya trae la pobreza con la metodología 2024 del Ministerio: 20,5% en total (6,5% con la anterior) y 14,9% en personas 65+ (2,2% con la anterior). "
                   "No se compara con cifras publicadas en 2023.")
        st.caption("**Falta.** Una serie en el tiempo con la misma metodología (CASEN 2017 y 2020 recalculadas) para ver si la pobreza en la vejez sube o baja; hoy el KPI solo muestra 2022. "
                   "Fuente: CASEN 2022, Ministerio de Desarrollo Social.")


kpi_card("2.1", render_2_1)
kpi_card("2.2", render_2_2)
kpi_card("2.3", render_2_3)


@st.cache_data
def datos_afp():
    """Serie del sistema y cuadros por administradora (Scripts/27) y los insumos de la comisión de equilibrio."""
    por_afp = load_csv("afp_resultados_por_afp.csv")
    d = afe.serie_sistema(load_csv("afp_resultados_sistema.csv"), por_afp)
    ult = int(d.index.max())
    cot = load_csv("cotizantes_por_region.csv")
    cotizantes = float(cot[(cot.region_label == "Total") & (cot.anio == ult)].cotizantes.iloc[0])
    f = load_csv("fichas_previsionales_mensual.csv")
    ingreso = float(f[f.mes_ref_ingreso.str[:4].astype(int) == ult].ingreso_promedio.mean())
    return d, por_afp, cotizantes, ingreso


def render_afp_economia():
    """Costos y economía de las administradoras: el negocio que pierde o gana con la base cotizante (no es costo del Estado)."""
    d, por_afp, cotizantes, ingreso = datos_afp()
    a0, a1 = int(d.index.min()), int(d.index.max())
    u, p0, prev = d.loc[a1], d.loc[a0], d.loc[a1 - 1]
    eq = afe.equilibrio(d, a1, cotizantes, ingreso)
    st.divider()
    st.header("Costos y economía de las administradoras de fondos de pensiones")
    st.markdown("Hasta aquí, el costo del **Estado**. Esta sección mira el negocio de las **administradoras**: lo que cobran (comisiones) y lo que les cuesta "
                "administrar las cuentas. No se mezclan: el Pilar Solidario no pasa por sus resultados.")
    st.caption("🟢 Calculado con datos reales · el escenario de la comisión de equilibrio es un escenario, no un pronóstico")
    kpi_card_row([
        (f"Comisiones {a1}", f"${u.comisiones_mm / 1e6:.2f} billones", f"{u.comision_sobre_ingresos:.1f}% de los ingresos de las administradoras",
         ["Incluye comisiones de cotizantes, pensionados en retiro programado y renta temporal, ahorro voluntario y Cuenta 2", "Millones de pesos del año"]),
        (f"Costos ÷ comisiones {a1}", f"{u.costo_sobre_comision:.1f}%", f"{p0.costo_sobre_comision:.1f}% en {a0}",
         ["Gasto de administración total del sistema ÷ ingresos por comisiones"]),
        (f"Ganancia {a1}", f"${u.ganancia_mm / 1e6:.2f} billones", f"Rentabilidad sobre patrimonio {u.roe_pct:.1f}%",
         ["Después de impuesto", f"Encaje: {u.encaje_sobre_ingresos:.1f}% de los ingresos"]),
        ("Comisión de equilibrio (escenario)", f"{eq['comision_equilibrio_pct']:.2f}% del sueldo", f"Implícita: {eq['comision_implicita_pct']:.2f}%",
         ["Costo por cotizante ÷ sueldo imponible anual", "Promedio del sistema, no costo marginal"]),
    ])
    c1, c2 = st.columns(2)
    with c1:
        mostrar(estilo_kpi(afp_cost_ratio_chart(d), 460))
        subtitulo_visible(f"Qué muestra: cuánto de cada peso de comisión se va en costos de administración. {a0}-{a1}, sistema completo.")
    with c2:
        mostrar(estilo_kpi(afp_waterfall_chart(afe.cascada(d, a1), a1, u.encaje_sobre_ingresos, prev.encaje_sobre_ingresos), 460))
        subtitulo_visible(f"Qué muestra: del ingreso a la ganancia de {a1}, en miles de millones de pesos.")
    real_c = 100 * (u.gastos_mm_2025 / p0.gastos_mm_2025 - 1)
    real_k = 100 * (u.comisiones_mm_2025 / p0.comisiones_mm_2025 - 1)
    sin_enc = 100 * (u.resultado_sin_encaje_mm / prev.resultado_sin_encaje_mm - 1)
    _texto(f"**Lectura:** entre {a0} y {a1}, en pesos de {a1}, los costos subieron {real_c:.1f}% y las comisiones {real_k:.1f}%: la eficiencia no mejora a nivel sistema. "
           f"La ganancia de {a1} sube sobre todo por el encaje ({u.encaje_sobre_ingresos:.1f}% de los ingresos, frente a {prev.encaje_sobre_ingresos:.1f}% en {a1 - 1}); "
           f"sin encaje, el resultado antes de impuesto crece solo {sin_enc:.1f}% nominal. **Para la administradora:** el negocio que se puede gestionar "
           "es comisión menos costo; el encaje no se controla.")
    c3, c4 = st.columns(2)
    with c3:
        mostrar(estilo_kpi(afp_sales_it_chart(d), 460))
        subtitulo_visible("Qué muestra: dos partidas del gasto, medidas contra lo que se cobra.")
    with c4:
        a_comp = max(a for a in por_afp.anio.unique() if a <= a1 - 3)
        mostrar(estilo_kpi(afp_by_firm_chart(afe.por_administradora(por_afp, a_comp, a1), a_comp, a1), 460))
        subtitulo_visible(f"Qué muestra: el costo de cada administradora sobre sus ingresos, {a_comp} y {a1}.")
    _texto("**Lectura:** el gasto se desplaza de la venta a la computación; que sea digitalización no está demostrado con estos datos. Entre administradoras, las que más "
           "crecieron no siempre bajaron su costo (n = 7: no se puede afirmar un efecto de escala).")
    mostrar(estilo_kpi(afp_stress_chart(afe.estres_comision(d, a1), eq["baja_max_pct"], a1), 440))
    subtitulo_visible(f"Qué muestra: escenario de una baja de la comisión con los costos de {a1} fijos. Costo por cotizante: ${eq['costo_por_cotizante']:,.0f} al año; "
                      f"cubrirlo exige {eq['comision_equilibrio_pct']:.2f}% de un sueldo imponible de ${eq['sueldo_mensual']:,.0f} al mes.")
    _texto(f"**Lectura:** hay margen ante la presión de precio de la Ley 21.735 (licitación de stock: cada 24 meses el 10% de los afiliados no pensionados, "
           f"solo pueden postular administradoras con menos de 25% de ellos), pero el margen depende del costo por cuenta: quien tenga un costo por cotizante "
           f"mayor que el promedio (${eq['costo_por_cotizante']:,.0f}) tiene menos espacio para bajar su comisión.")
    _nota(f"\\* Fuente: Superintendencia de Pensiones, «Costos de administración de los Fondos de Pensiones» {a0}-{a1} (estados financieros de las administradoras); "
          f"cotizantes de diciembre y sueldo imponible promedio {a1} (fichas previsionales); Nota Técnica de la Ley 21.735. Millones de pesos de cada año; pesos de {a1} con el IPC anual. "
          "Quiebre de serie 2020/21 (franja gris): no comparar crecimientos que lo crucen.")
    with st.expander("Método y fuentes (costos de las administradoras)"):
        _texto(
            "- **Comisiones:** ingresos por comisiones del sistema; incluyen pensionados en retiro programado y renta temporal, ahorro voluntario y Cuenta 2. Por eso la comisión implícita "
            f"({eq['comision_implicita_pct']:.2f}% del sueldo) está sobreestimada.\n"
            "- **Costos:** gasto total de administración (personal, operación, depreciación y otros). En 2019 y 2021 el total del informe incluye además la prima del seguro de invalidez "
            "y sobrevivencia (~330 millones).\n"
            "- **Venta y computación:** el informe publica el reparto del gasto en % con una decimal; las razones sobre la comisión se derivan de ese reparto.\n"
            "- **Por administradora:** el cuadro N° 1 no separa la comisión, se usan los ingresos ordinarios (incluyen otros ingresos operacionales); costo sin depreciación.\n"
            f"- **Comisión de equilibrio (escenario):** gasto {a1} ÷ cotizantes de diciembre ÷ (12 × sueldo imponible promedio {a1}). Es un costo promedio: el costo de un cotizante adicional es menor.\n"
            "- **Falta:** comisiones vigentes por administradora y cotizantes por administradora (costo por cuenta y cuota de mercado). Hallazgos: docs/COSTOS_AFP_HALLAZGOS.md.")


render_afp_economia()

st.info("**Mensaje clave:** el costo por adulto mayor está controlado, pero el número de adultos mayores no: la carga fiscal sube con "
        "reservas mínimas y sin margen para recortar sin aumentar la pobreza. La salida sostenible es ampliar la base cotizante, justo "
        "donde la AFP puede crecer.")
