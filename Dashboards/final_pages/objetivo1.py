"""Objetivo 1: retener y ampliar la base activa. KPIs 1.1, 1.2, 1.3."""
import pandas as pd
import streamlit as st
from utils import load_csv, load_geojson, kpi_card_row, BLUE, ORANGE, PLOTLY_DL_CONFIG
from components.kpi_card import kpi_card
from components.charts import (region_choropleth, region_bars, support_ratio_projection, commissionable_flow_bars,
                               commissionable_share_line, critical_point_chart)
from components import critical_point as cp

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
        nombre, a0 = "Chile", cp.ANIO_BASE_PAIS
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
        ("Punto crítico", pc_txt, f"Primer año desde el cual el costo supera la capacidad (carga máxima {carga:.0%})"),
        (f"Carga requerida {a0}", f"{f0.carga_requerida:.1%}", "Costo del Pilar Solidario de vejez / masa de ingreso de los trabajadores"),
        ("Carga requerida 2050", f"{f1.carga_requerida:.1%}", "Mismo cálculo en el escenario"),
        (f"{trab.capitalize()} por 65+ ({a0})", f"{f0.razon_soporte:.2f}", f"Razón de equilibrio R*: {f0.razon_equilibrio:.2f}"),
    ])
    st.plotly_chart(critical_point_chart(d, pc, "dinero" if vista == "Dinero" else "razon", nombre, trab, carga),
                    use_container_width=True, config=PLOTLY_DL_CONFIG)
    st.markdown(pc_lectura(d, pc, esc, nombre, a0, trab))
    st.caption(
        "Línea sólida = datos observados, punteada = escenario; ◆ = 2024, 2035 y 2050, los años con población regional "
        "(Censo 2024 y escenarios regionales); ★ = punto crítico. Se usan datos del mismo año: " + ("país 2025 (cotizantes de diciembre, ingreso imponible de diciembre, ocupados octubre-diciembre, "
                                           "gasto del año y población 65+ y 15-64 de las proyecciones INE). " if sel == "País" else
                                           "región 2024 (Censo 2024, cotizantes e ingreso imponible de diciembre 2024, ESI 2024 y gasto 2024) "
                                           "y escenarios regionales 2035 y 2050 (rombos); los años intermedios se interpolan. ")
        + "El costo por persona de 65+ es PGU + APS/PBS de vejez, constante en términos reales (la PGU se reajusta por IPC). "
          "La mediana de los cotizantes se calcula desde los tramos de ingreso imponible; la regional se estima con la nacional.")


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
