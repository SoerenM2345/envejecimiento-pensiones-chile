"""Objetivo 1: retener y ampliar la base activa. KPIs 1.1, 1.2, 1.3."""
import numpy as np
import pandas as pd
import streamlit as st
from utils import load_csv, load_geojson, kpi_card_row, BLUE, ORANGE, PLOTLY_DL_CONFIG
from components.kpi_card import kpi_card
from components.charts import (region_choropleth, region_bars, support_ratio_projection, commissionable_flow_bars,
                               commissionable_share_line, critical_point_chart, region_support_people_bars,
                               coverage_correlation_scatter, coverage_risk_matrix, risk_quadrant, num_cl, CUADRANTES)
from components import critical_point as cp

st.title("Objetivo 1: retener y ampliar la base activa")
st.markdown("Aumentar y retener la base de cotizantes activos por región, para sostener el ingreso por comisión pese al envejecimiento.")

pres = load_csv("kpi_presion_previsional_region.csv")
nac_cobertura = 100 * pres["cotizantes_2024"].sum() / pres["pob_15_64"].sum()
nac_soporte = pres["cotizantes_2024"].sum() / pres["pob_65_mas"].sum()


def render_1_1():
    kpi_card_row([
        ("Cobertura nacional", f"{nac_cobertura:.1f}%", "Cotizantes 2024 / población 15-64 (Censo 2024)",
         ["Cotizantes: personas con cotización pagada en AFP, diciembre", "Población 15-64: Censo 2024",
          "Cobertura = cotizantes ÷ población 15-64", "Quedan fuera los cotizantes sin región informada"]),
        ("Región con mayor cobertura", pres.sort_values("cobertura_previsional_pct").iloc[-1]["region_nombre"],
         f"{pres['cobertura_previsional_pct'].max():.1f}%",
         ["Misma cobertura, calculada por región", "Se compara con el promedio del país"]),
        ("Región con menor cobertura", pres.sort_values("cobertura_previsional_pct").iloc[0]["region_nombre"],
         f"{pres['cobertura_previsional_pct'].min():.1f}%",
         ["Misma cobertura, calculada por región", "Se compara con el promedio del país"]),
    ])
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(region_choropleth(pres, load_geojson("regiones_chile.geojson"), "cobertura_previsional_pct",
                                          "Cobertura previsional (%)"), use_container_width=True, config=PLOTLY_DL_CONFIG)
    with c2:
        st.plotly_chart(region_bars(pres, "cobertura_previsional_pct", "Cobertura previsional (% de 15-64 que cotiza)",
                                    nac_cobertura, ".1f", ORANGE), use_container_width=True, config=PLOTLY_DL_CONFIG)
    render_1_1_correlaciones()
    render_1_1_matriz()
    st.caption("Correlación no implica causalidad; n = 16 regiones. Ingreso de CASEN 2022 (encuesta muestral). "
               "Cotizantes 2024 vs. Censo 2024.")


# variable -> (etiqueta, unidad, nombre en el resumen de correlaciones)
VARS_COBERTURA = {
    "ingreso_per_capita_prom": ("Ingreso per cápita", "CASEN 2022, $ mensuales", "ingreso"),
    "pct_pobreza_65": ("Pobreza 65+", "% de personas 65+, CASEN 2022", "pobreza_65"),
    "pct_urbano": ("Población urbana", "% del total, Censo 2024", "urbano"),
    "pct_65_mas": ("Población 65+", "% del total, Censo 2024", "pct_65_mas"),
}


def _fuerza(r: float) -> str:
    return "fuerte" if abs(r) >= 0.7 else "moderada" if abs(r) >= 0.4 else "débil"


