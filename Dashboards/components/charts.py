"""Constructores de figuras compartidos por las páginas del modo final.
Cada función recibe DataFrames ya cargados (no lee archivos) y devuelve un go.Figure."""
import textwrap

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from components.cost_analysis import CARGA_MAX
from utils import (BLUE, ORANGE, VIOLET, RED, AQUA, INK_PRIMARY, INK_SECONDARY, INK_MUTED, GRIDLINE, SURFACE, PLOTLY_LAYOUT,
                   CATEGORICAL, lighten, es_cl)

UMBRAL_VEJEZ = 65
ANIO_BASE = 2024  # último año estimado de las proyecciones INE base 2024
BARRAS = dict(bargap=0.33)  # pauta de la clase: separación entre barras = ½ ancho de barra


def _titulo(mensaje: str, detalle: str = "", ancho: int = 50) -> str:
    """Pauta de la clase: el título dice el mensaje (no describe) y no lleva siglas. Debajo, más pequeño, la unidad o el alcance.
    Los números se escriben con punto decimal y aquí se pasan al formato es-CL. Plotly no parte las líneas largas: se parten aquí
    (`ancho` caracteres el mensaje, 20 más el detalle) y colores_legibles agranda el margen superior según las líneas."""
    lineas = textwrap.wrap(mensaje, ancho)
    if detalle:
        lineas.append("<sup>" + "<br>".join(textwrap.wrap(detalle, ancho + 20)) + "</sup>")
    return es_cl("<br>".join(lineas))


def _subtitulo(texto: str, ancho: int = 46) -> str:
    """Título de un gráfico dentro de una figura con varios (subplot): el mensaje, partido en líneas cortas."""
    return es_cl("<br>".join(textwrap.wrap(texto, ancho)))


def _extremos(d: pd.DataFrame, col: str) -> tuple:
    """(fila con el valor mínimo, fila con el valor máximo) de `col`."""
    return d.loc[d[col].idxmin()], d.loc[d[col].idxmax()]


def _envolver(texto: str, ancho: int = 22) -> str:
    return "<br>".join(textwrap.wrap(texto, ancho))


def rotular_final(fig: go.Figure, puntos: list, row: int = None, col: int = None, rango_y: tuple = None, alto_px: int = 360,
                  ancho_texto: int = 24) -> go.Figure:
    """Etiquetado directo (pauta de la clase: mejor que la leyenda): escribe el nombre de cada línea junto a su último punto.
    puntos = [(x, y, texto, color)]. Las etiquetas se separan en vertical lo justo para no taparse: se estima la altura de cada una
    (líneas de texto x 15 px) y los px por unidad del eje con rango_y (por defecto 0 a 1,1 x el mayor y) y alto_px (alto del área
    de trazado). Requiere dejar espacio a la derecha con ampliar_derecha(); en ejes de categorías x va por posición."""
    if not puntos:
        return fig
    lo, hi = rango_y if rango_y else (0.0, 1.1 * max(p[1] for p in puntos))
    px_u = alto_px / (hi - lo) if hi > lo else 1.0
    items = sorted(({"x": p[0], "y": p[1], "color": p[3], "texto": _envolver(p[2], ancho_texto)} for p in puntos), key=lambda i: i["y"])
    for i in items:
        i["h"] = 15 * (i["texto"].count("<br>") + 1) + 4
        i["pos"] = i["y"] * px_u
    for prev, cur in zip(items, items[1:]):  # de abajo hacia arriba: separa lo justo
        cur["pos"] = max(cur["pos"], prev["pos"] + (prev["h"] + cur["h"]) / 2)
    mover = sum(i["pos"] - i["y"] * px_u for i in items) / len(items)  # centra el desplazamiento total
    for i in items:
        fig.add_annotation(x=i["x"], y=i["y"], text=f"<span style='color:{i['color']}'>■</span> {i['texto']}", showarrow=False,
                           xanchor="left", xshift=8, yshift=i["pos"] - i["y"] * px_u - mover, align="left",
                           font=dict(color=INK_PRIMARY, size=12), row=row, col=col)
    return fig


def ampliar_derecha(fig: go.Figure, x0: float, x1: float, fraccion: float = 0.28, row: int = None, col: int = None) -> go.Figure:
    """Deja espacio a la derecha del último punto para las etiquetas directas."""
    fig.update_xaxes(range=[x0, x1 + fraccion * (x1 - x0)], row=row, col=col)
    return fig


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
    p65 = 100 * (h[h.index >= UMBRAL_VEJEZ].sum() + m[m.index >= UMBRAL_VEJEZ].sum()) / (h.sum() + m.sum())
    fig.update_layout(**PLOTLY_LAYOUT, barmode="overlay", height=520,
                      title=_titulo(f"El {p65:.1f}% de las personas en Chile tiene 65 años o más", "Pirámide de población por edad y sexo, Censo 2024"))
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
    p65 = []
    for col, (h, m) in enumerate([(ch, cm), (ah, am)], start=1):
        hp, mp = pct(h, m)
        p65.append(hp[hp.index >= UMBRAL_VEJEZ].sum() + mp[mp.index >= UMBRAL_VEJEZ].sum())
        xmax = max(xmax, hp.max(), mp.max())
        fig.add_bar(y=hp.index, x=-hp.values, orientation="h", name="Hombres", legendgroup="H", showlegend=col == 1,
                    marker_color=[lighten(BLUE) if e < UMBRAL_VEJEZ else BLUE for e in hp.index], row=1, col=col)
        fig.add_bar(y=mp.index, x=mp.values, orientation="h", name="Mujeres", legendgroup="M", showlegend=col == 1,
                    marker_color=[lighten(ORANGE) if e < UMBRAL_VEJEZ else ORANGE for e in mp.index], row=1, col=col)
        fig.add_hline(y=UMBRAL_VEJEZ, line_color=RED, line_width=1.2, line_dash="dot", row=1, col=col)
    fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=10, r=10, t=70, b=10)}, barmode="overlay", height=520,
                      title=_titulo(f"En 2024, {p65[0]:.1f}% de la población de Chile y {p65[1]:.1f}% de la de Alemania tiene 65 años o más",
                                    "Pirámides de población por edad y sexo, en % de la población total de cada país"))
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
    v24, v70 = (float(proy.loc[proy.anio == a, "pct_65_mas"].iloc[0]) for a in (ANIO_BASE, 2070))
    fig.update_layout(**PLOTLY_LAYOUT, title=_titulo(f"La población de 65 años o más pasará de {v24:.0f}% en {ANIO_BASE} a {v70:.0f}% en 2070",
                                                     "Chile, 1992-2070; desde 2025 es proyección"))
    fig.update_xaxes(title="Año")
    fig.update_yaxes(title="% de la población de 65 años o más", rangemode="tozero")
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
    fig.update_layout(**PLOTLY_LAYOUT, title=_titulo(f"La población de 15 a 64 años llega a su máximo en {int(peak.anio)} y desde entonces disminuye",
                                                     "Chile, personas en edad de trabajar, 1992-2070"))
    fig.update_xaxes(title="Año")
    fig.update_yaxes(title="Población de 15 a 64 años (millones)", rangemode="tozero")
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
    lo, hi = _extremos(df, var)
    fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=0, r=0, t=70, b=0)}, height=640,
                      title=_titulo(f"{hi.region_nombre} tiene el valor más alto ({hi[var]:.1f}) y {lo.region_nombre} el más bajo ({lo[var]:.1f})", label))
    return fig


def region_bars(df: pd.DataFrame, var: str, label: str, nacional: float, fmt: str = ".2f", color: str = BLUE) -> go.Figure:
    """Barras horizontales por región, ordenadas, con línea del promedio nacional."""
    d = df.sort_values(var)
    fig = px.bar(d, x=var, y="region_nombre", orientation="h", color_discrete_sequence=[color],
                 labels={var: label, "region_nombre": ""})
    fig.add_vline(x=nacional, line_dash="dash", line_color="#52514e",
                  annotation_text=f"País: {format(nacional, fmt)}", annotation_position="top")
    lo, hi = _extremos(d, var)
    fig.update_layout(**PLOTLY_LAYOUT, **BARRAS,
                      title=_titulo(f"{hi.region_nombre} tiene el valor más alto ({format(hi[var], fmt)}) y {lo.region_nombre} el más bajo ({format(lo[var], fmt)})", label))
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
    fig.update_layout(**PLOTLY_LAYOUT, barmode="group", title=titulo, **BARRAS, bargroupgap=0)
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
                               _titulo(f"En {d.iloc[0].region_nombre} hay {d.iloc[0].razon_soporte_previsional:.2f} cotizantes por persona de 65+; en "
                                       f"{d.iloc[-1].region_nombre}, {d.iloc[-1].razon_soporte_previsional:.2f}",
                                       f"Cotizantes y personas de 65+ por región* (país: {nacional:.2f})"))


