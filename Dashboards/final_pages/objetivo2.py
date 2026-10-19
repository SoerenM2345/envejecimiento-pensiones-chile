"""Objetivo 2: anticipar la presión fiscal del envejecimiento. KPIs 2.1, 2.2 y 2.3."""
import pandas as pd
import streamlit as st
from utils import cargar_escenarios, es_cl, load_csv, load_geojson, kpi_card_row, PLOTLY_DL_CONFIG
from components.kpi_card import kpi_card
from components.cost_analysis import serie_historica, proyeccion
from components.financiamiento import peso_historico, proyeccion_carga, trayectoria_reserva, fuentes_pilar, dependencia_regional, proyeccion_sin_pension
from components.charts import mostrar, cost_components_chart, beneficiaries_chart, cost_projection_chart, cost_per_person_chart, spending_vs_population_growth, spending_pct_pib, poverty_bars, poverty_people_bars, region_choropleth
from components.charts import num_cl, estilo_kpi, poverty_coverage_scatter, fiscal_weight_chart, financing_sources_chart, reserve_chart, fapp_flow_chart, fapp_schedule_chart, dependence_regions_chart

TITULO_OBJETIVO_2 = "Objetivo 2: anticipar la presión fiscal del envejecimiento"  # igual que config/kpis.yaml e Inicio.py
st.title(TITULO_OBJETIVO_2)
st.markdown("La carga del envejecimiento sobre el Estado crece y sus reservas son mínimas: eso genera presión para desviar cotizaciones "
            "de las cuentas individuales (KPI 1.3). Medimos cuánto cuesta, quién lo financia y dónde está el límite social.")


from components.charts import estilo_kpi as _estilo_2_1, cost_pct_pibpc_chart, burden_chart

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
    t1, t2, t3, t4, t5, t6 = st.tabs(["Evolución", "Qué lo explica", "Por beneficiario", "Frente al ingreso", "Proyección 2050", "Qué hacer"])
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            _g21(cost_per_person_chart(h.reset_index(), ANIO_PGU, "PGU"))
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

st.info("**Mensaje clave:** el costo por adulto mayor está controlado, pero el número de adultos mayores no: la carga fiscal sube con "
        "reservas mínimas y sin margen para recortar sin aumentar la pobreza. La salida sostenible es ampliar la base cotizante, justo "
        "donde la AFP puede crecer.")