def render_1_1_correlaciones():
    st.markdown("#### ¿Por qué cotizan más en unas regiones?")
    reg = load_csv("kpi_cobertura_correlaciones_region.csv")
    res = load_csv("kpi_cobertura_correlaciones_resumen.csv").set_index("variable")
    var = st.radio("Variable del eje x", list(VARS_COBERTURA), horizontal=True, key="cob_var_x",
                   format_func=lambda v: VARS_COBERTURA[v][0])
    etiqueta, unidad, clave = VARS_COBERTURA[var]
    corr = res.loc[clave]
    st.plotly_chart(coverage_correlation_scatter(reg, var, etiqueta, unidad, corr), use_container_width=True,
                    config=PLOTLY_DL_CONFIG, theme=None)

    # interpretación generada de los datos: dirección, fuerza, significancia y la región más lejos de la recta
    pendiente, intercepto = np.polyfit(reg[var], reg.cobertura_previsional_pct, 1)
    residuo = reg.cobertura_previsional_pct - (intercepto + pendiente * reg[var])
    arriba, abajo = reg.loc[residuo.idxmax()], reg.loc[residuo.idxmin()]
    signif = "estadísticamente significativa" if corr.pearson_p < 0.05 else "no significativa al 5%"
    st.markdown(
        f"Las regiones con mayor {etiqueta.lower()} tienen **{'mayor' if corr.pearson_r > 0 else 'menor'} cobertura** "
        f"(r = {num_cl(corr.pearson_r)}, relación {_fuerza(corr.pearson_r)} y {signif}, p = {num_cl(corr.pearson_p, 3)}). "
        f"Más por sobre lo esperado está {arriba.region_nombre} ({num_cl(residuo.max(), 1)} pp); "
        f"más por debajo, {abajo.region_nombre} ({num_cl(residuo.min(), 1)} pp)."
    )
    tabla = pd.DataFrame([{
        "Variable": VARS_COBERTURA[v][0],
        "r de Pearson": num_cl(res.loc[VARS_COBERTURA[v][2], "pearson_r"]),
        "p (Pearson)": num_cl(res.loc[VARS_COBERTURA[v][2], "pearson_p"], 3),
        "ρ de Spearman": num_cl(res.loc[VARS_COBERTURA[v][2], "spearman_rho"]),
        "p (Spearman)": num_cl(res.loc[VARS_COBERTURA[v][2], "spearman_p"], 3),
    } for v in VARS_COBERTURA])
    st.dataframe(tabla, hide_index=True, use_container_width=True)


def render_1_1_matriz():
    st.markdown("#### Matriz de riesgo: cobertura × envejecimiento")
    reg = load_csv("kpi_cobertura_correlaciones_region.csv")
    ind = load_csv("indicadores_region.csv")
    nac_65 = 100 * ind.pob_65_mas.sum() / ind.pob_total.sum()
    st.plotly_chart(coverage_risk_matrix(reg, nac_cobertura, nac_65), use_container_width=True,
                    config=PLOTLY_DL_CONFIG, theme=None)
    reg = reg.assign(cuadrante=risk_quadrant(reg, nac_cobertura, nac_65))
    cols = st.columns(4)
    for col, (nombre, _) in zip(cols, CUADRANTES.values()):
        regiones = reg[reg.cuadrante == nombre].sort_values("cotizantes", ascending=False)
        with col:
            st.markdown(f"**{nombre}** ({len(regiones)})")
            st.markdown("\n".join(f"- {r.region_nombre} ({num_cl(r.cobertura_previsional_pct, 1)}% / "
                                  f"{num_cl(r.pct_65_mas, 1)}%)" for r in regiones.itertuples()) or "—")
    doble = reg[reg.cuadrante == "Riesgo doble"]
    share_doble = doble.share_cotizantes_pct.sum()
    st.markdown(
        f"Cortes en los valores del país (cobertura {num_cl(nac_cobertura, 1)}%, 65+ {num_cl(nac_65, 1)}%). "
        f"**{len(doble)} regiones** combinan baja cobertura y alto envejecimiento; juntas reúnen el "
        f"{num_cl(share_doble, 1)}% de los cotizantes. Entre paréntesis: cobertura / % 65+."
    )