def region_coverage_people_bars(df: pd.DataFrame, nacional: float) -> go.Figure:
    """KPI 1.1, vista en personas: mismo orden que la cobertura, con la población de 15-64 (Censo 2024) y los cotizantes en
    valores absolutos y la cobertura escrita junto a cada región."""
    d = df.sort_values("cobertura_previsional_pct")
    return _region_people_bars(d, ("pob_15_64", "Población 15-64 (Censo 2024)", lighten(ORANGE)),
                               ("cotizantes_2024", "Cotizantes (dic-2024)", ORANGE),
                               [f"{c:.1f}%".replace(".", ",") for c in d.cobertura_previsional_pct],
                               _titulo(f"Cotiza {d.iloc[0].cobertura_previsional_pct:.1f}% de las personas de 15 a 64 años en {d.iloc[0].region_nombre} y "
                                       f"{d.iloc[-1].cobertura_previsional_pct:.1f}% en {d.iloc[-1].region_nombre}",
                                       "Cotizantes y población de 15 a 64 años por región"), dtick=2_000_000)


def poverty_people_bars(df: pd.DataFrame, nacional: float) -> go.Figure:
    """KPI 2.3, vista en personas: mismo orden que el % de pobreza, con las personas 65+ de la CASEN 2022 y las que están
    en pobreza (porcentaje × población expandida), y el porcentaje escrito junto a cada región. df: region_nombre,
    pob_65_expandida, n_pobres, pct_pobreza_65."""
    d = df.sort_values("pct_pobreza_65")
    return _region_people_bars(d, ("pob_65_expandida", "Personas 65+ (CASEN 2022)", lighten(ORANGE)),
                               ("n_pobres", "Personas 65+ en pobreza", ORANGE),
                               [f"{p:.1f}%".replace(".", ",") for p in d.pct_pobreza_65],
                               _titulo(f"En {d.iloc[-1].region_nombre}, {d.iloc[-1].pct_pobreza_65:.1f}% de las personas de 65+ está en pobreza; en "
                                       f"{d.iloc[0].region_nombre}, {d.iloc[0].pct_pobreza_65:.1f}%", "Personas de 65+ y en pobreza por región"), dtick=250_000)


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
                        name="Dato real (cotizantes diciembre / población 65+)", showlegend=False,
                        hovertemplate="%{x}: %{y:.2f}<extra>real</extra>")
        fig.add_scatter(x=esc.anio, y=esc.razon, mode="lines+markers", line=dict(color=RED, width=3, dash="dash"), marker=dict(size=4),
                        name="Escenario (cobertura constante, población INE)", showlegend=False,
                        hovertemplate="%{x}: %{y:.2f}<extra>escenario</extra>")
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
    r0, r1 = pts.iloc[0], pts.iloc[-1]
    fig.update_layout(**PLOTLY_LAYOUT, title=_titulo(f"En {nombre}, los cotizantes por persona de 65+ bajan de {r0.razon:.2f} en {int(r0.anio)} a {r1.razon:.2f} en {int(r1.anio)}",
                                                     "Línea continua = datos; punteada sobre fondo gris = escenario con cobertura constante"))
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
    v0, v1 = d.iloc[0], d.iloc[-1]
    fig.update_layout(**PLOTLY_LAYOUT, title=_titulo(f"El costo público por persona de 65+ subió de ${v0.costo_65 / 1e6:.2f} millones en {int(v0.anio)} a ${v1.costo_65 / 1e6:.2f} millones en {int(v1.anio)}",
                                                     "Gasto en vejez por persona de 65+, millones de pesos de 2025"))
    fig.update_xaxes(title="Año", dtick=1)
    fig.update_yaxes(title="Millones de $ de 2025 por persona", rangemode="tozero")
    return fig


def spending_vs_population_growth(d: pd.DataFrame) -> go.Figure:
    """KPI 2.1: crecimiento anual (%) del gasto real en edad avanzada vs. la población 65+. d: anio, gasto, pob_65."""
    g = d.set_index("anio")[["gasto", "pob_65"]].pct_change().dropna() * 100
    fig = go.Figure()
    fig.add_bar(x=g.index, y=g.gasto, name="Gasto real en edad avanzada", marker_color=RED)
    fig.add_bar(x=g.index, y=g.pob_65, name="Población 65+", marker_color=BLUE)
    n = len(d) - 1
    cagr = lambda c: 100 * ((d[c].iloc[-1] / d[c].iloc[0]) ** (1 / n) - 1)  # noqa: E731
    fig.update_layout(**PLOTLY_LAYOUT, barmode="group", **BARRAS,
                      title=_titulo(f"Entre {int(d.anio.iloc[0])} y {int(d.anio.iloc[-1])}, el gasto real creció {cagr('gasto'):.1f}% al año y la población de 65+, {cagr('pob_65'):.1f}%",
                                    "Variación anual de cada año, %"))
    fig.update_xaxes(title="Año", dtick=1)
    fig.update_yaxes(title="Variación anual (%)", zeroline=True, zerolinecolor=INK_MUTED)
    return fig


def cost_components_chart(h: pd.DataFrame) -> go.Figure:
    """KPI 2.1: costo público por persona 65+ apilado por componente (millones de $ de 2025). h: salida de serie_historica."""
    fig = go.Figure()
    for col, nombre, color in (("pgu_65", "Pensión Garantizada Universal (desde 2022)", BLUE), ("pbs_aps_65", "Pensión Básica y Aporte Previsional Solidario de vejez", VIOLET),
                               ("resto_65", "Resto de 'Edad avanzada' (sistema antiguo y otros)", ORANGE)):
        fig.add_bar(x=h.index, y=h[col] / 1e6, name=nombre, marker_color=color,
                    hovertemplate="%{x}: $%{y:.2f} millones<extra>" + nombre + "</extra>")
    fig.add_vline(x=2021.5, line_dash="dash", line_color=INK_MUTED, annotation_text="Pensión Garantizada Universal", annotation_position="top")
    ult = h.iloc[-1]
    tot = ult.pgu_65 + ult.pbs_aps_65 + ult.resto_65
    fig.update_layout(**PLOTLY_LAYOUT, barmode="stack", **BARRAS,
                      title=_titulo(f"En {int(h.index[-1])}, la Pensión Garantizada Universal es {100 * ult.pgu_65 / tot:.0f}% del costo público por persona de 65+",
                                    "Costo por persona de 65+ según componente, millones de pesos de 2025"))
    fig.update_xaxes(title="Año", dtick=1)
    fig.update_yaxes(title="Millones de $ de 2025 por persona 65+")
    return fig


def beneficiaries_chart(h: pd.DataFrame) -> go.Figure:
    """KPI 2.1: cuántos de cada 100 personas 65+ reciben un beneficio (PGU/PBS/APS) y cuánto paga el Estado por beneficio."""
    a0, a1 = h.index[0], h.index[-1]
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.12,
                        subplot_titles=(_subtitulo(f"De cada 100 personas de 65+, {100 * h.cobertura.iloc[0]:.0f} recibían un beneficio en {a0} y {100 * h.cobertura.iloc[-1]:.0f} en {a1}"),
                                        _subtitulo(f"El pago anual por beneficio pasó de ${h.monto_por_beneficio.iloc[0] / 1e6:.2f} a ${h.monto_por_beneficio.iloc[-1] / 1e6:.2f} millones")))
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
    fig.update_layout(**PLOTLY_LAYOUT, title=_titulo(f"El costo por persona de 65+ llegó a {h.costo_pct_pib_pc[pico]:.1f}% del producto interno bruto per cápita en {pico}",
                                                     "Costo público por persona de 65+ en % del producto interno bruto por habitante"))
    fig.update_xaxes(title="Año", dtick=1)
    fig.update_yaxes(title="% del producto interno bruto per cápita", rangemode="tozero")
    return fig


