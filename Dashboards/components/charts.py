"""Constructores de figuras compartidos por las páginas del modo final.
Cada función recibe DataFrames ya cargados (no lee archivos) y devuelve un go.Figure."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import (BLUE, ORANGE, VIOLET, RED, INK_PRIMARY, INK_MUTED, GRIDLINE, SURFACE, PLOTLY_LAYOUT,
                   CATEGORICAL, lighten)

UMBRAL_VEJEZ = 65
ANIO_BASE = 2024  # último año estimado de las proyecciones INE base 2024


def pyramid_chile(censo_pais: pd.DataFrame) -> go.Figure:
    """Pirámide de Chile, Censo 2024 (edad simple, 85+ agrupado). Miles de personas; tonos sólidos = 65+."""
    h = censo_pais[censo_pais.sexo == 1].set_index("edad")["poblacion"].sort_index()
    m = censo_pais[censo_pais.sexo == 2].set_index("edad")["poblacion"].sort_index()
    fig = go.Figure()
    fig.add_bar(y=h.index, x=-h.values / 1000, orientation="h", name="Hombres",
                marker_color=[lighten(BLUE) if e < UMBRAL_VEJEZ else BLUE for e in h.index])
    fig.add_bar(y=m.index, x=m.values / 1000, orientation="h", name="Mujeres",
                marker_color=[lighten(ORANGE) if e < UMBRAL_VEJEZ else ORANGE for e in m.index])
    fig.add_hline(y=UMBRAL_VEJEZ, line_color=RED, line_width=1.5, line_dash="dot")
    xmax = max(h.max(), m.max()) / 1000 * 1.1
    fig.update_layout(**PLOTLY_LAYOUT, barmode="overlay", height=520,
                      title="Pirámide poblacional de Chile, Censo 2024 (miles de personas)")
    fig.update_xaxes(range=[-xmax, xmax], zeroline=True, zerolinecolor=INK_MUTED, title="Miles de personas")
    fig.update_yaxes(title="Edad (85 = 85 y más)")
    return fig


def pyramid_chile_vs_alemania(censo_pais: pd.DataFrame, alemania: pd.DataFrame) -> go.Figure:
    """Pirámides lado a lado, eje en % de la población total de cada país. Sombra clara < 65, sólida 65+."""
    def pct(df_h, df_m):
        tot = df_h.sum() + df_m.sum()
        return 100 * df_h / tot, 100 * df_m / tot

    ch = censo_pais[censo_pais.sexo == 1].set_index("edad")["poblacion"].sort_index()
    cm = censo_pais[censo_pais.sexo == 2].set_index("edad")["poblacion"].sort_index()
    a = alemania[alemania.anio == 2024]
    ah = a[a.sexo == "H"].set_index("edad")["poblacion"].sort_index()
    am = a[a.sexo == "M"].set_index("edad")["poblacion"].sort_index()

    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.04,
                        subplot_titles=("Chile (Censo 2024)", "Alemania (Destatis, 2024)"))
    xmax = 0
    for col, (h, m) in enumerate([(ch, cm), (ah, am)], start=1):
        hp, mp = pct(h, m)
        xmax = max(xmax, hp.max(), mp.max())
        fig.add_bar(y=hp.index, x=-hp.values, orientation="h", name="Hombres", legendgroup="H", showlegend=col == 1,
                    marker_color=[lighten(BLUE) if e < UMBRAL_VEJEZ else BLUE for e in hp.index], row=1, col=col)
        fig.add_bar(y=mp.index, x=mp.values, orientation="h", name="Mujeres", legendgroup="M", showlegend=col == 1,
                    marker_color=[lighten(ORANGE) if e < UMBRAL_VEJEZ else ORANGE for e in mp.index], row=1, col=col)
        fig.add_hline(y=UMBRAL_VEJEZ, line_color=RED, line_width=1.2, line_dash="dot", row=1, col=col)
    fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=10, r=10, t=70, b=10)}, barmode="overlay", height=520,
                      title="Pirámide poblacional 2024: Chile vs. Alemania (% de la población total)")
    fig.update_xaxes(range=[-xmax * 1.1, xmax * 1.1], zeroline=True, zerolinecolor=INK_MUTED, title="% de la población")
    fig.update_yaxes(title_text="Edad", col=1)
    return fig


def age_group_shares(indicadores_region: pd.DataFrame) -> dict:
    """% 0-14, 15-64, 65+ del país (suma de regiones, Censo 2024)."""
    tot = indicadores_region["pob_total"].sum()
    return {
        "pct_0_14": 100 * indicadores_region["pob_0_14"].sum() / tot,
        "pct_15_64": 100 * indicadores_region["pob_15_64"].sum() / tot,
        "pct_65_mas": 100 * indicadores_region["pob_65_mas"].sum() / tot,
    }


def aging_share_series(proy: pd.DataFrame) -> go.Figure:
    """% población 65+ 1992-2070 (sólido hasta 2024, punteado proyectado) con hitos 2024 / 2050 / 2070."""
    est = proy[proy.anio <= ANIO_BASE]
    fut = proy[proy.anio >= ANIO_BASE]
    fig = go.Figure()
    fig.add_scatter(x=est.anio, y=est.pct_65_mas, mode="lines", name="Estimado", line=dict(color=VIOLET, width=3))
    fig.add_scatter(x=fut.anio, y=fut.pct_65_mas, mode="lines", name="Proyección INE",
                    line=dict(color=VIOLET, width=3, dash="dash"))
    for anio in (ANIO_BASE, 2050, 2070):
        v = float(proy.loc[proy.anio == anio, "pct_65_mas"].iloc[0])
        fig.add_scatter(x=[anio], y=[v], mode="markers+text", text=[f"{v:.0f}%"], textposition="top center",
                        marker=dict(size=9, color=RED if anio == ANIO_BASE else VIOLET), showlegend=False,
                        hovertemplate=f"{anio}: {v:.1f}%<extra></extra>")
    fig.update_layout(**PLOTLY_LAYOUT, title="Evolución y proyección del envejecimiento en Chile, 1992-2070")
    fig.update_xaxes(title="Año")
    fig.update_yaxes(title="% de la población de 65 años o más")
    return fig


def working_age_peak(proy: pd.DataFrame) -> go.Figure:
    """Población 15-64 (millones) con el máximo marcado; sombrea el declive posterior."""
    s = proy.sort_values("anio")
    peak = s.loc[s.pob_15_64.idxmax()]
    fig = go.Figure()
    fig.add_scatter(x=s.anio, y=s.pob_15_64 / 1e6, mode="lines", line=dict(color=BLUE, width=3), showlegend=False)
    fig.add_vrect(x0=peak.anio, x1=s.anio.max(), fillcolor=ORANGE, opacity=0.12, line_width=0)
    fig.add_vline(x=peak.anio, line_dash="dash", line_color=INK_MUTED)
    fig.add_scatter(x=[peak.anio], y=[peak.pob_15_64 / 1e6], mode="markers+text", marker=dict(size=10, color=RED),
                    text=[f"Máximo {int(peak.anio)}: {peak.pob_15_64 / 1e6:.2f}M"], textposition="top right",
                    showlegend=False)
    fig.update_layout(**PLOTLY_LAYOUT, title="Chile: cuándo comienza a declinar la población en edad de trabajar")
    fig.update_xaxes(title="Año")
    fig.update_yaxes(title="Población de 15 a 64 años (millones)")
    return fig


def region_choropleth(df: pd.DataFrame, geojson: dict, var: str, label: str, scale: str = "Blues") -> go.Figure:
    """Choropleth por región. df necesita region_id, region_nombre y la variable `var`."""
    fig = px.choropleth_map(
        df, geojson=geojson, locations="region_id", featureidkey="properties.region_id",
        color=var, hover_name="region_nombre", hover_data={"region_id": False, var: ":.2f"},
        color_continuous_scale=scale, map_style="carto-positron",
        center={"lat": -35.5, "lon": -71.5}, zoom=3.0, opacity=0.85,
        labels={var: label},
    )
    fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=0, r=0, t=30, b=0)}, height=640, title=label)
    return fig


def region_bars(df: pd.DataFrame, var: str, label: str, nacional: float, fmt: str = ".2f", color: str = BLUE) -> go.Figure:
    """Barras horizontales por región, ordenadas, con línea del promedio nacional."""
    d = df.sort_values(var)
    fig = px.bar(d, x=var, y="region_nombre", orientation="h", color_discrete_sequence=[color],
                 labels={var: label, "region_nombre": ""})
    fig.add_vline(x=nacional, line_dash="dash", line_color="#52514e",
                  annotation_text=f"País: {format(nacional, fmt)}", annotation_position="top")
    fig.update_layout(**PLOTLY_LAYOUT, title=label)
    fig.update_yaxes(categoryorder="total ascending")
    return fig


def region_support_people_bars(df: pd.DataFrame, nacional: float) -> go.Figure:
    """KPI 1.2, vista en personas: mismo orden que la razón de soporte, con cotizantes y personas de 65+ en valores
    absolutos (eje con marcas cada 500.000 y rejilla cada 100.000) y la razón escrita junto a cada región."""
    d = df.sort_values("razon_soporte_previsional")
    orden = list(d.region_nombre)
    fig = go.Figure()
    fig.add_bar(y=d.region_nombre, x=d.pob_65_mas, orientation="h", name="Personas de 65+", marker_color=ORANGE,
                hovertemplate="%{y}<br>65+: %{x:,.0f}<extra></extra>")
    fig.add_bar(y=d.region_nombre, x=d.cotizantes_2024, orientation="h", name="Cotizantes (dic-2024)", marker_color=BLUE,
                text=[f"{r:.2f}" for r in d.razon_soporte_previsional], textposition="outside",
                hovertemplate="%{y}<br>Cotizantes: %{x:,.0f}<extra></extra>")
    fig.update_layout(**PLOTLY_LAYOUT, barmode="group", separators=",.",
                      title=f"Cotizantes y personas de 65+ por región (número = cotizantes por adulto mayor; país: {nacional:.2f})")
    fig.update_yaxes(categoryorder="array", categoryarray=orden, title="")
    fig.update_xaxes(title="Personas", tickformat=",.0f", dtick=500_000, minor=dict(dtick=100_000, showgrid=True), rangemode="tozero")
    fig.update_layout(height=760, legend=dict(orientation="h", y=1.05, x=0))
    return fig


def support_ratio_projection(historico: float, filas: pd.DataFrame, nombre: str) -> go.Figure:
    """Línea 2024 -> 2035 -> 2050 de la razón de soporte (escenario). filas: anio, razon."""
    pts = pd.concat([pd.DataFrame([{"anio": ANIO_BASE, "razon": historico}]), filas]).sort_values("anio")
    fig = go.Figure()
    fig.add_scatter(x=pts.anio, y=pts.razon, mode="lines+markers+text", text=[f"{v:.2f}" for v in pts.razon],
                    textposition="top center", line=dict(color=RED, width=3), name=nombre)
    fig.update_layout(**PLOTLY_LAYOUT, title=f"Escenario: cotizantes por adulto mayor, {nombre}")
    fig.update_xaxes(title="Año", tickvals=list(pts.anio))
    fig.update_yaxes(title="Cotizantes por persona de 65+", rangemode="tozero")
    return fig


def cost_per_person_chart(d: pd.DataFrame, anio_hito: int, texto_hito: str) -> go.Figure:
    """KPI 2.1: costo público real por persona 65+ (millones de $ de 2025). d: anio, costo_65. Marca el año del salto."""
    fig = go.Figure()
    fig.add_scatter(x=d.anio, y=d.costo_65 / 1e6, mode="lines+markers+text", line=dict(color=RED, width=3),
                    text=[f"{v / 1e6:.2f}" for v in d.costo_65], textposition="top center", showlegend=False,
                    hovertemplate="%{x}: $%{y:.2f} millones<extra></extra>")
    fig.add_vline(x=anio_hito, line_dash="dash", line_color=INK_MUTED, annotation_text=texto_hito, annotation_position="top left")
    fig.update_layout(**PLOTLY_LAYOUT, title="Costo público real por persona de 65+ (millones de $ de 2025)")
    fig.update_xaxes(title="Año", dtick=1)
    fig.update_yaxes(title="Millones de $ de 2025 por persona", rangemode="tozero")
    return fig


def spending_vs_population_growth(d: pd.DataFrame) -> go.Figure:
    """KPI 2.1: crecimiento anual (%) del gasto real en edad avanzada vs. la población 65+. d: anio, gasto, pob_65."""
    g = d.set_index("anio")[["gasto", "pob_65"]].pct_change().dropna() * 100
    fig = go.Figure()
    fig.add_bar(x=g.index, y=g.gasto, name="Gasto real en edad avanzada", marker_color=RED)
    fig.add_bar(x=g.index, y=g.pob_65, name="Población 65+", marker_color=BLUE)
    fig.update_layout(**PLOTLY_LAYOUT, barmode="group", title="Crecimiento anual: gasto vs. población 65+ (%)")
    fig.update_xaxes(title="Año", dtick=1)
    fig.update_yaxes(title="Variación anual (%)", zeroline=True, zerolinecolor=INK_MUTED)
    return fig


def cost_components_chart(h: pd.DataFrame) -> go.Figure:
    """KPI 2.1: costo público por persona 65+ apilado por componente (millones de $ de 2025). h: salida de serie_historica."""
    fig = go.Figure()
    for col, nombre, color in (("pgu_65", "PGU (desde 2022)", BLUE), ("pbs_aps_65", "PBS y APS de vejez", VIOLET),
                               ("resto_65", "Resto de 'Edad avanzada' (sistema antiguo y otros)", ORANGE)):
        fig.add_bar(x=h.index, y=h[col] / 1e6, name=nombre, marker_color=color,
                    hovertemplate="%{x}: $%{y:.2f} millones<extra>" + nombre + "</extra>")
    fig.add_vline(x=2021.5, line_dash="dash", line_color=INK_MUTED, annotation_text="PGU", annotation_position="top")
    fig.update_layout(**PLOTLY_LAYOUT, barmode="stack", title="Costo público por persona 65+, por componente (millones de $ de 2025)")
    fig.update_xaxes(title="Año", dtick=1)
    fig.update_yaxes(title="Millones de $ de 2025 por persona 65+")
    return fig


def beneficiaries_chart(h: pd.DataFrame) -> go.Figure:
    """KPI 2.1: cuántos de cada 100 personas 65+ reciben un beneficio (PGU/PBS/APS) y cuánto paga el Estado por beneficio."""
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.12,
                        subplot_titles=("Beneficios de vejez por cada 100 personas 65+", "Pago anual por beneficio (millones de $ de 2025)"))
    fig.add_scatter(x=h.index, y=100 * h.cobertura, mode="lines+markers", line=dict(color=BLUE, width=3), showlegend=False,
                    hovertemplate="%{x}: %{y:.0f} por cada 100<extra></extra>", row=1, col=1)
    fig.add_scatter(x=h.index, y=h.monto_por_beneficio / 1e6, mode="lines+markers", line=dict(color=RED, width=3), showlegend=False,
                    hovertemplate="%{x}: $%{y:.2f} millones<extra></extra>", row=1, col=2)
    fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=10, r=10, t=70, b=10)})
    fig.update_xaxes(title_text="Año", dtick=2)
    fig.update_yaxes(title_text="Por cada 100 personas 65+", rangemode="tozero", col=1)
    fig.update_yaxes(title_text="Millones de $ de 2025", rangemode="tozero", col=2)
    return fig


def income_comparison_chart(h: pd.DataFrame) -> go.Figure:
    """KPI 2.1: costo por persona 65+ como % del PIB per cápita, y trabajadores necesarios (con el 10 % de la mediana) vs. disponibles."""
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.12,
                        subplot_titles=("Costo por persona 65+ (% del PIB per cápita)",
                                        "Ocupados por persona 65+: los que hay vs. los necesarios"))
    fig.add_scatter(x=h.index, y=h.costo_pct_pib_pc, mode="lines+markers", line=dict(color=RED, width=3), showlegend=False,
                    hovertemplate="%{x}: %{y:.1f}%<extra></extra>", row=1, col=1)
    fig.add_scatter(x=h.index, y=h.ocupados_por_65, mode="lines+markers", name="Ocupados por persona 65+",
                    line=dict(color=BLUE, width=3), row=1, col=2)
    fig.add_scatter(x=h.index, y=h.razon_necesaria, mode="lines+markers", name="Necesarios (cada uno aporta el 10 % de la mediana)",
                    line=dict(color=RED, width=3, dash="dash"), row=1, col=2)
    fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=10, r=10, t=70, b=10),
                      "legend": dict(orientation="h", y=-0.2, bgcolor="rgba(0,0,0,0)")})
    fig.update_xaxes(title_text="Año", dtick=2)
    fig.update_yaxes(title_text="% del PIB per cápita", rangemode="tozero", col=1)
    fig.update_yaxes(title_text="Ocupados por persona 65+", rangemode="tozero", col=2)
    return fig


def cost_projection_chart(h: pd.DataFrame, p: pd.DataFrame) -> go.Figure:
    """KPI 2.1: escenario 2025-2050. Izquierda: gasto en edad avanzada (% del PIB). Derecha: carga requerida sobre el sueldo mediano vs. 10 %."""
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.12,
                        subplot_titles=("Gasto en edad avanzada (% del PIB)", "Carga requerida sobre el sueldo mediano de los ocupados"))
    fig.add_scatter(x=h.index, y=h.pct_pib, mode="lines", line=dict(color=RED, width=3), showlegend=False,
                    hovertemplate="%{x}: %{y:.2f}%<extra></extra>", row=1, col=1)
    fig.add_scatter(x=p.index, y=p.pct_pib, mode="lines", line=dict(color=RED, width=3, dash="dash"), showlegend=False,
                    hovertemplate="%{x}: %{y:.2f}% (escenario)<extra></extra>", row=1, col=1)
    fig.add_scatter(x=h.index, y=100 * h.carga_requerida, mode="lines", line=dict(color=BLUE, width=3), name="Observado",
                    hovertemplate="%{x}: %{y:.1f}%<extra></extra>", row=1, col=2)
    fig.add_scatter(x=p.index, y=100 * p.carga_requerida, mode="lines", line=dict(color=BLUE, width=3, dash="dash"), name="Escenario",
                    hovertemplate="%{x}: %{y:.1f}% (escenario)<extra></extra>", row=1, col=2)
    fig.add_hline(y=10, line_dash="dot", line_color=INK_MUTED, annotation_text="10 % (cotización obligatoria)",
                  annotation_position="bottom right", row=1, col=2)
    fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=10, r=10, t=70, b=10),
                      "legend": dict(orientation="h", y=-0.2, bgcolor="rgba(0,0,0,0)")})
    fig.update_xaxes(title_text="Año")
    fig.update_yaxes(title_text="% del PIB", rangemode="tozero", col=1)
    fig.update_yaxes(title_text="% del sueldo mediano", rangemode="tozero", col=2)
    return fig


def spending_pct_pib(df: pd.DataFrame) -> go.Figure:
    """KPI 2.2 (ratio 1): % del PIB. df: anio, pilar_pct_pib, edad_avanzada_pct_pib (esta última puede traer NaN)."""
    fig = go.Figure()
    fig.add_scatter(x=df.anio, y=df.pilar_pct_pib, mode="lines+markers", name="PGU + pensiones solidarias (PBS/APS)",
                    line=dict(color=ORANGE, width=3))
    ea = df.dropna(subset=["edad_avanzada_pct_pib"])
    fig.add_scatter(x=ea.anio, y=ea.edad_avanzada_pct_pib, mode="lines+markers", name="Gasto total del Gobierno Central en edad avanzada",
                    line=dict(color=VIOLET, width=3, dash="dash"))
    fig.update_layout(**PLOTLY_LAYOUT, title="Peso fiscal de las pensiones no contributivas (% del PIB)")
    fig.update_xaxes(title="Año", dtick=1)
    fig.update_yaxes(title="% del PIB", rangemode="tozero")
    return fig


def poverty_bars(df: pd.DataFrame, nacional: float) -> go.Figure:
    """KPI 2.3: % de personas 65+ en pobreza por ingresos por región, con IC 95%. df: region_nombre, pct_pobreza_65, ic95_inf, ic95_sup."""
    d = df.sort_values("pct_pobreza_65")
    fig = go.Figure(go.Bar(
        y=d.region_nombre, x=d.pct_pobreza_65, orientation="h", marker_color=ORANGE,
        error_x=dict(type="data", symmetric=False, array=d.ic95_sup - d.pct_pobreza_65, arrayminus=d.pct_pobreza_65 - d.ic95_inf),
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    fig.add_vline(x=nacional, line_dash="dash", line_color="#52514e", annotation_text=f"País: {nacional:.1f}%", annotation_position="top")
    fig.update_layout(**PLOTLY_LAYOUT, title="Pobreza por ingresos en personas de 65+ (% con IC 95%)")
    fig.update_xaxes(title="% de personas 65+ en pobreza")
    return fig


def _unidad_dinero(max_clp: float):
    """Escala legible para masas de dinero en pesos: (divisor, etiqueta del eje)."""
    if max_clp >= 1e12:
        return 1e12, "billones de $ de 2025"
    if max_clp >= 1e9:
        return 1e9, "miles de millones de $ de 2025"
    return 1e6, "millones de $ de 2025"


def critical_point_chart(d: pd.DataFrame, pc: dict, view: str, nombre: str, trabajadores: str, carga_max: float) -> go.Figure:
    """KPI 1.2, análisis del punto crítico. d = salida de critical_point.serie_pais / serie_territorio;
    pc = critical_point.punto_critico(d); view = 'dinero' | 'razon'.
    En 'dinero' se superponen el costo (costo por persona de 65+ x población de 65+) y la capacidad (carga máxima x ingreso por
    trabajador x trabajadores); en 'razon', la razón de soporte observada y la razón de equilibrio R*. El cruce de las dos
    líneas es el punto crítico. Tramo observado sólido, escenario punteado; rombos = años con población regional (2024/2035/2050)."""
    if view == "dinero":
        div, unidad = _unidad_dinero(max(d.costo_total.max(), d.capacidad.max()))
        series = [("Costo del Pilar Solidario de vejez", d.costo_total / div, RED),
                  (f"Capacidad: {carga_max:.0%} del sueldo de los {trabajadores}", d.capacidad / div, BLUE)]
        ytitle, fmt = unidad, ",.2f"
        titulo = f"Costo vs. capacidad de financiamiento, {nombre}"
    else:
        series = [(f"Razón de soporte observada ({trabajadores} por persona de 65+)", d.razon_soporte, BLUE),
                  (f"Razón de equilibrio R* (carga máxima {carga_max:.0%})", d.razon_equilibrio, ORANGE)]
        ytitle, fmt = f"{trabajadores.capitalize()} por persona de 65+", ".2f"
        titulo = f"Razón de soporte vs. razón de equilibrio, {nombre}"

    obs, proy = d[~d.proyectado], d[d.proyectado]
    base = d[~d.proyectado].tail(1)
    proy_c = pd.concat([base, proy])  # el tramo punteado parte del último punto observado
    fig = go.Figure()
    for nom, y, col in series:
        yo, yp = y.loc[obs.index], y.loc[proy_c.index]
        fig.add_scatter(x=obs.anio, y=yo, mode="lines+markers" if len(obs) > 1 else "markers", name=nom, legendgroup=nom,
                        line=dict(color=col, width=3), marker=dict(size=6 if len(obs) > 1 else 10),
                        hovertemplate="%{x}: %{y:" + fmt + "}<extra>" + nom + "</extra>")
        fig.add_scatter(x=proy_c.anio, y=yp, mode="lines", name=nom + " (escenario)", legendgroup=nom, showlegend=False,
                        line=dict(color=col, width=3, dash="dash"),
                        hovertemplate="%{x}: %{y:" + fmt + "}<extra>" + nom + " (escenario)</extra>")
        if "ancla" in d and d.ancla.any():
            a = d[d.ancla]
            fig.add_scatter(x=a.anio, y=y.loc[a.index], mode="markers", legendgroup=nom, showlegend=False,
                            marker=dict(symbol="diamond", size=12, color=col, line=dict(color="white", width=1.5)),
                            hoverinfo="skip")
    if pc["estado"] in ("cruza", "ya_superado"):
        xc = pc["anio_exacto"]
        yc = float(np.interp(xc, d.anio, series[0][1].values))
        fig.add_vline(x=xc, line_dash="dot", line_color=INK_MUTED)
        fig.add_scatter(x=[xc], y=[yc], mode="markers+text", showlegend=False, hoverinfo="skip",
                        text=[f"Punto crítico: {pc['anio']}" if pc["estado"] == "cruza" else f"Superado desde {pc['anio']}"],
                        textposition="top left", marker=dict(symbol="star", size=18, color=VIOLET, line=dict(color="white", width=1.5)))
    fig.update_layout(**PLOTLY_LAYOUT, title=titulo)
    fig.update_xaxes(title="Año")
    fig.update_yaxes(title=ytitle, rangemode="tozero")
    return fig

# KPI 1.3: texto oscuro explícito, para que título, ejes y leyenda se lean sobre el fondo claro aunque el
# dashboard esté en tema oscuro (llamar st.plotly_chart con theme=None para que Streamlit no lo reemplace)
_TEXTO_CLARO = dict(title_font_color=INK_PRIMARY, legend_font_color=INK_PRIMARY)
_EJE_CLARO = dict(tickfont_color=INK_PRIMARY, title_font_color=INK_PRIMARY, linecolor=GRIDLINE, automargin=True)
_MARGEN = dict(margin=dict(l=70, r=20, t=60, b=10))


def commissionable_flow_bars(df: pd.DataFrame) -> go.Figure:
    """KPI 1.3: flujo al sistema por destino, barras apiladas (billones de pesos) para los años reales.
    df: anio, cuentas_individuales, seguro_social_fapp, estado, flujo_total. Segmentos < 2% se rotulan fuera de la barra."""
    anios = df.anio.astype(int).astype(str)
    fig = go.Figure()
    base = pd.Series(0.0, index=df.index)
    for col, nombre, color in [("cuentas_individuales", "Cuentas individuales AFP (comisionable)", BLUE),
                               ("seguro_social_fapp", "Seguro Social (FAPP)", ORANGE),
                               ("estado", "Estado (PGU + PBS + APS)", VIOLET)]:
        val = df[col] / 1e12
        pct = 100 * df[col] / df.flujo_total
        fig.add_bar(x=anios, y=val, name=nombre, marker_color=color,
                    text=[f"{v:.2f} ({p:.0f}%)" if p >= 2 else "" for v, p in zip(val, pct)],
                    textposition="inside", insidetextanchor="middle", textfont_color="white",
                    customdata=pct, hovertemplate=nombre + ": %{y:.2f} billones (%{customdata:.1f}%)<extra></extra>")
        for i, (v, p, b) in enumerate(zip(val, pct, base)):
            if 0 < p < 2:  # segmento muy delgado: rótulo al lado, con flecha
                # x por posición: un año como texto ("2025") se leería como posición 2025 del eje de categorías
                fig.add_annotation(x=i, y=b + v / 2, text=f"{v:.2f} ({p:.1f}%)", showarrow=True, arrowhead=0,
                                   ax=150, ay=0, font=dict(color=INK_PRIMARY, size=12), arrowcolor=INK_MUTED)
        base = base + val
    fig.update_layout(**{**PLOTLY_LAYOUT, **_MARGEN, "legend": dict(orientation="h", y=-0.15, bgcolor="rgba(0,0,0,0)")},
                      **_TEXTO_CLARO, barmode="stack", bargap=0.45,
                      title="Flujo al sistema previsional por destino (billones de pesos)")
    fig.update_xaxes(type="category", title="Año", **_EJE_CLARO)
    fig.update_yaxes(title="Billones de pesos (10^12)", rangemode="tozero", **_EJE_CLARO)
    return fig


def commissionable_share_line(df: pd.DataFrame) -> go.Figure:
    """KPI 1.3: % del flujo que pasa por cuentas individuales, real (línea continua) y escenarios (punteados).
    df: anio, tipo (real / escenario / escenario_crec_1_5), kpi_1_3_pct."""
    real = df[df.tipo == "real"].sort_values("anio")
    ancla = real.iloc[[-1]]  # los escenarios parten del último año real
    fig = go.Figure()
    fig.add_scatter(x=real.anio.astype(str), y=real.kpi_1_3_pct, mode="lines+markers+text", name="Real",
                    line=dict(color=BLUE, width=3), text=[f"{v:.1f}%" for v in real.kpi_1_3_pct],
                    textposition="top center", textfont_color=INK_PRIMARY)
    for tipo, nombre, color, dash in [("escenario", "Escenario base (ingreso real constante)", RED, "dash"),
                                      ("escenario_crec_1_5", "Escenario ingreso real +1,5% anual", INK_MUTED, "dot")]:
        e = pd.concat([ancla, df[df.tipo == tipo]]).sort_values("anio")
        if len(e) == 1:
            continue
        rotulos = ["" if a not in (2028, 2033, 2035) or tipo != "escenario" else f"{v:.1f}%"
                   for a, v in zip(e.anio, e.kpi_1_3_pct)]
        fig.add_scatter(x=e.anio.astype(str), y=e.kpi_1_3_pct, mode="lines+markers+text", name=nombre,
                        line=dict(color=color, width=2.5, dash=dash), text=rotulos, textposition="bottom center",
                        textfont_color=INK_PRIMARY)
    fig.update_layout(**{**PLOTLY_LAYOUT, **_MARGEN, "legend": dict(orientation="h", y=-0.2, bgcolor="rgba(0,0,0,0)")},
                      **_TEXTO_CLARO, title="Parte del flujo previsional que pasa por cuentas individuales AFP (%)")
    fig.update_xaxes(type="category", title="Año", **_EJE_CLARO)
    fig.update_yaxes(title="% del flujo total", range=[0, 70], **_EJE_CLARO)
    return fig


# KPI 1.1 (diagnóstico): dispersión de cobertura y matriz de riesgo
_TAM_MAX_PX = 55  # diámetro de la burbuja más grande (Metropolitana)
_AREA_PX = (900, 400)  # área de trazado aproximada en el dashboard (ancho, alto), para ubicar los rótulos
_POSICIONES = [  # (dirección x, dirección y) alrededor de la burbuja, en el orden en que se prueban
    (0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1),
]


def _rango(serie: pd.Series, margen: float) -> tuple:
    d = serie.max() - serie.min()
    return serie.min() - margen * d, serie.max() + margen * d


def _ubicar_rotulos(x, y, textos, radios_px, rango_x, rango_y):
    """Elige para cada rótulo un desplazamiento (en píxeles) alrededor de su burbuja que no se cruce con rótulos ya
    puestos ni con otras burbujas; si no hay lugar libre cerca, lo aleja más (y se dibuja con línea guía).
    Heurística voraz sobre el área de trazado aproximada _AREA_PX. Devuelve [(dx, dy, con_linea)] por punto."""
    ancho, alto = _AREA_PX
    px_x = (np.asarray(x, float) - rango_x[0]) / (rango_x[1] - rango_x[0]) * ancho
    px_y = (np.asarray(y, float) - rango_y[0]) / (rango_y[1] - rango_y[0]) * alto
    cajas, salida = [], [None] * len(px_x)

    def libre(caja, i):
        if caja[0] < 0 or caja[2] > ancho or caja[1] < 0 or caja[3] > alto:
            return False
        if any(not (caja[2] < c[0] or caja[0] > c[2] or caja[3] < c[1] or caja[1] > c[3]) for c in cajas):
            return False
        return not any((max(caja[0], min(px_x[j], caja[2])) - px_x[j]) ** 2
                       + (max(caja[1], min(px_y[j], caja[3])) - px_y[j]) ** 2 < (radios_px[j] + 2) ** 2
                       for j in range(len(px_x)))

    for i in np.argsort(-np.asarray(radios_px)):  # primero las burbujas grandes
        w, h = 6.5 * len(textos[i]) + 6, 15
        for distancia in (0, 18, 36, 54):  # 0 = pegado a la burbuja; más lejos = con línea guía
            for ux, uy in _POSICIONES:
                norma = np.hypot(ux, uy)
                dx = ux / norma * (radios_px[i] + distancia) + ux * w / 2
                dy = uy / norma * (radios_px[i] + distancia) + uy * h / 2
                caja = (px_x[i] + dx - w / 2, px_y[i] + dy - h / 2, px_x[i] + dx + w / 2, px_y[i] + dy + h / 2)
                if libre(caja, i):
                    salida[i] = (dx, dy, distancia > 0)
                    cajas.append(caja)
                    break
            if salida[i]:
                break
        if salida[i] is None:  # sin lugar: arriba de la burbuja (el hover lo identifica igual)
            salida[i] = (0, radios_px[i] + h / 2, False)
    return salida


def _burbujas(fig, df, x, y, hover, color, rango_x, rango_y):
    """Burbujas por región con tamaño = cotizantes; rótulos como anotaciones sin solaparse."""
    sizeref = df.cotizantes.max() / _TAM_MAX_PX ** 2
    radios = list(np.sqrt(df.cotizantes / sizeref) / 2)
    fig.add_scatter(x=df[x], y=df[y], mode="markers", text=df.region_nombre, showlegend=False,
                    marker=dict(size=df.cotizantes, sizemode="area", sizeref=sizeref, sizemin=4, color=color,
                                opacity=0.75, line=dict(color="white", width=1)),
                    customdata=np.stack([df.cotizantes, df.share_cotizantes_pct], axis=1),
                    hovertemplate="<b>%{text}</b><br>" + hover
                    + "<br>Cotizantes: %{customdata[0]:,.0f} (%{customdata[1]:.1f}% del total)<extra></extra>")
    for (dx, dy, linea), xi, yi, nombre in zip(_ubicar_rotulos(df[x], df[y], list(df.region_nombre), radios,
                                                               rango_x, rango_y), df[x], df[y], df.region_nombre):
        fig.add_annotation(x=xi, y=yi, text=nombre, showarrow=linea, arrowhead=0, arrowwidth=1, arrowcolor=INK_MUTED,
                           ax=dx, ay=-dy, xshift=0 if linea else dx, yshift=0 if linea else dy,
                           font=dict(color=INK_PRIMARY, size=11))


def num_cl(v: float, dec: int = 2) -> str:
    """Número con coma decimal (formato chileno) para textos y anotaciones."""
    return f"{v:.{dec}f}".replace(".", ",")


def coverage_correlation_scatter(df: pd.DataFrame, var: str, etiqueta: str, unidad: str, corr: pd.Series) -> go.Figure:
    """KPI 1.1: cobertura previsional (%) vs. una variable regional, burbuja = cotizantes, recta MCO.
    df: kpi_cobertura_correlaciones_region.csv; corr: fila del resumen (pearson_r, spearman_rho, n)."""
    fig = go.Figure()
    pendiente, intercepto = np.polyfit(df[var], df.cobertura_previsional_pct, 1)
    xs = np.linspace(df[var].min(), df[var].max(), 50)
    fig.add_scatter(x=xs, y=intercepto + pendiente * xs, mode="lines", name="Recta MCO",
                    line=dict(color=RED, width=2, dash="dash"), hoverinfo="skip")
    formato_x = ":$,.0f" if var == "ingreso_per_capita_prom" else ":.1f"
    rx, ry = _rango(df[var], 0.08), _rango(df.cobertura_previsional_pct, 0.12)
    _burbujas(fig, df, var, "cobertura_previsional_pct",
              f"{etiqueta}: %{{x{formato_x}}}<br>Cobertura: %{{y:.1f}}%", BLUE, rx, ry)
    fig.add_annotation(xref="paper", yref="paper", x=0.01, y=0.99, xanchor="left", yanchor="top", showarrow=False,
                       text=f"r = {num_cl(corr.pearson_r)}, ρ = {num_cl(corr.spearman_rho)}, n = {int(corr.n)}",
                       font=dict(color=INK_PRIMARY, size=13), bgcolor="rgba(255,255,255,0.8)")
    fig.update_layout(**{**PLOTLY_LAYOUT, **_MARGEN}, **_TEXTO_CLARO, height=520, showlegend=False,
                      title=f"Cobertura previsional vs. {etiqueta.lower()} (burbuja = cotizantes)")
    fig.update_xaxes(title=f"{etiqueta} ({unidad})", tickformat="$,.0f" if var == "ingreso_per_capita_prom" else None,
                     range=list(rx), **_EJE_CLARO)
    fig.update_yaxes(title="Cobertura previsional (% de 15-64 que cotiza)", ticksuffix="%", range=list(ry), **_EJE_CLARO)
    return fig


CUADRANTES = {  # (cobertura alta, envejecimiento alto) -> (nombre, color de fondo)
    (False, True): ("Riesgo doble", RED),
    (False, False): ("Potencial de captación", ORANGE),
    (True, True): ("Base que envejece", VIOLET),
    (True, False): ("Núcleo a retener", BLUE),
}


def coverage_risk_matrix(df: pd.DataFrame, nac_cobertura: float, nac_65: float) -> go.Figure:
    """KPI 1.1: matriz de riesgo cobertura × % 65+, cuadrantes cortados en los valores nacionales.
    df: kpi_cobertura_correlaciones_region.csv."""
    x0, x1 = _rango(df.cobertura_previsional_pct, 0.12)
    y0, y1 = _rango(df.pct_65_mas, 0.12)
    fig = go.Figure()
    for (alta_cob, alto_env), (nombre, color) in CUADRANTES.items():
        qx0, qx1 = (nac_cobertura, x1) if alta_cob else (x0, nac_cobertura)
        qy0, qy1 = (nac_65, y1) if alto_env else (y0, nac_65)
        fig.add_shape(type="rect", x0=qx0, x1=qx1, y0=qy0, y1=qy1, fillcolor=color, opacity=0.07, line_width=0,
                      layer="below")
        fig.add_annotation(x=qx1 if alta_cob else qx0, y=qy1 if alto_env else qy0, text=f"<b>{nombre}</b>",
                           xanchor="right" if alta_cob else "left", yanchor="top" if alto_env else "bottom",
                           showarrow=False, font=dict(color=color, size=13), xshift=-6 if alta_cob else 6,
                           yshift=-4 if alto_env else 4)
    fig.add_vline(x=nac_cobertura, line_dash="dash", line_color=INK_MUTED,
                  annotation_text=f"Cobertura país {num_cl(nac_cobertura, 1)}%", annotation_position="bottom right",
                  annotation_font_color=INK_PRIMARY)
    fig.add_hline(y=nac_65, line_dash="dash", line_color=INK_MUTED,
                  annotation_text=f"65+ país {num_cl(nac_65, 1)}%", annotation_position="top left",
                  annotation_font_color=INK_PRIMARY)
    _burbujas(fig, df, "cobertura_previsional_pct", "pct_65_mas", "Cobertura: %{x:.1f}%<br>65+: %{y:.1f}%", INK_MUTED,
              (x0, x1), (y0, y1))
    fig.update_layout(**{**PLOTLY_LAYOUT, **_MARGEN}, **_TEXTO_CLARO, height=560, showlegend=False,
                      title="Matriz de riesgo: cobertura previsional × envejecimiento (burbuja = cotizantes)")
    fig.update_xaxes(title="Cobertura previsional (% de 15-64 que cotiza)", ticksuffix="%", range=[x0, x1], **_EJE_CLARO)
    fig.update_yaxes(title="Población de 65 años y más (% del total)", ticksuffix="%", range=[y0, y1], **_EJE_CLARO)
    return fig


def risk_quadrant(df: pd.DataFrame, nac_cobertura: float, nac_65: float) -> pd.Series:
    """Nombre del cuadrante de cada región (mismo corte que coverage_risk_matrix)."""
    return pd.Series([CUADRANTES[(c >= nac_cobertura, e > nac_65)][0]
                      for c, e in zip(df.cobertura_previsional_pct, df.pct_65_mas)], index=df.index)