@st.cache_data
def pc_serie(territorio: str, region_id: int, comuna_code: int, esc: cp.Escenario):
    """Serie del análisis del punto crítico para el país, una región o una comuna (aproximación) y su punto crítico."""
    params = load_csv("kpi_pc_parametros_reforma.csv")
    if territorio == "pais":
        d = cp.serie_pais(load_csv("kpi_pc_nacional.csv"), load_csv("proyeccion_envejecimiento_pais.csv"), params, esc)
    else:
        dt = cp.datos_territorio(region_id, load_csv("kpi_pc_region.csv"), load_csv("kpi_pc_nacional.csv"),
                                 load_csv("indicadores_region.csv"), load_csv("kpi_proyeccion_regional.csv"))
        if territorio == "comuna":
            c = load_csv("indicadores_comuna.csv")
            c = c[c.comuna == comuna_code].iloc[0]
            dt = cp.comuna_desde_region(dt, float(c.pob_65_mas), float(c.pob_15_64))
        d = cp.serie_territorio(dt, params, esc)
    return d, cp.punto_critico(d)


def pc_lectura(d: pd.DataFrame, pc: dict, esc: cp.Escenario, nombre: str, a0: int, trab: str) -> str:
    """Frase de lectura del gráfico, calculada con los datos que se están viendo."""
    f0, f1 = cp.fila_anio(d, a0), cp.fila_anio(d, d.anio.max() if d.anio.max() <= 2050 else 2050)
    txt = (f"**Lectura:** en {a0}, financiar el Pilar Solidario de vejez en {nombre} equivale a **{f0.carga_requerida:.1%} del sueldo** "
           f"de los {trab} ({f0.razon_soporte:.2f} {trab} por persona de 65+; el equilibrio con una carga de {esc.carga_max:.0%} "
           f"estaría en {f0.razon_equilibrio:.2f}). En {int(f1.anio)} la carga sube a **{f1.carga_requerida:.1%}** "
           f"({f1.razon_soporte:.2f} por persona de 65+). ")
    if pc["estado"] == "cruza":
        txt += f"Con un máximo tolerable de {esc.carga_max:.0%}, el costo supera la capacidad de pago desde **{pc['anio']}**."
    elif pc["estado"] == "ya_superado":
        txt += f"Con un máximo tolerable de {esc.carga_max:.0%}, el costo ya supera la capacidad de pago desde el inicio de la serie."
    else:
        txt += f"Con un máximo tolerable de {esc.carga_max:.0%}, la capacidad de pago alcanza para cubrir el costo en todo el período."
    return txt


@st.cache_data
def pc_tabla_comunas(region_id: int, esc: cp.Escenario) -> pd.DataFrame:
    """Cifras de todas las comunas de una región (aproximación: heredan cobertura, ingreso y costo por 65+ de su región)."""
    params = load_csv("kpi_pc_parametros_reforma.csv")
    dt = cp.datos_territorio(region_id, load_csv("kpi_pc_region.csv"), load_csv("kpi_pc_nacional.csv"),
                             load_csv("indicadores_region.csv"), load_csv("kpi_proyeccion_regional.csv"))
    com = load_csv("indicadores_comuna.csv")
    filas = []
    for c in com[com.region == region_id].itertuples():
        d = cp.serie_territorio(cp.comuna_desde_region(dt, float(c.pob_65_mas), float(c.pob_15_64)), params, esc)
        pc = cp.punto_critico(d)
        f0, f1 = cp.fila_anio(d, cp.ANIO_BASE_REGION), cp.fila_anio(d, 2050)
        filas.append({"Comuna": c.comuna_nombre, "Personas 65+ (Censo 2024)": int(round(f0.pob_65)), "Trabajadores (aprox.)": int(round(f0.trabajadores)),
                      "Razón de soporte 2024": round(f0.razon_soporte, 2), "Carga requerida 2024 (%)": round(100 * f0.carga_requerida, 1),
                      "Carga requerida 2050 (%)": round(100 * f1.carga_requerida, 1),
                      "Punto crítico": str(pc["anio"]) if pc["estado"] == "cruza" else ("ya superado" if pc["estado"] == "ya_superado" else "no antes de 2050")})
    return pd.DataFrame(filas).sort_values("Razón de soporte 2024").reset_index(drop=True)