def burden_chart(h: pd.DataFrame, base: str = "mediana") -> go.Figure:
    """KPI 2.1: izquierda, pago plano mensual por ocupado frente al 10 % del ingreso típico (mediana o promedio);
    derecha, ocupados por persona 65+: los que hay vs. los necesarios si cada uno aportara ese 10 %."""
    u = h.iloc[-1]
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.22,
                        subplot_titles=(_subtitulo(f"En {h.index[-1]}, repartir el gasto cuesta ${u.pago_plano:,.0f} al mes por ocupado: {100 * u.pago_plano / u.ingreso_mensual:.1f}% del ingreso ({base})"),
                                        _subtitulo(f"Hay {u.ocupados_por_65:.1f} ocupados por persona de 65+; harían falta {u.razon_necesaria:.1f} aportando el 10 %")))
    fig.add_scatter(x=h.index, y=h.pago_plano, mode="lines+markers", name="Pago por ocupado si se repartiera el gasto", showlegend=False,
                    line=dict(color=RED, width=3), row=1, col=1, hovertemplate="%{x}: $%{y:,.0f} al mes<extra></extra>")
    fig.add_scatter(x=h.index, y=CARGA_MAX * h.ingreso_mensual, mode="lines+markers", name=f"10 % del ingreso ({base})", showlegend=False,
                    line=dict(color=INK_MUTED, width=3, dash="dot"), row=1, col=1, hovertemplate="%{x}: $%{y:,.0f} al mes<extra></extra>")
    fig.add_scatter(x=h.index, y=h.ocupados_por_65, mode="lines+markers", name="Ocupados por persona 65+ (los que hay)", showlegend=False,
                    line=dict(color=BLUE, width=3), row=1, col=2)
    fig.add_scatter(x=h.index, y=h.razon_necesaria, mode="lines+markers", name="Ocupados necesarios aportando el 10 %", showlegend=False,
                    line=dict(color=RED, width=3, dash="dash"), row=1, col=2)
    x0, x1 = float(h.index.min()), float(h.index.max())
    rotular_final(fig, [(x1, u.pago_plano, "Pago por ocupado si se repartiera el gasto", RED),
                        (x1, CARGA_MAX * u.ingreso_mensual, f"10 % del ingreso ({base})", INK_MUTED)], row=1, col=1)
    rotular_final(fig, [(x1, u.ocupados_por_65, "Ocupados por persona de 65+ (los que hay)", BLUE),
                        (x1, u.razon_necesaria, "Ocupados necesarios aportando el 10 %", RED)], row=1, col=2)
    fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=10, r=170, t=90, b=10)})  # r: sitio para las etiquetas del panel derecho
    fig.update_xaxes(title_text="Año", dtick=2)
    ampliar_derecha(fig, x0, x1, row=1, col=1)
    ampliar_derecha(fig, x0, x1, row=1, col=2)
    fig.update_yaxes(title_text="$ de 2025 al mes", rangemode="tozero", col=1)
    fig.update_yaxes(title_text="Ocupados por persona 65+", rangemode="tozero", col=2)
    return fig


def cost_projection_chart(h: pd.DataFrame, p: pd.DataFrame, base: str = "mediana") -> go.Figure:
    """KPI 2.1: escenario 2025-2050. Izquierda: gasto en edad avanzada (% del PIB). Derecha: carga requerida sobre el sueldo mediano vs. 10 %."""
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.12,
                        subplot_titles=(_subtitulo(f"El gasto en edad avanzada pasaría de {h.pct_pib.iloc[-1]:.1f}% a {p.pct_pib.iloc[-1]:.1f}% del producto interno bruto entre {h.index[-1]} y {p.index[-1]}"),
                                        _subtitulo(f"La carga sobre el ingreso ({base}) pasaría de {100 * h.carga_requerida.iloc[-1]:.1f}% a {100 * p.carga_requerida.iloc[-1]:.1f}% en {p.index[-1]}")))
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
    fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=10, r=10, t=90, b=10),
                      "legend": dict(orientation="h", y=-0.2, bgcolor="rgba(0,0,0,0)")})
    fig.update_xaxes(title_text="Año")
    fig.update_yaxes(title_text="% del producto interno bruto", rangemode="tozero", col=1)
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
    u = df.dropna(subset=["pilar_pct_pib"]).iloc[-1]
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False,
                      title=_titulo(f"En {int(u.anio)}, la Pensión Garantizada Universal y las pensiones solidarias pesan {u.pilar_pct_pib:.2f}% del producto interno bruto",
                                    "Peso fiscal de las pensiones no contributivas, % del producto interno bruto"))
    rotular_final(fig, [(df.anio.max(), df.pilar_pct_pib.iloc[-1], "Pensión Garantizada Universal y pensiones solidarias", ORANGE)]
                  + ([(ea.anio.max(), ea.edad_avanzada_pct_pib.iloc[-1], "Gasto total del Gobierno Central en edad avanzada", VIOLET)] if len(ea) else []))
    fig.update_xaxes(title="Año", dtick=1)
    ampliar_derecha(fig, float(df.anio.min()), float(df.anio.max()), 0.4)
    fig.update_yaxes(title="% del producto interno bruto", rangemode="tozero")
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
                        line=dict(color=VIOLET, width=3, dash="dash"), fill="tonexty" if mostrar[1] else None, fillcolor="rgba(92,26,92,0.12)",
                        hovertemplate="%{x}: %{y:.2f}% (escenario)<extra></extra>")
    fig.add_hline(y=base, line_dash="dot", line_color=INK_MUTED, annotation_text=f"Peso de 2025: {base:.2f}%",
                  annotation_position="bottom right")
    fin = p.carga_pct_pib.iloc[-1] if con_fapp and mostrar[2] else p.pilar_pct_pib.iloc[-1]
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False,
                      title=_titulo(f"El peso fiscal del Pilar Solidario pasaría de {base:.2f}% en {int(p.index.min())} a {fin:.2f}% del producto interno bruto en {int(p.index.max())}",
                                    "Observado hasta el último año con datos; escenario después"))
    puntos = []
    if mostrar[0]:
        puntos.append((hist.anio.max(), hist.pilar_pct_pib.iloc[-1], "Observado", ORANGE))
    if mostrar[1]:
        puntos.append((p.index.max(), p.pilar_pct_pib.iloc[-1], "Escenario del Pilar Solidario", ORANGE))
    if con_fapp and mostrar[2]:
        puntos.append((p.index.max(), p.carga_pct_pib.iloc[-1], "Escenario con aporte al Fondo de Ahorro Previsional Solidario", VIOLET))
    rotular_final(fig, puntos)
    fig.update_xaxes(title="Año")
    ampliar_derecha(fig, float(hist.anio.min()), float(p.index.max()), 0.4)
    fig.update_yaxes(title="% del producto interno bruto", rangemode="tozero")
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
    fig.update_layout(**PLOTLY_LAYOUT, barmode="stack", **BARRAS,
                      title=_titulo(f"En {int(f.anio.iloc[-1])}, el Fondo de Reserva de Pensiones financió {pct.iloc[-1]:.1f}% del Pilar Solidario; el resto salió del presupuesto general",
                                    "Quién paga el Pilar Solidario, billones de pesos de 2025"))
    fig.update_yaxes(title="Billones de pesos de 2025")
    return fig


