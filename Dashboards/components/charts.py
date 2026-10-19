"""Constructores de figuras compartidos por las páginas del modo final.
Cada función recibe DataFrames ya cargados (no lee archivos) y devuelve un go.Figure."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from components.cost_analysis import CARGA_MAX
from utils import (BLUE, ORANGE, VIOLET, RED, INK_PRIMARY, INK_SECONDARY, INK_MUTED, GRIDLINE, SURFACE, PLOTLY_LAYOUT,
                   CATEGORICAL, lighten, es_cl)

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


def _region_people_bars(d: pd.DataFrame, total: tuple, parte: tuple, texto: list, titulo: str, dtick: int = 500_000) -> go.Figure:
    """Barras en personas por región, en el orden de d (el mismo de la vista relativa): total = (columna, nombre, color) y
    parte = (columna, nombre, color) con la tasa escrita junto a la barra. Eje con marcas cada dtick personas y rejilla cada dtick / 5."""
    fig = go.Figure()
    fig.add_bar(y=d.region_nombre, x=d[total[0]], orientation="h", name=total[1], marker_color=total[2],
                hovertemplate="%{y}<br>" + total[1] + ": %{x:,.0f}<extra></extra>")
    fig.add_bar(y=d.region_nombre, x=d[parte[0]], orientation="h", name=parte[1], marker_color=parte[2],
                text=texto, textposition="outside", hovertemplate="%{y}<br>" + parte[1] + ": %{x:,.0f}<extra></extra>")
    fig.update_layout(**PLOTLY_LAYOUT, barmode="group", title=titulo)
    fig.update_yaxes(categoryorder="array", categoryarray=list(d.region_nombre), title="")
    fig.update_xaxes(title="Personas", tickformat=",.0f", dtick=dtick, minor=dict(dtick=dtick // 5, showgrid=True), tickangle=0,
                     rangemode="tozero")
    return fig


def region_support_people_bars(df: pd.DataFrame, nacional: float) -> go.Figure:
    """KPI 1.2, vista en personas: mismo orden que la razón de soporte, con cotizantes y personas de 65+ en valores
    absolutos y la razón escrita junto a cada región."""
    d = df.sort_values("razon_soporte_previsional")
    return _region_people_bars(d, ("pob_65_mas", "Personas de 65+", ORANGE), ("cotizantes_2024", "Cotizantes (dic-2024)", BLUE),
                               [f"{r:.2f}" for r in d.razon_soporte_previsional],
                               f"Cotizantes y personas de 65+ por región* (país: {nacional:.2f})")


def region_coverage_people_bars(df: pd.DataFrame, nacional: float) -> go.Figure:
    """KPI 1.1, vista en personas: mismo orden que la cobertura, con la población de 15-64 (Censo 2024) y los cotizantes en
    valores absolutos y la cobertura escrita junto a cada región."""
    d = df.sort_values("cobertura_previsional_pct")
    return _region_people_bars(d, ("pob_15_64", "Población 15-64 (Censo 2024)", lighten(ORANGE)),
                               ("cotizantes_2024", "Cotizantes (dic-2024)", ORANGE),
                               [f"{c:.1f}%".replace(".", ",") for c in d.cobertura_previsional_pct],
                               "Cotizantes y población de 15-64 por región", dtick=2_000_000)


def poverty_people_bars(df: pd.DataFrame, nacional: float) -> go.Figure:
    """KPI 2.3, vista en personas: mismo orden que el % de pobreza, con las personas 65+ de la CASEN 2022 y las que están
    en pobreza (porcentaje × población expandida), y el porcentaje escrito junto a cada región. df: region_nombre,
    pob_65_expandida, n_pobres, pct_pobreza_65."""
    d = df.sort_values("pct_pobreza_65")
    return _region_people_bars(d, ("pob_65_expandida", "Personas 65+ (CASEN 2022)", lighten(ORANGE)),
                               ("n_pobres", "Personas 65+ en pobreza", ORANGE),
                               [f"{p:.1f}%".replace(".", ",") for p in d.pct_pobreza_65],
                               "Personas de 65+ y en pobreza por región", dtick=250_000)


def zona_escenario(fig: go.Figure, desde: float, hasta: float) -> go.Figure:
    """Fondo gris con el rótulo «Escenario» para los años proyectados (desde el primer año que no es dato)."""
    fig.add_vrect(x0=desde, x1=hasta, fillcolor=INK_MUTED, opacity=0.08, line_width=0, layer="below")
    fig.add_annotation(x=desde, xref="x", y=1, yref="paper", text="Escenario", showarrow=False, xanchor="left", yanchor="top",
                       xshift=6, font=dict(color=INK_SECONDARY, size=12))
    return fig


def support_ratio_projection(historico: float, filas: pd.DataFrame, nombre: str, todos_los_anios: bool = False,
                             anio_ultimo_real: int = ANIO_BASE) -> go.Figure:
    """Razón de soporte: años reales con línea continua, escenario (cobertura constante) punteado sobre fondo gris.
    filas: anio, razon (años siguientes a ANIO_BASE; los <= anio_ultimo_real son datos observados).
    todos_los_anios=True (país): el INE publica población de cada año, así que se marca cada año con un punto pequeño y se
    rotulan solo los años clave. False (región): solo 2024 (Censo) y 2035 / 2050 (escenario regional) son datos de población;
    se marcan con rombos (lleno = 2024, vacío = escenarios) y la recta entre ellos es interpolación."""
    pts = pd.concat([pd.DataFrame([{"anio": ANIO_BASE, "razon": historico}]), filas]).sort_values("anio").reset_index(drop=True)
    real, esc = pts[pts.anio <= anio_ultimo_real], pts[pts.anio >= anio_ultimo_real]
    fig = go.Figure()
    zona_escenario(fig, anio_ultimo_real + 0.5, pts.anio.max() + (0.5 if todos_los_anios else 1))
    if todos_los_anios:
        clave = pts.anio.isin([2024, 2025, 2030, 2035, 2040, 2050, 2060, 2070])
        fig.add_scatter(x=real.anio, y=real.razon, mode="lines+markers", line=dict(color=RED, width=3), marker=dict(size=7),
                        name="Dato real (cotizantes diciembre / población 65+)", hovertemplate="%{x}: %{y:.2f}<extra>real</extra>")
        fig.add_scatter(x=esc.anio, y=esc.razon, mode="lines+markers", line=dict(color=RED, width=3, dash="dash"), marker=dict(size=4),
                        name="Escenario (cobertura constante, población INE)", hovertemplate="%{x}: %{y:.2f}<extra>escenario</extra>")
        # 2024 y 2025 son años vecinos: rótulos a izquierda / derecha para que no se tapen
        posiciones = ["middle left" if a == ANIO_BASE else "top right" if a == anio_ultimo_real else "top center" for a in pts.anio[clave]]
        fig.add_scatter(x=pts.anio[clave], y=pts.razon[clave], mode="text", text=[f"{v:.2f}" for v in pts.razon[clave]],
                        textposition=posiciones, showlegend=False, hoverinfo="skip")
    else:
        fig.add_scatter(x=esc.anio, y=esc.razon, mode="lines", line=dict(color=RED, width=3, dash="dash"), showlegend=False, hoverinfo="skip")
        fig.add_scatter(x=real.anio, y=real.razon, mode="markers+text", text=[f"{v:.2f}" for v in real.razon], textposition="top center",
                        marker=dict(symbol="diamond", size=13, color=RED, line=dict(color="white", width=1.5)), name="Año observado (Censo 2024)")
        fig.add_scatter(x=esc.anio[1:], y=esc.razon[1:], mode="markers+text", text=[f"{v:.2f}" for v in esc.razon[1:]], textposition="top center",
                        marker=dict(symbol="diamond", size=13, color="white", line=dict(color=RED, width=2.5)),
                        name="Población del escenario regional")
    fig.update_layout(**PLOTLY_LAYOUT, title=f"Cotizantes por adulto mayor, {nombre}")
    fig.update_xaxes(title="Año", **({} if todos_los_anios else dict(tickvals=list(pts.anio))))
    fig.update_yaxes(title="Cotizantes por persona de 65+", rangemode="tozero")
    return fig


def cost_per_person_chart(d: pd.DataFrame, anio_hito: int, texto_hito: str) -> go.Figure:
    """KPI 2.1: costo público real por persona 65+ (millones de $ de 2025). d: anio, costo_65. Marca el año del salto."""
    fig = go.Figure()
    fig.add_scatter(x=d.anio, y=d.costo_65 / 1e6, mode="lines+markers+text", line=dict(color=RED, width=3),
                    text=[f"{v / 1e6:.2f}" for v in d.costo_65], textposition="top center", showlegend=False,
                    hovertemplate="%{x}: $%{y:.2f} millones<extra></extra>")
    # rótulo abajo: arriba tapaba el valor del año del salto
    fig.add_vline(x=anio_hito, line_dash="dash", line_color=INK_MUTED, annotation_text=texto_hito, annotation_position="bottom left")
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


def cost_pct_pibpc_chart(h: pd.DataFrame) -> go.Figure:
    """KPI 2.1 (indicador principal): costo por persona 65+ como % del PIB per cápita, con el máximo marcado. h: serie_historica."""
    pico = h.costo_pct_pib_pc.idxmax()
    fig = go.Figure()
    fig.add_scatter(x=h.index, y=h.costo_pct_pib_pc, mode="lines+markers+text", line=dict(color=RED, width=3), showlegend=False,
                    text=[f"{v:.1f}" if a in (h.index[0], pico, h.index[-1]) else "" for a, v in h.costo_pct_pib_pc.items()],
                    textposition="top center", hovertemplate="%{x}: %{y:.1f}% del PIB per cápita<extra></extra>")
    fig.update_layout(**PLOTLY_LAYOUT, title="Costo por persona 65+ como % del PIB per cápita")
    fig.update_xaxes(title="Año", dtick=1)
    fig.update_yaxes(title="% del PIB per cápita", rangemode="tozero")
    return fig


def burden_chart(h: pd.DataFrame, base: str = "mediana") -> go.Figure:
    """KPI 2.1: izquierda, pago plano mensual por ocupado frente al 10 % del ingreso típico (mediana o promedio);
    derecha, ocupados por persona 65+: los que hay vs. los necesarios si cada uno aportara ese 10 %."""
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.12,
                        subplot_titles=(f"Pago por ocupado vs. 10 % del ingreso ({base}), $ de 2025 al mes",
                                        "Ocupados por persona 65+: los que hay vs. los necesarios"))
    fig.add_scatter(x=h.index, y=h.pago_plano, mode="lines+markers", name="Pago por ocupado si se repartiera el gasto",
                    line=dict(color=RED, width=3), row=1, col=1, hovertemplate="%{x}: $%{y:,.0f} al mes<extra></extra>")
    fig.add_scatter(x=h.index, y=CARGA_MAX * h.ingreso_mensual, mode="lines+markers", name=f"10 % del ingreso ({base})",
                    line=dict(color=INK_MUTED, width=3, dash="dot"), row=1, col=1, hovertemplate="%{x}: $%{y:,.0f} al mes<extra></extra>")
    fig.add_scatter(x=h.index, y=h.ocupados_por_65, mode="lines+markers", name="Ocupados por persona 65+ (los que hay)",
                    line=dict(color=BLUE, width=3), row=1, col=2)
    fig.add_scatter(x=h.index, y=h.razon_necesaria, mode="lines+markers", name="Ocupados necesarios aportando el 10 %",
                    line=dict(color=RED, width=3, dash="dash"), row=1, col=2)
    fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=10, r=10, t=70, b=10),
                         "legend": dict(orientation="h", y=-0.2, bgcolor="rgba(0,0,0,0)")})
    fig.update_xaxes(title_text="Año", dtick=2)
    fig.update_yaxes(title_text="$ de 2025 al mes", rangemode="tozero", col=1)
    fig.update_yaxes(title_text="Ocupados por persona 65+", rangemode="tozero", col=2)
    return fig


def cost_projection_chart(h: pd.DataFrame, p: pd.DataFrame, base: str = "mediana") -> go.Figure:
    """KPI 2.1: escenario 2025-2050. Izquierda: gasto en edad avanzada (% del PIB). Derecha: carga requerida sobre el sueldo mediano vs. 10 %."""
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.12,
                        subplot_titles=("Gasto en edad avanzada (% del PIB)", f"Pago plano por ocupado como % del ingreso ({base})"))
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
    fig.update_yaxes(title_text=f"% del ingreso ({base})", rangemode="tozero", col=2)
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


def fiscal_weight_chart(hist: pd.DataFrame, p: pd.DataFrame, con_fapp: bool, mostrar=(True, True, True)) -> go.Figure:
    """KPI 2.2, peso fiscal 2009-2050 (% del PIB). hist = financiamiento.peso_historico; p = financiamiento.proyeccion_carga.
    mostrar = (observado, escenario del Pilar, escenario con aporte al FAPP). Observado sólido, escenario punteado; la franja es el aporte
    del Estado al FAPP; la línea punteada gris es el peso de 2025."""
    fig = go.Figure()
    zona_escenario(fig, float(p.index.min()) + 0.5, float(p.index.max()) + 0.5)
    base = p.pilar_pct_pib.iloc[0]
    if mostrar[0]:
        fig.add_scatter(x=hist.anio, y=hist.pilar_pct_pib, mode="lines+markers", name="Observado: PGU + pensiones solidarias",
                        line=dict(color=ORANGE, width=3), hovertemplate="%{x}: %{y:.2f}%<extra></extra>")
    if mostrar[1]:
        fig.add_scatter(x=p.index, y=p.pilar_pct_pib, mode="lines", name="Escenario: PGU + pensiones solidarias",
                        line=dict(color=ORANGE, width=3, dash="dash"), hovertemplate="%{x}: %{y:.2f}% (escenario)<extra></extra>")
    if con_fapp and mostrar[2]:
        fig.add_scatter(x=p.index, y=p.carga_pct_pib, mode="lines", name="Escenario: más aporte del Estado al FAPP",
                        line=dict(color=VIOLET, width=3, dash="dash"), fill="tonexty" if mostrar[1] else None, fillcolor="rgba(120,90,170,0.15)",
                        hovertemplate="%{x}: %{y:.2f}% (escenario)<extra></extra>")
    fig.add_hline(y=base, line_dash="dot", line_color=INK_MUTED, annotation_text=f"Peso de 2025: {base:.2f}%",
                  annotation_position="bottom right")
    fig.update_layout(**PLOTLY_LAYOUT, title="Peso fiscal del Pilar Solidario y la PGU (% del PIB)")
    fig.update_xaxes(title="Año")
    fig.update_yaxes(title="% del PIB", rangemode="tozero")
    return fig


def financing_sources_chart(f: pd.DataFrame) -> go.Figure:
    """KPI 2.2, quién paga el Pilar. f: anio, retiros_real (pesos de 2025 del retiro del FRP), pilar_real (gasto total del Pilar, pesos de 2025).
    Barras apiladas en billones de pesos de 2025: lo que financió el fondo de reserva y el resto (presupuesto general).
    Bajo cada año va la parte que financió el FRP."""
    resto = f.pilar_real - f.retiros_real
    pct = 100 * f.retiros_real / f.pilar_real
    anios = [f"{int(a)}<br>FRP: {v:.1f}%" for a, v in zip(f.anio, pct)]
    fig = go.Figure()
    fig.add_bar(x=anios, y=f.retiros_real / 1e12, name="Retiro del Fondo de Reserva de Pensiones", marker_color=BLUE,
                hovertemplate="%{y:.2f} billones<extra>Retiro del FRP</extra>")
    fig.add_bar(x=anios, y=resto / 1e12, name="Resto: presupuesto general", marker_color=lighten(ORANGE),
                hovertemplate="%{y:.2f} billones<extra>Presupuesto general</extra>")
    fig.update_layout(**PLOTLY_LAYOUT, barmode="stack", title="Quién paga el Pilar (billones de $ de 2025)")
    fig.update_yaxes(title="Billones de pesos de 2025")
    return fig


def fapp_schedule_chart(p: pd.DataFrame) -> go.Figure:
    """KPI 2.2, calendario del aporte del Estado al FAPP (Ley 21.735). p = financiamiento.proyeccion_carga (aporte_fapp, pib_real25)."""
    d = p[p.aporte_fapp > 0]
    fig = go.Figure(go.Bar(x=d.index, y=d.aporte_fapp / 1e12, marker_color=VIOLET, customdata=100 * d.aporte_fapp / d.pib_real25,
                           hovertemplate="%{x}: %{y:.2f} billones (%{customdata:.2f}% del PIB)<extra></extra>"))
    fig.update_layout(**PLOTLY_LAYOUT, title="Aporte del Estado al FAPP (billones de $ de 2025)", showlegend=False)
    fig.update_xaxes(title="Año")
    fig.update_yaxes(title="Billones de pesos de 2025", rangemode="tozero")
    return fig


def reserve_chart(d: pd.DataFrame, res: dict, cubre: str, mostrar=(True, True)) -> go.Figure:
    """KPI 2.2, reserva vs gasto. d = financiamiento.trayectoria_reserva (con gasto_cubierto y saldo); res = resumen.
    mostrar = (gasto cubierto, saldo). Barras = gasto que cubre la reserva cada año; línea = saldo (mismo eje, billones);
    la estrella (año en que se agota) aparece solo mientras se ve el saldo."""
    fig = go.Figure()
    zona_escenario(fig, float(d.index.min()) + 0.5, float(d.index.max()) + 0.5)
    if mostrar[0]:
        fig.add_bar(x=d.index, y=d.gasto_cubierto / 1e12, name="Gasto que cubre la reserva (escenario)", marker_color=lighten(ORANGE, 0.4),
                    hovertemplate="%{x}: %{y:.2f} billones<extra>Gasto cubierto</extra>")
    if mostrar[1]:
        # 31-dic-2025 es dato (punto lleno); desde 2026 el saldo es escenario (punteado)
        fig.add_scatter(x=d.index[:1], y=d.saldo.iloc[:1] / 1e12, mode="markers", name="Reserva al 31-dic-2025 (dato)",
                        marker=dict(color=BLUE, size=10), hovertemplate="%{x}: %{y:.2f} billones<extra>dato</extra>")
        fig.add_scatter(x=d.index, y=d.saldo.clip(lower=0) / 1e12, mode="lines", name="Saldo de la reserva (escenario)",
                        line=dict(color=BLUE, width=3, dash="dash"), hovertemplate="%{x}: %{y:.2f} billones<extra>Saldo (escenario)</extra>")
        if res["anio_agotamiento"]:
            a = res["anio_agotamiento"]
            fig.add_scatter(x=[a], y=[0], mode="markers", marker=dict(symbol="star", size=18, color=RED), name=f"Se agota en {a}")
    fig.update_layout(**PLOTLY_LAYOUT, title="Reserva frente al gasto que cubre (billones de $ de 2025)")
    fig.update_xaxes(title="Año")
    fig.update_yaxes(title="Billones de pesos de 2025", rangemode="tozero")
    return fig


def fapp_flow_chart(b: pd.DataFrame) -> go.Figure:
    """KPI 2.2, caja del FAPP en el primer semestre de 2026. b = fila de fapp_balance.csv (cierre 2026-06-30), montos en millones de pesos."""
    r = b.iloc[0]
    neto = r.cotizaciones_periodo_mm - r.beneficios_periodo_mm
    fig = go.Figure(go.Bar(
        x=["Cotizaciones recibidas", "Beneficios pagados", "Resultado del semestre"],
        y=[r.cotizaciones_periodo_mm / 1e6, -r.beneficios_periodo_mm / 1e6, neto / 1e6],
        marker_color=[BLUE, ORANGE, RED], text=[f"{v / 1e6:.2f}" for v in (r.cotizaciones_periodo_mm, -r.beneficios_periodo_mm, neto)],
        textposition="outside", cliponaxis=False, hovertemplate="%{x}: %{y:.2f} billones<extra></extra>"))
    fig.update_layout(**PLOTLY_LAYOUT, title="FAPP, enero-junio de 2026 (billones de pesos corrientes)", showlegend=False)
    fig.update_yaxes(title="Billones de pesos")
    return fig


def dependence_regions_chart(reg: pd.DataFrame, nacional: float) -> go.Figure:
    """KPI 2.2, dónde. reg: region_nombre, pct_sin_pension (% de los beneficiarios de la PGU que no reciben otra pensión)."""
    d = reg.sort_values("pct_sin_pension")
    detalle = {"beneficios_por_100", "peso_mes_por_65", "razon_soporte"} <= set(d.columns)
    fig = go.Figure(go.Bar(
        y=d.region_nombre, x=d.pct_sin_pension, orientation="h", marker_color=ORANGE,
        customdata=d[["beneficios_por_100", "peso_mes_por_65", "razon_soporte"]] if detalle else None,
        hovertemplate="<b>%{y}</b><br>Sin pensión propia: %{x:.1f}%"
                      + ("<br>Beneficios (PGU + APS vejez) por 100 personas 65+: %{customdata[0]:.0f}"
                         "<br>Por persona 65+: $%{customdata[1]:,.0f} al mes (pesos de 2025)"
                         "<br>Cotizantes por persona 65+: %{customdata[2]:.2f}" if detalle else "") + "<extra></extra>"))
    fig.add_vline(x=nacional, line_dash="dash", line_color=INK_MUTED, annotation_text=f"País: {nacional:.1f}%", annotation_position="top")
    fig.update_layout(**PLOTLY_LAYOUT, title="Sin pensión propia por región (% de la PGU)")
    fig.update_xaxes(title="% de los beneficiarios de la PGU")
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


def critical_point_chart(d: pd.DataFrame, pc: dict, view: str, nombre: str, trabajadores: str, carga_max: float,
                         mostrar: tuple = (True, True), pais: bool = True, es_base: bool = True) -> go.Figure:
    """KPI 1.2, análisis del punto crítico. d = salida de critical_point.serie_pais / serie_territorio;
    pc = critical_point.punto_critico(d); view = 'dinero' | 'razon'.
    En 'dinero' se superponen el costo (costo por persona de 65+ x población de 65+) y la capacidad (carga máxima x ingreso por
    trabajador x trabajadores); en 'razon', la razón de soporte observada y la razón de equilibrio R*. El cruce de las dos
    líneas es el punto crítico. Tramo observado sólido, escenario punteado; rombos = años con población regional (2024/2035/2050).
    mostrar = (primera línea, segunda línea): oculta la que esté en False (la estrella sólo se dibuja con ambas).
    Marcas de datos: país = un punto por cada año observado (2010-2025, todos los insumos existen); región = rombo lleno en 2024
    (único año con todos los insumos observados) y rombos vacíos en 2035 y 2050 (población del escenario regional; ingreso y
    costo son supuestos). Los años sin marca son interpolación o escenario, no datos."""
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
    zona_escenario(fig, float(obs.anio.max()) + 0.5, float(d.anio.max()) + 0.5)
    for (nom, y, col), visible in zip(series, mostrar):
        if not visible:
            continue
        yo, yp = y.loc[obs.index], y.loc[proy_c.index]
        if pais:  # un punto por año observado
            fig.add_scatter(x=obs.anio, y=yo, mode="lines+markers", name=nom, legendgroup=nom,
                            line=dict(color=col, width=3), marker=dict(size=6),
                            hovertemplate="%{x}: %{y:" + fmt + "}<extra>" + nom + "</extra>")
        else:     # región: un solo año observado, rombo lleno
            fig.add_scatter(x=obs.anio, y=yo, mode="lines+markers", name=nom, legendgroup=nom,
                            line=dict(color=col, width=3), marker=dict(symbol="diamond", size=13, color=col, line=dict(color="white", width=1.5)),
                            hovertemplate="%{x}: %{y:" + fmt + "}<extra>" + nom + "</extra>")
        fig.add_scatter(x=proy_c.anio, y=yp, mode="lines", name=nom + " (escenario)", legendgroup=nom, showlegend=False,
                        line=dict(color=col, width=3, dash="dash"),
                        hovertemplate="%{x}: %{y:" + fmt + "}<extra>" + nom + " (escenario)</extra>")
        if not pais and "ancla" in d and d.ancla.any():  # 2035 y 2050: población del escenario regional, rombo vacío
            a = d[d.ancla & d.proyectado]
            fig.add_scatter(x=a.anio, y=y.loc[a.index], mode="markers", legendgroup=nom, showlegend=False,
                            marker=dict(symbol="diamond", size=13, color="white", line=dict(color=col, width=2.5)),
                            hovertemplate="%{x}: %{y:" + fmt + "}<extra>" + nom + " (población del escenario)</extra>")
    # claves de lectura de las marcas (leyenda)
    gris = INK_SECONDARY
    if pais:
        claves = [("circle", gris, "solid", "Año observado (cotizantes, ingreso y gasto)"), (None, gris, "dash", "Escenario (supuestos)")]
    else:
        claves = [("diamond", gris, "solid", "Año observado (todos los insumos)"), ("diamond-open", gris, "solid", "Población del escenario regional"),
                  (None, gris, "dash", "Escenario (supuestos)")]
    for simbolo, c, dash, txt in claves:
        if simbolo:
            fig.add_scatter(x=[None], y=[None], mode="markers", name=txt, marker=dict(symbol=simbolo, size=10, color=c, line=dict(color=c, width=2)))
        else:
            fig.add_scatter(x=[None], y=[None], mode="lines", name=txt, line=dict(color=c, width=2, dash=dash))
    if all(mostrar) and pc["estado"] in ("cruza", "ya_superado"):
        xc = pc["anio_exacto"]
        yc = float(np.interp(xc, d.anio, series[0][1].values))
        rotulo = (f"Punto crítico ({'escenario base' if es_base else 'escenario'}): {pc['anio']}" if pc["estado"] == "cruza"
                  else f"Superado desde {pc['anio']}")
        fig.add_vline(x=xc, line_dash="dot", line_color=VIOLET, line_width=2)
        # rótulo bajo el de «Escenario» (que va arriba de la zona gris) para que no se tapen
        fig.add_annotation(x=xc, y=0.9, yref="paper", text=rotulo, showarrow=False, xanchor="right", xshift=-6,
                           font=dict(color=INK_PRIMARY, size=12), bgcolor="rgba(255,255,255,0.85)")
        fig.add_scatter(x=[xc], y=[yc], mode="markers", showlegend=False, hoverinfo="skip",
                        marker=dict(symbol="star", size=18, color=VIOLET, line=dict(color="white", width=1.5)))
    fig.update_layout(**PLOTLY_LAYOUT, title=titulo)
    fig.update_xaxes(title="Año")
    fig.update_yaxes(title=ytitle, rangemode="tozero")
    return fig


def estilo_kpi(fig: go.Figure, alto: int = 560) -> go.Figure:
    """Mismo estilo de texto que los gráficos del KPI 1.3: título, ejes, leyenda (abajo) y rótulos en negro sobre fondo claro.
    Llamar st.plotly_chart con theme=None para que Streamlit no reemplace estos colores."""
    fig.update_layout(title_font_color=INK_PRIMARY, legend_font_color=INK_PRIMARY, margin=dict(l=70, r=40, t=70, b=50),
                      legend=dict(orientation="h", y=-0.2, bgcolor="rgba(0,0,0,0)", font_color=INK_PRIMARY), height=alto,
                      separators=",.", modebar=dict(orientation="v"))
    con_coma(fig)
    fig.update_xaxes(tickfont_color=INK_PRIMARY, title_font_color=INK_PRIMARY, linecolor=GRIDLINE, automargin=True)
    fig.update_yaxes(tickfont_color=INK_PRIMARY, title_font_color=INK_PRIMARY, linecolor=GRIDLINE, automargin=True)
    fig.for_each_trace(lambda tr: tr.update(textfont_color=INK_PRIMARY) if hasattr(tr, "textfont") else None)   # mapas y otras trazas no tienen textfont
    fig.update_coloraxes(colorbar_tickfont_color=INK_PRIMARY, colorbar_title_font_color=INK_PRIMARY)
    fig.update_annotations(font_color=INK_PRIMARY)
    return fig

# KPI 1.3: texto oscuro explícito, para que título, ejes y leyenda se lean sobre el fondo claro aunque el
# dashboard esté en tema oscuro (llamar st.plotly_chart con theme=None para que Streamlit no lo reemplace)
_TEXTO_CLARO = dict(title_font_color=INK_PRIMARY, legend_font_color=INK_PRIMARY)
_EJE_CLARO = dict(tickfont_color=INK_PRIMARY, title_font_color=INK_PRIMARY, linecolor=GRIDLINE, automargin=True)
_MARGEN = dict(margin=dict(l=70, r=40, t=70, b=50))


def con_coma(fig: go.Figure) -> go.Figure:
    """Rótulos de texto y anotaciones con coma decimal (es-CL); los ejes y el hover ya usan separators=",."."""
    for tr in fig.data:
        t = getattr(tr, "text", None)
        if isinstance(t, str):
            tr.text = es_cl(t)
        elif t is not None:
            tr.text = [es_cl(x) for x in t]
    for a in fig.layout.annotations:
        a.text = es_cl(a.text)
    return fig


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
    return con_coma(fig)


def commissionable_share_line(df: pd.DataFrame, crec_base: float = 0.01) -> go.Figure:
    """KPI 1.3: % del flujo que pasa por cuentas individuales, real (línea continua) y escenarios (punteados), variante
    sin SIS; la variante con SIS va como línea gris delgada de sensibilidad (real + escenario base).
    df: anio, tipo (real / escenario / escenario_crec_1_5), variante (sin_sis / con_sis), kpi_1_3_pct."""
    sens = df[(df.variante == "con_sis") & df.tipo.isin(["real", "escenario"])].sort_values("anio")
    df = df[df.variante == "sin_sis"]
    real = df[df.tipo == "real"].sort_values("anio")
    ancla = real.iloc[[-1]]  # los escenarios parten del último año real
    fig = go.Figure()
    fig.add_scatter(x=sens.anio.astype(str), y=sens.kpi_1_3_pct, mode="lines", name="Incluyendo SIS en todos los años",
                    line=dict(color=lighten(INK_MUTED), width=1.5),
                    hovertemplate="Incluyendo SIS: %{y:.1f}%<extra></extra>")
    fig.add_scatter(x=real.anio.astype(str), y=real.kpi_1_3_pct, mode="lines+markers+text", name="Real",
                    line=dict(color=BLUE, width=3), text=[f"{v:.1f}%" for v in real.kpi_1_3_pct],
                    textposition="top center", textfont_color=INK_PRIMARY)
    variantes = sorted(t for t in df.tipo.unique() if t.startswith("escenario_crec_"))
    for tipo, nombre, color, dash in [("escenario", f"Escenario base (salario real {crec_base:+.1%} anual)".replace(".", ","), RED, "dash")] + [
            (t, f"Variante: salario real +{t.removeprefix('escenario_crec_').replace('_', ',')}% anual", INK_MUTED, "dot") for t in variantes]:
        e = pd.concat([ancla, df[df.tipo == tipo]]).sort_values("anio")
        if len(e) == 1:
            continue
        # rótulos en el mínimo, en 2033 (cotización completa) y en el último año del escenario base
        futuro = e[e.anio > ancla.anio.iloc[0]]
        claves = {int(futuro.loc[futuro.kpi_1_3_pct.idxmin(), "anio"]), 2033, int(e.anio.max())}
        rotulos = ["" if a not in claves or tipo != "escenario" else f"{v:.1f}%"
                   for a, v in zip(e.anio, e.kpi_1_3_pct)]
        fig.add_scatter(x=e.anio.astype(str), y=e.kpi_1_3_pct, mode="lines+markers+text", name=nombre,
                        line=dict(color=color, width=2.5, dash=dash), text=rotulos, textposition="bottom center",
                        textfont_color=INK_PRIMARY)
    fig.update_layout(**{**PLOTLY_LAYOUT, **_MARGEN, "legend": dict(orientation="h", y=-0.2, bgcolor="rgba(0,0,0,0)")},
                      **_TEXTO_CLARO, title="Parte del flujo previsional que pasa por cuentas individuales AFP (%)")
    fig.update_xaxes(type="category", title="Año", **_EJE_CLARO)
    fig.update_yaxes(title="% del flujo total", range=[0, 70], **_EJE_CLARO)
    return con_coma(fig)


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


def _burbujas(fig, df, x, y, hover, color, rango_x, rango_y, tam="cotizantes", tam_nombre="Cotizantes",
              tam_pct="share_cotizantes_pct"):
    """Burbujas por región con tamaño = `tam` (por defecto cotizantes); rótulos como anotaciones sin solaparse."""
    sizeref = df[tam].max() / _TAM_MAX_PX ** 2
    radios = list(np.sqrt(df[tam] / sizeref) / 2)
    fig.add_scatter(x=df[x], y=df[y], mode="markers", text=df.region_nombre, showlegend=False,
                    marker=dict(size=df[tam], sizemode="area", sizeref=sizeref, sizemin=4, color=color,
                                opacity=0.75, line=dict(color="white", width=1)),
                    customdata=np.stack([df[tam], df[tam_pct]], axis=1),
                    hovertemplate="<b>%{text}</b><br>" + hover
                    + f"<br>{tam_nombre}: %{{customdata[0]:,.0f}} (%{{customdata[1]:.1f}}% del total)<extra></extra>")
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
    return con_coma(fig)


CUADRANTES = {  # (cobertura alta, envejecimiento alto) -> (nombre, color de fondo, color del rótulo); tonos apagados
    (False, True): ("Riesgo doble", "#d9695f", "#9c2f27"),
    (False, False): ("Potencial de captación", "#e0a44a", "#8a5a0c"),
    (True, True): ("Base que envejece", "#9a85c4", "#5b448f"),
    (True, False): ("Núcleo a retener", "#5fa3b8", "#1f6179"),
}


def coverage_risk_matrix(df: pd.DataFrame, nac_cobertura: float, nac_65: float, pct_pob: dict) -> go.Figure:
    """KPI 1.1: matriz de riesgo cobertura × % 65+, cuadrantes cortados en los valores nacionales.
    df: kpi_cobertura_correlaciones_region.csv; pct_pob: nombre del cuadrante -> % de la población (Censo 2024)."""
    x0, x1 = _rango(df.cobertura_previsional_pct, 0.12)
    y0, y1 = _rango(df.pct_65_mas, 0.12)
    fig = go.Figure()
    for (alta_cob, alto_env), (nombre, color, color_texto) in CUADRANTES.items():
        qx0, qx1 = (nac_cobertura, x1) if alta_cob else (x0, nac_cobertura)
        qy0, qy1 = (nac_65, y1) if alto_env else (y0, nac_65)
        fig.add_shape(type="rect", x0=qx0, x1=qx1, y0=qy0, y1=qy1, fillcolor=color, opacity=0.2, line_width=0,
                      layer="below")
        fig.add_annotation(x=qx1 if alta_cob else qx0, y=qy1 if alto_env else qy0, text=f"<b>{nombre}</b><br>{num_cl(pct_pob.get(nombre, 0), 1)}% de la población",
                           xanchor="right" if alta_cob else "left", yanchor="top" if alto_env else "bottom",
                           align="right" if alta_cob else "left", showarrow=False, font=dict(color=color_texto, size=13), xshift=-6 if alta_cob else 6,
                           yshift=-4 if alto_env else 4)
    fig.add_vline(x=nac_cobertura, line_dash="dash", line_color=INK_MUTED,
                  annotation_text=f"Cobertura país {num_cl(nac_cobertura, 1)}%", annotation_position="bottom right",
                  annotation_font_color=INK_PRIMARY)
    fig.add_hline(y=nac_65, line_dash="dash", line_color=INK_MUTED,
                  annotation_text=f"65+ país {num_cl(nac_65, 1)}%", annotation_position="top left",
                  annotation_font_color=INK_PRIMARY)
    _burbujas(fig, df, "cobertura_previsional_pct", "pct_65_mas", "Cobertura: %{x:.1f}%<br>65+: %{y:.1f}%", INK_SECONDARY,
              (x0, x1), (y0, y1))
    fig.update_layout(**{**PLOTLY_LAYOUT, **_MARGEN}, **_TEXTO_CLARO, height=560, showlegend=False,
                      title="Matriz de riesgo: cobertura previsional × envejecimiento (burbuja = cotizantes)")
    fig.update_xaxes(title="Cobertura previsional (% de 15-64 que cotiza)", ticksuffix="%", range=[x0, x1], **_EJE_CLARO)
    fig.update_yaxes(title="Población de 65 años y más (% del total)", ticksuffix="%", range=[y0, y1], **_EJE_CLARO)
    return con_coma(fig)


def risk_quadrant(df: pd.DataFrame, nac_cobertura: float, nac_65: float) -> pd.Series:
    """Nombre del cuadrante de cada región (mismo corte que coverage_risk_matrix)."""
    return pd.Series([CUADRANTES[(c >= nac_cobertura, e > nac_65)][0]
                      for c, e in zip(df.cobertura_previsional_pct, df.pct_65_mas)], index=df.index)


def poverty_coverage_scatter(df: pd.DataFrame, r: float, rho: float, n: int) -> go.Figure:
    """KPI 2.3: pobreza 65+ (%) vs. cobertura previsional (%), burbuja = personas 65+ en pobreza, recta MCO.
    df: kpi_pobreza_cobertura_region.csv (region_nombre, cobertura_previsional_pct, pct_pobreza_65, n_pobres_65, share_pobres_pct)."""
    fig = go.Figure()
    pendiente, intercepto = np.polyfit(df.cobertura_previsional_pct, df.pct_pobreza_65, 1)
    xs = np.linspace(df.cobertura_previsional_pct.min(), df.cobertura_previsional_pct.max(), 50)
    fig.add_scatter(x=xs, y=intercepto + pendiente * xs, mode="lines", name="Recta MCO",
                    line=dict(color=RED, width=2, dash="dash"), hoverinfo="skip")
    rx, ry = _rango(df.cobertura_previsional_pct, 0.08), _rango(df.pct_pobreza_65, 0.12)
    _burbujas(fig, df, "cobertura_previsional_pct", "pct_pobreza_65", "Cobertura: %{x:.1f}%<br>Pobreza 65+: %{y:.1f}%", ORANGE,
              rx, ry, tam="n_pobres_65", tam_nombre="Personas 65+ en pobreza", tam_pct="share_pobres_pct")
    fig.add_annotation(xref="paper", yref="paper", x=0.99, y=0.99, xanchor="right", yanchor="top", showarrow=False,
                       text=f"r = {num_cl(r)}, ρ = {num_cl(rho)}, n = {n}", font=dict(color=INK_PRIMARY, size=13),
                       bgcolor="rgba(255,255,255,0.8)")
    fig.update_layout(**{**PLOTLY_LAYOUT, **_MARGEN}, **_TEXTO_CLARO, height=520, showlegend=False,
                      title="Pobreza 65+ vs. cobertura previsional (burbuja = personas 65+ en pobreza)")
    fig.update_xaxes(title="Cobertura previsional (% de 15-64 que cotiza, 2024)", ticksuffix="%", range=list(rx), **_EJE_CLARO)
    fig.update_yaxes(title="Personas 65+ en pobreza (%, CASEN 2022)", ticksuffix="%", range=list(ry), **_EJE_CLARO)
    return con_coma(fig)


def colores_legibles(fig: go.Figure) -> go.Figure:
    """Texto oscuro explícito en TODO el gráfico (título, ejes, ticks, barra de color, leyenda, rótulos y anotaciones), fondo claro,
    coma decimal y barra de herramientas vertical. Sin esto, el tema oscuro de Streamlit pinta el texto gris claro sobre fondo blanco."""
    fig.update_layout(font_color=INK_PRIMARY, title_font_color=INK_PRIMARY, legend_font_color=INK_PRIMARY,
                      legend_title_font_color=INK_PRIMARY, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
                      separators=",.", modebar=dict(orientation="v"))
    # automargin: los nombres de región y los ticks no se cortan (el margen fijo de 10 px era muy chico)
    fig.update_xaxes(tickfont_color=INK_PRIMARY, title_font_color=INK_PRIMARY, automargin=True)
    fig.update_yaxes(tickfont_color=INK_PRIMARY, title_font_color=INK_PRIMARY, automargin=True)
    if any(getattr(tr, "coloraxis", None) for tr in fig.data):  # solo si hay escala de color (mapas): si no, aparece una barra vacía
        fig.update_coloraxes(colorbar_tickfont_color=INK_PRIMARY, colorbar_title_font_color=INK_PRIMARY)
    for tr in fig.data:
        if hasattr(tr, "textfont") and tr.textfont.color is None:   # respeta rótulos con color propio (p. ej. blanco dentro de barras)
            tr.textfont.color = INK_PRIMARY
    for an in fig.layout.annotations:
        if an.font.color is None:
            an.font.color = INK_PRIMARY
    return con_coma(fig)


def mostrar(fig: go.Figure, config: dict = None, **kwargs):
    """Única forma de dibujar un gráfico en el dashboard: colores legibles y theme=None (Streamlit no reemplaza los colores)."""
    import streamlit as st
    from utils import PLOTLY_DL_CONFIG
    st.plotly_chart(colores_legibles(fig), use_container_width=True, config=config or PLOTLY_DL_CONFIG, theme=None, **kwargs)