def render_1_2_punto_critico():
    st.divider()
    st.markdown("#### ¿Dónde está el punto crítico?")
    st.markdown(
        "Se superponen dos masas de dinero, año a año y en pesos de 2025: el **costo** (costo del Pilar Solidario de vejez por "
        "persona de 65+ × población de 65+) y la **capacidad** (carga máxima tolerable × ingreso por trabajador × trabajadores). "
        "Donde las líneas se cruzan está el punto crítico: ahí la razón de soporte cae bajo la razón de equilibrio R\\*.")
    reg_ids = pres.set_index("region_nombre")["region_id"].astype(int).to_dict()
    c1, c2 = st.columns(2)
    sel = c1.selectbox("Territorio", ["País"] + sorted(reg_ids), key="pc_territorio")
    comuna_code, comuna_nombre = 0, None
    if sel != "País":
        com = load_csv("indicadores_comuna.csv")
        com = com[com.region == reg_ids[sel]].sort_values("comuna_nombre")
        opts = {"Toda la región": 0, **dict(zip(com.comuna_nombre, com.comuna.astype(int)))}
        comuna_nombre = c2.selectbox("Comuna (aproximación)", list(opts), key="pc_comuna",
                                     help="No hay cotizantes, sueldos ni gasto por comuna: la comuna hereda de su región la cobertura, "
                                          "el ingreso y el costo por persona de 65+; solo su estructura de edad (Censo 2024) es propia.")
        comuna_code = opts[comuna_nombre]

    t1, t2, t3 = st.columns(3)
    base = t1.radio("Base de ingreso", ["Cotizantes", "Todos los ocupados"], horizontal=True, key="pc_base",
                    help="Cotizantes: ingreso imponible (Superintendencia de Pensiones) de quienes aportan hoy. "
                         "Todos los ocupados: ingreso de la Encuesta Suplementaria de Ingresos (INE), como si todos cotizaran.")
    est = t2.radio("Estadístico", ["Promedio", "Mediana"], horizontal=True, key="pc_estadistico")
    vista = t3.radio("Vista", ["Dinero", "Razón de soporte"], horizontal=True, key="pc_vista")

    s1, s2, s3, s4 = st.columns(4)
    carga = s1.slider("Carga máxima tolerable (% del sueldo)", 3.0, 20.0, 10.0, 0.5, key="pc_carga",
                      help="Parte del sueldo que se considera tolerable destinar a financiar el Pilar Solidario. "
                           "10 % = la cotización obligatoria para pensión.") / 100
    crec = s2.slider("Crecimiento real del sueldo (% anual)", -1.0, 3.0, 1.0, 0.5, key="pc_crec") / 100
    cobertura = s3.slider("Cotizantes / población 15-64 en 2050 (hoy = 100)", 70, 130, 100, 5, key="pc_cobertura",
                          disabled=base != "Cotizantes", help="Solo aplica a la base de cotizantes (formalización).") / 100
    pgu = s4.checkbox("Incluir PGU de $250.000 (Ley 21.735)", value=True, key="pc_pgu")

    esc = cp.Escenario(base="A" if base == "Cotizantes" else "B", estadistico="promedio" if est == "Promedio" else "mediana",
                       crec_salarial=crec, carga_max=carga, cobertura_2050=cobertura, pgu_250=pgu)
    if sel == "País":
        d, pc = pc_serie("pais", 0, 0, esc)
        nombre, a0 = "Chile", cp.ANIO_BASE_REGION  # el año del Censo, igual que la razón de arriba
    else:
        d, pc = pc_serie("comuna" if comuna_code else "region", reg_ids[sel], comuna_code, esc)
        nombre, a0 = (f"{comuna_nombre} ({sel})" if comuna_code else sel), cp.ANIO_BASE_REGION
    trab = cp.NOMBRE_TRABAJADORES[esc.base]

    f0 = cp.fila_anio(d, a0)
    f1 = cp.fila_anio(d, 2050)
    if pc["estado"] == "cruza":
        pc_txt = str(pc["anio"])
    elif pc["estado"] == "ya_superado":
        pc_txt = f"ya superado ({pc['anio']})"
    else:
        pc_txt = f"no antes de {int(d.anio.max())}"
    kpi_card_row([
        ("Punto crítico", pc_txt, f"Primer año desde el cual el costo supera la capacidad (carga máxima {carga:.0%})",
         ["Costo: PGU + PBS/APS de vejez, por persona 65+ × población 65+", "Capacidad: carga máxima × ingreso por trabajador × trabajadores",
          "Punto crítico: primer año en que el costo supera la capacidad", "Pesos reales de 2025"]),
        (f"Carga requerida {a0}", f"{f0.carga_requerida:.1%}", "Costo del Pilar Solidario de vejez / masa de ingreso de los trabajadores",
         ["Costo: PGU + PBS/APS de vejez", "Masa de ingreso: trabajadores × ingreso anual", "Compara con la carga máxima tolerable (10% = cotización obligatoria)"]),
        ("Carga requerida 2050", f"{f1.carga_requerida:.1%}", "Mismo cálculo en el escenario",
         ["Población: Censo 2024 (país: dinámica INE llevada al nivel del Censo)", "Ingreso real crece según el escenario elegido", "PGU de $250.000 si está marcada"]),
        (f"{trab.capitalize()} por 65+ ({a0})", f"{f0.razon_soporte:.2f}", f"Razón de equilibrio R*: {f0.razon_equilibrio:.2f}",
         ["Trabajadores ÷ población 65+", "R*: trabajadores por persona 65+ que cubren el costo con la carga máxima",
          "Si el valor baja de R*, el costo supera la capacidad"]),
    ])
    st.plotly_chart(critical_point_chart(d, pc, "dinero" if vista == "Dinero" else "razon", nombre, trab, carga),
                    use_container_width=True, config=PLOTLY_DL_CONFIG)
    st.markdown(pc_lectura(d, pc, esc, nombre, a0, trab))
    nac_pc = load_csv("kpi_pc_nacional.csv").set_index("anio")
    ajuste_pais = (f"País: población con la dinámica de las proyecciones INE llevada al nivel del Censo 2024 (65+ × {nac_pc.loc[2024, 'factor_censo_65']:.3f}, "
                   f"15-64 × {nac_pc.loc[2024, 'factor_censo_15_64']:.3f}; el INE corrige el subconteo del censo, ver docs/DISCUSION_FUENTES.md). "
                   "El país incluye los cotizantes sin región, por eso difiere ~1 % de la suma de las regiones. ")
    st.caption(
        "Línea sólida = datos observados, punteada = escenario; ◆ = 2024, 2035 y 2050, los años con población regional "
        "(Censo 2024 y escenarios regionales); ★ = punto crítico. Se usan datos del mismo año: " + ("país 2024 (el año del Censo; la serie observada llega a 2025): cotizantes e ingreso imponible de diciembre, "
                                           "ocupados octubre-diciembre y gasto del año. " + ajuste_pais if sel == "País" else
                                           "región 2024 (Censo 2024, cotizantes e ingreso imponible de diciembre 2024, ESI 2024 y gasto 2024) "
                                           "y escenarios regionales 2035 y 2050 (rombos); los años intermedios se interpolan. ")
        + "El costo por persona de 65+ es PGU + APS/PBS de vejez, constante en términos reales (la PGU se reajusta por IPC). "
          "La mediana de los cotizantes se calcula desde los tramos de ingreso imponible; la regional se estima con la nacional.")
    if sel != "País":
        with st.expander(f"Cifras de todas las comunas de {sel} (aproximación, con los supuestos de arriba)"):
            tabla = pc_tabla_comunas(reg_ids[sel], esc)
            st.dataframe(tabla, hide_index=True, use_container_width=True)
            st.caption("Cada comuna hereda de su región la cobertura (trabajadores / población 15-64), el ingreso por trabajador y el costo por persona "
                       "de 65+; solo su población por edad (Censo 2024) es propia, así que la razón de soporte mide su estructura de edad, "
                       "no sus cotizantes reales. Ordenadas de mayor a menor presión.")