def fapp_schedule_chart(p: pd.DataFrame) -> go.Figure:
    """KPI 2.2, calendario del aporte del Estado al FAPP (Ley 21.735). p = financiamiento.proyeccion_carga (aporte_fapp, pib_real25)."""
    d = p[p.aporte_fapp > 0]
    fig = go.Figure(go.Bar(x=d.index, y=d.aporte_fapp / 1e12, marker_color=VIOLET, customdata=100 * d.aporte_fapp / d.pib_real25,
                           hovertemplate="%{x}: %{y:.2f} billones (%{customdata:.2f}% del PIB)<extra></extra>"))
    fig.update_layout(**PLOTLY_LAYOUT, **BARRAS, showlegend=False,
                      title=_titulo(f"El Estado aportará al Fondo de Ahorro Previsional Solidario desde {int(d.index.min())}, hasta {d.aporte_fapp.max() / 1e12:.2f} billones al año",
                                    "Calendario del aporte según la Ley 21.735, billones de pesos de 2025"))
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
            fig.add_scatter(x=[a], y=[0], mode="markers", marker=dict(symbol="star", size=18, color=VIOLET), name=f"Se agota en {a}")
    msg = (f"La reserva se agotaría en {res['anio_agotamiento']}" if res["anio_agotamiento"]
           else f"La reserva alcanza para todo el período hasta {int(d.index.max())}")
    fig.update_layout(**PLOTLY_LAYOUT, title=_titulo(msg, "Reserva frente al gasto que cubre, billones de pesos de 2025"))
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
        marker_color=BLUE, text=[f"{v / 1e6:.2f}" for v in (r.cotizaciones_periodo_mm, -r.beneficios_periodo_mm, neto)],
        textposition="outside", cliponaxis=False, hovertemplate="%{x}: %{y:.2f} billones<extra></extra>"))
    fig.update_layout(**PLOTLY_LAYOUT, **BARRAS, showlegend=False,
                      title=_titulo(f"En el primer semestre de 2026 el Fondo de Ahorro Previsional Solidario recibió {r.cotizaciones_periodo_mm / 1e6:.2f} billones y pagó {r.beneficios_periodo_mm / 1e6:.2f}",
                                    "Caja de enero a junio de 2026, billones de pesos corrientes"))
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
    lo, hi = d.iloc[0], d.iloc[-1]
    fig.update_layout(**PLOTLY_LAYOUT, **BARRAS,
                      title=_titulo(f"En {hi.region_nombre}, {hi.pct_sin_pension:.0f}% de quienes reciben la Pensión Garantizada Universal no tiene otra pensión; en {lo.region_nombre}, {lo.pct_sin_pension:.0f}%",
                                    "Sin pensión propia por región, % de los beneficiarios"))
    fig.update_xaxes(title="% de los beneficiarios de la Pensión Garantizada Universal")
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
    lo, hi = d.iloc[0], d.iloc[-1]
    fig.update_layout(**PLOTLY_LAYOUT, **BARRAS,
                      title=_titulo(f"La pobreza en personas de 65+ va de {lo.pct_pobreza_65:.1f}% en {lo.region_nombre} a {hi.pct_pobreza_65:.1f}% en {hi.region_nombre}",
                                    "Pobreza por ingresos, % de personas de 65+ (barra = intervalo de confianza de 95%)"))
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
                         mostrar: tuple = (True, True), pais: bool = True, es_base: bool = True,
                         colchon: pd.Series = None, r_colchon: float = 0.0) -> go.Figure:
    """KPI 1.2, análisis del punto crítico. d = salida de critical_point.serie_pais / serie_territorio;
    pc = critical_point.punto_critico(d); view = 'dinero' | 'razon'.
    En 'dinero' se superponen el costo (costo por persona de 65+ x población de 65+) y la capacidad (carga máxima x ingreso por
    trabajador x trabajadores); en 'razon', la razón de soporte observada y la razón de equilibrio R*. El cruce de las dos
    líneas es el punto crítico. Tramo observado sólido, escenario punteado; rombos = años con población regional (2024/2035/2050).
    mostrar = (primera línea, segunda línea): oculta la que esté en False (la estrella sólo se dibuja con ambas).
    colchon (opcional, solo vista 'dinero'): colchón acumulado de critical_point.colchon, como área en el mismo eje (misma unidad,
    pero es un saldo acumulado, no un flujo anual); r_colchon = rentabilidad real con la que se calculó (la lleva la tarjeta).
    Marcas de datos: país = un punto por cada año observado (2010-2025, todos los insumos existen); región = rombo lleno en 2024
    (único año con todos los insumos observados) y rombos vacíos en 2035 y 2050 (población del escenario regional; ingreso y
    costo son supuestos). Los años sin marca son interpolación o escenario, no datos."""
    if view == "dinero":
        div, unidad = _unidad_dinero(max(d.costo_total.max(), d.capacidad.max()))
        series = [("Costo del Pilar Solidario de vejez", d.costo_total / div, RED),
                  (f"Capacidad: {carga_max:.0%} del sueldo de los {trabajadores}", d.capacidad / div, BLUE)]
        ytitle, fmt = unidad, ",.2f"
        titulo = _titulo({"cruza": f"{nombre}: el costo del Pilar Solidario supera la capacidad desde {pc['anio']}",
                          "ya_superado": f"{nombre}: el costo del Pilar Solidario ya supera la capacidad desde {pc['anio']}",
                          "no_cruza": f"{nombre}: el costo del Pilar Solidario no supera la capacidad antes de {int(d.anio.max())}"}[pc["estado"]],
                         f"Costo frente a capacidad (tope de {carga_max:.0%} del sueldo), {unidad}")
    else:
        series = [(f"Razón de soporte observada ({trabajadores} por persona de 65+)", d.razon_soporte, BLUE),
                  (f"Razón de equilibrio R* (carga máxima {carga_max:.0%})", d.razon_equilibrio, ORANGE)]
        ytitle, fmt = f"{trabajadores.capitalize()} por persona de 65+", ".2f"
        titulo = _titulo({"cruza": f"{nombre}: los {trabajadores} por persona de 65+ caen bajo la razón de equilibrio desde {pc['anio']}",
                          "ya_superado": f"{nombre}: los {trabajadores} por persona de 65+ ya están bajo la razón de equilibrio desde {pc['anio']}",
                          "no_cruza": f"{nombre}: los {trabajadores} por persona de 65+ no caen bajo la razón de equilibrio antes de {int(d.anio.max())}"}[pc["estado"]],
                         f"Razón de soporte frente a razón de equilibrio (tope de {carga_max:.0%} del sueldo)")

    ancho = d.anio.max() - d.anio.min()
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
            fig.add_scatter(x=obs.anio, y=yo, mode="lines+markers", name=nom, legendgroup=nom, showlegend=False,
                            line=dict(color=col, width=3), marker=dict(size=6),
                            hovertemplate="%{x}: %{y:" + fmt + "}<extra>" + nom + "</extra>")
        else:     # región: un solo año observado, rombo lleno
            fig.add_scatter(x=obs.anio, y=yo, mode="lines+markers", name=nom, legendgroup=nom, showlegend=False,
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
    if colchon is not None and view == "dinero":
        # pauta de la clase para el doble eje: estilo distinto (área) y color contrastante; se dibuja hasta que el colchón se agota
        c = (colchon / div).dropna()
        neg = c[c <= 0]
        if len(neg):
            c = c.loc[:neg.index[0]].clip(lower=0)
        fig.add_scatter(x=d.anio.loc[c.index], y=c, mode="lines", name="Colchón acumulado", showlegend=False,
                        line=dict(color=AQUA, width=1.5), fill="tozeroy", fillcolor="rgba(27,175,122,0.18)",
                        hovertemplate="%{x}: %{y:" + fmt + "}<extra>Colchón acumulado</extra>")
        fig.add_annotation(x=float(d.anio.loc[c.index].iloc[-1]), y=0, text=f"<span style='color:{AQUA}'>■</span> Colchón acumulado",
                           showarrow=False, xanchor="left", xshift=8, yshift=26, font=dict(color=INK_PRIMARY, size=12))
    # etiquetado directo de las líneas (pauta de la clase); la leyenda queda solo para las claves de las marcas
    puntos = [(float(d.anio.max()), float(y.iloc[-1]), nom, col) for (nom, y, col), visible in zip(series, mostrar) if visible]
    rotular_final(fig, puntos)
    paso = 10 if ancho > 30 else 5  # sin marcas en el espacio que se deja para las etiquetas
    fig.update_xaxes(range=[d.anio.min() - 0.5, d.anio.max() + 0.34 * ancho],
                     tickvals=list(range(int(np.ceil(d.anio.min() / paso) * paso), int(d.anio.max()) + 1, paso)))
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


def carga_waterfall(dec: dict, nombre: str, a0: int, a1: int) -> go.Figure:
    """KPI 1.2, gráfico de cascada (pauta de la clase para mostrar de qué se compone un aumento): de la carga requerida del año a0
    a la del año a1, cuánto aporta cada factor. dec = critical_point.descomponer_carga. Barras en puntos porcentuales del sueldo."""
    partes = dec["partes"]
    sube = lambda v: v > 0  # noqa: E731
    x = [f"Carga {a0}"] + [n for n, _, _ in partes] + [f"Carga {a1}"]
    y = [100 * dec["carga0"]] + [100 * v for _, v, _ in partes] + [100 * dec["carga1"]]
    fig = go.Figure(go.Waterfall(
        x=x, y=y, measure=["absolute"] + ["relative"] * len(partes) + ["total"], orientation="v",
        text=[f"{v:.1f}%" if i in (0, len(y) - 1) else f"{v:+.1f} puntos" for i, v in enumerate(y)], textposition="outside",
        increasing=dict(marker=dict(color=ORANGE)), decreasing=dict(marker=dict(color=BLUE)),
        totals=dict(marker=dict(color=INK_SECONDARY)), connector=dict(line=dict(color=INK_MUTED, width=1)),
        customdata=[None] + [r for _, _, r in partes] + [None],
        hovertemplate="%{x}: %{y:.2f}<extra></extra>", cliponaxis=False))
    mayor = max(partes, key=lambda p: p[1])
    msg = (f"{nombre}: la carga sube de {100 * dec['carga0']:.1f}% a {100 * dec['carga1']:.1f}% del sueldo, sobre todo por la «{mayor[0].lower()}»"
           if dec["carga1"] > dec["carga0"] else
           f"{nombre}: la carga baja de {100 * dec['carga0']:.1f}% a {100 * dec['carga1']:.1f}% del sueldo")
    fig.update_layout(**PLOTLY_LAYOUT, **BARRAS, showlegend=False,
                      title=_titulo(msg, f"Aporte de cada factor al cambio de la carga requerida entre {a0} y {a1}, en puntos porcentuales del sueldo"))
    fig.update_yaxes(title="% del sueldo de los trabajadores", rangemode="tozero")
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
    ult = df.iloc[-1]
    fig.update_layout(**{**PLOTLY_LAYOUT, **_MARGEN, "legend": dict(orientation="h", y=-0.15, bgcolor="rgba(0,0,0,0)")},
                      **_TEXTO_CLARO, barmode="stack", **BARRAS,
                      title=_titulo(f"En {int(ult.anio)}, las cuentas individuales reciben {100 * ult.cuentas_individuales / ult.flujo_total:.0f}% del flujo previsional",
                                    "Flujo al sistema previsional por destino, billones de pesos"))
    fig.update_xaxes(type="category", title="Año", **_EJE_CLARO)
    fig.update_yaxes(title="Billones de pesos (10^12)", rangemode="tozero", **_EJE_CLARO)
    return con_coma(fig)


def commissionable_share_line(df: pd.DataFrame, crec_base: float = 0.01, con_sis: bool = False) -> go.Figure:
    """KPI 1.3: % del flujo que pasa por cuentas individuales, real (línea continua) y escenarios (punteados), variante
    sin SIS. Pauta de la clase: máximo 4 líneas, así que la variante con SIS (línea gris delgada, real + escenario base) solo se
    dibuja con con_sis=True.
    df: anio, tipo (real / escenario / escenario_crec_1_5), variante (sin_sis / con_sis), kpi_1_3_pct."""
    sens = df[(df.variante == "con_sis") & df.tipo.isin(["real", "escenario"])].sort_values("anio")
    df = df[df.variante == "sin_sis"]
    real = df[df.tipo == "real"].sort_values("anio")
    ancla = real.iloc[[-1]]  # los escenarios parten del último año real
    fig = go.Figure()
    anios_cat = [str(int(a)) for a in sorted(set(df.anio) | set(sens.anio))]
    pos = lambda a: anios_cat.index(str(int(a)))  # noqa: E731
    puntos = []
    if con_sis:
        fig.add_scatter(x=sens.anio.astype(str), y=sens.kpi_1_3_pct, mode="lines", name="Incluyendo SIS en todos los años", showlegend=False,
                        line=dict(color=lighten(INK_MUTED), width=1.5),
                        hovertemplate="Incluyendo SIS: %{y:.1f}%<extra></extra>")
        puntos.append((pos(sens.anio.max()), float(sens.kpi_1_3_pct.iloc[-1]), "Con el Seguro de Invalidez y Sobrevivencia", lighten(INK_MUTED)))
    fig.add_scatter(x=real.anio.astype(str), y=real.kpi_1_3_pct, mode="lines+markers+text", name="Real", showlegend=False,
                    line=dict(color=BLUE, width=3), text=[f"{v:.1f}%" for v in real.kpi_1_3_pct],
                    textposition="top center", textfont_color=INK_PRIMARY)
    base_e = ancla
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
        fig.add_scatter(x=e.anio.astype(str), y=e.kpi_1_3_pct, mode="lines+markers+text", name=nombre, showlegend=False,
                        line=dict(color=color, width=2.5, dash=dash), text=rotulos, textposition="bottom center",
                        textfont_color=INK_PRIMARY)
        puntos.append((pos(e.anio.max()), float(e.kpi_1_3_pct.iloc[-1]), nombre, color))
        if tipo == "escenario":
            base_e = e
    rotular_final(fig, puntos, rango_y=(0, 70), alto_px=330)
    fig.add_annotation(x=pos(real.anio.min()), y=float(real.kpi_1_3_pct.iloc[0]), text=f"<span style='color:{BLUE}'>■</span> Real",
                       showarrow=False, xanchor="left", yshift=-22, font=dict(color=INK_PRIMARY, size=12))
    # el mensaje del título sale del escenario base: mínimo y último año
    fut = base_e[base_e.anio > ancla.anio.iloc[0]]
    if fut.empty:
        fut = base_e
    imin = fut.kpi_1_3_pct.idxmin()
    if int(fut.loc[imin, "anio"]) == int(base_e.anio.max()):
        msg = f"La parte del flujo en cuentas individuales llegaría a {fut.loc[imin, 'kpi_1_3_pct']:.1f}% en {int(fut.loc[imin, 'anio'])}"
    else:
        msg = (f"La parte del flujo en cuentas individuales bajaría a {fut.loc[imin, 'kpi_1_3_pct']:.1f}% en {int(fut.loc[imin, 'anio'])} "
               f"y volvería a {base_e.kpi_1_3_pct.iloc[-1]:.1f}% en {int(base_e.anio.max())}")
    fig.update_layout(**{**PLOTLY_LAYOUT, **_MARGEN}, **_TEXTO_CLARO,
                      title=_titulo(msg, "Cuentas individuales de las Administradoras de Fondos de Pensiones, % del flujo previsional"))
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=anios_cat, title="Año",
                     range=[-0.5, len(anios_cat) - 0.5 + 0.45 * len(anios_cat)], **_EJE_CLARO)
    fig.update_yaxes(title="% del flujo total", range=[0, 70], **_EJE_CLARO)
    return con_coma(fig)


