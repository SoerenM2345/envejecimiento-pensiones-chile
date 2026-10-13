"""Constructores de figuras compartidos por las páginas del modo final.
Cada función recibe DataFrames ya cargados (no lee archivos) y devuelve un go.Figure."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import (BLUE, ORANGE, VIOLET, RED, INK_MUTED, GRIDLINE, SURFACE, PLOTLY_LAYOUT,
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