def render_1_2():
    kpi_card_row([
        ("Cotizantes por adulto mayor (país)", f"{nac_soporte:.2f}", "Cotizantes 2024 / población 65+ (Censo 2024)",
         ["Cotizantes de diciembre (Superintendencia de Pensiones)", "Población 65+: Censo 2024", "Más alto = más cotizantes por cada adulto mayor"]),
        ("Región más presionada", pres.sort_values("razon_soporte_previsional").iloc[0]["region_nombre"],
         f"{pres['razon_soporte_previsional'].min():.2f}", ["Menos cotizantes por adulto mayor entre las 16 regiones"]),
        ("Región menos presionada", pres.sort_values("razon_soporte_previsional").iloc[-1]["region_nombre"],
         f"{pres['razon_soporte_previsional'].max():.2f}", ["Más cotizantes por adulto mayor entre las 16 regiones"]),
    ])
    vista_reg = st.radio("Vista por región", ["Razón (relativa)", "Personas (mismo orden)"], horizontal=True, key="s12_vista_region",
                         help="Razón: cotizantes por adulto mayor. Personas: mismo orden de regiones, con los cotizantes y las "
                              "personas de 65+ en números absolutos y la razón escrita junto a cada región.")
    if vista_reg == "Razón (relativa)":
        fig_reg = region_bars(pres, "razon_soporte_previsional", "Razón de soporte: cotizantes por adulto mayor",
                              nac_soporte, ".2f", BLUE)
    else:
        fig_reg = region_support_people_bars(pres, nac_soporte)
    st.plotly_chart(fig_reg, use_container_width=True, config=PLOTLY_DL_CONFIG)

    st.markdown("**Escenario 2035 / 2050 (cobertura previsional 2024 constante)**")
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
        # (cobertura con cotizantes de diciembre de 2024, el mismo año del Censo y de la razón actual)
        filas = pd.DataFrame({"anio": r.anio, "razon": fila.cobertura_previsional_pct / r.indice_dependencia_vejez_proy})
        fig = support_ratio_projection(fila.razon_soporte_previsional, filas, sel)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DL_CONFIG)
    render_1_2_punto_critico()