# KPI 1.1 (diagnóstico): dispersión de cobertura y matriz de riesgo
_TAM_MAX_PX = 55  # diámetro de la burbuja más grande (Metropolitana)
_AREA_PX = (900, 400)  # área de trazado aproximada en el dashboard (ancho, alto), para ubicar los rótulos
_POSICIONES = [  # (dirección x, dirección y) alrededor de la burbuja, en el orden en que se prueban
    (0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1),
]


def _rango(serie: pd.Series, margen: float) -> tuple:
    """Rango del eje: pauta de la clase, los ejes de las dispersiones parten en 0 (un eje recortado distorsiona la lectura)."""
    return 0.0, float(serie.max()) * (1 + margen)


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
    # punto negro en el centro de cada burbuja: ahí termina la línea del rótulo (sin él la línea acababa en la nada)
    fig.add_scatter(x=df[x], y=df[y], mode="markers", showlegend=False, hoverinfo="skip", marker=dict(size=5, color="black"))
    for (dx, dy, linea), xi, yi, nombre in zip(_ubicar_rotulos(df[x], df[y], list(df.region_nombre), radios,
                                                               rango_x, rango_y), df[x], df[y], df.region_nombre):
        fig.add_annotation(x=xi, y=yi, text=nombre, showarrow=linea, arrowhead=0, arrowwidth=1, arrowcolor=INK_MUTED, standoff=0,
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
                    line=dict(color=INK_PRIMARY, width=2, dash="dash"), hoverinfo="skip")
    formato_x = ":$,.0f" if var == "ingreso_per_capita_prom" else ":.1f"
    rx, ry = _rango(df[var], 0.08), _rango(df.cobertura_previsional_pct, 0.12)
    _burbujas(fig, df, var, "cobertura_previsional_pct",
              f"{etiqueta}: %{{x{formato_x}}}<br>Cobertura: %{{y:.1f}}%", BLUE, rx, ry)
    fig.add_annotation(xref="paper", yref="paper", x=0.01, y=0.99, xanchor="left", yanchor="top", showarrow=False,
                       text=f"r = {num_cl(corr.pearson_r)}, ρ = {num_cl(corr.spearman_rho)}, n = {int(corr.n)}",
                       font=dict(color=INK_PRIMARY, size=13), bgcolor="rgba(255,255,255,0.8)")
    r = float(corr.pearson_r)
    msg = (f"La cobertura previsional casi no se relaciona con {etiqueta.lower()}" if abs(r) < 0.3 else
           f"Las regiones con mayor {etiqueta.lower()} tienen {'mayor' if r > 0 else 'menor'} cobertura previsional")
    fig.update_layout(**{**PLOTLY_LAYOUT, **_MARGEN}, **_TEXTO_CLARO, height=520, showlegend=False,
                      title=_titulo(msg + f" (r = {r:.2f})", "Una burbuja por región; su tamaño es el número de cotizantes"))
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
                  annotation_text=f"Cobertura país {num_cl(nac_cobertura, 1)}%", annotation_position="bottom left",
                  annotation_font_color=INK_PRIMARY)
    fig.add_hline(y=nac_65, line_dash="dash", line_color=INK_MUTED,
                  annotation_text=f"65+ país {num_cl(nac_65, 1)}%", annotation_position="top left",
                  annotation_font_color=INK_PRIMARY)
    _burbujas(fig, df, "cobertura_previsional_pct", "pct_65_mas", "Cobertura: %{x:.1f}%<br>65+: %{y:.1f}%", INK_SECONDARY,
              (x0, x1), (y0, y1))
    n_doble = int((risk_quadrant(df, nac_cobertura, nac_65) == "Riesgo doble").sum())
    fig.update_layout(**{**PLOTLY_LAYOUT, **_MARGEN}, **_TEXTO_CLARO, height=560, showlegend=False,
                      title=_titulo(f"{n_doble} regiones combinan baja cobertura previsional y alto envejecimiento",
                                    "Cobertura previsional frente a envejecimiento; una burbuja por región, su tamaño es el número de cotizantes"))
    fig.update_xaxes(title="Cobertura previsional (% de 15-64 que cotiza)", ticksuffix="%", range=[x0, x1], **_EJE_CLARO)
    fig.update_yaxes(title="Población de 65 años y más (% del total)", ticksuffix="%", range=[y0, y1], **_EJE_CLARO)
    return con_coma(fig)


def region_change_bars(df: pd.DataFrame, ids_sel: list, cambio_pais: float, desde: int = 2022, hasta: int = 2024) -> go.Figure:
    """KPI 1.1: cuánto cambió la cobertura de cada región entre `desde` y `hasta` (puntos), con el mismo diseño de las barras de
    cobertura por región (barras horizontales y línea punteada del país). La región que más perdió, arriba; las regiones prioritarias
    en naranja y las demás en azul. df = filas de región de kpi_cobertura_regiones.csv (region_id, region_nombre, cambio_2022_ref)."""
    d = df.sort_values("cambio_2022_ref")
    sel = d.region_id.isin(ids_sel)
    fig = go.Figure(go.Bar(y=d.region_nombre, x=d.cambio_2022_ref, orientation="h", marker_color=[ORANGE if v else BLUE for v in sel],
                           text=[f"{v:+.1f}" for v in d.cambio_2022_ref], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}: %{x:+.2f} puntos<extra></extra>"))
    fig.add_vline(x=cambio_pais, line_dash="dash", line_color="#52514e", annotation_text=f"Chile: {cambio_pais:+.1f}", annotation_position="top")
    peor, mejor = d.iloc[0], d.iloc[-1]
    n_baja = int((d.cambio_2022_ref < 0).sum())
    fig.update_layout(**PLOTLY_LAYOUT, **BARRAS, showlegend=False,
                      title=_titulo(f"{peor.region_nombre} perdió la mayor cobertura desde {desde} ({peor.cambio_2022_ref:+.1f} puntos); {n_baja} de {len(d)} regiones bajaron",
                                    f"Puntos de cobertura entre {desde} y {hasta}; naranja = prioritarias", ancho=60))
    fig.update_yaxes(categoryorder="total descending", title="")
    lim = float(d.cambio_2022_ref.abs().max()) * 1.25
    fig.update_xaxes(range=[-lim, lim], zeroline=True, zerolinecolor=INK_PRIMARY, title=f"Puntos de cobertura ({hasta} menos {desde})")
    return fig


SERIE_LARGA = {1: 801, 15: 801, 10: 810, 14: 810, 8: 816, 16: 816}  # región -> serie fusionada de 2002 (ver Scripts/24)


def extremos_largo(reg: pd.DataFrame, ids_sel: list, modo: str = "nivel"):
    """(región prioritaria que se dibuja, mejor región del país) del gráfico largo: entre las prioritarias, la de menor cobertura hoy
    («nivel») o la que más cayó desde 2022 («caida»); la mejor es la de mayor cobertura hoy entre las 16."""
    sel = reg[reg.region_id.isin(ids_sel)]
    peor = sel.loc[sel.cobertura_ref.idxmin() if modo == "nivel" else sel.cambio_2022_ref.idxmin()]
    return peor, reg.loc[reg.cobertura_ref.idxmax()]


def coverage_long_chart(t: pd.DataFrame, reg: pd.DataFrame, ids_sel: list, modo: str = "nivel") -> go.Figure:
    """KPI 1.1: la cobertura de 2002 a hoy con tres líneas (pauta de la clase: máximo 4): Chile, la región prioritaria que hoy está peor
    y la mejor región del país. modo «nivel» = la prioritaria con la cobertura más baja hoy; «caida» = la que más cayó desde 2022.
    Las regiones que antes de 2007 (o 2018) iban dentro de otra se dibujan como la serie fusionada. t = kpi_cobertura_tendencia.csv;
    reg = filas de región de kpi_cobertura_regiones.csv. Gris claro = 2020 y 2021."""
    peor, mejor = extremos_largo(reg, ids_sel, modo)
    serie = lambda rid: t[t.territorio_id == SERIE_LARGA.get(int(rid), int(rid))].sort_values("anio")  # noqa: E731
    lineas = [(t[t.territorio_id == 0].sort_values("anio"), "Chile", INK_PRIMARY, 3.5),
              (serie(peor.region_id), peor.region_nombre if int(peor.region_id) not in SERIE_LARGA else serie(peor.region_id).territorio.iloc[0], ORANGE, 3),
              (serie(mejor.region_id), mejor.region_nombre, BLUE, 3)]
    fig = go.Figure()
    fig.add_vrect(x0=2019.5, x1=2021.5, fillcolor=GRIDLINE, opacity=0.6, line_width=0, layer="below")
    puntos = []
    for d, nombre, color, ancho in lineas:
        fig.add_scatter(x=d.anio, y=d.cobertura_pct, mode="lines", line=dict(color=color, width=ancho), showlegend=False,
                        hovertemplate="%{x}: %{y:.1f}%<extra>" + nombre + "</extra>")
        puntos.append((int(d.anio.max()), float(d.cobertura_pct.iloc[-1]), f"{nombre}: {d.cobertura_pct.iloc[-1]:.1f}%", color))
    a0, a1 = int(lineas[0][0].anio.min()), int(lineas[0][0].anio.max())
    rotular_final(fig, puntos, rango_y=(0, 65), alto_px=380, ancho_texto=26)
    ampliar_derecha(fig, a0, a1, 0.26)
    fig.add_annotation(x=2020.5, y=3, text="2020-2021", showarrow=False, font=dict(color=INK_PRIMARY, size=11))
    brecha0 = float(lineas[2][0].cobertura_pct.iloc[0] - lineas[1][0].cobertura_pct.iloc[0])
    brecha1 = float(lineas[2][0].cobertura_pct.iloc[-1] - lineas[1][0].cobertura_pct.iloc[-1])
    fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=60, r=30, t=110, b=50)}, showlegend=False,
                      title=_titulo((f"La distancia entre {mejor.region_nombre} y {lineas[1][1]} no se ha cerrado: {brecha0:.0f} puntos en {a0} y {brecha1:.0f} en {a1}"
                                    if abs(brecha1 - brecha0) < 1 else
                                    f"La distancia entre {mejor.region_nombre} y {lineas[1][1]} {'creció' if brecha1 > brecha0 else 'se achicó'} de {brecha0:.0f} puntos en {a0} a {brecha1:.0f} en {a1}"),
                                    f"Cobertura previsional (cotizantes ÷ población de 15 a 64 años): Chile, la región prioritaria {'con la cobertura más baja' if modo == 'nivel' else 'que más cayó desde 2022'} y la mejor región", ancho=70))
    fig.update_yaxes(range=[0, 65], ticksuffix="%", title="")
    fig.update_xaxes(title="", dtick=2)
    return fig


VENTANAS_TENDENCIA = {  # nombre -> (primer año, territorios)
    "Desde 2019, las 16 regiones": (2019, [1, 15, 2, 3, 4, 5, 13, 6, 7, 16, 8, 9, 14, 10, 11, 12]),
    "Desde 2002, con regiones fusionadas": (2002, [801, 2, 3, 4, 5, 6, 7, 816, 9, 810, 11, 12, 13]),
}