def render_1_3():
    flujo = load_csv("kpi_flujo_comisionable.csv")
    real = flujo[flujo.tipo == "real"].sort_values("anio")
    esc = flujo[flujo.tipo == "escenario"].set_index("anio")
    r25 = real.iloc[-1]
    a_meta = 2033
    e33 = esc.loc[a_meta]
    minimo = esc.kpi_1_3_pct.idxmin()
    kpi_card_row([
        (f"Flujo comisionable {int(r25.anio)} (real)", f"{r25.kpi_1_3_pct:.1f}%", "Cuentas individuales / flujo total",
         ["Cuentas individuales: cotización del trabajador (10%) + empleador a cuenta individual", "Flujo total: cuentas individuales + Seguro Social (FAPP) + Estado (PGU, PBS, APS)",
          "Aporte del trabajador estimado con ingreso imponible promedio"]),
        (f"Flujo comisionable {a_meta} (escenario)", f"{e33.kpi_1_3_pct:.1f}%", "Cotización del empleador completa (8,5%)",
         ["Escenario de la Ley 21.735 con la cotización del empleador completa", "División empleador: cuenta individual vs Seguro Social según la Nota Técnica", "Es escenario, no pronóstico"]),
        (f"Variación {int(r25.anio)}-{a_meta}", f"{e33.kpi_1_3_pct - r25.kpi_1_3_pct:+.1f} pp",
         f"Mínimo del escenario: {esc.kpi_1_3_pct.min():.1f}% en {minimo}",
         ["pp = puntos porcentuales", "Diferencia entre el escenario y el dato real"]),
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