def coverage_trend_panels(t: pd.DataFrame, prioritarias: list, ventana: str = "Desde 2019, las 16 regiones", sin_ajustar: bool = False,
                          columnas: int = 4) -> go.Figure:
    """KPI 1.1, tendencia de la cobertura (cotizantes / población 15-64), un panel por territorio con Chile en gris como referencia
    (2 líneas por panel, pauta de la clase: máximo 4). Paneles de la cobertura más baja a la más alta; el eje parte en 0 y es el
    mismo en todos. t = kpi_cobertura_tendencia.csv; prioritarias = ids de región (en la ventana larga, 8 y 16 marcan el panel
    «Biobío y Ñuble»: la Superintendencia las publicó juntas hasta 2017; Arica y Los Ríos, antes de 2007, dentro de Tarapacá y Los Lagos).
    sin_ajustar=True usa la proyección del INE tal como se publicó (base 2017) y muestra el Censo 2024 como punto aparte (rombo): la
    cobertura que resulta con la población contada. Gris claro = 2020 y 2021 (pandemia). Prioritarias en naranja."""
    desde, ids = VENTANAS_TENDENCIA[ventana]
    col = "cobertura_sin_ajuste_pct" if sin_ajustar else "cobertura_pct"
    t = t[t.anio >= desde]
    ultimo = int(t.anio.max())
    pais = t[t.territorio_id == 0].set_index("anio")[col]
    terr = t[t.territorio_id.isin(ids)]
    orden = terr[terr.anio == ultimo].sort_values(col)[["territorio_id", "territorio"]].values.tolist()
    filas = -(-len(orden) // columnas)

    def cambio(tid):  # puntos entre el primer y el último año de la ventana
        v = terr[terr.territorio_id == tid].set_index("anio")[col]
        return v[ultimo] - v[desde]

    titulos = [es_cl(f"{n}: {cambio(tid):+.1f} puntos") if desde >= 2019 else n for tid, n in orden]
    fig = make_subplots(rows=filas, cols=columnas, shared_xaxes=True, shared_yaxes=True, horizontal_spacing=0.025, vertical_spacing=0.1,
                        subplot_titles=titulos)
    for i, (tid, nombre) in enumerate(orden):
        r, c = i // columnas + 1, i % columnas + 1
        es_prio = tid in prioritarias or (tid == 816 and ({8, 16} & set(prioritarias)))
        color = ORANGE if es_prio else BLUE
        s_ = terr[terr.territorio_id == tid].sort_values("anio")
        fig.add_vrect(x0=2019.5, x1=2021.5, fillcolor=GRIDLINE, opacity=0.6, line_width=0, layer="below", row=r, col=c, exclude_empty_subplots=False)
        fig.add_scatter(x=pais.index, y=pais.values, mode="lines", line=dict(color=INK_MUTED, width=1.5), showlegend=False,
                        hovertemplate="%{x}: %{y:.1f}% (Chile)<extra></extra>", row=r, col=c)
        rotulos = [f"{v:.0f}%" if k in (0, len(s_) - 1) else "" for k, v in enumerate(s_[col])]
        fig.add_scatter(x=s_.anio, y=s_[col], mode="lines+text", line=dict(color=color, width=2.5), showlegend=False,
                        text=rotulos, textposition=["top right"] + ["top center"] * (len(s_) - 2) + ["middle right"], textfont=dict(size=10, color=INK_PRIMARY),
                        hovertemplate="%{x}: %{y:.1f}%<extra>" + nombre + "</extra>", row=r, col=c)
        if sin_ajustar and 2024 in set(s_.anio):
            censo = s_[s_.anio == 2024].iloc[0]
            fig.add_scatter(x=[2024], y=[censo.cobertura_pct], mode="markers", showlegend=False,
                            marker=dict(symbol="diamond", size=9, color=INK_PRIMARY, line=dict(color="white", width=1)),
                            hovertemplate="Censo 2024: %{y:.1f}%<extra>" + nombre + "</extra>", row=r, col=c)
    p0, p1 = pais.loc[desde], pais.loc[ultimo]
    if desde >= 2019:
        n_baja = sum(1 for tid, _ in orden if terr[(terr.territorio_id == tid) & (terr.anio == ultimo)][col].iloc[0]
                     < terr[(terr.territorio_id == tid) & (terr.anio == desde)][col].iloc[0])
        msg = f"Desde {desde} la cobertura de Chile pasó de {p0:.1f}% a {p1:.1f}%; {n_baja} de {len(orden)} regiones están hoy bajo su nivel de {desde}"
    else:
        a_pico = int(pais.idxmax())
        msg = (f"La cobertura de Chile subió de {p0:.0f}% en {desde} a {pais.max():.0f}% en {a_pico} y desde entonces bajó a {p1:.0f}%"
               if a_pico < ultimo else f"La cobertura de Chile subió de {p0:.0f}% en {desde} a {p1:.0f}% en {ultimo}")
    detalle = ("Cotizantes ÷ población de 15 a 64 años; gris = Chile, naranja = regiones prioritarias, franja = 2020 y 2021"
               + ("; ◆ = Censo 2024 (población sin ajustar)" if sin_ajustar else ""))
    fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=50, r=20, t=135, b=40)}, showlegend=False, title=_titulo(msg, detalle, ancho=70))
    holgura = max(1.5, 0.12 * (ultimo - desde))  # sitio a la derecha para la etiqueta del último punto
    fig.update_xaxes(tickvals=[desde, ultimo] if desde >= 2019 else [desde, 2010, 2020], range=[desde - 0.7, ultimo + holgura])
    fig.update_yaxes(range=[0, 65], dtick=20, ticksuffix="%")
    for an in fig.layout.annotations:  # títulos de panel más chicos
        an.font = dict(size=12, color=INK_PRIMARY)
    return fig


FRASE_FACTOR = {  # (frase para la brecha con Chile, frase para el cambio en el tiempo)
    "participacion": ("que menos personas trabajan o buscan trabajo", "la participación laboral"),
    "empleo": ("el desempleo", "el desempleo"),
    "cotizacion": ("que menos ocupados cotizan", "los ocupados que cotizan"),
}


def decomposition_panels(d: pd.DataFrame, comparacion: str, ids: list, nombres: dict, todas: bool = False, orden: str = "total",
                         ascendente: bool = True) -> go.Figure:
    """KPI 1.1, de dónde viene la diferencia de cobertura: cobertura = participación × empleo × cotización de los ocupados; el aporte
    de cada factor, en puntos, suma exacto la diferencia (media logarítmica). d = kpi_cobertura_descomposicion.csv; comparacion =
    «Nivel frente a Chile en 2024», «Cambio 2023-2024» o «Cambio 2019-2024»; ids = regiones prioritarias; nombres = id -> nombre de las 16
    regiones. todas=True muestra las 16 regiones con las prioritarias en naranja; si no, solo las prioritarias. `orden` es la columna por la
    que se ordenan las filas («total», «participacion», «empleo» o «cotizacion») y `ascendente` la dirección: True = de menor a mayor, con
    la que más pierde arriba. La línea punteada es Chile: el 0 en la diferencia con Chile y su propio valor en el cambio."""
    nivel = comparacion.startswith("Nivel")
    ver = list(nombres) if todas else list(ids)
    dd = d[d.comparacion == comparacion]
    ancho = dd[dd.territorio_id.isin(ver)].pivot(index="territorio_id", columns="factor", values="aporte_pp")
    ancho["total"] = ancho.sum(axis=1)
    ancho = ancho.sort_values(orden, ascending=not ascendente)  # de abajo hacia arriba; la primera categoría del eje queda abajo
    chile = {} if nivel else dd[dd.territorio_id == 0].set_index("factor").aporte_pp.to_dict()
    chile = {k: chile.get(k, 0.0) for k in ("participacion", "empleo", "cotizacion")} if not nivel else {"participacion": 0.0, "empleo": 0.0, "cotizacion": 0.0}
    chile["total"] = sum(chile.values())
    marcas = [i in ids for i in ancho.index]
    nom = [nombres[i] for i in ancho.index]
    paneles = [("participacion", "Participación laboral"), ("empleo", "Empleo (1 − desocupación)"), ("cotizacion", "Ocupados que cotizan"), ("total", "Diferencia total")]
    fig = make_subplots(rows=1, cols=4, shared_yaxes=True, horizontal_spacing=0.03, subplot_titles=[n for _, n in paneles])
    for j, (k, titulo_panel) in enumerate(paneles, start=1):
        fig.add_bar(y=nom, x=ancho[k], orientation="h", marker_color=[ORANGE if m else BLUE for m in marcas], showlegend=False,
                    text=[f"{v:+.1f}" for v in ancho[k]], textposition="outside", cliponaxis=False, textfont=dict(size=11, color=INK_PRIMARY),
                    hovertemplate="%{y}: %{x:+.1f} puntos<extra>" + titulo_panel + "</extra>", row=1, col=j)
        fig.add_vline(x=chile[k], line_dash="dash", line_color="#52514e", line_width=1.2, row=1, col=j)
    prio = ancho.loc[[i for i in ancho.index if i in ids]]
    fac3 = ["participacion", "empleo", "cotizacion"]
    mayor = prio[fac3].abs().idxmax(axis=1) if not nivel else prio[fac3].idxmin(axis=1)
    f_top, n_top = mayor.value_counts().index[0], int(mayor.value_counts().iloc[0])
    if nivel:
        msg = f"En {n_top} de las {len(prio)} regiones prioritarias, la brecha con Chile viene sobre todo de {FRASE_FACTOR[f_top][0]}"
    else:
        msg = f"Entre {comparacion[7:11]} y {comparacion[12:]}, en {n_top} de las {len(prio)} regiones prioritarias el mayor cambio vino de {FRASE_FACTOR[f_top][1]}"
    alto_margen = 120
    fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=110, r=30, t=alto_margen, b=40)}, **BARRAS, showlegend=False, title=_titulo(msg, "", ancho=80))
    lim = float(np.abs(ancho.drop(columns="total").to_numpy()).max()) * 1.3
    for j, (k, _) in enumerate(paneles, start=1):
        r_ = float(np.abs(ancho[k]).max()) * 1.4 if k == "total" else lim
        fig.update_xaxes(range=[-r_, r_], zeroline=True, zerolinecolor=INK_PRIMARY, showticklabels=False, row=1, col=j)
    fig.update_yaxes(categoryorder="array", categoryarray=nom)  # la primera categoría va abajo: la que más pierde (la última) queda arriba
    for an in fig.layout.annotations:
        an.font = dict(size=12, color=INK_PRIMARY)
    return fig


PANELES_ESCENARIOS = (  # (clave de kpi_pc_escenarios_fijos.csv, título del panel); la fila de arriba cambia el tope, la de abajo la cobertura
    ("tope_10", "Tope 10 % (base)"), ("tope_11", "Tope 11 %"), ("tope_12", "Tope 12 %"),
    ("cobertura_cae", "Cobertura sigue cayendo"), ("mitad_informalidad", "Mitad de los informales cotiza"), ("sin_informalidad", "Todos los informales cotizan"),
)


def fixed_scenarios_chart(esc: pd.DataFrame, series: dict, hasta: int = 2065) -> go.Figure:
    """KPI 1.2, escenarios fijos: un panel por escenario con las dos curvas del punto crítico, el costo del Pilar Solidario de vejez (la misma
    en los seis, en rojo) y la capacidad (tope de carga × masa de ingreso de los cotizantes, en azul). El punto crítico es donde se cruzan: una
    línea punteada baja del cruce al eje y el año se escribe fuera del gráfico, bajo el eje. Fila de arriba: el tope cambia (10, 11, 12 %);
    fila de abajo: cambia la cobertura (tope de 10 %). Mismo eje vertical en los seis. esc = kpi_pc_escenarios_fijos.csv;
    series = {clave: (serie del motor, punto_critico)}."""
    unidades = {}
    for clave, _ in PANELES_ESCENARIOS:
        d = series[clave][0]
        d = d[(d.anio >= 2025) & (d.anio <= hasta)]
        unidades[clave] = d
    div, unidad = _unidad_dinero(max(max(d.costo_total.max(), d.capacidad.max()) for d in unidades.values()))
    ymax = max(max(d.costo_total.max(), d.capacidad.max()) for d in unidades.values()) / div * 1.08
    fig = make_subplots(rows=2, cols=3, shared_yaxes=True, horizontal_spacing=0.04, vertical_spacing=0.2,
                        subplot_titles=[t for _, t in PANELES_ESCENARIOS])
    for i, (clave, _) in enumerate(PANELES_ESCENARIOS):
        r, c = i // 3 + 1, i % 3 + 1
        d, pc = unidades[clave], series[clave][1]
        fig.add_scatter(x=d.anio, y=d.costo_total / div, mode="lines", line=dict(color=RED, width=2.5), showlegend=False,
                        hovertemplate="%{x}: %{y:.1f}<extra>Costo</extra>", row=r, col=c)
        fig.add_scatter(x=d.anio, y=d.capacidad / div, mode="lines", line=dict(color=BLUE, width=2.5), showlegend=False,
                        hovertemplate="%{x}: %{y:.1f}<extra>Capacidad</extra>", row=r, col=c)
        rotular_final(fig, [(hasta, float(d.costo_total.iloc[-1] / div), "Costo", RED), (hasta, float(d.capacidad.iloc[-1] / div), "Capacidad", BLUE)],
                      row=r, col=c, rango_y=(0, ymax), alto_px=220, ancho_texto=12)
        ampliar_derecha(fig, 2025, hasta, 0.38, row=r, col=c)
        if pc["estado"] == "cruza":
            y_cruce = float(np.interp(pc["anio_exacto"], d.anio, d.capacidad / div))
            fig.add_shape(type="line", x0=pc["anio_exacto"], x1=pc["anio_exacto"], y0=0, y1=y_cruce, line=dict(color=INK_PRIMARY, width=1.2, dash="dash"), row=r, col=c)
            eje = "" if i == 0 else str(i + 1)  # make_subplots numera los ejes x, x2, x3... en orden de panel
            fig.add_annotation(x=pc["anio_exacto"], y=0, xref=f"x{eje}", yref=f"y{eje}", text=f"<b>{pc['anio']}</b>", showarrow=False,
                               yshift=-34, yanchor="top", font=dict(size=12, color=INK_PRIMARY))
    anios = {c: series[c][1]["anio"] for c, _ in PANELES_ESCENARIOS if series[c][1]["estado"] == "cruza"}
    lo, hi = min(anios, key=anios.get), max(anios, key=anios.get)
    nombre = dict(PANELES_ESCENARIOS)
    fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=60, r=20, t=110, b=60)}, showlegend=False,
                      title=_titulo(f"El punto crítico va de {anios[lo]} a {anios[hi]}: de «{nombre[lo].lower()}» a «{nombre[hi].lower()}»",
                                    f"Costo y capacidad del Pilar Solidario de vejez, {unidad}; el punto crítico es donde se cruzan (año bajo el eje)", ancho=80))
    fig.update_xaxes(tickvals=[2025, 2045, 2065], range=[2025, hasta + 0.38 * (hasta - 2025)])
    fig.update_yaxes(range=[0, ymax])
    for an in fig.layout.annotations[:6]:
        an.font = dict(size=12, color=INK_PRIMARY)
    return fig


def factor_bars(fac: pd.DataFrame) -> go.Figure:
    """KPI 1.1, factores candidatos: correlación (Pearson) de cada factor con la cobertura de las 16 regiones. fac = filas elegidas de
    kpi_cobertura_factores.csv (nombre, pearson_r, pearson_p). Un solo color; el signo se lee por el lado de la barra (eje de -1 a 1)."""
    d = fac.reindex(fac.pearson_r.abs().sort_values().index)
    fig = go.Figure(go.Bar(y=d.nombre, x=d.pearson_r, orientation="h", marker_color=BLUE,
                           text=[f"{v:+.2f}" + ("" if p < 0.05 else " (no significativa)") for v, p in zip(d.pearson_r, d.pearson_p)],
                           textposition="outside", cliponaxis=False, hovertemplate="%{y}<br>r = %{x:.2f}<extra></extra>"))
    top = d.iloc[-1]
    sentido = "más" if top.pearson_r > 0 else "menos"
    fig.update_layout(**PLOTLY_LAYOUT, **BARRAS, showlegend=False,
                      title=_titulo(f"Las regiones con más {top.nombre.lower().split(' (')[0]} tienen {sentido} cobertura previsional (r = {top.pearson_r:.2f})",
                                    "Correlación de cada factor con la cobertura de las 16 regiones; asociación, no causa", ancho=70))
    fig.update_xaxes(range=[-1, 1], title="Correlación con la cobertura previsional (de -1 a +1)", zeroline=True, zerolinecolor=INK_PRIMARY)
    fig.update_yaxes(title="")
    return fig


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
                    line=dict(color=INK_PRIMARY, width=2, dash="dash"), hoverinfo="skip")
    rx, ry = _rango(df.cobertura_previsional_pct, 0.08), _rango(df.pct_pobreza_65, 0.12)
    _burbujas(fig, df, "cobertura_previsional_pct", "pct_pobreza_65", "Cobertura: %{x:.1f}%<br>Pobreza 65+: %{y:.1f}%", ORANGE,
              rx, ry, tam="n_pobres_65", tam_nombre="Personas 65+ en pobreza", tam_pct="share_pobres_pct")
    fig.add_annotation(xref="paper", yref="paper", x=0.99, y=0.99, xanchor="right", yanchor="top", showarrow=False,
                       text=f"r = {num_cl(r)}, ρ = {num_cl(rho)}, n = {n}", font=dict(color=INK_PRIMARY, size=13),
                       bgcolor="rgba(255,255,255,0.8)")
    msg = ("La pobreza en personas de 65+ casi no se relaciona con la cobertura previsional" if abs(r) < 0.3 else
           f"Las regiones con menor cobertura previsional tienen {'más' if r < 0 else 'menos'} pobreza en personas de 65+")
    fig.update_layout(**{**PLOTLY_LAYOUT, **_MARGEN}, **_TEXTO_CLARO, height=520, showlegend=False,
                      title=_titulo(msg + f" (r = {r:.2f})", "Una burbuja por región; su tamaño es el número de personas de 65+ en pobreza"))
    fig.update_xaxes(title="Cobertura previsional (% de 15-64 que cotiza, 2024)", ticksuffix="%", range=list(rx), **_EJE_CLARO)
    fig.update_yaxes(title="Personas 65+ en pobreza (%, CASEN 2022)", ticksuffix="%", range=list(ry), **_EJE_CLARO)
    return con_coma(fig)


def colores_legibles(fig: go.Figure) -> go.Figure:
    """Texto oscuro explícito en TODO el gráfico (título, ejes, ticks, barra de color, leyenda, rótulos y anotaciones), fondo claro,
    coma decimal y barra de herramientas vertical. Sin esto, el tema oscuro de Streamlit pinta el texto gris claro sobre fondo blanco."""
    fig.update_layout(font_color=INK_PRIMARY, title_font_color=INK_PRIMARY, legend_font_color=INK_PRIMARY,
                      legend_title_font_color=INK_PRIMARY, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
                      separators=",.", modebar=dict(orientation="v"))
    # margen superior según las líneas del título (y de los títulos de subgráficos), para que el texto largo no se corte
    lineas = (fig.layout.title.text or "").split("<br>") if fig.layout.title.text else []
    en_sup, alto = False, (28 if lineas else 0)
    for l in lineas:  # las líneas del subtítulo (<sup> ... </sup>) son más bajas que las del mensaje
        en_sup = en_sup or "<sup>" in l
        alto += 20 if en_sup else 26
        en_sup = en_sup and "</sup>" not in l
    subtitulos = [an for an in fig.layout.annotations if an.yref == "paper" and an.y is not None and an.y >= 1 and an.text and not an.showarrow]
    for an in subtitulos:
        alto = max(alto, 20 * (an.text.count("<br>") + 1) + 28)
    if subtitulos and lineas:  # título general y títulos de los subgráficos: que no se pisen
        alto += 20 + 24 * len(subtitulos[0].text.split("<br>"))
    if alto:
        fig.update_layout(margin_t=max(fig.layout.margin.t or 0, alto + 8))
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
