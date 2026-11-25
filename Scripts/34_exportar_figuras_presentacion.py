"""Exporta las figuras de la presentación (pptx) en alta resolución, con las pautas de diseño de la clase.

Qué hace
  1. Captura los gráficos y tablas del dashboard sin servidor: corre las páginas de la versión final (y la extendida para 2.4.x)
     con streamlit.testing.v1.AppTest, reemplazando components.charts.mostrar, numeracion.etiqueta, st.table, st.dataframe y
     st.caption por funciones que anotan (clave, figura, tabla, pies). El dashboard no cambia.
  2. Rehace cada figura para la diapositiva según config/figuras_presentacion.yaml (mensaje, subtítulo, fuente, cambios).
  3. Arma las figuras nuevas N.0-N.11 con Data processed/*.csv.
  4. Exporta dos variantes por figura (__slide sin ningún título, __standalone con el mensaje y el subtítulo), con la nota de fuente
     impresa abajo (sin número de figura en la imagen: el número solo va en el nombre del archivo).
  5. Revisa cada figura con reglas automáticas (pautas G3-G21 de la clase, tamaño de letra, resolución) y escribe manifest.csv/json,
     qa_report.md, README.md, contact_sheet.pdf y figuras_pptx.zip en Outputs/figuras_pptx/.

Uso (desde la raíz del proyecto):
  "Data raw/.venv/bin/python" Scripts/34_exportar_figuras_presentacion.py            # todo
  "Data raw/.venv/bin/python" Scripts/34_exportar_figuras_presentacion.py --solo 1.2.7 N.8   # solo esas figuras (para revisar)
  --cache RUTA guarda/lee la captura del dashboard (pickle) para no repetirla mientras se ajustan las figuras.

Requiere kaleido >= 1 con Chrome (plotly_get_chrome) y la letra Helvetica Neue del sistema (macOS) para la nota de fuente.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import pickle
import re
import sys
import textwrap
import unicodedata
import zipfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import yaml
from plotly.subplots import make_subplots
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DASH = ROOT / "Dashboards"
DP = ROOT / "Data processed"
CONFIG = ROOT / "config" / "figuras_presentacion.yaml"
sys.path.insert(0, str(DASH))

from utils import (BLUE, ORANGE, RED, AQUA, VIOLET, INK_PRIMARY, INK_SECONDARY, INK_MUTED, GRIDLINE, SURFACE,  # noqa: E402
                   SEQ_BLUE, lighten)
from components import numeracion  # noqa: E402

sys.path.insert(0, str(ROOT / "Scripts"))
import pie_fuente  # noqa: E402  (pie de fuente común: Fig. 1.2.4 es la referencia)

# ------------------------------------------------------------------------------------------------ constantes de estilo
FONT_FAMILY = "Helvetica Neue, Helvetica, Arial, sans-serif"
FONT_FILE = "/System/Library/Fonts/HelveticaNeue.ttc"
BASE, TICK, ANNOT, MIN_FONT, NOTE, MSG = 24, 22, 22, 20, 18, 30  # px CSS (≥ 12 pt en una diapositiva de 13,33 pulgadas)
NOTE_BAND = 66            # alto (px CSS) de la franja de la nota de fuente, debajo del gráfico
PAD = 24                  # margen lateral
GREY_BAR = "#c9c8c2"      # barras de contexto
GREY_DARK = INK_SECONDARY
ORANGE_LIGHT = "#f4b99f"  # = charts.ORANGE_CLARO: «ya entró por otro factor»
ORANGE_TINT = "#fbe3d8"   # fondo de celdas destacadas
CORTE_BRECHA = 0.80       # regla de dos preguntas: corte acumulado de la brecha (Scripts/35)
EXCLUIDAS = {"Biobío"}    # pedido 20-nov: Biobío sale de la selección de regiones críticas (7 en vez de 8); las demás regiones no cambian
SIN_NOTA = {"T"}          # la franja de seguimiento no lleva nota
SIGLAS = ["AFP", "AFPs", "PGU", "FAPP", "SIS", "ENE", "CASEN", "INE", "PIB", "FRP", "IPS", "DIPRES", "APS", "PBS", "SP", "RM", "pp"]
SIGLAS_RE = re.compile(r"\b(" + "|".join(SIGLAS) + r")\b")


def cl(v: float, d: int = 1, signo: bool = False) -> str:
    """Número con formato es-CL: punto de miles y coma decimal; signo menos tipográfico."""
    s = f"{abs(v):,.{d}f}".replace(",", "§").replace(".", ",").replace("§", ".")
    if v < 0 and float(s.replace(".", "").replace(",", ".")) != 0:
        return "−" + s
    return ("+" + s) if signo and v > 0 else s


def wrap(texto: str, ancho: int) -> str:
    return "<br>".join(textwrap.wrap(texto, ancho, break_long_words=False))


def cuadro(color: str, texto: str) -> str:
    """Rótulo directo: cuadrado del color de la serie y el texto en tinta (el texto nunca va en el color de la serie)."""
    return f"<span style='color:{color}'>■</span> {texto}"


def criticas(reg: pd.DataFrame) -> pd.DataFrame:
    """Regiones críticas de kpi_cobertura_regiones.csv sin las excluidas por decisión del equipo (EXCLUIDAS)."""
    return reg[reg.prioridad_rangos.notna() & ~reg.region_nombre.isin(EXCLUIDAS)]


def arr(v) -> np.ndarray:
    return np.asarray(list(v) if v is not None else [])


def meta(fig: go.Figure) -> dict:
    m = fig.layout.meta
    if not isinstance(m, dict):
        m = {}
    return m


def set_meta(fig: go.Figure, **kw) -> go.Figure:
    m = dict(meta(fig))
    m.update(kw)
    fig.update_layout(meta=m)
    return fig


def nueva(**kw) -> go.Figure:
    f = go.Figure()
    f.update_layout(showlegend=False, plot_bgcolor=SURFACE, paper_bgcolor=SURFACE, separators=",.", **kw)
    return f


def banda(fig, x0, x1, texto, row=None, col=None, yref="paper"):
    """Franja gris de escenario/proyección con su rótulo arriba (no una línea punteada)."""
    kw = dict(row=row, col=col) if row else {}
    fig.add_vrect(x0=x0, x1=x1, fillcolor=INK_MUTED, opacity=0.09, line_width=0, layer="below", **kw)
    fig.add_annotation(x=(x0 + x1) / 2 if not isinstance(x0, str) else x0, y=1, yref="paper" if not row else f"y{'' if col in (None, 1) else col} domain",
                       yanchor="top", text=texto, showarrow=False, font=dict(color=INK_SECONDARY, size=ANNOT), xref=f"x{'' if col in (None, 1) else col}")


def rotulos_finales(fig, items, rango_y, alto_px, xshift=12, lh=27, xref="x", yref="y"):
    """Etiquetado directo al final de cada línea, separado lo justo para no taparse. items = [(x, y, texto, color)]."""
    lo, hi = rango_y
    pxu = alto_px / (hi - lo)
    its = sorted(({"x": x, "y": y, "t": t, "c": c, "h": lh * (t.count("<br>") + 1)} for x, y, t, c in items), key=lambda i: i["y"])
    for i in its:
        i["pos"] = (i["y"] - lo) * pxu
    for a, b in zip(its, its[1:]):
        b["pos"] = max(b["pos"], a["pos"] + (a["h"] + b["h"]) / 2 + 4)
    for i in its:
        fig.add_annotation(x=i["x"], y=i["y"], xref=xref, yref=yref, text=cuadro(i["c"], i["t"]), showarrow=False, xanchor="left",
                           xshift=xshift, yshift=i["pos"] - (i["y"] - lo) * pxu, align="left", font=dict(size=ANNOT, color=INK_PRIMARY))


def cruce(x, a, b):
    """Primer año en que a pasa a superar a b (interpolación lineal). Devuelve (x, y) o None."""
    x, a, b = map(lambda v: np.asarray(v, float), (x, a, b))
    d = a - b
    for i in range(1, len(d)):
        if d[i - 1] < 0 <= d[i]:
            t = -d[i - 1] / (d[i] - d[i - 1])
            return x[i - 1] + t * (x[i] - x[i - 1]), a[i - 1] + t * (a[i] - a[i - 1])
    return None


# ------------------------------------------------------------------------------------------------ 1. captura del dashboard
def capturar() -> dict:
    """Corre las páginas sin servidor y devuelve {clave: {"fig": dict de la figura, "table": DataFrame, "captions": [...]}}."""
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    import components.charts as ch
    import components.numeracion as nu

    eventos = []
    orig = (ch.mostrar, nu.etiqueta, st.table, st.dataframe, st.caption)

    def rec_mostrar(fig, config=None, num=None, **kw):
        eventos.append(["fig", num, ch.colores_legibles(fig).to_dict()])

    def envolver(nombre, f):
        def g(*a, **k):
            obj = a[0] if a else (k.get("data") if "data" in k else k.get("body"))
            if hasattr(obj, "data") and hasattr(obj, "to_html"):  # Styler
                obj = obj.data
            eventos.append([nombre, None, obj.copy() if hasattr(obj, "copy") else obj])
            return f(*a, **k)
        return g

    ch.mostrar = rec_mostrar
    nu.etiqueta = lambda clave: eventos.append(["tab_key", clave, None])
    st.table, st.dataframe, st.caption = envolver("table", st.table), envolver("dataframe", st.dataframe), envolver("caption", st.caption)
    corridas = [
        ("final_pages/problema.py", {}, {}),
        ("final_pages/objetivo1.py", {}, {}),
        ("final_pages/objetivo1.py", {"pc_vista": "Razón de soporte", "s13_variantes": "Efecto de la reforma en el empleo formal"}, {}),
        ("extended_pages/objetivo2.py", {}, {"ext_mode": True}),
    ]
    cap = {}
    cwd = os.getcwd()
    os.chdir(DASH)
    try:
        for pagina, radios, estado in corridas:
            eventos.clear()
            at = AppTest.from_file(str(DASH / pagina), default_timeout=240)
            at.session_state["_nav_active"] = True
            for k, v in estado.items():
                at.session_state[k] = v
            at.run()
            if radios:
                for k, v in radios.items():
                    at.radio(key=k).set_value(v)
                eventos.clear()
                at.run()
            if at.exception:
                raise RuntimeError(f"{pagina}: {[e.value for e in at.exception]}")
            actual = None
            for tipo, clave, obj in eventos:
                if tipo in ("fig", "tab_key"):
                    actual = clave
                    cap.setdefault(clave, {"fig": obj if tipo == "fig" else None, "table": None, "captions": [], "page": pagina, "radios": radios})
                elif tipo in ("table", "dataframe") and actual and cap[actual]["fig"] is None and cap[actual]["table"] is None:
                    cap[actual]["table"] = obj
                elif tipo == "caption" and actual and str(obj) not in cap[actual]["captions"]:
                    cap[actual]["captions"].append(str(obj))
    finally:
        os.chdir(cwd)
        ch.mostrar, nu.etiqueta, st.table, st.dataframe, st.caption = orig
    return cap


def _decodificar(o):
    """Plotly ≥ 6 guarda los arreglos de to_dict() como {dtype, bdata[, shape]} en base64: se vuelven arreglos de numpy."""
    import base64
    if isinstance(o, dict):
        if "bdata" in o and "dtype" in o:
            a = np.frombuffer(base64.b64decode(o["bdata"]), dtype=o["dtype"])
            if o.get("shape"):
                a = a.reshape(tuple(int(s) for s in str(o["shape"]).split(",")))
            return a
        return {k: _decodificar(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_decodificar(v) for v in o]
    return o


def fig_de(ctx, clave) -> go.Figure:
    return go.Figure(_decodificar(ctx["cap"][clave]["fig"]))


def tabla_de(ctx, clave) -> pd.DataFrame:
    return ctx["cap"][clave]["table"].copy()


# ------------------------------------------------------------------------------------------------ 2. figuras del dashboard
def t_pico(ctx, spec):
    f0 = fig_de(ctx, "P/pico")
    lin = next(t for t in f0.data if t.mode == "lines")
    pk = next(t for t in f0.data if t.mode and "markers" in t.mode)
    x, y = arr(lin.x).astype(float), arr(lin.y).astype(float)
    xp, yp = float(pk.x[0]), float(pk.y[0])
    f = nueva()
    f.add_vrect(x0=2024.5, x1=x.max(), fillcolor=INK_MUTED, opacity=0.09, line_width=0, layer="below")
    f.add_annotation(x=(2024.5 + x.max()) / 2, y=1, yref="paper", yanchor="top", text="Proyección", showarrow=False, font=dict(color=INK_SECONDARY))
    f.add_scatter(x=x, y=y, mode="lines", line=dict(color=BLUE, width=4))
    f.add_scatter(x=[xp], y=[yp], mode="markers", marker=dict(color=ORANGE, size=18, line=dict(color=SURFACE, width=2)))
    f.add_annotation(x=xp, y=yp, text=f"Máximo en {int(xp)}:<br><b>{cl(yp, 2)} millones</b>", showarrow=True, arrowhead=0, arrowcolor=INK_MUTED,
                     ax=0, ay=-62, font=dict(size=ANNOT))
    f.update_yaxes(range=[0, 21], title="Millones de personas", gridcolor=GRIDLINE, zeroline=False)
    f.update_xaxes(range=[1983, 2073], tickvals=[1990, 2010, 2030, 2050, 2070], title="", showgrid=False)
    return set_meta(f, pts=dict(maximo=yp))


def t_envejecimiento(ctx, spec):
    f0 = fig_de(ctx, "P/envejecimiento")
    est = next(t for t in f0.data if t.name == "Estimado")
    pro = next(t for t in f0.data if t.name and t.name.startswith("Proyecci"))
    pts = {int(t.x[0]): float(t.y[0]) for t in f0.data if t.mode == "markers+text"}
    f = nueva()
    x1 = float(max(arr(pro.x)))
    f.add_vrect(x0=2024.5, x1=x1, fillcolor=INK_MUTED, opacity=0.09, line_width=0, layer="below")
    f.add_annotation(x=(2024.5 + x1) / 2, y=1, yref="paper", yanchor="top", text="Proyección", showarrow=False, font=dict(color=INK_SECONDARY))
    f.add_scatter(x=arr(est.x), y=arr(est.y), mode="lines", line=dict(color=ORANGE, width=4))
    f.add_scatter(x=arr(pro.x), y=arr(pro.y), mode="lines", line=dict(color=lighten(ORANGE, 0.45), width=4))
    f.add_scatter(x=[2024], y=[pts[2024]], mode="markers", marker=dict(color=INK_PRIMARY, size=14, line=dict(color=SURFACE, width=2)))
    f.add_annotation(x=2024, y=pts[2024], text=f"<b>Censo 2024: {cl(pts[2024], 1)} %</b>", showarrow=True, arrowhead=0, arrowcolor=INK_MUTED, ax=-70, ay=-70)
    f.add_scatter(x=[2070], y=[pts[2070]], mode="markers", marker=dict(color=ORANGE, size=14, line=dict(color=SURFACE, width=2)))
    f.add_annotation(x=2070, y=pts[2070], text=f"<b>{cl(pts[2070], 0)} %</b><br>en 2070", showarrow=False, yanchor="bottom", yshift=14, xanchor="right")
    f.update_yaxes(range=[0, 60], ticksuffix=" %", title="% de la población", gridcolor=GRIDLINE, zeroline=False)
    f.update_xaxes(range=[1983, 2073], tickvals=[1990, 2010, 2030, 2050, 2070], title="", showgrid=False)
    return f


def _ticks_absolutos(f, xmax, paso, axes=("xaxis",)):
    vals = [v * paso for v in range(-int(xmax // paso), int(xmax // paso) + 1)]
    for a in axes:
        f.layout[a].update(tickvals=vals, ticktext=[cl(abs(v), 1 if paso < 1 else 0) for v in vals])


def _piramide_rotulos(f, xref="x", yref="y", xmax=None):
    f.add_annotation(x=-0.55 * xmax, y=92, xref=xref, yref=yref, text=cuadro(BLUE, "<b>Hombres</b>"), showarrow=False)
    f.add_annotation(x=0.55 * xmax, y=92, xref=xref, yref=yref, text=cuadro(ORANGE, "<b>Mujeres</b>"), showarrow=False)
    f.add_annotation(x=xmax * 0.98, y=65, xref=xref, yref=yref, text="65 años y más<br>(tono fuerte)", showarrow=False, xanchor="right", yanchor="bottom",
                     font=dict(color=INK_SECONDARY, size=MIN_FONT))


def t_piramide(ctx, spec):
    f = fig_de(ctx, "P/piramide")
    f.update_layout(showlegend=False, title=None, height=None, bargap=0.0)
    xmax = float(f.layout.xaxis.range[1])
    for s in f.layout.shapes:
        s.line.color, s.line.width = INK_MUTED, 1.5
    _ticks_absolutos(f, xmax, 50)
    _piramide_rotulos(f, xmax=xmax)
    f.update_yaxes(range=[-1, 99])
    return set_meta(f, orden="por edad (orden natural de la pirámide)")


def t_alemania(ctx, spec):
    f = fig_de(ctx, "P/alemania")
    f.update_layout(showlegend=False, title=None, height=None)
    for s in f.layout.shapes:
        s.line.color, s.line.width = INK_MUTED, 1.5
    for an in f.layout.annotations:
        an.font.size = ANNOT + 2
        an.text = f"<b>{an.text}</b>"
    xmax = float(f.layout.xaxis.range[1])
    _ticks_absolutos(f, xmax, 0.5, ("xaxis", "xaxis2"))
    _piramide_rotulos(f, xmax=xmax)
    f.update_yaxes(range=[-1, 99])
    return set_meta(f, extra_top=40, orden="por edad (orden natural de la pirámide)")


def t_rs_pais(ctx, spec):
    f0 = fig_de(ctx, "1.2/rs_pais")
    obs, esc = f0.data[0], f0.data[1]
    cats = list(obs.x) + list(esc.x)
    vals = [float(v) for v in list(obs.y) + list(esc.y)]
    n_obs = len(obs.x)
    neg = {cats[0], "2024", cats[-1]}
    txt = [f"<b>{cl(v, 2)}</b>" if c in neg else cl(v, 2) for c, v in zip(cats, vals)]
    col = [BLUE] * n_obs + [lighten(BLUE, 0.55)] * (len(cats) - n_obs - 1) + [ORANGE]  # acento: el final del escenario
    f = nueva(bargap=0.33)
    f.add_vrect(x0=n_obs - 0.5, x1=len(cats) - 0.5, fillcolor=INK_MUTED, opacity=0.08, line_width=0, layer="below")
    f.add_annotation(x=(n_obs - 0.5 + len(cats) - 0.5) / 2, y=1, yref="paper", yanchor="top", showarrow=False,
                     text="Escenario: cobertura de 2025 constante, no es un pronóstico", font=dict(color=INK_SECONDARY))
    f.add_bar(x=cats, y=vals, marker_color=col, text=txt, textposition="outside", cliponaxis=False, textfont=dict(size=BASE))
    f.update_xaxes(type="category", title="", tickangle=0)
    f.update_yaxes(range=[0, max(vals) * 1.45], title="Cotizantes por persona de 65 años o más", gridcolor=GRIDLINE, zeroline=False)
    return set_meta(f, valores=dict(zip(cats, vals)))


NOMBRES_CASCADA = {"Población de 65+": "Más personas de<br>65 años o más", "Costo por persona de 65+": "Costo por persona<br>de 65 años o más",
                   "Cantidad de trabajadores": "Cantidad de<br>trabajadores", "Ingreso por trabajador": "Ingreso por<br>trabajador"}


def t_cascada(ctx, spec):
    f0 = fig_de(ctx, "1.2/pc_cascada")
    w = next(t for t in f0.data if t.type == "waterfall")
    x, y, m = list(w.x), [float(v) for v in w.y], list(w.measure)
    acum, base, alto, tipo = 0.0, [], [], []
    for v, mm in zip(y, m):
        if mm == "absolute":
            base.append(0.0); alto.append(v); acum = v; tipo.append("total")
        elif mm == "relative":
            base.append(acum if v >= 0 else acum + v); alto.append(abs(v)); acum += v; tipo.append("sube" if v >= 0 else "baja")
        else:
            base.append(0.0); alto.append(acum); tipo.append("total")
    rel = [abs(v) if t != "total" else 0 for v, t in zip(y, tipo)]
    mayor = int(np.argmax(rel))
    col, txt = [], []
    for i, (v, t) in enumerate(zip(y, tipo)):
        if t == "total":
            col.append(GREY_DARK); txt.append(f"<b>{cl(alto[i], 1)} %</b>")
        else:
            col.append(ORANGE if i == mayor else (ORANGE_LIGHT if t == "sube" else lighten(BLUE, 0.45)))
            txt.append(f"{'+' if v > 0 else '−'}{cl(abs(v), 1)} puntos")
    nombres = [NOMBRES_CASCADA.get(c, c) for c in x]
    f = nueva(bargap=0.33)
    f.add_bar(x=nombres, y=alto, base=base, marker_color=col, text=txt, textposition="outside", cliponaxis=False, textfont=dict(size=BASE))
    acum = 0.0
    for i in range(len(x) - 1):  # conectores finos
        nivel = base[i] + alto[i] if tipo[i] in ("total", "sube") else base[i]
        f.add_shape(type="line", x0=i + 0.335, x1=i + 0.665, y0=nivel, y1=nivel, line=dict(color=INK_MUTED, width=1))
    f.add_hline(y=10, line=dict(color=INK_MUTED, width=1.5, dash="dot"))
    f.add_annotation(x=0, y=10, text="Tope: 10 % del sueldo", showarrow=False, xanchor="center", yanchor="bottom",
                     font=dict(color=INK_SECONDARY))
    f.update_xaxes(type="category", title="", tickangle=0)
    f.update_yaxes(range=[0, 12.5], ticksuffix=" %", title="% del sueldo de quienes cotizan", gridcolor=GRIDLINE, zeroline=False)
    pasos = {c: v for c, v, t in zip(x, y, tipo) if t != "total"}
    return set_meta(f, cascada=True, pasos=pasos, inicio=alto[0], fin=alto[-1], suma=float(sum(pasos.values())))


def _cruce_fig(ctx, clave, nombres, colores, ytitulo, sombra_si="A>B"):
    """1.2.7 y 1.2.8: dos series (observado + escenario), cruce y sombra donde se pasa el umbral."""
    f0 = fig_de(ctx, clave)
    a0, a1, b0, b1 = f0.data[0], f0.data[1], f0.data[2], f0.data[3]
    pc = next(t for t in f0.data if t.mode == "markers" and len(t.x) == 1 and t.x[0] is not None)
    xc, yc = float(pc.x[0]), float(pc.y[0])
    ca, cb = colores
    ymax = max(arr(a1.y).max(), arr(b1.y).max(), arr(a0.y).max(), arr(b0.y).max())
    f = nueva()
    f.add_vrect(x0=2025.5, x1=2070.5, fillcolor=INK_MUTED, opacity=0.08, line_width=0, layer="below")
    f.add_annotation(x=2048, y=1, yref="paper", yanchor="top", showarrow=False, text="Escenario, no es un pronóstico", font=dict(color=INK_SECONDARY))
    xs = np.union1d(arr(a1.x).astype(float), arr(b1.x).astype(float))
    xs = xs[xs > xc]
    ya, yb = np.interp(xs, arr(a1.x).astype(float), arr(a1.y).astype(float)), np.interp(xs, arr(b1.x).astype(float), arr(b1.y).astype(float))
    f.add_scatter(x=[xc, *xs, *xs[::-1], xc], y=[yc, *ya, *yb[::-1], yc], fill="toself", mode="lines", line=dict(width=0),
                  fillcolor="rgba(227,73,72,0.13)", hoverinfo="skip")
    for t0, t1, c in ((a0, a1, ca), (b0, b1, cb)):
        f.add_scatter(x=arr(t1.x), y=arr(t1.y), mode="lines", line=dict(color=lighten(c, 0.45), width=4))
        f.add_scatter(x=arr(t0.x), y=arr(t0.y), mode="lines+markers", line=dict(color=c, width=4), marker=dict(size=9, color=c))
    f.add_shape(type="line", x0=xc, x1=xc, y0=0, y1=yc, line=dict(color=INK_MUTED, width=1.5))
    f.add_scatter(x=[xc], y=[yc], mode="markers", marker=dict(color=ORANGE, size=20, line=dict(color=SURFACE, width=3)))
    f.add_annotation(x=xc, y=yc, text=f"<b>Punto crítico: {round(xc)}</b>", showarrow=True, arrowhead=0, arrowcolor=INK_MUTED, ax=-110, ay=-80)
    rango = (0, ymax * 1.35)
    ult = lambda t: (float(arr(t.x)[-1]), float(arr(t.y)[-1]))  # noqa: E731
    rotulos_finales(f, [(*ult(a1), nombres[0], ca), (*ult(b1), nombres[1], cb)], rango, 470)
    f.update_xaxes(range=[2005, 2097], tickvals=list(range(2010, 2071, 10)), title="", showgrid=False)
    f.update_yaxes(range=list(rango), title=ytitulo, gridcolor=GRIDLINE, zeroline=False)
    return set_meta(f, cruce=round(xc))


def t_pc_dinero(ctx, spec):
    return _cruce_fig(ctx, "1.2/pc_dinero", ["Costo del Pilar<br>Solidario de vejez", "Capacidad: 10 % del<br>sueldo de quienes cotizan"],
                      (RED, BLUE), "Billones de pesos de 2025")


def t_pc_razon(ctx, spec):
    return _cruce_fig(ctx, "1.2/pc_razon", ["Cotizantes por persona<br>de 65 años o más", "Cotizantes necesarios<br>(tope de 10 %)"],
                      (BLUE, GREY_DARK), "Cotizantes por persona de 65 años o más")


def t_razon_proyeccion(ctx, spec):
    f0 = fig_de(ctx, "1.2/razon_proyeccion")
    real, esc, txt = f0.data[0], f0.data[1], f0.data[2]
    f = nueva()
    banda(f, 2025.5, 2070.5, "Escenario, no es un pronóstico")
    f.add_scatter(x=arr(esc.x), y=arr(esc.y), mode="lines+markers", line=dict(color=lighten(BLUE, 0.45), width=4), marker=dict(size=8))
    f.add_scatter(x=arr(real.x), y=arr(real.y), mode="lines+markers", line=dict(color=BLUE, width=4), marker=dict(size=9))
    tx, ty, tt = arr(txt.x).astype(float), arr(txt.y).astype(float), list(txt.text)
    keep = [i for i, x in enumerate(tx) if int(round(x)) in (2024, 2030, 2040, 2050, 2070)]
    f.add_scatter(x=tx[keep], y=ty[keep], mode="text", text=[tt[i] for i in keep], textposition="top right", textfont=dict(size=ANNOT, color=INK_PRIMARY))
    f.add_scatter(x=[arr(esc.x)[-1]], y=[arr(esc.y)[-1]], mode="markers", marker=dict(color=ORANGE, size=16, line=dict(color=SURFACE, width=2)))
    ymax = float(max(arr(real.y).max(), arr(esc.y).max()))
    f.update_xaxes(range=[2021.5, 2074], tickvals=[2024, 2030, 2040, 2050, 2060, 2070])
    f.update_yaxes(range=[0, ymax * 1.4], title="Cotizantes por persona de 65 años o más", gridcolor=GRIDLINE, zeroline=False)
    f.update_xaxes(title="", showgrid=False, tickvals=list(range(2010, 2071, 10)))
    return f


def t_afp_costos(ctx, spec):
    f = fig_de(ctx, "2.4/afp_costos")
    f.update_layout(title=None, height=None)
    tr = f.data[0]
    tr.line.width, tr.marker.size = 4, 10
    tr.text = [t.replace("%", " %") if t else t for t in tr.text]
    tr.textfont = dict(size=BASE, color=INK_PRIMARY)
    for an in f.layout.annotations:
        if "Quiebre" in (an.text or ""):
            an.text, an.font.size = "Cambio de serie<br>2020/21", MIN_FONT
    f.update_yaxes(range=[0, 95], title="% de las comisiones")
    f.update_xaxes(tickangle=0)
    return f


def t_afp_estres(ctx, spec):
    f = fig_de(ctx, "2.4/afp_estres")
    f.update_layout(title=None, height=None)
    f.data[0].line.dash, f.data[0].line.width = "solid", 4
    y = arr(f.data[0].y).astype(float)
    for an in f.layout.annotations:
        an.font.size = ANNOT
        if "pronóstico" in (an.text or ""):
            an.yanchor, an.y, an.x, an.xanchor = "top", 1, 0.99, "right"
    f.update_yaxes(range=[min(y.min(), 0) * 1.25, y.max() * 1.45], zeroline=False)
    return f


def _por_100(valores):
    """Porcentajes con un decimal que suman exactamente 100,0 (resto mayor)."""
    v = np.asarray(valores, float)
    p = v / v.sum() * 1000
    base = np.floor(p)
    falta = int(round(1000 - base.sum()))
    for i in np.argsort(-(p - base))[:falta]:
        base[i] += 1
    return base / 10


def t_flujo_barras(ctx, spec):
    f0 = fig_de(ctx, "1.3/flujo_barras")
    partes = {t.name: (list(t.x), [float(v) for v in t.y]) for t in f0.data}
    cuentas, seguro, estado = (partes[k] for k in ("Cuentas individuales AFP (comisionable)", "Seguro Social (FAPP)", "Estado (PGU + PBS + APS)"))
    anios = cuentas[0]
    pct = [_por_100([cuentas[1][i], seguro[1][i], estado[1][i]]) for i in range(len(anios))]
    f = nueva(bargap=0.33, barmode="stack")
    for (xs, ys), color, j, tcol in ((cuentas, ORANGE, 0, INK_PRIMARY), (seguro, GREY_DARK, 1, SURFACE), (estado, GREY_BAR, 2, INK_PRIMARY)):
        txt = [f"<b>{cl(ys[i], 2)} billones<br>{cl(pct[i][j], 1)} %</b>" if j != 1 else "" for i in range(len(xs))]
        f.add_bar(x=xs, y=ys, marker_color=color, text=txt, textposition="inside", insidetextanchor="middle",
                  textfont=dict(size=BASE, color=tcol), marker_line=dict(color=SURFACE, width=2))
    i = len(anios) - 1
    yc = cuentas[1][i] / 2
    ys = cuentas[1][i] + seguro[1][i] / 2
    ye = cuentas[1][i] + seguro[1][i] + estado[1][i] / 2
    for y_, t_ in ((yc, cuadro(ORANGE, "<b>Cuentas individuales</b><br>(la administradora cobra comisión)")),
                   (ys, cuadro(GREY_DARK, f"<b>Seguro Social</b>: {cl(seguro[1][i], 2)} billones ({cl(pct[i][1], 1)} %)<br>(sin comisión)")),
                   (ye, cuadro(GREY_BAR, "<b>Estado</b>: Pensión Garantizada<br>Universal y aportes solidarios<br>(sin comisión)"))):
        f.add_annotation(x=i, y=y_, text=t_, showarrow=False, xanchor="left", xshift=175, align="left")
    tot = max(cuentas[1][k] + seguro[1][k] + estado[1][k] for k in range(len(anios)))
    f.update_xaxes(type="category", range=[-0.6, 2.6], title="", tickangle=0)
    f.update_yaxes(range=[0, tot * 1.15], title="Billones de pesos", gridcolor=GRIDLINE, zeroline=False)
    return set_meta(f, sumas=[float(sum(p)) for p in pct], pct_2025=float(pct[-1][0]))


def t_flujo_reforma(ctx, spec):
    f0 = fig_de(ctx, "1.3/flujo_reforma")
    real, base_, bajo, alto = f0.data[:4]
    cats = sorted(set(map(str, list(real.x) + list(base_.x))), key=int)
    pos = {c: i for i, c in enumerate(cats)}
    f = nueva()
    x0 = pos[str(list(real.x)[-1])] + 0.5
    f.add_vrect(x0=x0, x1=len(cats) - 0.5, fillcolor=INK_MUTED, opacity=0.08, line_width=0, layer="below")
    f.add_annotation(x=(x0 + len(cats) - 0.5) / 2, y=1, yref="paper", yanchor="top", showarrow=False, text="Escenario, no es un pronóstico",
                     font=dict(color=INK_SECONDARY))
    px_ = lambda t: [pos[str(v)] for v in t.x]  # noqa: E731
    for t in (bajo, alto):
        f.add_scatter(x=px_(t), y=arr(t.y), mode="lines", line=dict(color=INK_MUTED, width=2))
    f.add_scatter(x=px_(base_), y=arr(base_.y), mode="lines+markers", line=dict(color=ORANGE, width=4), marker=dict(size=8))
    f.add_scatter(x=px_(real), y=arr(real.y), mode="lines+markers", line=dict(color=BLUE, width=4), marker=dict(size=10))
    by = dict(zip(map(str, base_.x), map(float, base_.y)))
    ry = dict(zip(map(str, real.x), map(float, real.y)))
    for c, yy in (("2028", by["2028"]), ("2035", by["2035"])):
        f.add_scatter(x=[pos[c]], y=[yy], mode="markers", marker=dict(color=ORANGE, size=16, line=dict(color=SURFACE, width=2)))
        f.add_annotation(x=pos[c], y=yy, text=f"<b>{cl(yy, 1)} %</b>", showarrow=False, yshift=-38 if c == "2028" else 32,
                         xanchor="center" if c == "2028" else "right", xshift=0 if c == "2028" else -6, yanchor="middle")
    f.add_annotation(x=pos["2025"], y=ry["2025"], text=f"<b>{cl(ry['2025'], 1)} %</b>", showarrow=False, yshift=30)
    rotulos_finales(f, [(pos["2035"], by["2035"] + 1.5, "Escenario base", ORANGE),
                        (pos["2035"], float(arr(alto.y)[-1]) - 1.5, "Reforma con menos<br>empleo formal (dos<br>supuestos de elasticidad)", INK_MUTED)],
                    (0, 80), 470, xshift=16)
    f.update_xaxes(tickvals=list(range(len(cats))), ticktext=[c if int(c) % 2 == 0 or c in ("2025", "2035") else "" for c in cats],
                   range=[-0.5, len(cats) + 3.3], title="", showgrid=False, tickangle=0, zeroline=False)
    f.update_yaxes(range=[0, 80], ticksuffix=" %", title="% del flujo previsional", gridcolor=GRIDLINE, zeroline=False)
    return set_meta(f, v2028=by["2028"], v2035=by["2035"])


# ---------------------------------------------------------------- mapa
def _merc(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def _centroides(geo):
    out = {}
    for ft in geo["features"]:
        g = ft["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        mejor, area_max = None, -1
        for p in polys:
            ring = np.asarray(p[0])
            xx, yy = ring[:, 0], ring[:, 1]
            a = 0.5 * (xx[:-1] * yy[1:] - xx[1:] * yy[:-1]).sum()
            if abs(a) > area_max:
                cx = ((xx[:-1] + xx[1:]) * (xx[:-1] * yy[1:] - xx[1:] * yy[:-1])).sum() / (6 * a)
                cy = ((yy[:-1] + yy[1:]) * (xx[:-1] * yy[1:] - xx[1:] * yy[:-1])).sum() / (6 * a)
                mejor, area_max = (cx, cy), abs(a)
        out[int(ft["properties"]["region_id"])] = mejor
    return out


def t_mapa(ctx, spec):
    W, H = ctx["cfg"]["lienzos"][spec["canvas"]]
    top = ctx["top_px"]
    geo = json.load(open(DP / "geo" / "regiones_chile.geojson", encoding="utf-8"))
    pres = pd.read_csv(DP / "kpi_presion_previsional_region.csv")
    reg = pd.read_csv(DP / "kpi_cobertura_regiones.csv")
    crit = set(criticas(reg).region_id.astype(int))
    nac = float(reg.loc[reg.region_id == 0, "cobertura_ref"].iloc[0])
    var = "cobertura_previsional_pct"
    z0 = sorted(arr(fig_de(ctx, "1.1/mapa").data[0].z).astype(float))
    assert np.allclose(z0, sorted(pres[var])), "el mapa del dashboard no usa los mismos datos"
    Wm, Hm = W, H - NOTE_BAND - top  # top = alto del título impreso arriba (el mapa no tiene margen propio)
    lat_n, lat_s = -17.3, -56.2
    zoom = math.log2((Hm - 36) / ((_merc(lat_n) - _merc(lat_s)) / (2 * math.pi) * 512))
    world = 512 * 2 ** zoom
    my = (_merc(lat_n) + _merc(lat_s)) / 2
    clat = math.degrees(2 * math.atan(math.exp(my)) - math.pi / 2)
    ppd = world / 360
    clon = -71 + (Wm / 2 - 0.17 * Wm) / ppd
    px_x = lambda lon: Wm / 2 + (lon - clon) * ppd  # noqa: E731
    px_y = lambda lat: Hm / 2 - (_merc(lat) - my) / (2 * math.pi) * world  # noqa: E731
    escala = [[i / (len(SEQ_BLUE) - 1), c] for i, c in enumerate(SEQ_BLUE)]
    f = nueva(margin=dict(l=0, r=0, t=top, b=0))
    f.add_choroplethmap(geojson=geo, locations=pres.region_id, featureidkey="properties.region_id", z=pres[var], colorscale=escala,
                        marker_line_color="white", marker_line_width=1, marker_opacity=0.95,
                        colorbar=dict(orientation="h", x=0.97, xanchor="right", y=0.10, yanchor="bottom", len=0.34, thickness=20,
                                      title=dict(text="Cotizantes ÷ población de 15 a 64 años (%)", side="top", font=dict(size=ANNOT)),
                                      tickfont=dict(size=MIN_FONT), dtick=4))
    f.add_choroplethmap(geojson=geo, locations=sorted(crit), featureidkey="properties.region_id", z=[1] * len(crit),
                        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False, marker_line_color=ORANGE, marker_line_width=3.5)
    f.update_layout(map=dict(style="carto-positron", center=dict(lat=clat, lon=clon), zoom=zoom, domain=dict(x=[0, 1], y=[0, 1])))
    cen = _centroides(geo)
    d = pres.set_index("region_id")
    lo, hi = d[var].idxmin(), d[var].idxmax()
    filas = sorted(((rid, px_x(c[0]), px_y(c[1])) for rid, c in cen.items()), key=lambda r: r[2])
    col_x = px_x(-63.5)
    ys, prev = [], -1e9
    for _, _, y in filas:
        yy = max(y, prev + 31)
        ys.append(yy); prev = yy
    exceso = ys[-1] - (Hm - 30)
    if exceso > 0:
        ys = [y - exceso for y in ys]
        for k in range(len(ys) - 2, -1, -1):
            ys[k] = min(ys[k], ys[k + 1] - 31)
    for (rid, cx, cy), ly in zip(filas, ys):
        nombre = d.loc[rid, "region_nombre"]
        v = cl(float(d.loc[rid, var]), 1)
        extra = " (la más baja)" if rid == lo else (" (la más alta)" if rid == hi else "")
        if rid in crit:
            txt = f"<span style='color:{ORANGE}'>■</span> <b>{nombre}: {v} %{extra}</b>"
        else:
            txt = f"<span style='color:{INK_SECONDARY}'>{nombre}: {v} %{extra}</span>" if not extra else f"<b>{nombre}: {v} %{extra}</b>"
        f.add_annotation(x=cx / Wm, y=1 - cy / Hm, xref="paper", yref="paper", ax=col_x - cx, ay=ly - cy, text=txt, showarrow=True,
                         arrowhead=0, arrowwidth=1, arrowcolor=INK_MUTED, xanchor="left", standoff=2, font=dict(size=MIN_FONT))
    f.add_annotation(x=0.97, y=0.96, xref="paper", yref="paper", xanchor="right", yanchor="top", showarrow=False, align="right",
                     text=f"<b>Chile: {cl(nac, 1)} %</b><br><span style='color:{ORANGE}'>■</span> borde naranja = región crítica ({len(crit)})",
                     font=dict(size=ANNOT), bgcolor="rgba(252,252,251,0.85)", borderpad=6)
    return set_meta(f, mapa=True, fixed_margin=True)


def t_prio(ctx, spec):
    f = fig_de(ctx, spec["key"])
    f.update_layout(title=None, height=None)
    tr = f.data[0]
    tr.marker.color = [GREY_BAR if c == BLUE else c for c in tr.marker.color]
    tr.textfont = dict(size=ANNOT, color=INK_PRIMARY)
    tr.text = [t.replace("  (", " (").replace("+-", "−").replace("-", "−") for t in tr.text]
    tr.marker.color = [GREY_BAR if y in EXCLUIDAS else c for y, c in zip(tr.y, tr.marker.color)]  # excluida: no entra
    if spec.get("sin_rango"):  # sin el rango entre paréntesis: «−10,0 (1)» pasa a «−10,0»
        tr.text = [re.sub(r"\s*\(\d+\)\s*$", "", t) for t in tr.text]
    f.update_yaxes(categoryorder="array", categoryarray=list(tr.y))  # la primera categoría va abajo: la mejor abajo, la peor arriba
    f.add_annotation(x=1, y=1.0, xref="paper", yref="paper", xanchor="right", yanchor="bottom", yshift=6, showarrow=False,
                     text=f"{cuadro(ORANGE, 'entra por este factor')}    {cuadro(ORANGE_LIGHT, 'ya entró por otro factor')}    {cuadro(GREY_BAR, 'no entra')}")
    if "brecha" in spec["key"]:
        f.update_xaxes(tickformat=",.0f")
    f.update_xaxes(title=dict(font=dict(size=TICK)))
    return set_meta(f, extra_top=36, orden="de la peor (arriba) a la mejor")


def _tabla(header, cols, fills=None, widths=None, h_cell=40, h_head=56, font=MIN_FONT, align=None):
    fills = fills or [[SURFACE] * len(cols[0])] * len(cols)
    return go.Table(columnwidth=widths, header=dict(values=[f"<b>{h}</b>" for h in header], fill_color="#e7eef7", line_color=GRIDLINE,
                                                    font=dict(size=font, color=INK_PRIMARY), align="left", height=h_head),
                    cells=dict(values=cols, fill_color=fills, line_color=GRIDLINE, font=dict(size=font, color=INK_PRIMARY),
                               align=align or "left", height=h_cell))


def t_tabla_rangos(ctx, spec):
    t = tabla_de(ctx, "1.1/tabla_rangos")
    c = list(t.columns)
    reg, cob, niv, rn, ten, rt, bre, rb, nf, sr, res = c
    fmt_r = lambda v: cl(v, 1).replace(",0", "")  # noqa: E731
    t[res] = [("Excluida" if r in EXCLUIDAS else e) for r, e in zip(t[reg], t[res])]  # excluida por decisión del equipo: no entra
    cols = [[f"<b>{r}</b>" if e == "Entra" else r for r, e in zip(t[reg], t[res])],
            [cl(v, 1) for v in t[cob]], [cl(v, 1, True) for v in t[niv]], [fmt_r(v) for v in t[rn]],
            [cl(v, 1, True) for v in t[ten]], [fmt_r(v) for v in t[rt]], [cl(v, 0, True) for v in t[bre]], [fmt_r(v) for v in t[rb]],
            [str(int(v)) for v in t[nf]], [fmt_r(v) for v in t[sr]],
            [("<b>Entra</b>" if v == "Entra" else ("No (sobre Chile)" if "promedio" in v else "No (ningún factor)" if "ningún" in v else "No (excluida)" if v == "Excluida" else v)) for v in t[res]]]
    base = [SURFACE] * len(t)
    fills = [base, base, base, [ORANGE_TINT if v <= 5 else SURFACE for v in t[rn]], base, [ORANGE_TINT if v <= 5 else SURFACE for v in t[rt]],
             base, [ORANGE_TINT if v <= 5 else SURFACE for v in t[rb]], base, base, base]
    head = ["Región", "Cobertura 2024 (%)", "Nivel (puntos)", "Rango", "Tendencia (puntos)", "Rango", "Brecha (personas)", "Rango",
            "Factores entre las 5 peores", "Suma de rangos", "Resultado"]
    f = nueva()
    f.add_trace(_tabla(head, cols, fills, widths=[1.6, 1.0, 0.9, 0.6, 1.0, 0.6, 1.1, 0.6, 0.9, 0.8, 1.4], h_cell=38, h_head=80))
    f.update_layout(margin=dict(l=PAD, r=PAD, b=4))
    return set_meta(f, tabla=True)


def t_paneles_2019(ctx, spec):
    f = fig_de(ctx, "1.1/paneles_2019")
    f.update_layout(title=None, height=None)
    for an in f.layout.annotations:
        an.font.size = MIN_FONT
    for tr in f.data:
        if tr.textfont is not None:
            tr.textfont.size = MIN_FONT
        tr.line.width = 3
    f.update_xaxes(tickvals=[2019, 2024], tickfont=dict(size=MIN_FONT), showgrid=False)
    f.update_yaxes(tickfont=dict(size=MIN_FONT))
    return set_meta(f, extra_top=28)


PANEL_DESC = ["participacion", "empleo", "cotizacion", "total"]


def t_desc_nivel(ctx, spec):
    acento = spec.get("params", {}).get("acento", "cotizacion")
    f = fig_de(ctx, "1.1/desc_nivel")
    f.update_layout(title=None, height=None)
    for tr in f.data:                                       # sin las regiones excluidas (Biobío)
        quedan = [i for i, y in enumerate(tr.y) if y not in EXCLUIDAS]
        tr.x, tr.y = [tr.x[i] for i in quedan], [tr.y[i] for i in quedan]
        if tr.text is not None and not isinstance(tr.text, str):
            tr.text = [tr.text[i] for i in quedan]
    for k, tr in zip(PANEL_DESC, f.data):
        n = len(tr.x)
        tr.marker.color = [ORANGE if k == acento else (GREY_DARK if k == "total" else GREY_BAR)] * n
        tr.textfont = dict(size=ANNOT, color=INK_PRIMARY)
        tr.text = [("0,0" if t in ("-0,0", "+0,0", "−0,0") else t.replace("-", "−")) for t in tr.text]
    f.update_xaxes(showgrid=False)
    for s in f.layout.shapes:
        s.line.dash, s.line.color, s.line.width = "solid", INK_MUTED, 1
    nombres = {"participacion": "Participación laboral", "empleo": "Empleo (1 − desocupación)", "cotizacion": "Ocupados que cotizan", "total": "Diferencia total"}
    for an, k in zip(f.layout.annotations, PANEL_DESC):
        an.font = dict(size=ANNOT, color=INK_PRIMARY)
        an.text = f"<b>{nombres[k]}</b>" if k == acento else nombres[k]
    f.update_yaxes(tickfont=dict(size=ANNOT))
    f.update_layout(margin=dict(l=PAD, r=PAD + 20))
    return set_meta(f, extra_top=34, orden="por diferencia total con Chile (mismo orden en los cuatro paneles)")


def n12_desc_16(ctx, spec):
    """1.1.25 en cuatro gráficos (uno por panel: participación, empleo, ocupados que cotizan y diferencia total), con las 16 regiones
    en 2024 ordenadas de la que más resta (arriba) a la que más suma (abajo). Naranja = regiones críticas (sin Biobío); gris = las demás."""
    panel = spec["params"]["panel"]
    d = pd.read_csv(DP / "kpi_cobertura_descomposicion.csv")
    d = d[d.comparacion == "Nivel frente a Chile en 2024"]
    reg = pd.read_csv(DP / "kpi_cobertura_regiones.csv")
    reg = reg[reg.region_id > 0]                                  # las 16 regiones (sin el territorio histórico «Biobío y Ñuble»)
    w = d[d.territorio_id.isin(reg.region_id)].pivot(index="territorio_id", columns="factor", values="aporte_pp")
    w["total"] = w[["participacion", "empleo", "cotizacion"]].sum(axis=1)
    nombre = dict(zip(reg.region_id, reg.region_nombre))
    crit = set(criticas(reg).region_nombre)
    w = w.assign(region=[nombre[i] for i in w.index]).sort_values(panel, ascending=False)  # la primera categoría va abajo: la mejor abajo, la peor arriba
    v = w[panel].to_numpy(float)
    f = nueva(bargap=0.3)
    f.add_bar(y=w.region, x=v, orientation="h", marker_color=[ORANGE if r in crit else GREY_BAR for r in w.region],
              text=[("0,0" if abs(x) < 0.05 else cl(x, 1, True)) for x in v], textposition="outside", cliponaxis=False,
              textfont=dict(size=ANNOT, color=INK_PRIMARY))
    pad = (v.max() - v.min()) * 0.16
    f.update_xaxes(range=[min(v.min(), 0) - pad, max(v.max(), 0) + pad], title=dict(text="Puntos de cobertura frente a Chile (0 = igual que Chile)", font=dict(size=TICK)),
                   zeroline=True, zerolinecolor=INK_MUTED, zerolinewidth=1.5, gridcolor=GRIDLINE, tickfont=dict(size=TICK), tickformat=",.0f" if v.max() - v.min() > 5 else ",.1f")
    f.update_yaxes(categoryorder="array", categoryarray=list(w.region), tickfont=dict(size=ANNOT),
                   tickmode="array", tickvals=list(w.region), ticktext=[f"<b>{r}</b>" if r in crit else r for r in w.region])
    f.add_annotation(x=1, y=1.0, xref="paper", yref="paper", xanchor="right", yanchor="bottom", yshift=6, showarrow=False,
                     text=f"{cuadro(ORANGE, 'región crítica')}    {cuadro(GREY_BAR, 'las demás regiones')}")
    return set_meta(f, extra_top=36, orden="de la que más resta (arriba) a la que más suma (abajo)", valores={r: round(x, 2) for r, x in zip(w.region, v)})


def t_tipo_trabajo(ctx, spec):
    f0 = fig_de(ctx, "1.1/tipo_trabajo")
    ind = next(t for t in f0.data if t.name == "Independientes")
    dep = next(t for t in f0.data if t.name != "Independientes")
    v_ind = dict(zip(ind.y, map(float, ind.x)))
    v_dep = dict(zip(dep.y, map(float, dep.x)))
    k_cot = next(k for k in v_ind if k.startswith("Cotizantes"))
    k_ocu = next(k for k in v_ind if k.startswith("Ocupados"))
    ycat = {k_ocu: "Ocupados<br>(Censo 2024)", k_cot: "Cotizantes<br>(dic. 2024)"}
    f = nueva(barmode="stack", bargap=0.45)
    f.add_bar(y=[ycat[k_ocu], ycat[k_cot]], x=[v_ind[k_ocu], v_ind[k_cot]], orientation="h", marker_color=ORANGE, marker_line=dict(color=SURFACE, width=2),
              text=[f"<b>Independientes<br>{cl(v_ind[k_ocu], 1)} %</b>", ""], textposition="inside", insidetextanchor="middle",
              textfont=dict(size=ANNOT, color=INK_PRIMARY))
    f.add_bar(y=[ycat[k_ocu], ycat[k_cot]], x=[v_dep[k_ocu], v_dep[k_cot]], orientation="h", marker_color=GREY_BAR, marker_line=dict(color=SURFACE, width=2),
              text=[f"Dependientes y otros<br>{cl(v_dep[k_ocu], 1)} %", f"Dependientes y otros: {cl(v_dep[k_cot], 1)} %"],
              textposition="inside", insidetextanchor="middle", textfont=dict(size=ANNOT, color=INK_PRIMARY))
    f.add_annotation(x=v_ind[k_cot], y=ycat[k_cot], text=f"<b>Independientes: {cl(v_ind[k_cot], 1)} %</b>", showarrow=True, arrowhead=0,
                     arrowcolor=ORANGE, arrowwidth=2, ax=60, ay=-58, xanchor="left")
    f.update_xaxes(range=[0, 100], ticksuffix=" %", dtick=25, title="% de cada grupo", gridcolor=GRIDLINE, zeroline=False)
    f.update_yaxes(categoryorder="array", categoryarray=[ycat[k_cot], ycat[k_ocu]], title="")
    return set_meta(f, sumas=[v_ind[k_ocu] + v_dep[k_ocu], v_ind[k_cot] + v_dep[k_cot]])


COLOR_COMP = {"Cotizan: dependientes": BLUE, "Cotizan: independientes y voluntarios": "#184f95", "No cotizan: ocupados informales": ORANGE,
              "No cotizan: ocupados formales fuera de la estadística": "#f4ac8f", "Buscan trabajo (desocupados)": "#a8a7a1", "Ni trabajan ni buscan": "#dddcd6"}


def t_composicion(ctx, spec):
    if spec.get("region"):  # región sin pestaña en el dashboard (Magallanes): mismas cifras, leídas del mismo CSV, en el mismo orden de bloques
        comp = pd.read_csv(DP / "kpi_cobertura_composicion_region.csv")
        seg = [(r.grupo, float(r.pct_15_64)) for r in comp[comp.region_nombre == spec["region"]].itertuples()]
        assert len(seg) == 6, spec["region"]
        if spec.get("region_es_maxima"):  # el titular dice «la región con más cobertura»: se comprueba con los datos
            cob = pd.read_csv(DP / "kpi_cobertura_regiones.csv").query("region_id != 0").set_index("region_nombre").cobertura_ref
            assert cob.idxmax() == spec["region"], cob.idxmax()
    else:
        clave = spec["key"] + (f":{spec['letter']}" if spec.get("letter") else "")
        f0 = fig_de(ctx, clave)
        seg = [(t.name, float(t.x[0])) for t in f0.data if t.type == "bar"]
    v = dict(seg)
    cot = v["Cotizan: dependientes"] + v["Cotizan: independientes y voluntarios"]
    inf, fue = v["No cotizan: ocupados informales"], v["No cotizan: ocupados formales fuera de la estadística"]
    des, nin = v["Buscan trabajo (desocupados)"], v["Ni trabajan ni buscan"]
    f = nueva(barmode="stack", bargap=0.0)
    for nombre, x in seg:
        f.add_bar(y=[0], x=[x], orientation="h", width=0.5, marker_color=COLOR_COMP[nombre], marker_line=dict(color=SURFACE, width=2))
    a = 0.0
    centros = {}
    for nombre, x in seg:
        centros[nombre] = a + x / 2
        a += x
    f.add_annotation(x=cot / 2, y=0, text=f"<b>Cotizan<br>{cl(cot, 1)} %</b>", showarrow=False, font=dict(color=SURFACE, size=BASE + 2))
    # llave sobre «trabajan y no cotizan»
    x0, x1 = cot, cot + inf + fue
    for s in ((x0, 0.36, x1, 0.36), (x0, 0.30, x0, 0.36), (x1, 0.30, x1, 0.36)):
        f.add_shape(type="line", x0=s[0], y0=s[1], x1=s[2], y1=s[3], line=dict(color=ORANGE, width=3))
    f.add_annotation(x=(x0 + x1) / 2, y=0.40, yanchor="bottom", showarrow=False, text=f"<b>Trabajan y no cotizan: {cl(inf + fue, 1)} de cada 100</b>")
    abajo = dict(y=-0.30, yanchor="top", showarrow=False)
    f.add_annotation(x=centros["No cotizan: ocupados informales"], text=f"Informales<br><b>{cl(inf, 1)} %</b>", **abajo)
    f.add_annotation(x=centros["No cotizan: ocupados formales fuera de la estadística"], text=f"Formales fuera de<br>la estadística <b>{cl(fue, 1)} %</b>", **abajo)
    f.add_annotation(x=centros["Ni trabajan ni buscan"], text=f"Ni trabajan ni buscan<br><b>{cl(nin, 1)} %</b> (resto)", **abajo)
    f.add_annotation(x=cot / 2, font=dict(color=INK_SECONDARY, size=MIN_FONT),
                     text=f"{cl(v['Cotizan: dependientes'], 1)} dependientes + {cl(v['Cotizan: independientes y voluntarios'], 1)}<br>independientes y voluntarios", **abajo)
    f.add_annotation(x=centros["Buscan trabajo (desocupados)"], y=-0.25, ax=46, ay=112, showarrow=True, arrowhead=0, arrowcolor=INK_MUTED, arrowwidth=1.5,
                     text=f"Buscan trabajo <b>{cl(des, 1)} %</b>", xanchor="left")
    extra = {}
    if spec.get("letter"):
        reg = pd.read_csv(DP / "kpi_cobertura_regiones.csv")
        nac = float(reg.loc[reg.region_id == 0, "cobertura_ref"].iloc[0])
        dif = round(round(cot, 1) - round(nac, 1), 1)
        f.add_annotation(x=cot / 2, y=0.30, yanchor="bottom", showarrow=False, font=dict(size=ANNOT, color=INK_PRIMARY),
                         text=f"Chile: {cl(nac, 1)} % → aquí <b>{cl(abs(dif), 1)} puntos {'más' if dif > 0 else 'menos'}</b>")
        extra["chile"] = nac
    f.update_xaxes(range=[0, 100.5], ticksuffix=" %", dtick=10, title="% de las personas de 15 a 64 años", gridcolor=GRIDLINE, zeroline=False)
    f.update_yaxes(range=[-1.0, 0.72], visible=False)
    f.update_xaxes(showgrid=False)
    return set_meta(f, sumas=[float(sum(x for _, x in seg))], **extra)


def t_palancas_dispersion(ctx, spec):
    f = fig_de(ctx, "1.1/palancas_dispersion")
    f.update_layout(title=None, height=None)
    f.data[0].line.update(color=INK_MUTED, width=1.5, dash="solid")
    reg = pd.read_csv(DP / "kpi_cobertura_regiones.csv")
    dejar = set(criticas(reg).region_nombre) | {"Metropolitana"}
    crit = dejar - {"Metropolitana"}
    burb = next(t for t in f.data if t.marker is not None and t.marker.size is not None and not isinstance(t.marker.size, (int, float)))
    pts = sorted(((n, float(x), float(y)) for n, x, y in zip(burb.text, burb.x, burb.y) if n in crit), key=lambda r: -(r[2] + 1.5 * r[1]))  # sin cruces
    met = next((float(x), float(y)) for n, x, y in zip(burb.text, burb.x, burb.y) if n == "Metropolitana")
    f.layout.annotations = []
    for k, (n, x, y) in enumerate(pts):
        f.add_annotation(x=x, y=y, axref="x", ayref="y", ax=49, ay=33 - 3.6 * k, text=n, xanchor="left", showarrow=True, arrowhead=0,
                         arrowwidth=1, arrowcolor=INK_MUTED, font=dict(size=MIN_FONT, color=INK_PRIMARY))
    f.add_annotation(x=met[0], y=met[1], text="Metropolitana", showarrow=False, yshift=40, font=dict(size=MIN_FONT))
    return set_meta(f, etiquetas="7 regiones críticas en columna, con línea guía")


def t_factores(ctx, spec):
    f = fig_de(ctx, "1.1/factores")
    f.update_layout(title=None, height=None)
    tr = f.data[0]
    ys = list(tr.y)
    tr.marker.color = [ORANGE if "informales" in y.lower() else GREY_BAR for y in ys]
    tr.textfont = dict(size=ANNOT, color=INK_PRIMARY)
    tr.text = [t.replace("-", "−") for t in tr.text]
    f.update_yaxes(tickfont=dict(size=ANNOT))
    return set_meta(f, orden="por valor absoluto de la correlación")


def t_acciones_tabla(ctx, spec):
    t = tabla_de(ctx, "1.1/acciones_tabla").reset_index()
    pal = pd.read_csv(DP / "kpi_cobertura_palancas.csv").set_index("palanca")
    directo = [a == "Directo" for a in t["Alcance de la administradora"]]
    fill_row = [ORANGE_TINT if d else SURFACE for d in directo]
    f = nueva()
    if spec.get("params", {}).get("modo") == "resumida":
        cols = [[f"<b>{wrap(p, 26)}</b>" for p in t.Palanca], [wrap(q, 32) for q in t["Quién actúa"]], list(t["Alcance de la administradora"]),
                [cl(pal.loc[p, "personas"] / 1e6, 2) for p in t.Palanca], list(t.Impacto)]
        head = ["Palanca", "Quién actúa", "Alcance de la administradora", "Personas alcanzadas (millones)", "Impacto (juicio del equipo)"]
        f.add_trace(_tabla(head, cols, [fill_row] * 5, widths=[2.2, 2.6, 1.3, 1.3, 1.2], h_cell=84, h_head=60))
    else:
        cols = [[f"<b>{wrap(p, 14)}</b>" for p in t.Palanca], [wrap(q, 46) for q in t["Qué es"]], [wrap(q, 18) for q in t["Quién actúa"]],
                list(t["Alcance de la administradora"]), [wrap(q, 20) for q in t["A quiénes alcanza"]], list(t.Efecto), list(t.Impacto), [wrap(q, 12) for q in t.Respaldo]]
        head = ["Palanca", "Qué es", "Quién actúa", "Alcance", "A quiénes alcanza", "Efecto", "Impacto", "Respaldo"]
        f.add_trace(_tabla(head, cols, [fill_row] * 8, widths=[1.3, 3.5, 1.4, 0.9, 1.5, 0.9, 0.8, 1.0], h_cell=40, h_head=46, font=MIN_FONT))
    f.update_layout(margin=dict(l=PAD, r=PAD, b=4))
    return set_meta(f, tabla=True)


def t_palancas_tabla(ctx, spec):
    t = tabla_de(ctx, "1.1/palancas_tabla")
    t = t[~t[t.columns[0]].isin(EXCLUIDAS)].reset_index(drop=True)   # sin las regiones excluidas (Biobío)
    c = list(t.columns)
    inf = [ORANGE_TINT if p in ("Ambas", "Informalidad") else SURFACE for p in t[c[1]]]
    par = [ORANGE_TINT if p in ("Ambas", "Participación") else SURFACE for p in t[c[1]]]
    base = [SURFACE] * len(t)
    head = [h.replace("Chile 26.3", "Chile 26,3").replace("Chile 62.3", "Chile 62,3") for h in c]
    cols = [[f"<b>{v}</b>" for v in t[c[0]]]] + [[str(v) for v in t[k]] for k in c[1:]]
    f = nueva()
    f.add_trace(_tabla([wrap(h, 18) for h in head], cols, [base, base, inf, par, base, base, base], widths=[1.6, 1.2, 1.3, 1.3, 1, 1.2, 1.4],
                       h_cell=62, h_head=92))
    f.update_layout(margin=dict(l=PAD, r=PAD, b=4))
    return set_meta(f, tabla=True)


def _paneles_escenarios(ctx):
    """Series de 1.2.10 por panel: {eje: (x, costo, capacidad, año del cruce rotulado)}."""
    f0 = fig_de(ctx, "1.2/esc_fijos")
    out = {}
    for t in f0.data:
        ax = t.xaxis or "x"
        out.setdefault(ax, {})["costo" if t.line.color == RED else "cap"] = (arr(t.x).astype(float), arr(t.y).astype(float))
    for an in f0.layout.annotations:
        if an.text and an.text.startswith("<b>") and an.xref and an.xref.startswith("x"):
            out[an.xref]["anio"] = int(re.sub(r"\D", "", an.text))
    titulos = [a.text for a in f0.layout.annotations if a.yref == "paper" and a.xref == "paper"]
    return out, titulos


ESC_EJE = {"x": "Cobertura constante (base)", "x4": "Cobertura sigue cayendo", "x5": "Mitad de los informales cotiza", "x6": "Todos los informales cotizan"}


def t_esc_fijos(ctx, spec):
    p, _ = _paneles_escenarios(ctx)
    ejes = ["x4", "x5", "x6"]
    f = make_subplots(rows=1, cols=3, shared_yaxes=True, horizontal_spacing=0.04,
                      subplot_titles=[f"{ESC_EJE[e]}: <b>{p[e]['anio']}</b>" for e in ejes])
    ymax = max(p[e][k][1].max() for e in ejes for k in ("costo", "cap"))
    for j, e in enumerate(ejes, start=1):
        (xc, yc), (xk, yk) = p[e]["costo"], p[e]["cap"]
        f.add_scatter(x=xk, y=yk, mode="lines", line=dict(color=BLUE, width=4), row=1, col=j)
        f.add_scatter(x=xc, y=yc, mode="lines", line=dict(color=RED, width=4), row=1, col=j)
        cr = cruce(xc, yc, np.interp(xc, xk, yk))
        if cr:
            f.add_shape(type="line", x0=cr[0], x1=cr[0], y0=0, y1=cr[1], line=dict(color=INK_MUTED, width=1.5), row=1, col=j)
            f.add_scatter(x=[cr[0]], y=[cr[1]], mode="markers", marker=dict(color=ORANGE, size=16, line=dict(color=SURFACE, width=2)), row=1, col=j)
        if j == 1:
            f.add_annotation(x=xc[-1], y=yc[-1], text=cuadro(RED, "Costo"), showarrow=False, xanchor="right", yanchor="bottom", yshift=8, row=1, col=j)
            f.add_annotation(x=xk[-1], y=yk[-1], text=cuadro(BLUE, "Capacidad"), showarrow=False, xanchor="right", yanchor="top", yshift=-8, row=1, col=j)
    for an in f.layout.annotations:
        an.font = dict(size=ANNOT, color=INK_PRIMARY)
    f.update_layout(showlegend=False, plot_bgcolor=SURFACE, paper_bgcolor=SURFACE, separators=",.")
    f.update_yaxes(range=[0, ymax * 1.1], gridcolor=GRIDLINE, zeroline=False)
    f.update_yaxes(title="Billones de pesos de 2025", row=1, col=1)
    f.update_xaxes(range=[2021.5, 2066], tickvals=[2025, 2035, 2045, 2055, 2065], showgrid=False, tickangle=0)
    return set_meta(f, extra_top=34, cruces={ESC_EJE[e]: p[e]["anio"] for e in ejes})


def t_esc_fijos_tabla(ctx, spec):
    t = tabla_de(ctx, "1.2/esc_fijos_tabla").reset_index()
    ren = {"Sin informalidad": "Todos los informales cotizan", "Mitad del camino": "Mitad de los informales cotiza"}
    esc = [ren.get(e, e) for e in t.Escenario]
    c = list(t.columns)
    dest = [ORANGE_TINT if e in ("Tope de carga 10 % (base)", "Todos los informales cotizan", "Mitad de los informales cotiza") else SURFACE for e in esc]
    cols = [[f"<b>{wrap(e, 22)}</b>" for e in esc], [wrap(str(v), 48) for v in t[c[1]]]] + [[str(v).replace("-", "−") for v in t[k]] for k in c[2:]]
    head = ["Escenario", "Qué supone", "Punto crítico", "Frente a la base (años)", "Carga requerida en 2050 (% del sueldo)", "Cotizantes por persona de 65 años o más en 2050"]
    f = nueva()
    f.add_trace(_tabla([wrap(h, 20) for h in head], cols, [dest] * len(cols), widths=[1.6, 3.6, 0.9, 1.0, 1.2, 1.3], h_cell=90, h_head=92))
    f.update_layout(margin=dict(l=PAD, r=PAD, b=4))
    return set_meta(f, tabla=True, renombrados=ren)


def t_reforma_esc(ctx, spec):
    f = fig_de(ctx, "1.2/reforma_esc")
    f.update_layout(title=None, height=None)
    for an in f.layout.annotations:
        an.font.size = ANNOT
    for tr in f.data:
        tr.line.width = 4
    for sh in f.layout.shapes:
        sh.line.dash, sh.line.color, sh.line.width = "solid", INK_MUTED, 1.5
    f.update_xaxes(tickangle=0, showgrid=False, range=[2021.5, 2080.2])
    f.update_layout(margin=dict(b=60))
    return set_meta(f, extra_top=34, margen_b=60)


# ------------------------------------------------------------------------------------------------ 3. figuras nuevas
def t_vista_directa(ctx, spec):
    """Vista del dashboard tal cual (sin título; el titular y el subtítulo los pone la exportación): ranking de cobertura por región (1.1.2),
    serie 2002-2024 de Chile, la región más rezagada y la mejor (1.1.16) y los seis paneles de escenarios (1.2.10 en su versión de seis paneles)."""
    f = fig_de(ctx, spec["key"])
    f.update_layout(title=None, height=None)
    for sh in f.layout.shapes:
        sh.line.dash = "solid" if sh.type == "line" else sh.line.dash
    if spec.get("xticks"):  # [primero, último+1, paso]: sin años vacíos a la derecha (el espacio extra es para los rótulos finales)
        f.update_xaxes(tickvals=list(range(*spec["xticks"])))
    return set_meta(f, **spec.get("meta", {}))


def n0_seguimiento(paso_activo: str, pasos: list) -> go.Figure:
    f = nueva(margin=dict(l=PAD, r=PAD, t=8, b=8))
    n = len(pasos)
    ancho = 1 / n
    for i, p in enumerate(pasos):
        x0, x1 = i * ancho + 0.006, (i + 1) * ancho - 0.006
        act = p == paso_activo
        f.add_shape(type="path", xref="paper", yref="paper",
                    path=f"M {x0},0.05 L {x1 - 0.012},0.05 L {x1},0.5 L {x1 - 0.012},0.95 L {x0},0.95 L {x0 + (0.012 if i else 0)},0.5 Z",
                    fillcolor=ORANGE if act else "#ecebe6", line=dict(color=SURFACE, width=2))
        f.add_annotation(x=(x0 + x1) / 2 + 0.004, y=0.5, xref="paper", yref="paper", showarrow=False,
                         text=f"<b>{p}</b>" if act else p, font=dict(size=ANNOT, color=INK_PRIMARY if act else INK_SECONDARY))
    f.update_xaxes(visible=False)
    f.update_yaxes(visible=False)
    return set_meta(f, fixed_margin=True, diagrama=True)


def n0_resumen(ctx, spec):
    f = nueva()
    tiles = [("2034", "máximo de la población de 15 a 64 años"), ("2038", "punto crítico del Pilar Solidario (escenario)"),
             ("46,5 %", "cobertura de Chile en 2024")]
    for i, (num, txt) in enumerate(tiles):
        x0, x1 = 0.005 + i * 0.25, 0.235 + i * 0.25
        f.add_shape(type="rect", xref="paper", yref="paper", x0=x0, x1=x1, y0=0.02, y1=0.98, fillcolor="#f1f0eb", line=dict(width=0))
        f.add_annotation(x=x0 + 0.015, y=0.50, xref="paper", yref="paper", xanchor="left", yanchor="bottom", showarrow=False, text=f"<b>{num}</b>",
                         font=dict(size=46, color=INK_PRIMARY))
        f.add_annotation(x=x0 + 0.015, y=0.44, xref="paper", yref="paper", xanchor="left", yanchor="top", showarrow=False, text=wrap(txt, 34), align="left",
                         font=dict(size=MIN_FONT, color=INK_SECONDARY))
    f.add_annotation(x=0.80, y=0.5, xref="paper", yref="paper", xanchor="left", showarrow=False, text="<b>→ ¿Dónde?</b>",
                     font=dict(size=44, color=ORANGE))
    f.update_xaxes(visible=False)
    f.update_yaxes(visible=False)
    return set_meta(f, diagrama=True)


PASOS = [("Definición del problema", "Página «Problema»: envejecimiento y máximo de 2034"),
         ("Establecer objetivos", "Objetivo 1: base activa; Objetivo 2: presión fiscal"),
         ("Identificar métricas claves", "Indicadores 1.1-1.3 y 2.1-2.3 (config/kpis.yaml)"),
         ("Seleccionar datos relevantes", "Censo 2024, proyecciones de población, Superintendencia, Presupuestos"),
         ("Diseñar estrategia analítica", "Regla de rangos (nivel, tendencia, brecha) y motor del punto crítico"),
         ("Implementación tecnología y herramientas", "{n_scripts} scripts de Python y tablero en Streamlit"),
         ("Análisis y modelado de datos", "Descomposición de la cobertura y 6 escenarios fijos"),
         ("Generación de insights estratégicos", "7 regiones críticas; punto crítico en 2038"),
         ("Diseño de plan de acción", "Palancas: qué hace la administradora y qué el Estado"),
         ("Seguimiento y medición continua", "{n_tests} archivos de pruebas automáticas y auditoría de fuentes (16-11-2026)")]
FASES = [("Entender", 0, 3, BLUE), ("Datos", 3, 6, AQUA), ("Análisis", 6, 8, VIOLET), ("Acción", 8, 10, ORANGE)]


def conteos() -> dict:
    raw = ROOT / "Data raw"
    ign = {".venv", "archive", "development sources"}
    fuentes = [p for p in raw.rglob("*") if p.is_file() and not any(part in ign for part in p.relative_to(raw).parts)
               and not p.name.startswith(".") and p.suffix.lower() not in (".md",) and "import_KPI1.2" not in p.parts]
    externas = [p for p in (raw / "_external").iterdir() if not p.name.startswith(".")]
    raiz = [p for p in raw.iterdir() if p.is_file() and not p.name.startswith(".") and p.suffix.lower() != ".md"]
    return dict(n_fuentes=len(externas) + len(raiz), n_raw=len(fuentes), n_scripts=len(list((ROOT / "Scripts").glob("[0-9][0-9]_*.py"))),
                n_proc=len(list(DP.glob("*.csv"))), n_kpi=len(list(DP.glob("kpi_*.csv"))), n_tests=len(list((ROOT / "tests").glob("test_*.py"))),
                n_paginas=len(list((DASH / "final_pages").glob("*.py"))))


def n1_diez_pasos(ctx, spec):
    """Dos filas de cinco pasos (en una sola fila los nombres del curso no caben con letra de 20 px)."""
    c = ctx["conteos"]
    f = nueva()
    w = 1 / 5
    filas = [(0.99, 0.0), (0.49, 0.0)]  # (borde superior de la fila, -)
    for i, (paso, prod) in enumerate(PASOS):
        fila, col = divmod(i, 5)
        top = filas[fila][0]
        color = next(cc for _, a, b, cc in FASES if a <= i < b)
        fase = next(n for n, a, b, _ in FASES if a <= i < b)
        x0, x1 = col * w + 0.004, (col + 1) * w - 0.004
        f.add_shape(type="rect", xref="paper", yref="paper", x0=x0, x1=x1, y0=top - 0.065, y1=top, fillcolor=color, line=dict(width=0))
        primero = i == 0 or next(n for n, a, b, _ in FASES if a <= i - 1 < b) != fase or col == 0
        if primero:
            f.add_annotation(x=x0 + 0.008, y=top - 0.0325, xref="paper", yref="paper", xanchor="left", text=f"<b>{fase}</b>", showarrow=False,
                             font=dict(color="white", size=MIN_FONT))
        y0c, y1c = top - 0.25, top - 0.08
        ym = (y0c + y1c) / 2
        f.add_shape(type="path", xref="paper", yref="paper",
                    path=f"M {x0},{y0c} L {x1 - 0.016},{y0c} L {x1},{ym} L {x1 - 0.016},{y1c} L {x0},{y1c} L {x0 + (0.016 if col else 0)},{ym} Z",
                    fillcolor=lighten(color, 0.80), line=dict(color=color, width=2))
        f.add_annotation(x=(x0 + x1) / 2, y=ym, xref="paper", yref="paper", xanchor="center", showarrow=False, text=f"<b>{i + 1}. {wrap(paso, 22)}</b>",
                         font=dict(size=MIN_FONT))
        f.add_annotation(x=x0 + 0.006, y=y0c - 0.015, xref="paper", yref="paper", xanchor="left", yanchor="top", showarrow=False, align="left",
                         text=wrap(prod.format(**c), 25), font=dict(size=MIN_FONT, color=INK_SECONDARY))
    f.update_xaxes(visible=False)
    f.update_yaxes(visible=False)
    return set_meta(f, diagrama=True)


FUENTES = ["Censo 2024", "Proyecciones de población", "Superintendencia de Pensiones",
           "Encuesta Nacional de Empleo", "Encuesta Casen 2022", "Presupuestos y Previsión Social"]
NIVEL = ["comunal<br>2024", "nacional (regional:<br>base 2017)<br>1992-2070", "regional<br>diciembre 2025", "regional<br>mayo 2024 (+ dic.<br>2024 del anexo)",
         "regional<br>2022", "nacional<br>2025"]
PREGUNTAS = [("Demografía", {0: "●", 1: "●"}),
             ("Cobertura y carga", {0: "●", 1: "●", 2: "●", 3: "○", 5: "●"}),
             ("Negocio de la administradora", {1: "○", 2: "●", 5: "●"}),
             ("Regiones críticas", {0: "●", 1: "○", 2: "●"}),
             ("Causas", {0: "●", 2: "●", 3: "●¹", 4: "○"}),
             ("Palancas", {0: "●", 2: "○", 3: "○²", 5: "●"}),
             ("Proyección", {0: "○", 1: "●³", 2: "●", 3: "○", 5: "●"})]
VACIOS = ["¹ Encuesta de empleo regional: el archivo del Instituto Nacional de Estadísticas llega a mayo 2024; diciembre 2024 sale del anexo de la Asociación de AFP; 2025 no existe por región.",
          "² Falta la encuesta de empleo regional por sexo y por razones de inactividad (los archivos regionales traen «Ambos sexos»).",
          "³ Falta la proyección regional base 2024 del Instituto Nacional de Estadísticas (no publicada): las regiones usan la base 2017 llevada al Censo 2024."]


def n2_matriz_fuentes(ctx, spec):
    f = nueva()
    x_lab, x0 = 0.0, 0.19
    cw = (1 - x0) / len(FUENTES)
    y_head, y_rows_top, y_rows_bot = 0.99, 0.86, 0.36
    rh = (y_rows_top - y_rows_bot) / len(PREGUNTAS)
    for j, fu in enumerate(FUENTES):
        xc = x0 + (j + 0.5) * cw
        f.add_annotation(x=xc, y=(y_head + y_rows_top) / 2, xref="paper", yref="paper", text=f"<b>{wrap(fu, 15)}</b>", showarrow=False, font=dict(size=MIN_FONT))
        f.add_annotation(x=xc, y=y_rows_bot - 0.015, xref="paper", yref="paper", yanchor="top", text=NIVEL[j], showarrow=False,
                         font=dict(size=MIN_FONT, color=INK_SECONDARY))
    for i, (preg, celdas) in enumerate(PREGUNTAS):
        yt = y_rows_top - i * rh
        yc = yt - rh / 2
        f.add_shape(type="line", xref="paper", yref="paper", x0=0, x1=1, y0=yt, y1=yt, line=dict(color=GRIDLINE, width=1))
        f.add_annotation(x=x_lab, y=yc, xref="paper", yref="paper", xanchor="left", text=f"<b>{preg}</b>", showarrow=False, font=dict(size=ANNOT))
        for j, marca in celdas.items():
            cx0, cx1 = x0 + j * cw + 0.004, x0 + (j + 1) * cw - 0.004
            vacio = any(s in marca for s in "¹²³")
            if vacio:
                f.add_shape(type="rect", xref="paper", yref="paper", x0=cx0, x1=cx1, y0=yt - rh + 0.006, y1=yt - 0.006, line=dict(color=ORANGE, width=2),
                            fillcolor=ORANGE_TINT)
                for k in range(1, 12):  # rayado
                    a = cx0 + k * (cx1 - cx0) / 12
                    f.add_shape(type="line", xref="paper", yref="paper", x0=a - 0.012, x1=a + 0.004, y0=yt - rh + 0.008, y1=yt - 0.008,
                                line=dict(color=ORANGE_LIGHT, width=2))
            simbolo = marca.rstrip("¹²³")
            sup = marca[len(simbolo):]
            f.add_annotation(x=(cx0 + cx1) / 2, y=yc, xref="paper", yref="paper", showarrow=False,
                             text=f"<span style='font-size:34px;color:{BLUE if simbolo == '●' else INK_SECONDARY}'>{simbolo}</span>{('<b> ' + sup + '</b>') if sup else ''}",
                             font=dict(size=ANNOT, color=INK_PRIMARY))
    f.add_shape(type="line", xref="paper", yref="paper", x0=0, x1=1, y0=y_rows_bot, y1=y_rows_bot, line=dict(color=GRIDLINE, width=1))
    f.add_annotation(x=x_lab, y=y_rows_bot - 0.015, xref="paper", yref="paper", xanchor="left", yanchor="top", showarrow=False,
                     text="<i>Nivel · último dato</i>", font=dict(size=MIN_FONT, color=INK_SECONDARY))
    f.add_annotation(x=0, y=0.0, xref="paper", yref="paper", xanchor="left", yanchor="bottom", showarrow=False, align="left",
                     text="<br>".join(wrap(v, 150) for v in VACIOS), font=dict(size=MIN_FONT, color=INK_PRIMARY))
    f.update_xaxes(visible=False)
    f.update_yaxes(visible=False)
    return set_meta(f, diagrama=True, vacios=3)


def n3_pipeline(ctx, spec):
    c = ctx["conteos"]
    etapas = [("Fuentes oficiales", "", "Importar de varias fuentes", "Censo, Superintendencia, encuesta de empleo", f"{c['n_fuentes']} fuentes",
               "Auditoría contra la fuente original"),
              ("Data raw/", "Bronce", "Copias sin tocar, con inventario", "cotizantes_region.xls", f"{c['n_raw']} archivos", "Inventario de cada archivo"),
              ("Scripts/NN_*.py", "Plata", "Limpiar: tipos, formatos, regiones, años, unidades", "03_procesar_…py", f"{c['n_scripts']} scripts",
               "Las 16 regiones suman el país"),
              ("Data processed/", "Oro", "Columnas calculadas, ranking, unión por region_id", "kpi_pc_nacional.csv", f"{c['n_kpi']} tablas kpi_*.csv",
               "Las partes suman la cobertura de cada región"),
              ("Dashboards/", "Consumo", "Visualizar en Streamlit (final y extendida)", "objetivo1.py", f"{c['n_paginas']} páginas finales",
               "Cada página corre sin errores"),
              ("Diapositivas", "", "Exportar figuras con mensaje y fuente", "figuras_pptx/", "este paquete", "Revisión automática de las pautas")]
    f = nueva()
    n = len(etapas)
    w = 1 / n
    for i, (nombre, capa, verbo, ejemplo, conteo, control) in enumerate(etapas):
        x0, x1 = i * w + 0.008, (i + 1) * w - 0.022
        oro = capa == "Oro"
        f.add_shape(type="rect", xref="paper", yref="paper", x0=x0, x1=x1, y0=0.70, y1=0.92, fillcolor=ORANGE_TINT if oro else "#ecebe6",
                    line=dict(color=ORANGE if oro else GRIDLINE, width=3 if oro else 1))
        if capa:
            f.add_annotation(x=(x0 + x1) / 2, y=0.97, xref="paper", yref="paper", text=f"<b>{capa}</b>", showarrow=False, font=dict(size=MIN_FONT, color=INK_SECONDARY))
        f.add_annotation(x=(x0 + x1) / 2, y=0.81, xref="paper", yref="paper", xanchor="center", text=f"<b>{wrap(nombre, 16)}</b>", showarrow=False, font=dict(size=ANNOT))
        texto = (f"{wrap(verbo, 18)}<br><i>Ejemplo:</i><br>{wrap(ejemplo, 18)}<br><b>{wrap(conteo, 18)}</b><br>"
                 f"<span style='color:{INK_SECONDARY}'><i>Control:</i><br>{wrap(control, 18)}</span>")
        f.add_annotation(x=x0, y=0.65, xref="paper", yref="paper", xanchor="left", yanchor="top", align="left", text=texto, showarrow=False,
                         font=dict(size=MIN_FONT))
        if i < n - 1:
            f.add_annotation(x=x1 + 0.019, y=0.81, xref="paper", yref="paper", ax=-16, ay=0, showarrow=True, arrowhead=2, arrowsize=1.4,
                             arrowwidth=2.5, arrowcolor=INK_SECONDARY, text="")
    f.update_xaxes(visible=False)
    f.update_yaxes(visible=False)
    return set_meta(f, diagrama=True, conteos=c)


def n4_limpieza(ctx, spec):
    """Versión simple, media diapositiva: tres reglas a la izquierda y una sola barra a la derecha (con región + sin región = total)."""
    raw = pd.read_excel(ROOT / "Data raw" / "cotizantes_region.xls", header=None)
    anios_raw = list(raw.iloc[5])
    k24 = next(k for k, a in enumerate(anios_raw) if isinstance(a, (int, float)) and not pd.isna(a) and int(a) == 2024)
    fila_sin = next(r for r in range(6, len(raw)) if str(raw.iloc[r, 0]).strip() == "Sin Información")
    proc = pd.read_csv(DP / "cotizantes_por_region.csv")
    r24 = proc[proc.anio == 2024]
    total = int(r24.loc[r24.region_label == "Total", "cotizantes"].iloc[0])
    sin = int(r24.loc[r24.region_label == "Sin Información", "cotizantes"].iloc[0])
    con = int(r24.loc[r24.region_id.notna(), "cotizantes"].sum())
    n_reg = int(r24.region_id.notna().sum())
    assert sin == int(float(raw.iloc[fila_sin, k24])), "el dato limpio debe ser el del archivo original"
    assert con + sin == total and n_reg == 16, (con, sin, total, n_reg)
    f = nueva()
    f.update_xaxes(visible=False, range=[0, 1])
    f.update_yaxes(visible=False, range=[0, 1])
    px = dict(xref="paper", yref="paper", showarrow=False)
    f.add_annotation(x=0.0, y=0.97, xanchor="left", yanchor="top", text="<b>Qué hicimos con el archivo</b>", font=dict(size=ANNOT), **px)
    reglas = ["Un año por fila", "Cada región con su nombre oficial (16 regiones)", "Sin región: se muestra aparte, no se reparte"]
    for i, t in enumerate(reglas):
        y = 0.71 - i * 0.26
        f.add_scatter(x=[0.018], y=[y], mode="markers", marker=dict(size=44, color=ORANGE), hoverinfo="skip")  # círculo de tamaño fijo en px
        f.add_annotation(x=0.018, y=y, text=f"<b>{i + 1}</b>", font=dict(size=ANNOT, color="#ffffff"), **px)
        f.add_annotation(x=0.05, y=y, xanchor="left", text=t, font=dict(size=ANNOT), **px)
    f.add_shape(type="line", xref="paper", yref="paper", x0=0.475, x1=0.475, y0=0.06, y1=0.92, line=dict(color=GRIDLINE, width=2))
    f.add_annotation(x=0.50, y=0.97, xanchor="left", yanchor="top", text="<b>Cotizantes, diciembre de 2024</b>", font=dict(size=ANNOT), **px)
    f.add_bar(y=[""], x=[con], orientation="h", marker_color=BLUE, xaxis="x2", yaxis="y2", width=0.6)
    f.add_bar(y=[""], x=[sin], orientation="h", marker_color=ORANGE, xaxis="x2", yaxis="y2", width=0.6)
    f.update_layout(barmode="stack", xaxis2=dict(domain=[0.50, 0.99], range=[0, total], visible=False), yaxis2=dict(domain=[0.34, 0.62], visible=False))
    f.add_annotation(x=0.50, y=0.70, xanchor="left", yanchor="bottom", text=f"<b>{cl(con, 0)}</b> con región", font=dict(size=ANNOT, color=BLUE), **px)
    f.add_annotation(x=0.99, y=0.70, xanchor="right", yanchor="bottom", text=f"<b>{cl(sin, 0)}</b> sin región", font=dict(size=ANNOT, color=ORANGE), **px)
    f.add_shape(type="line", xref="paper", yref="paper", x0=0.50, x1=0.99, y0=0.22, y1=0.22, line=dict(color=INK_SECONDARY, width=2))
    f.add_annotation(x=0.745, y=0.10, xanchor="center", yanchor="middle", text=f"<b>Total {cl(total, 0)}</b>   ✓ la suma cuadra",
                     font=dict(size=ANNOT), bgcolor="#e8f3ec", borderpad=6, **px)
    return set_meta(f, diagrama=True, fixed_margin=True, total=total, sin=sin, con=con)


def n5_factores_seleccion(ctx, spec):
    t = tabla_de(ctx, "1.1/tabla_rangos")
    c = list(t.columns)
    reg, niv, rn, ten, rt, bre, rb, res = c[0], c[2], c[3], c[4], c[5], c[6], c[7], c[10]
    entra = (t[res] == "Entra") & ~t[reg].isin(EXCLUIDAS)
    nombres = [f"<b>{r}</b>" if e else r for r, e in zip(t[reg], entra)]
    f = make_subplots(rows=1, cols=3, shared_yaxes=True, horizontal_spacing=0.07,
                      subplot_titles=["<b>Nivel</b>: puntos frente a Chile", "<b>Tendencia</b>: puntos ganados desde 2007 frente a Chile",
                                      "<b>Brecha</b>: miles de cotizantes que faltan (−)"])
    fr = lambda v: cl(v, 1).replace(",0", "")  # noqa: E731
    for j, (col, rk, esc, dec) in enumerate(((niv, rn, 1, 1), (ten, rt, 1, 1), (bre, rb, 1e3, 0)), start=1):
        v = t[col] / esc
        colr = [ORANGE if (r <= 5 and e) else GREY_BAR for r, e in zip(t[rk], entra)]
        f.add_bar(y=nombres, x=v, orientation="h", marker_color=colr, text=[f"{cl(x, dec, True)} ({fr(r)})" for x, r in zip(v, t[rk])],
                  textposition="outside", cliponaxis=False, textfont=dict(size=MIN_FONT, color=INK_PRIMARY), row=1, col=j)
        lim = float(np.abs(v).max()) * 1.95
        f.update_xaxes(range=[-lim, lim], zeroline=True, zerolinecolor=INK_MUTED, showgrid=False, showticklabels=False, row=1, col=j)
    n8 = int(entra.sum())
    f.update_yaxes(categoryorder="array", categoryarray=nombres[::-1], tickfont=dict(size=MIN_FONT))
    f.add_shape(type="line", xref="paper", yref="y", x0=-0.13, x1=1, y0=len(t) - n8 - 0.5, y1=len(t) - n8 - 0.5, line=dict(color=INK_PRIMARY, width=1.5))
    f.add_annotation(x=1, y=1.0, xref="paper", yref="paper", xanchor="right", yanchor="bottom", yshift=40, showarrow=False,
                     text=f"{cuadro(ORANGE, 'entra por este factor (bajo Chile y entre las 5 peores)')}    {cuadro(GREY_BAR, 'no entra por este factor')}")
    for an in f.layout.annotations:
        if an.font.size is None:
            an.font = dict(size=MIN_FONT, color=INK_PRIMARY)
    f.update_layout(showlegend=False, plot_bgcolor=SURFACE, paper_bgcolor=SURFACE, separators=",.", bargap=0.33)
    brecha8 = float(-t.loc[entra, bre].sum())
    return set_meta(f, extra_top=70, brecha_8=brecha8, n=n8, orden="factores y suma de rangos")


# ---------------------------------------------------------------- regla de dos preguntas (Scripts/35) y figuras de S13 / S14
def _seleccion() -> dict:
    """Secciones de Data processed/kpi_seleccion_dos_preguntas.csv (lo escribe Scripts/35_seleccion_dos_preguntas.py)."""
    ruta = DP / "kpi_seleccion_dos_preguntas.csv"
    if not ruta.exists():
        raise FileNotFoundError(f"Falta {ruta.name}: correr antes Scripts/35_seleccion_dos_preguntas.py")
    d = pd.read_csv(ruta)
    S = {k: d[d.section == k].reset_index(drop=True) for k in ("chile", "ranking", "gap", "selection", "decomposition")}
    exc = S["selection"]["name"].isin(EXCLUIDAS)          # decisión del equipo: la región sigue en el cálculo de la brecha, pero no queda seleccionada
    S["selection"].loc[exc, ["selected", "motivo"]] = [False, "excluida"]
    S["selection"]["selected"] = S["selection"]["selected"].astype(bool)
    S["decomposition"] = S["decomposition"][~S["decomposition"]["name"].isin(EXCLUIDAS)].reset_index(drop=True)
    return S


def _exigir(spec: dict, *cifras: str) -> None:
    """Cada cifra que el mensaje cita sale de los datos; si el texto del YAML dice otra cosa, se detiene (los datos mandan)."""
    for c in cifras:
        assert c in spec["message"], f"{spec['id']}: el mensaje del YAML no contiene «{c}» (dato calculado); actualizar config/figuras_presentacion.yaml"


class _Px:
    """Coordenadas en píxeles dentro del área del gráfico (margen fijo: 8 px arriba y abajo, PAD a los lados) para tablas y recuadros."""

    def __init__(self, fig: go.Figure, W: int, plot_h: int):
        self.f, self.w, self.h = fig, W - 2 * PAD, plot_h - 16

    def x(self, v):
        return v / self.w

    def y(self, v):
        return 1 - v / self.h

    def txt(self, x, y, texto, ax="left", ay="middle", size=MIN_FONT, color=INK_PRIMARY, bold=False, align=None, **kw):
        self.f.add_annotation(x=self.x(x), y=self.y(y), xref="paper", yref="paper", xanchor=ax, yanchor=ay, showarrow=False,
                              text=f"<b>{texto}</b>" if bold else texto, align=align or ax, font=dict(size=size, color=color), **kw)

    def rect(self, x0, y0, x1, y1, fill, line=None):
        self.f.add_shape(type="rect", xref="paper", yref="paper", x0=self.x(x0), x1=self.x(x1), y0=self.y(y0), y1=self.y(y1), fillcolor=fill,
                         line=dict(color=line, width=1) if line else dict(width=0), layer="below")

    def hline(self, x0, x1, y, color=GRIDLINE, width=1):
        self.f.add_shape(type="line", xref="paper", yref="paper", x0=self.x(x0), x1=self.x(x1), y0=self.y(y), y1=self.y(y), line=dict(color=color, width=width))


def _lienzo_px(ctx, spec, plot_min: int):
    """Alto del área del gráfico: el del lienzo si alcanza; si no (variante con título largo), el lienzo crece solo en esa variante."""
    W, H = ctx["cfg"]["lienzos"][spec["canvas"]]
    top = ctx["top_px"]
    plot_h = H - NOTE_BAND - top
    if plot_h < plot_min:
        plot_h = plot_min
    return W, plot_h, plot_h + NOTE_BAND + top


def _fig_vacia() -> go.Figure:
    f = nueva()
    f.update_xaxes(visible=False, range=[0, 1])
    f.update_yaxes(visible=False, range=[0, 1])
    return f


def n5_ranking_tabla(ctx, spec):
    """Tabla de puestos 2007 frente a 2024 con flechas (Chile + las 9 regiones bajo Chile, en el orden de 2024). Dibujada con formas y textos."""
    S = _seleccion()
    ch, rk = S["chile"].iloc[0], S["ranking"]
    todas = bool(spec.get("params", {}).get("todas"))   # N.5e: los 15 territorios (16 regiones, Biobío y Ñuble unidos), del mayor al menor cambio en puntos
    if todas:
        bajo = rk.sort_values("change_pp", ascending=False)
        perd = bajo[bajo.by_trend.astype(bool)]
        assert len(bajo) == 15 and len(perd) == 3, "N.5e: se esperaban 15 territorios y 3 bajo Chile que pierden puestos"
        menos = bajo[bajo.change_pp < ch.change_pp]
        _exigir(spec, cl(ch.change_pp, 1, True), cl(bajo.iloc[0].change_pp, 1, True), *list(menos["name"]))
        assert len(menos) == 4, "N.5e: el mensaje supone cuatro territorios con menos puntos que Chile"
    else:
        bajo = rk[rk.below_chile.astype(bool)].sort_values("rank_end")
        perd = bajo[bajo.by_trend.astype(bool)]
        _exigir(spec, *[f"{r['name']} ({int(r.rank_start)}.º a {int(r.rank_end)}.º)" for _, r in perd.iterrows()])
        assert len(perd) == 3 and len(bajo) == 9, "N.5a: se esperaban 9 territorios bajo Chile y 3 que pierden puestos"
    n = len(bajo) + 1
    cab, pie = 58, 124                      # alto del encabezado; alto de la llave y la nota al pie
    W, plot_h, canvas_h = _lienzo_px(ctx, spec, plot_min=8 + cab + n * 34 + pie + 8)
    fila = min(44, (plot_h - 16 - cab - pie - 10) / n)
    f = _fig_vacia()
    P = _Px(f, W, plot_h)
    C = dict(nom=0, p07=240, fl=313, p24=385, cob=495, pts=610, pct=P.w)        # x de cada columna (nombre: izquierda; resto: centro; % : derecha)
    P.rect(0, 0, P.w, cab, "#e7eef7")
    for k, (t, ax_) in {"nom": ("Región", "left"), "p07": ("Puesto<br>2007", "center"), "fl": ("Cambio<br>puestos", "center"), "p24": ("Puesto<br>2024", "center"),
                        "cob": ("Cobertura %<br>2007 → 2024", "center"), "pts": ("Cambio<br>(puntos)" + (" ↓" if todas else ""), "center"), "pct": ("Cambio<br>(%)", "right")}.items():
        P.txt(C[k] + (6 if k == "nom" else 0), cab / 2, t, ax=ax_, bold=True, align="center" if ax_ != "left" else "left")
    y = cab
    filas = [("Chile", None, None, ch)] + [(r["name"], r, None, r) for _, r in bajo.iterrows()]
    for i, (nombre, r, _, d) in enumerate(filas):
        yc = y + fila / 2
        es_chile, pierde = r is None, r is not None and bool(r.by_trend)
        P.rect(0, y, P.w, y + fila, "#eceae4" if es_chile else (lighten(BLUE, 0.86) if pierde else SURFACE))
        P.hline(0, P.w, y + fila)
        neg = es_chile or pierde
        P.txt(C["nom"] + 6, yc, nombre, bold=neg)
        if not es_chile:
            P.txt(C["p07"], yc, f"{int(r.rank_start)}.º", ax="center", bold=pierde)
            P.txt(C["p24"], yc, f"{int(r.rank_end)}.º", ax="center", bold=pierde)
            ganados = -int(r.places_lost)
            if pierde:
                P.txt(C["fl"], yc, f"<span style='color:{BLUE}'>↓</span> {cl(ganados, 0)}", ax="center", bold=True)
            elif ganados < 0:                       # solo en N.5e: pierde puestos pero está sobre Chile (no se destaca)
                P.txt(C["fl"], yc, f"<span style='color:{INK_MUTED}'>↓</span> {cl(ganados, 0)}", ax="center", color=INK_SECONDARY)
            elif ganados > 0:
                P.txt(C["fl"], yc, f"<span style='color:{INK_MUTED}'>↑</span> {cl(ganados, 0, True)}", ax="center", color=INK_SECONDARY)
            else:
                P.txt(C["fl"], yc, "=", ax="center", color=INK_SECONDARY)
        else:
            for k in ("p07", "fl", "p24"):
                P.txt(C[k], yc, "–", ax="center", color=INK_MUTED)
        P.txt(C["cob"], yc, f"{cl(d.cov_start, 1)} → {cl(d.cov_end, 1)}", ax="center", bold=neg)
        P.txt(C["pts"], yc, cl(d.change_pp, 1, True), ax="center", bold=neg)
        P.txt(C["pct"], yc, cl(d.change_pct, 1, True), ax="right", bold=neg)
        y += fila
    P.hline(0, P.w, y, color=INK_MUTED, width=1.5)
    if todas:
        P.txt(0, y + 24, f"<span style='color:{BLUE}'><b>↓</b></span> azul = bajo Chile y pierde puestos     <span style='color:{INK_MUTED}'>↑ ↓</span> gris = el resto     = igual", color=INK_SECONDARY)
        nota = (f"Orden: cambio de cobertura en puntos, de mayor a menor. Solo {len(menos)} territorios suben menos que Chile ({cl(ch.change_pp, 1, True)}): "
                + ", ".join(menos["name"][:-1]) + f" y {menos['name'].iloc[-1]}.")
        for k, linea in enumerate(partir_nota(nota, _fuente_pil(MIN_FONT), P.w)):
            P.txt(0, y + 60 + k * 26, linea, color=INK_PRIMARY)
        return set_meta(f, diagrama=True, tabla=True, fixed_margin=True, canvas_h=canvas_h, orden="por cambio en puntos 2007-2024, de mayor a menor (Chile como referencia arriba)",
                        perdedoras=list(perd["name"]), chile=dict(ini=float(ch.cov_start), fin=float(ch.cov_end)))
    val = rk[rk["name"] == "Valparaíso"].iloc[0]
    sube_pct, sube_pp = val.change_pct > ch.change_pct, val.change_pp > ch.change_pp
    assert sube_pct and not sube_pp, "N.5a: la nota de Valparaíso supone más en % y menos en puntos que Chile"
    nota = (f"Valparaíso sube más que Chile en % ({cl(val.change_pct, 1, True)} % frente a {cl(ch.change_pct, 1, True)} %), "
            f"pero menos en puntos ({cl(val.change_pp, 1, True)} frente a {cl(ch.change_pp, 1, True)}).")
    for k, linea in enumerate(partir_nota(nota, _fuente_pil(MIN_FONT), P.w)):
        P.txt(0, y + 60 + k * 26, linea, color=INK_PRIMARY)
    return set_meta(f, diagrama=True, tabla=True, fixed_margin=True, canvas_h=canvas_h, orden="por puesto en 2024 (Chile como referencia arriba)",
                    perdedoras=list(perd["name"]), chile=dict(ini=float(ch.cov_start), fin=float(ch.cov_end)))


def n5_cobertura_chile(ctx, spec):
    """Cobertura de Chile 2007-2024: una línea azul, extremos en naranja; con params.con_perdedoras suma las tres regiones que pierden puestos."""
    S = _seleccion()
    ch = S["chile"].iloc[0]
    tend = pd.read_csv(DP / "kpi_cobertura_tendencia.csv")
    serie = lambda tid: tend[(tend.territorio_id == tid) & tend.anio.between(2007, 2024)].sort_values("anio")  # noqa: E731
    sc = serie(0)
    con = spec.get("params", {}).get("con_perdedoras", False)
    pp, pc = cl(ch.change_pp, 1, True), cl(ch.change_pct, 1, True)
    if not con:
        _exigir(spec, f"{cl(ch.cov_start, 1)} %", f"{cl(ch.cov_end, 1)} %", pp, pc)
    f = nueva()
    f.add_vrect(x0=2019.5, x1=2021.5, fillcolor=INK_MUTED, opacity=0.09, line_width=0, layer="below")
    f.add_annotation(x=2020.5, y=1, yref="paper", yanchor="top", text="Pandemia", showarrow=False, font=dict(color=INK_SECONDARY, size=ANNOT))
    items = []
    rk = S["ranking"]
    perd = rk[rk.by_trend.astype(bool)].sort_values("cov_end", ascending=False)
    if con:
        _exigir(spec, *[cl(r.change_pp, 1, True) for _, r in perd.iterrows()], pp)
        for _, r in perd.iterrows():
            s = serie(int(r.id))
            f.add_scatter(x=s.anio, y=s.cobertura_pct, mode="lines", line=dict(color=ORANGE, width=2.5))
            items.append((2024, float(s.cobertura_pct.iloc[-1]), f"{r['name']} {cl(s.cobertura_pct.iloc[-1], 1)} %", ORANGE))
    f.add_scatter(x=sc.anio, y=sc.cobertura_pct, mode="lines", line=dict(color=BLUE, width=5))
    f.add_scatter(x=[2007, 2024], y=[sc.cobertura_pct.iloc[0], sc.cobertura_pct.iloc[-1]], mode="markers", marker=dict(color=ORANGE, size=16, line=dict(color=SURFACE, width=2)))
    lo, hi = 30, 50
    if con:
        items.append((2024, float(sc.cobertura_pct.iloc[-1]), f"<b>Chile {cl(ch.cov_end, 1)} %</b>", BLUE))
        rotulos_finales(f, items, (lo, hi), _lienzo_px(ctx, spec, 0)[1] - 130, xshift=16, lh=26)
        f.add_annotation(x=2007, y=float(sc.cobertura_pct.iloc[0]), text=f"<b>{cl(ch.cov_start, 1)} %</b>", showarrow=False, xanchor="left", yanchor="bottom", yshift=14, xshift=-6)
    else:
        f.add_annotation(x=2007, y=float(sc.cobertura_pct.iloc[0]), text=f"<b>{cl(ch.cov_start, 1)} %</b>", showarrow=False, xanchor="left", yanchor="bottom", yshift=14, xshift=-6)
        f.add_annotation(x=2024, y=float(sc.cobertura_pct.iloc[-1]), text=f"<b>{cl(ch.cov_end, 1)} %</b>", showarrow=False, xanchor="right", yanchor="bottom", yshift=14)
        f.add_annotation(x=2013, y=float(np.interp(2013, sc.anio, sc.cobertura_pct)), text=f"<b>{pp} puntos · {pc} %</b>", showarrow=False, xanchor="left",
                         yanchor="top", yshift=-22, xshift=14)
    f.update_xaxes(range=[2006.4, 2030.2 if con else 2024.6], tickvals=list(range(2007, 2025)), title="", showgrid=False, ticktext=[str(a) if a % 2 == 1 else "" for a in range(2007, 2025)])
    f.update_yaxes(range=[lo, hi], ticksuffix=" %", dtick=5, title="", gridcolor=GRIDLINE, zeroline=False)
    return set_meta(f, extra_top=26, cambio=dict(pp=float(ch.change_pp), pct=float(ch.change_pct)))


def n5_brecha_colores(ctx, spec):
    """Cotizantes que faltan para igualar a Chile, las 10 regiones bajo Chile ordenadas por brecha; color = motivo de selección."""
    S = _seleccion()
    g, sel, rk = S["gap"], S["selection"].set_index("id"), S["ranking"]
    g = g.sort_values("gap_people", ascending=False).reset_index(drop=True)
    total = float(g.gap_people.sum())
    uni = g[g.id.map(sel.selected.astype(bool))]
    s8 = float(uni.gap_people.sum())
    _exigir(spec, f"{cl(s8 / total * 100, 0)} %")
    col = {"brecha": ORANGE, "ambas": ORANGE, "tendencia": BLUE, "ninguna": GREY_BAR, "excluida": GREY_BAR}
    motivos = [sel.loc[i, "motivo"] for i in g.id]
    nombres = [f"{n} <span style='color:{BLUE}'>▼</span>" if m == "ambas" else (f"{n} (excluida)" if m == "excluida" else n) for n, m in zip(g["name"], motivos)]
    textos = [f"<b>{cl(v / 1e3, 0)} mil</b> · {cl(c * 100, 0)} %" for v, c in zip(g.gap_people, g.gap_cum_share)]
    f = nueva(bargap=0.33)
    f.add_bar(y=nombres, x=g.gap_people / 1e3, orientation="h", marker_color=[col[m] for m in motivos], text=textos, textposition="outside", cliponaxis=False,
              textfont=dict(size=MIN_FONT, color=INK_PRIMARY))
    xmax = float(g.gap_people.max() / 1e3) * 1.62
    corte = int(g.index[g.gap_cum_share >= 0.8][0])  # última fila que entra por la brecha (la que cruza el 80 %)
    f.update_yaxes(categoryorder="array", categoryarray=nombres[::-1], tickfont=dict(size=ANNOT), title="")
    f.update_xaxes(range=[0, xmax], showgrid=False, showticklabels=False, zeroline=True, zerolinecolor=INK_MUTED, title="", domain=[0.31, 1])
    f.add_shape(type="line", xref="paper", yref="y", x0=0.31, x1=1, y0=len(g) - corte - 1.5, y1=len(g) - corte - 1.5, line=dict(color=INK_PRIMARY, width=1.5, dash="dash"))
    f.add_annotation(x=1, y=len(g) - corte - 1.5, xref="paper", yref="y", xanchor="right", yanchor="bottom", yshift=4, showarrow=False,
                     text=f"corte: {cl(CORTE_BRECHA * 100, 0)} % de la brecha", font=dict(size=ANNOT, color=INK_SECONDARY))
    f.add_annotation(x=1, y=0.5, xref="paper", yref="y", xanchor="right", yanchor="middle", showarrow=False, align="right",
                     text=f"<b>{len(uni)} regiones: {cl(s8 / 1e3, 0)} mil<br>de {cl(total / 1e3, 0)} mil = {cl(s8 / total * 100, 0)} %</b>", font=dict(size=ANNOT, color=INK_PRIMARY))
    f.add_annotation(x=0, y=1.0, xref="paper", yref="paper", xanchor="left", yanchor="bottom", yshift=8, showarrow=False, align="left",
                     text=(f"{cuadro(ORANGE, 'entra por la brecha')}    {cuadro(BLUE, 'entra solo por la tendencia')}<br>"
                           f"{cuadro(GREY_BAR, 'no entra')}    <span style='color:{BLUE}'>▼</span> también pierde puestos<br>"
                           "Cada barra: miles de cotizantes que faltan · % acumulado de la brecha"), font=dict(size=ANNOT))
    f.add_annotation(x=0, y=0, xref="paper", yref="paper", xanchor="left", yanchor="top", yshift=-10, showarrow=False, align="left",
                     text=wrap("Brecha = (cobertura de Chile − cobertura de la región) × población de 15 a 64 años.", 70),
                     font=dict(size=MIN_FONT, color=INK_SECONDARY))
    return set_meta(f, extra_top=92, margen_b=84, canvas_h=_lienzo_px(ctx, spec, plot_min=570)[2], orden="por brecha, de mayor a menor", brecha_8=s8, total=total, n=len(uni))


def n5_descomposicion_ocho(ctx, spec):
    """Descomposición en tres etapas para las regiones críticas (7, sin Biobío): embudo de Chile frente a La Araucanía, barras apiladas y tres cifras."""
    S = _seleccion()
    d = S["decomposition"].sort_values("order").reset_index(drop=True)
    N = len(d)
    gente = {k: float(d[f"{k}_people"].sum()) for k in ("cotizacion", "participacion", "empleo")}
    tot = -sum(gente.values())
    pct = {k: -v / tot * 100 for k, v in gente.items()}
    entero = {k: int(round(v)) for k, v in pct.items()}   # para el titular («80 %»)
    dec1 = dict(zip(pct, _por_100(list(pct.values()))))   # para las cifras de la franja: un decimal, suman exactamente 100,0
    assert abs(sum(dec1.values()) - 100) < 1e-9, f"N.5d: las tres participaciones no suman 100: {dec1}"
    _exigir(spec, f"{entero['cotizacion']} %")
    top = d.iloc[0]                                        # la región con mayor diferencia (La Araucanía)
    mayor = d[["cotizacion_pp", "participacion_pp", "empleo_pp"]].idxmin(axis=1).str.replace("_pp", "")
    n_cot = int((mayor == "cotizacion").sum())
    otras = list(d.loc[mayor != "cotizacion", "name"])
    W, plot_h, canvas_h = _lienzo_px(ctx, spec, plot_min=640)
    f = _fig_vacia()
    P = _Px(f, W, plot_h)
    banda_inf = 236                                        # alto de la franja inferior (tres cifras + nota)
    y_cab, y_ini, y_fin = 6, 52, P.h - banda_inf - 40
    # ---- izquierda: embudo de tres etapas
    P.txt(0, y_cab + 14, "<b>Las tres etapas: cobertura = etapa 1 × etapa 2 × etapa 3</b>", size=ANNOT)
    cx = dict(c=372, r=490, d=606)
    P.txt(cx["c"], y_ini - 8, "Chile", ax="center", bold=True)
    P.txt(cx["r"], y_ini - 8, top["name"], ax="center", bold=True)
    P.txt(cx["d"], y_ini - 8, "Puntos", ax="center", bold=True)
    etapas = [("participacion", "Etapa 1 · Participación", "trabajan o buscan trabajo", GREY_DARK),
              ("empleo", "Etapa 2 · Empleo", "de ellos, con empleo", GREY_BAR),
              ("cotizacion", "Etapa 3 · Ocupados que cotizan", "de los ocupados, cotizan", ORANGE)]
    alto_f = (y_fin - y_ini - 10) / 4
    y = y_ini + 8
    for k, nombre, desc, c in etapas + [("total", "Cobertura", "= etapa 1 × etapa 2 × etapa 3", None)]:
        foco = k == "cotizacion"
        if foco:
            P.rect(0, y, 640, y + alto_f - 6, ORANGE_TINT)
        if k == "total":
            P.hline(0, 640, y - 2, color=INK_MUTED, width=1.5)
            vch, vre, dif = float(top.cov_chile), float(top.cov_region), float(top.total_pp)
        else:
            vch, vre, dif = float(top[f"{k}_level_chile"]), float(top[f"{k}_level"]), float(top[f"{k}_pp"])
        P.txt(6, y + alto_f * 0.30, cuadro(c, f"<b>{nombre}</b>") if c else f"<b>{nombre}</b>")
        P.txt(6, y + alto_f * 0.62, desc, color=INK_SECONDARY)
        P.txt(cx["c"], y + alto_f * 0.46, f"{cl(vch, 1)} %", ax="center", bold=k == "total")
        P.txt(cx["r"], y + alto_f * 0.46, f"{cl(vre, 1)} %", ax="center", bold=foco or k == "total")
        P.txt(cx["d"], y + alto_f * 0.46, cl(dif, 1, True), ax="center", bold=True)
        y += alto_f
    # ---- derecha: barras apiladas (puntos de cobertura que faltan frente a Chile)
    x0d, x1d = 700 + 215, P.w
    P.txt(700, y_cab + 14, "<b>Puntos de cobertura que faltan frente a Chile, por etapa</b>", size=ANNOT)
    P.txt(700, y_cab + 14 + 28, f"{cuadro(ORANGE, 'ocupados que cotizan')}   {cuadro(GREY_DARK, 'participación')}   {cuadro(GREY_BAR, 'empleo')}", size=MIN_FONT)
    lo_x, hi_x = -12.0, 1.4
    f.update_layout(xaxis=dict(domain=[P.x(x0d), P.x(x1d)], range=[lo_x, hi_x], visible=True, showgrid=True, gridcolor=GRIDLINE, zeroline=True, zerolinecolor=INK_MUTED,
                               tickvals=[-10, -8, -6, -4, -2, 0], ticktext=["−10", "−8", "−6", "−4", "−2", "0"], title="", tickfont=dict(size=TICK)),
                    yaxis=dict(domain=[P.y(y_fin), P.y(y_ini + 40)], visible=True, autorange="reversed", tickfont=dict(size=ANNOT)), barmode="relative", bargap=0.33)
    nombres = list(d["name"])
    for k, c, tc in (("cotizacion", ORANGE, INK_PRIMARY), ("participacion", GREY_DARK, SURFACE), ("empleo", GREY_BAR, INK_PRIMARY)):
        v = d[f"{k}_pp"]
        f.add_bar(y=nombres, x=v, orientation="h", marker=dict(color=c, line=dict(color=SURFACE, width=1.5)), text=[cl(x, 1) if abs(x) >= 1.9 else "" for x in v],
                  textposition="inside", insidetextanchor="middle", textfont=dict(size=ANNOT, color=tc), cliponaxis=False)
    for nombre, (_, r) in zip(nombres, d.iterrows()):
        izq = sum(min(r[f"{k}_pp"], 0) for k in ("cotizacion", "participacion", "empleo"))
        f.add_annotation(x=izq - 0.15, y=nombre, xref="x", yref="y", xanchor="right", yanchor="middle", showarrow=False, text=f"<b>{cl(r.total_pp, 1)}</b>", font=dict(size=ANNOT))
    # ---- franja inferior: tres cifras
    yb = P.h - banda_inf + 4
    P.hline(0, P.w, yb - 8, color=INK_MUTED, width=1.5)
    P.txt(0, yb + 16, f"<b>De los {cl(tot / 1e3, 0)} mil cotizantes que faltan en las {N} regiones, por etapa:</b>", size=ANNOT)
    tiles = [("cotizacion", "ocupados sin cotizar (etapa 3)", ORANGE_TINT), ("participacion", "fuera de la fuerza de trabajo (etapa 1)", "#eceae4"),
             ("empleo", "desocupados (etapa 2)", "#eceae4")]
    ancho_t = (P.w - 2 * 18) / 3
    for i, (k, desc, fondo) in enumerate(tiles):
        xa = i * (ancho_t + 18)
        P.rect(xa, yb + 40, xa + ancho_t, yb + 40 + 116, fondo)
        P.txt(xa + 16, yb + 40 + 38, f"{cl(dec1[k], 1)} %", size=46, bold=True)
        P.txt(xa + 205, yb + 40 + 28, f"<b>{cl(-gente[k] / 1e3, 0)} mil</b> personas", size=ANNOT)
        P.txt(xa + 205, yb + 40 + 62, wrap(desc, 26), size=MIN_FONT, color=INK_SECONDARY, ay="top", align="left")
    if not otras:
        final = f"En las {N} regiones la etapa 3 es la mayor."
    else:
        final = f"En {n_cot} de {N} regiones la etapa 3 es la mayor" + (f"; en {otras[0]} lidera la participación." if len(otras) == 1 else f"; en {', '.join(otras)} lidera otra etapa.")
    P.txt(0, yb + 40 + 116 + 24, final, color=INK_PRIMARY)
    return set_meta(f, diagrama=True, fixed_margin=True, canvas_h=canvas_h, orden="por diferencia total con Chile", sumas=[float(sum(dec1.values()))],
                    etapa3_mayor=n_cot, pct=dec1, pct_entero=entero, personas={k: round(-v) for k, v in gente.items()}, total=round(-tot))


def n6_ingreso_administradora(ctx, spec):
    a = pd.read_csv(DP / "afiliados_por_region_edad.csv")
    a = a[(a.fecha.str[5:7] == "12") & (a.region_label.str.upper() == "TOTAL")].groupby("anio").afiliados.sum()
    c = pd.read_csv(DP / "cotizantes_por_region.csv")
    c = c[c.region_label == "Total"].set_index("anio").cotizantes
    anios = [y for y in range(2010, 2026) if y in a.index and y in c.index]
    af, co = a.loc[anios] / 1e6, c.loc[anios] / 1e6
    no = af - co
    s = pd.read_csv(DP / "afp_resultados_sistema.csv").set_index("anio")
    g = float(s.loc[2025, "gastos_mm"]) * 1e6
    costo_cot, costo_af = g / c.loc[2025], g / a.loc[2025]
    f = nueva(barmode="stack", bargap=0.33)
    f.add_bar(x=anios, y=co, marker_color=BLUE, marker_line=dict(color=SURFACE, width=1.5))
    f.add_bar(x=anios, y=no, marker_color=ORANGE, marker_line=dict(color=SURFACE, width=1.5))
    f.add_annotation(x=2025, y=co.loc[2025] / 2, text=cuadro(BLUE, f"<b>Cotizan: {cl(co.loc[2025], 2)} millones</b>"), showarrow=False, xanchor="left", xshift=30, align="left")
    f.add_annotation(x=2025, y=co.loc[2025] + no.loc[2025] / 2, text=cuadro(ORANGE, f"<b>No cotizan: {cl(no.loc[2025], 2)} millones</b>"),
                     showarrow=False, xanchor="left", xshift=30, align="left")
    f.add_annotation(x=2010, y=18.3, xanchor="left", yanchor="top", showarrow=False, align="left", font=dict(size=ANNOT),
                     text=f"Costo de administración 2025, por persona y año:<br><b>${cl(costo_cot, 0)} por cotizante</b> · ${cl(costo_af, 0)} por afiliado")
    f.update_layout(xaxis=dict(domain=[0.40, 0.79], dtick=5, tick0=2010, range=[2008.2, 2025.6], title="", tickangle=0),
                    yaxis=dict(range=[0, 18.5], title="Millones de personas", gridcolor=GRIDLINE, zeroline=False))
    # árbol del ingreso
    f.add_annotation(x=0.0, y=0.93, xref="paper", yref="paper", xanchor="left", yanchor="top", showarrow=False, align="left",
                     text="<b>Ingreso de la administradora</b><br>= cotizantes activos<br>× sueldo imponible<br>× % de comisión",
                     font=dict(size=ANNOT + 2), bgcolor="#f1f0eb", borderpad=12)
    f.add_annotation(x=0.0, y=0.42, xref="paper", yref="paper", xanchor="left", yanchor="top", showarrow=False, align="left",
                     text=f"<span style='color:{BLUE}'>■</span> <b>↓ cotizantes activos</b><br>→ menos comisión",
                     font=dict(size=ANNOT), bordercolor=BLUE, borderwidth=2, borderpad=10)
    f.add_annotation(x=0.0, y=0.17, xref="paper", yref="paper", xanchor="left", yanchor="top", showarrow=False, align="left",
                     text=f"<span style='color:{ORANGE}'>■</span> <b>↑ afiliados que no cotizan</b><br>→ sube el costo por cotizante",
                     font=dict(size=ANNOT), bordercolor=ORANGE, borderwidth=2, borderpad=10)
    f.add_annotation(x=0.12, y=0.43, xref="paper", yref="paper", ax=0, ay=-58, showarrow=True, arrowhead=2, arrowwidth=2, arrowcolor=INK_SECONDARY, text="")
    return set_meta(f, costo_cot=round(costo_cot), costo_af=round(costo_af), co_2025=float(co.loc[2025]), af_2025=float(af.loc[2025]),
                    razon={y: round(float(af.loc[y] / co.loc[y]), 3) for y in (anios[0], anios[-1])})


def n7_palancas(ctx, spec):
    p = pd.read_csv(DP / "kpi_cobertura_palancas.csv")
    dest = spec.get("params", {}).get("destacar")
    grupos = [("Suma personas", "Suman personas a la cobertura"), ("Protege lo que ya hay", "Protegen lo que ya hay")]
    f = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.14, row_heights=[4, 2], subplot_titles=[g[1] for g in grupos])
    for r, (g, _) in enumerate(grupos, start=1):
        d = p[p.efecto == g].sort_values("personas", ascending=True)
        if dest:
            col = [ORANGE if x == dest else GREY_BAR for x in d.palanca]
        else:
            col = [ORANGE if a == "Directo" else BLUE for a in d.alcance_afp]
        txt = []
        for _, row in d.iterrows():
            t = f"<b>{cl(row.personas / 1e6, 2)} millones</b> · {row.actor.split(';')[0]}"
            if dest and row.palanca == dest:
                t += f"<br>alcance de la administradora: <b>{row.alcance_afp.lower()}</b>"
            txt.append(t)
        f.add_bar(y=[wrap(x, 30) for x in d.palanca], x=d.personas / 1e6, orientation="h", marker_color=col, text=txt, textposition="outside",
                  cliponaxis=False, textfont=dict(size=MIN_FONT, color=INK_PRIMARY), row=r, col=1)
    f.update_xaxes(range=[0, 11.5], gridcolor=GRIDLINE, zeroline=False)
    f.update_xaxes(title="Millones de personas", row=2, col=1)
    f.update_yaxes(tickfont=dict(size=MIN_FONT))
    for an in f.layout.annotations:
        an.font = dict(size=ANNOT, color=INK_PRIMARY)
        an.text = f"<b>{an.text}</b>"
        an.x, an.xanchor = 0, "left"
    if not dest:
        f.add_annotation(x=1, y=1.0, xref="paper", yref="paper", xanchor="right", yanchor="bottom", yshift=4, showarrow=False,
                         text=f"{cuadro(ORANGE, 'directo: la administradora')}    {cuadro(BLUE, 'indirecto o sin alcance: Estado, empleadores')}")
    f.update_layout(showlegend=False, plot_bgcolor=SURFACE, paper_bgcolor=SURFACE, separators=",.", bargap=0.33)
    n_dir = int((p.alcance_afp == "Directo").sum())
    return set_meta(f, extra_top=30, directas=n_dir, total=len(p))


def n8_escenarios(ctx, spec):
    p, _ = _paneles_escenarios(ctx)
    xc, yc = p["x"]["costo"]
    for e in ("x4", "x5", "x6"):
        assert np.allclose(p[e]["costo"][1], yc), "el costo no es el mismo en todos los paneles"
    colores = {"x4": "#9ec5f4", "x": "#5598e7", "x5": "#1f62b8", "x6": "#0d366b"}
    f = nueva()
    hasta = 2065
    m = xc <= hasta
    f.add_vrect(x0=2025.5, x1=hasta, fillcolor=INK_MUTED, opacity=0.06, line_width=0, layer="below")
    f.add_annotation(x=2045, y=1, yref="paper", yanchor="top", showarrow=False, text="Escenario, no es un pronóstico", font=dict(color=INK_SECONDARY))
    items, cruces = [], {}
    ymax = 0
    for e in ("x4", "x", "x5", "x6"):
        xk, yk = p[e]["cap"]
        mk = xk <= hasta
        f.add_scatter(x=xk[mk], y=yk[mk], mode="lines", line=dict(color=colores[e], width=4 if e in ("x5", "x6") else 3.5))
        items.append((float(xk[mk][-1]), float(yk[mk][-1]), ESC_EJE[e], colores[e]))
        cr = cruce(xc, yc, np.interp(xc, xk, yk))
        cruces[ESC_EJE[e]] = (cr, p[e]["anio"])
        ymax = max(ymax, yk[mk].max())
    f.add_scatter(x=xc[m], y=yc[m], mode="lines", line=dict(color=RED, width=4))
    items.append((float(xc[m][-1]), float(yc[m][-1]), "<b>Costo del Pilar Solidario</b>", RED))
    ymax = max(ymax, yc[m].max()) * 1.18
    for k, (nombre, ((x_, y_), anio)) in enumerate(sorted(cruces.items(), key=lambda kv: kv[1][1])):
        f.add_shape(type="line", x0=x_, x1=x_, y0=0, y1=y_, line=dict(color=INK_MUTED, width=1.2))
        f.add_scatter(x=[x_], y=[y_], mode="markers", marker=dict(color=ORANGE, size=15, line=dict(color=SURFACE, width=2)))
        f.add_annotation(x=x_, y=0, yanchor="bottom", yshift=6 + (34 if k == 1 else 0), text=f"<b>{anio}</b>", showarrow=False,
                         bgcolor=SURFACE, font=dict(size=ANNOT))
    rotulos_finales(f, items, (0, ymax), 470)
    f.update_xaxes(range=[2022, 2083], tickvals=[2025, 2035, 2045, 2055, 2065], title="", showgrid=False)
    f.update_yaxes(range=[0, ymax], title="Billones de pesos de 2025", gridcolor=GRIDLINE, zeroline=False)
    return set_meta(f, cruces={k: v[1] for k, v in cruces.items()}, cruces_calc={k: round(v[0][0], 2) for k, v in cruces.items()},
                    g8_justificada="4 líneas de capacidad + 1 de costo (especificación N.8), todas rotuladas directamente")


def n9_participacion(ctx, spec):
    reg = pd.read_csv(DP / "kpi_cobertura_regiones.csv")
    nac = float(reg.loc[reg.region_id == 0, "participacion_ene"].iloc[0])
    d = criticas(reg).assign(dif=lambda x: x.participacion_ene - nac).sort_values("dif", ascending=False)
    f = nueva(bargap=0.33)
    f.add_bar(y=d.region_nombre, x=d.dif, orientation="h", marker_color=[ORANGE if v < 0 else GREY_BAR for v in d.dif],
              text=[f"<b>{cl(v, 1, True)}</b> ({cl(p_, 1)} %)" for v, p_ in zip(d.dif, d.participacion_ene)], textposition="outside", cliponaxis=False,
              textfont=dict(size=ANNOT, color=INK_PRIMARY))
    f.update_xaxes(range=[-7.5, 4.5], title=f"Puntos frente a Chile (Chile = {cl(nac, 1)} %)", zeroline=True, zerolinecolor=INK_PRIMARY,
                   zerolinewidth=1.5, gridcolor=GRIDLINE)
    f.update_yaxes(tickfont=dict(size=ANNOT))
    bajo = d[d.dif < 0]
    return set_meta(f, n_bajo=len(bajo), chile=nac, peores={r: round(v, 2) for r, v in zip(d.region_nombre, d.dif)}, orden="peor arriba")


def bloqueada(ctx, spec):
    f = nueva()
    f.add_shape(type="rect", xref="paper", yref="paper", x0=0.01, x1=0.99, y0=0.03, y1=0.97, line=dict(color=INK_MUTED, width=2, dash="dash"),
                fillcolor="#f1f0eb")
    f.add_annotation(x=0.5, y=0.6, xref="paper", yref="paper", showarrow=False, text="<b>Figura pendiente: faltan datos</b>", font=dict(size=34, color=INK_SECONDARY))
    f.add_annotation(x=0.5, y=0.38, xref="paper", yref="paper", showarrow=False, text=wrap(spec["source"], 80), font=dict(size=ANNOT, color=INK_SECONDARY))
    f.update_xaxes(visible=False)
    f.update_yaxes(visible=False)
    return set_meta(f, diagrama=True, bloqueada=True)


TRANSFORMS = {k[2:] if k.startswith("t_") else k: v for k, v in globals().items() if callable(v) and (k.startswith("t_") or k.startswith("n") and k[1:2].isdigit() or k == "bloqueada")}


# ------------------------------------------------------------------------------------------------ 4. estilo de diapositiva
def chars_por_linea(px_ancho: float, tam: int, factor: float = 0.52) -> int:
    return max(20, int(px_ancho / (tam * factor)))


MSG_LH, SUB_LH = round(MSG * 1.25), round(TICK * 1.32)


def bloque_titulo(canvas_w: int, variante: str, mensaje: str, subtitulo: str) -> tuple:
    """Líneas del título (mensaje en negrita + subtítulo, o solo el subtítulo) partidas con la métrica real de la letra, y su alto en px.
    El título se imprime con Pillow sobre la imagen (Plotly recorta la primera línea de los títulos de varias líneas)."""
    ancho = canvas_w - 2 * PAD
    # __slide: sin ningún título (ni el mensaje en negrita ni el subtítulo gris); __standalone: los dos.
    msg = partir_nota(mensaje, _fuente_pil(MSG, True), ancho) if (variante == "standalone" and mensaje) else []
    sub = partir_nota(subtitulo, _fuente_pil(TICK), ancho) if (variante == "standalone" and subtitulo) else []
    alto = (14 + MSG_LH * len(msg) + (8 if msg and sub else 0) + SUB_LH * len(sub) + 12) if (msg or sub) else 0
    return {"msg": msg, "sub": sub}, alto, len(sub)


def apply_slide_style(fig: go.Figure, canvas: tuple, variant: str, message: str, subtitle: str, source: str, fig_num: str) -> go.Figure:
    """Lienzo, letra, márgenes y fondo; guarda en meta las líneas del título (se imprimen al exportar, arriba) y el alto del gráfico.
    La nota de fuente también se imprime al exportar (franja inferior)."""
    W, H = canvas
    m = meta(fig)
    titulo, alto_t, _ = bloque_titulo(W, variant, message, subtitle)
    alto_plot = H - (0 if m.get("sin_nota") else NOTE_BAND) - alto_t
    top = 10 + m.get("extra_top", 0)
    fig.update_layout(width=W, height=alto_plot, showlegend=False, hovermode=False, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, separators=",.",
                      font=dict(family=FONT_FAMILY, size=BASE, color=INK_PRIMARY), title=dict(text=""))
    if m.get("mapa"):
        fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
    elif m.get("fixed_margin"):
        fig.update_layout(margin=dict(t=8, b=8, l=PAD, r=PAD))
    else:
        mg = fig.layout.margin
        fig.update_layout(margin=dict(t=top, l=PAD, r=max(PAD, mg.r or 0), b=mg.b if (m.get("tabla") and mg.b is not None) else m.get("margen_b", PAD),
                                      autoexpand=True))
    set_meta(fig, _titulo=titulo, _alto_titulo=alto_t)
    enforce_fonts(fig)
    return fig


def enforce_fonts(fig: go.Figure) -> None:
    """Letra mínima de 20 px en todo (ticks 22, títulos de eje 22, anotaciones 22) y rótulos horizontales."""
    for k in fig.layout:
        if k.startswith(("xaxis", "yaxis")):
            ax = fig.layout[k]
            if ax.visible is False:
                continue
            ts = ax.tickfont.size
            ax.tickfont.size = max(ts, MIN_FONT) if ts else TICK
            ax.title.font.size = max(ax.title.font.size or TICK, MIN_FONT)
            ax.automargin = True
            ax.tickfont.color = ax.tickfont.color or INK_PRIMARY
            if k.startswith("xaxis") and ax.tickangle is None:
                ax.tickangle = 0
    for an in fig.layout.annotations:
        an.font.size = max(an.font.size, MIN_FONT) if an.font.size else ANNOT
        an.font.color = an.font.color or INK_PRIMARY
        if an.xanchor in (None, "auto") and not an.showarrow:  # «auto» cambia el anclaje según la posición: centrar siempre
            an.xanchor = "center"
        if an.yanchor in (None, "auto") and not an.showarrow:
            an.yanchor = "middle"
        if an.text and "$" in an.text:  # Plotly lee $…$ como fórmula
            an.text = an.text.replace("$", "&#36;")
    horizontales = any(t.type == "bar" and t.orientation == "h" for t in fig.data)
    dispersion = any(t.type == "scatter" and t.mode == "markers" and t.x is not None and len(t.x) >= 5 for t in fig.data)
    if not horizontales and not dispersion:
        fig.update_xaxes(showgrid=False)
    for tr in fig.data:
        if tr.type == "table":
            continue
        if hasattr(tr, "textfont") and tr.textfont is not None:
            tr.textfont.size = max(tr.textfont.size, MIN_FONT) if tr.textfont.size else ANNOT
        if hasattr(tr, "showlegend"):
            tr.showlegend = False
        if tr.type == "scatter" and tr.text is not None and not isinstance(tr.text, str):
            tr.text = [t.replace("$", "&#36;") if isinstance(t, str) else t for t in tr.text]
        if getattr(tr, "colorbar", None) is not None and tr.type.startswith("choropleth"):
            tr.colorbar.tickfont.size = max(tr.colorbar.tickfont.size or MIN_FONT, MIN_FONT)
    if fig.layout.coloraxis and fig.layout.coloraxis.colorbar:
        fig.layout.coloraxis.colorbar.tickfont.size = TICK


_fuente_pil, partir_nota = pie_fuente.fuente_pil, pie_fuente.partir_nota


def exportar(fig: go.Figure, ruta: Path, canvas: tuple, source: str, fig_num: str, cfg: dict, con_nota: bool = True) -> dict:
    """PNG del gráfico + franja con la nota de fuente (gris, abajo a la izquierda; Scripts/pie_fuente.py). El número de la figura NO se imprime en la
    imagen (pie_fuente.NUMERO_EN_IMAGEN = False): solo va en el nombre del archivo (y en manifest.csv)."""
    W, H = canvas
    escala = max(cfg["escala"], math.ceil(cfg["ancho_min_px"] / W))
    m = meta(fig)
    alto_t, titulo = m.get("_alto_titulo", 0), m.get("_titulo", {"msg": [], "sub": []})
    alto_plot = H - (NOTE_BAND if con_nota else 0) - alto_t
    png = fig.to_image(format="png", width=W, height=alto_plot, scale=escala)
    img = Image.open(io.BytesIO(png)).convert("RGB")
    out = Image.new("RGB", (W * escala, H * escala), SURFACE)
    out.paste(img, (0, alto_t * escala))
    d = ImageDraw.Draw(out)
    y = 14 * escala
    for linea in titulo["msg"]:
        d.text((PAD * escala, y), linea, fill=INK_PRIMARY, font=_fuente_pil(MSG * escala, True))
        y += MSG_LH * escala
    if titulo["msg"] and titulo["sub"]:
        y += 8 * escala
    for linea in titulo["sub"]:
        d.text((PAD * escala, y), linea, fill=INK_SECONDARY, font=_fuente_pil(TICK * escala))
        y += SUB_LH * escala
    n_lineas = 0
    if con_nota:  # pie de fuente común (Scripts/pie_fuente.py): mismo código que usan las pirámides de Scripts/05 y 11
        n_lineas = pie_fuente.add_source_footer(out, source, css_width=W, y_top=(alto_t + alto_plot) * escala, fig_num=fig_num)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    out.save(ruta, dpi=(380, 380), optimize=True)
    return dict(width_px=out.width, height_px=out.height, note_lines=n_lineas)


# ------------------------------------------------------------------------------------------------ 5. control automático (pautas de la clase)
def _hex(c):
    if not isinstance(c, str):
        return None
    c = c.strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", c):
        return c.lower()
    m = re.fullmatch(r"rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)", c)
    if m and (m.group(4) is None or float(m.group(4)) >= 0.5):
        return "#%02x%02x%02x" % tuple(int(m.group(i)) for i in (1, 2, 3))
    return None


def _lin(c):
    v = np.array([int(c[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def _oklab(lin):
    M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
    M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])
    return M2 @ np.cbrt(M1 @ np.clip(lin, 0, 1))


CVD = {"deutan": np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]]),
       "protan": np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]])}


def colores_de_marcas(fig: go.Figure) -> list:
    cols = []
    for tr in fig.data:
        if tr.type == "table":
            continue
        mk = getattr(tr, "marker", None)
        if mk is not None and getattr(mk, "color", None) is not None:
            c = mk.color
            cols += [c] if isinstance(c, str) else [x for x in c if isinstance(x, str)]
        mln = getattr(mk, "line", None) if mk is not None else None
        if mln is not None and isinstance(getattr(mln, "color", None), str) and (getattr(mln, "width", 0) or 0) >= 2:
            cols.append(mln.color)
        ln = getattr(tr, "line", None)
        if ln is not None and getattr(ln, "color", None) and (tr.type != "scatter" or "lines" in (tr.mode or "")):
            if not (tr.type == "scatter" and (ln.width or 2) <= 0):
                cols.append(ln.color)
    hx = {h for h in map(_hex, cols) if h}
    return sorted(hx)


def cvd_min(colores: list) -> tuple:
    """Menor diferencia entre pares de colores con color (no grises) bajo deuteranopía y protanopía, en ΔE OKLab × 100."""
    sat = [c for c in colores if np.hypot(*_oklab(_lin(c))[1:]) > 0.04]
    peor = (999.0, None)
    for i in range(len(sat)):
        for j in range(i + 1, len(sat)):
            for nombre, M in CVD.items():
                a, b = _oklab(M @ _lin(sat[i])), _oklab(M @ _lin(sat[j]))
                de = float(np.linalg.norm(a - b) * 100)
                if de < peor[0]:
                    peor = (de, f"{sat[i]}↔{sat[j]} ({nombre})")
    return peor


def fuentes_de(fig: go.Figure) -> list:
    tam = []
    for k in fig.layout:
        if k.startswith(("xaxis", "yaxis")) and fig.layout[k].visible is not False and fig.layout[k].showticklabels is not False:
            tam.append(fig.layout[k].tickfont.size)
    tam += [an.font.size for an in fig.layout.annotations]
    for tr in fig.data:
        if tr.type == "table":
            tam += [tr.header.font.size, tr.cells.font.size]
        elif hasattr(tr, "textfont") and tr.textfont is not None and tr.text is not None:
            tam.append(tr.textfont.size)
    return [t for t in tam if t is not None]


def _n(v) -> int:
    return 0 if v is None else len(v)


def lint(fig: go.Figure, spec: dict, mensaje: str, subtitulo: str, fuente: str, info: dict) -> dict:
    """Pautas G3-G21 que se pueden revisar con el código. Valor: ('ok' | 'falla' | 'n.a.' | 'justificada', detalle)."""
    m = meta(fig)
    R = {}
    es_tabla = m.get("tabla")
    es_diag = m.get("diagrama")
    bloq = m.get("bloqueada")
    # G3: mensaje ≤ 25 palabras y sin siglas en mensaje y subtítulo
    palabras = [p for p in mensaje.split() if re.search(r"\w", p)]
    siglas = sorted(set(SIGLAS_RE.findall(mensaje + " " + subtitulo)))
    if bloq:
        R["G3"] = ("n.a.", "bloqueada")
    else:
        R["G3"] = ("ok" if len(palabras) <= 25 and not siglas else "falla", f"{len(palabras)} palabras" + (f"; siglas: {', '.join(siglas)}" if siglas else ""))
    R["G4"] = ("ok" if subtitulo and fuente else "falla", "subtítulo y nota presentes" if subtitulo and fuente else "falta subtítulo o nota")
    cols = colores_de_marcas(fig)
    hay_acento = any(c in (ORANGE.lower(), RED.lower()) for c in cols) or any(
        ORANGE_TINT in str(getattr(tr.cells, "fill", {}).color) for tr in fig.data if tr.type == "table") or es_diag
    R["G5"] = ("n.a." if bloq else ("ok" if hay_acento else "falla"), "acento naranja/rojo presente" if hay_acento else "sin color de acento")
    # G7 barras
    barras = [t for t in fig.data if t.type == "bar"]
    if barras and not es_diag:
        prob = []
        gap = fig.layout.bargap
        n_cat = max(len(t.x if t.orientation != "h" else t.y) for t in barras)
        if n_cat > 1 and fig.layout.barmode != "stack" and (gap is None or gap < 0.25) and not m.get("piramide"):
            if not (spec["transform"] in ("piramide", "alemania")):
                prob.append(f"bargap {gap}")
        for t in barras:  # eje de valores: y en columnas, x en barras horizontales
            ax = (t.xaxis or "x") if t.orientation == "h" else (t.yaxis or "y")
            k = ax.replace("x", "xaxis").replace("y", "yaxis")
            rg = fig.layout[k].range if k in fig.layout else None
            if rg is not None and isinstance(rg[0], (int, float)) and rg[0] > 0:
                prob.append(f"{k} (valores) empieza en {rg[0]}")
        for k in fig.layout:
            if k.startswith("xaxis") and fig.layout[k].tickangle not in (None, 0):
                prob.append("rótulos inclinados")
        R["G7"] = ("ok" if not prob else "falla", "; ".join(prob) or "eje desde 0, separación y rótulos horizontales")
    else:
        R["G7"] = ("n.a.", "")
    # G8 / G15 líneas
    lineas = [t for t in fig.data if t.type == "scatter" and t.mode and "lines" in t.mode and t.fill not in ("toself", "tonexty")
              and not (t.line.width is not None and t.line.width <= 1.6) and _n(t.x) > 2]
    if lineas:
        dash = [t for t in lineas if t.line.dash not in (None, "solid")]
        por_panel = {}
        for t in lineas:
            por_panel[(t.xaxis or "x", t.yaxis or "y")] = por_panel.get((t.xaxis or "x", t.yaxis or "y"), 0) + 1
        series = {}  # líneas distintas por panel (cada color es una serie; el tramo de escenario en tono claro cuenta aparte, por eso se es estricto)
        for t in lineas:
            series.setdefault((t.xaxis or "x"), set()).add(_hex(t.line.color))
        max_l = max(len(v) for v in series.values())
        ceros = []
        for k in fig.layout:
            if k.startswith("yaxis") and fig.layout[k].range is not None:
                lo = fig.layout[k].range[0]
                if lo is not None and lo > 0:
                    ceros.append(k)
        prob = []
        if dash:
            prob.append(f"{len(dash)} líneas de datos punteadas")
        if ceros and "no parte de 0" not in fuente:
            prob.append("eje y no parte de 0")
        just = m.get("g8_justificada")
        if max_l > 4:
            R["G8"] = ("justificada" if just and not prob else "falla", (just or f"{max_l} series en un panel") + ("; " + "; ".join(prob) if prob else ""))
        else:
            R["G8"] = ("ok" if not prob else "falla", "; ".join(prob) or f"líneas continuas, máx. {max_l} series por panel, eje desde 0")
        R["G15"] = ("ok" if max_l <= 4 else ("justificada" if just else "falla"), f"{len(series)} panel(es)")
    else:
        R["G8"] = R["G15"] = ("n.a.", "")
    # G9 doble eje
    dobles = [k for k in fig.layout if k.startswith("yaxis") and fig.layout[k].overlaying]
    R["G9"] = ("ok" if not dobles else "falla", "sin doble eje" if not dobles else str(dobles))
    # G10 dispersión
    disp = [t for t in fig.data if t.type == "scatter" and t.mode == "markers" and _n(t.x) >= 5]
    if disp:
        lo = fig.layout.yaxis.range[0] if fig.layout.yaxis.range else 0
        R["G10"] = ("ok" if (lo is not None and lo <= 0) or "no parte de 0" in fuente else "falla", f"eje y desde {lo}")
    else:
        R["G10"] = ("n.a.", "")
    # G11 burbujas por área
    burb = [t for t in fig.data if t.type == "scatter" and t.marker is not None and t.marker.size is not None and not isinstance(t.marker.size, (int, float))]
    R["G11"] = ("n.a.", "") if not burb else (("ok", "tamaño por área") if all(t.marker.sizemode == "area" for t in burb) else ("falla", "tamaño por diámetro"))
    R["G12"] = ("falla", "torta") if any(t.type == "pie" for t in fig.data) else ("ok" if not bloq else "n.a.", "sin tortas")
    sumas = m.get("sumas")
    R["G13"] = ("n.a.", "") if not sumas else (("ok", "partes suman 100 %: " + ", ".join(cl(s, 2) for s in sumas))
                                               if all(abs(s - 100) < 0.05 for s in sumas) else ("falla", f"sumas {sumas}"))
    R["G14"] = ("n.a.", "") if not m.get("cascada") else (("ok", f"pasos rotulados; {cl(m['inicio'], 2)} + {cl(m['suma'], 2)} = {cl(m['fin'], 2)}")
                                                         if abs(m["inicio"] + m["suma"] - m["fin"]) < 0.01 else ("falla", "la cascada no cierra"))
    # G16 orden
    if m.get("orden"):
        R["G16"] = ("ok", m["orden"])
    elif barras and any(t.orientation == "h" and _n(t.y) >= 5 for t in barras):
        t = next(t for t in barras if t.orientation == "h" and len(t.y) >= 5)
        x = arr(t.x).astype(float)
        R["G16"] = ("ok" if (np.all(np.diff(x) >= -1e-9) or np.all(np.diff(x) <= 1e-9)) else "falla", "barras ordenadas por valor")
    else:
        R["G16"] = ("n.a.", "")
    # G17 daltonismo
    de, par = cvd_min(cols)
    rojo_verde = any(c in cols for c in ("#008300",)) and RED.lower() in cols
    if de >= 8 and not rojo_verde:
        R["G17"] = ("ok", f"ΔE mínimo {de:.1f}" if de < 999 else "un solo color con tono")
    elif de >= 4 and not rojo_verde:
        R["G17"] = ("ok", f"ΔE mínimo {de:.1f} ({par}): mismo tono en claro/oscuro, con rótulo directo")
    else:
        R["G17"] = ("falla", f"ΔE {de:.1f} {par}" + ("; rojo y verde juntos" if rojo_verde else ""))
    leyenda = fig.layout.showlegend is not False and any(t.showlegend for t in fig.data if hasattr(t, "showlegend"))
    R["G18"] = ("ok" if not leyenda else "falla", "sin leyenda; rótulos directos" if not leyenda else "hay leyenda")
    nat = spec.get("nature")
    req = {"escenario": "no es un pronóstico", "juicio": "juicio del equipo"}.get(nat)
    falta = []
    if req and req not in fuente.lower():
        falta.append(req)
    if m.get("mapa") and "OpenStreetMap" not in fuente:
        falta.append("atribución del mapa")
    R["G21"] = ("ok" if not falta else "falla", "advertencia en la nota" + (": falta " + ", ".join(falta) if falta else f" ({nat})"))
    chicas = [t for t in fuentes_de(fig) if t < MIN_FONT]
    R["LETRA"] = ("ok" if not chicas else "falla", f"mínimo {min(fuentes_de(fig) or [MIN_FONT])} px" + (f"; {len(chicas)} textos < 20 px" if chicas else ""))
    R["NOTA"] = ("ok" if 0 < info.get("note_lines", 0) <= 2 or spec["canvas"] in SIN_NOTA else "falla", f"{info.get('note_lines')} líneas")
    R["RES"] = ("ok" if info.get("width_px", 0) >= 4680 else "falla", f"{info.get('width_px')}×{info.get('height_px')} px")
    return R


REGLAS_AUTO = ["G3", "G4", "G5", "G7", "G8", "G9", "G10", "G11", "G12", "G13", "G14", "G15", "G16", "G17", "G18", "G21", "LETRA", "NOTA", "RES"]


# ------------------------------------------------------------------------------------------------ 6. orquestación
def numero_de(spec: dict) -> str:
    if not spec.get("key"):
        return spec["id"]
    clave = spec["key"] + (f":{spec['letter']}" if spec.get("letter") else "")
    return numeracion.numero(clave, extendida=spec["version"] == "extendida")


def expandir(figuras: list) -> list:
    out = []
    for s in figuras:
        if s.get("letters"):
            for le in s["letters"]:
                out.append({**s, "letter": le, "slug": f"{s['slug']}_{le}", "id": f"{s['id']}{le}"})
        else:
            out.append(dict(s))
    return out


def textos(spec: dict, ctx: dict) -> tuple:
    msg, sub = spec["message"], spec["subtitle"]
    if spec.get("region"):
        sub = sub.replace("{region}", spec["region"])
    elif spec.get("letter"):
        t = ctx["cap"][f"{spec['key']}:{spec['letter']}"]["fig"]["layout"]["title"]["text"]
        principal = re.sub(r"<sup>.*", "", t).replace("<br>", " ").strip()
        msg = msg.replace("{titulo_dashboard}", principal.rstrip(".") + ".")
        region = re.search(r"En (.+?) cotizan", principal).group(1)
        sub = sub.replace("{region}", region)
    return msg, sub


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--solo", nargs="*", help="ids de figura a exportar (por defecto, todas)")
    ap.add_argument("--cache", help="pickle con la captura del dashboard (se crea si no existe)")
    args = ap.parse_args()
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    out = ROOT / cfg["salida"]
    out.mkdir(parents=True, exist_ok=True)
    try:  # Chrome persistente para kaleido (más rápido); si no está disponible, se exporta igual
        import kaleido
        kaleido.start_sync_server(silence_warnings=True)
    except Exception:
        pass
    if args.cache and Path(args.cache).exists():
        cap = pickle.load(open(args.cache, "rb"))
    else:
        print("Capturando el dashboard (AppTest, sin servidor)…", flush=True)
        cap = capturar()
        if args.cache:
            pickle.dump(cap, open(args.cache, "wb"))
    ctx = {"cap": cap, "cfg": cfg, "conteos": conteos()}
    carpetas = {d["id"]: d["carpeta"] for d in cfg["diapositivas"]}
    filas, discrepancias = [], []
    specs = expandir(cfg["figuras"])
    for spec in specs:
        if args.solo and spec["id"] not in args.solo and spec["id"].rstrip("abcdefgh") not in args.solo:
            continue
        num = numero_de(spec)
        if spec.get("key"):
            esperado = spec["id"]
            if num != esperado:
                discrepancias.append(f"Número: {spec['key']} da {num} en ORDEN (components/numeracion.py), el mapa decía {esperado}.")
        canvas = tuple(cfg["lienzos"][spec["canvas"]])
        msg, sub = textos(spec, ctx)
        archivos, info, figs = {}, {}, {}
        for variante in ("slide", "standalone"):
            _, alto, _ = bloque_titulo(canvas[0], variante, msg, sub)
            ctx["top_px"] = alto
            fig = TRANSFORMS[spec["transform"]](ctx, spec)
            cv = (canvas[0], max(canvas[1], int(meta(fig).get("canvas_h", 0))))  # tablas: la variante con título largo puede ser más alta que el lienzo
            apply_slide_style(fig, cv, variante, msg, sub, spec["source"], num)
            ruta = out / carpetas[spec["slide"]] / f"{num}__{spec['slug']}__{variante}.png"
            info[variante] = exportar(fig, ruta, cv, spec["source"], num, cfg)
            archivos[variante] = ruta.relative_to(out).as_posix()
            figs[variante] = fig
            print(f"  {num:8s} {variante:10s} {ruta.relative_to(out)}", flush=True)
        R = lint(figs["slide"], spec, msg, sub, spec["source"], info["slide"])
        fallas = [f"{k}: {v[1]}" for k, v in R.items() if v[0] == "falla"]
        status = spec.get("status", "done")
        filas.append(dict(slide_id=spec["slide"], storyline_point=spec["storyline_point"], figure_num=num, key=spec.get("key") or "",
                          canvas=spec["canvas"], version=spec["version"], role=spec["role"], file_slide=archivos["slide"], file_standalone=archivos["standalone"],
                          message_es=msg, subtitle_es=sub, source_es=spec["source"], width_px=info["slide"]["width_px"], height_px=info["slide"]["height_px"],
                          changes_applied=" | ".join(spec.get("changes", [])), qa_flags="; ".join(fallas) if fallas else "ok", status=status,
                          notes=spec.get("notes", ""), _lint=R, _meta=meta(figs["slide"])))
    if not args.solo:
        seg = cfg["seguimiento"]
        for i, paso in enumerate(seg["pasos"]):
            letra = "abcdef"[i]
            fig = n0_seguimiento(paso, seg["pasos"])
            canvas = tuple(cfg["lienzos"]["T"])
            set_meta(fig, sin_nota=True)
            apply_slide_style(fig, canvas, "slide", "", "", "", f"N.0{letra}")
            ascii_ = unicodedata.normalize("NFKD", paso.lower()).encode("ascii", "ignore").decode()
            ruta = out / carpetas["S13-S19"] / f"N.0{letra}__seguimiento_{re.sub(r'[^a-z0-9]+', '_', ascii_).strip('_')}__slide.png"
            inf = exportar(fig, ruta, canvas, "", f"N.0{letra}", cfg, con_nota=False)
            usos = ", ".join(s for s, p in seg["uso"].items() if p == paso) or "(sin uso en esta versión)"
            R = lint(fig, {"transform": "n0", "canvas": "T", "nature": "proceso"}, "", "-", "-", inf)
            R["G3"], R["G4"], R["NOTA"] = ("n.a.", "franja sin texto de mensaje"), ("n.a.", "franja de navegación"), ("n.a.", "sin nota")
            filas.append(dict(slide_id="S13-S19", storyline_point=f"Franja de seguimiento, paso activo «{paso}» (diapositivas {usos})", figure_num=f"N.0{letra}",
                              key="", canvas="T", version="final", role="context", file_slide=ruta.relative_to(out).as_posix(), file_standalone="",
                              message_es="", subtitle_es="", source_es="", width_px=inf["width_px"], height_px=inf["height_px"],
                              changes_applied="Figura nueva: seis pasos, el activo en naranja", qa_flags="; ".join(f"{k}: {v[1]}" for k, v in R.items() if v[0] == "falla") or "ok",
                              status="done", notes="", _lint=R, _meta={}))
            print(f"  N.0{letra}     slide      {ruta.relative_to(out)}", flush=True)
        escribir_salidas(out, cfg, filas, discrepancias, ctx)
    else:
        for f_ in filas:
            print(f_["figure_num"], f_["qa_flags"])


# ------------------------------------------------------------------------------------------------ 7. manifest, informe, README, hoja de contactos, zip
COLUMNAS = ["slide_id", "storyline_point", "figure_num", "key", "canvas", "version", "file_slide", "file_standalone", "message_es", "subtitle_es",
            "source_es", "width_px", "height_px", "changes_applied", "qa_flags", "status", "notes"]


def escribir_salidas(out: Path, cfg: dict, filas: list, discrepancias: list, ctx: dict):
    with open(out / "manifest.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNAS + ["role"], extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)
    json.dump([{k: v for k, v in f.items() if not k.startswith("_")} for f in filas], open(out / "manifest.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    hoja_de_contactos(out, filas)
    escribir_qa(out, cfg, filas, discrepancias, ctx)
    escribir_readme(out, cfg, filas)
    with zipfile.ZipFile(out / "figuras_pptx.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.rglob("*")):
            if p.is_file() and p.name != "figuras_pptx.zip":
                z.write(p, p.relative_to(out))


def hoja_de_contactos(out: Path, filas: list):
    """6 figuras por página (A4 apaisado), variante __slide, con su número y archivo."""
    paginas, W, H = [], 3508, 2480
    fnt, fntb = _fuente_pil(34), _fuente_pil(40, True)
    items = [f for f in filas if f["file_slide"]]
    for k in range(0, len(items), 6):
        pg = Image.new("RGB", (W, H), "white")
        d = ImageDraw.Draw(pg)
        d.text((80, 40), f"Figuras de la presentación · hoja {k // 6 + 1} de {math.ceil(len(items) / 6)}", fill=INK_PRIMARY, font=fntb)
        for j, f in enumerate(items[k:k + 6]):
            cx, cy = 80 + (j % 2) * 1700, 140 + (j // 2) * 770
            im = Image.open(out / f["file_slide"])
            im.thumbnail((1600, 660))
            pg.paste(im, (cx, cy))
            d.rectangle([cx, cy, cx + im.width, cy + im.height], outline=GRIDLINE, width=2)
            d.text((cx, cy + im.height + 8), f"{f['figure_num']} · {f['slide_id']} · {f['status']} · {f['file_slide']}"[:110], fill=INK_SECONDARY, font=fnt)
        paginas.append(pg)
    paginas[0].save(out / "contact_sheet.pdf", save_all=True, append_images=paginas[1:], resolution=300)


SIMB = {"ok": "✓", "falla": "✗", "n.a.": "–", "justificada": "J"}


def escribir_qa(out: Path, cfg: dict, filas: list, discrepancias: list, ctx: dict):
    L = ["# Informe de calidad: figuras de la presentación", "",
         f"Generado por `Scripts/34_exportar_figuras_presentacion.py` el {date.today().isoformat()} a partir de `config/figuras_presentacion.yaml`.", "",
         "## Método", "",
         "- **Captura sin servidor:** las páginas `final_pages/problema.py`, `final_pages/objetivo1.py` (dos corridas: vista por defecto y con "
         "`pc_vista = «Razón de soporte»` y `s13_variantes = «Efecto de la reforma en el empleo formal»`) y `extended_pages/objetivo2.py` (solo para 2.4.x) "
         "se corren con `streamlit.testing.v1.AppTest`; `components.charts.mostrar`, `numeracion.etiqueta`, `st.table`, `st.dataframe` y `st.caption` "
         "se reemplazan por funciones que anotan cada figura (después de `colores_legibles`, igual que en pantalla), cada tabla y sus pies. "
         "Las pestañas por región (1.1.6a-h) se dibujan todas en una corrida. No se usó el servidor en vivo.",
         "- **Exportación:** kaleido 1.5.2 (instalado en `Data raw/.venv` para este trabajo) con Chrome descargado por `plotly_get_chrome`. "
         "La nota de fuente se imprime con Pillow en una franja de 66 px (letra Helvetica Neue de 18 px), así nunca se cruzan con los ejes.",
         "- **Control automático:** `lint()` revisa las pautas que se pueden medir en la figura (abajo). Las pautas de juicio (G1, G2, G6, G19, G20, G22, G23) "
         "se revisaron mirando cada PNG en `contact_sheet.pdf`.",
         "- **Daltonismo (G17):** simulación de deuteranopía y protanopía (Machado 2009) y distancia en OKLab ×100 entre los colores con tono de cada figura; "
         "además se corrió el validador de la skill dataviz (`validate_palette.js`): azul/naranja/rojo pasan todos los chequeos (ΔE CVD ≥ 9,8). "
         "El gris de contexto y el naranja claro «fallan» solo el piso de croma/luminosidad por diseño (son tonos de fondo, no categorías) y siempre llevan rótulo directo.",
         "", "Leyenda: ✓ cumple · ✗ falla · – no aplica · J excepción justificada (detalle abajo).", "",
         "## Figura × regla", "",
         "| Figura | Diapositiva | Estado | " + " | ".join(REGLAS_AUTO) + " |", "|" + "---|" * (3 + len(REGLAS_AUTO))]
    for f in filas:
        R = f["_lint"]
        L.append(f"| {f['figure_num']} ({f['file_slide'].split('__')[1] if '__' in f['file_slide'] else ''}) | {f['slide_id']} | {f['status']} | "
                 + " | ".join(SIMB[R[r][0]] for r in REGLAS_AUTO) + " |")
    L += ["", "Reglas: G3 mensaje ≤ 25 palabras y sin siglas · G4 título/subtítulo/nota · G5 acento · G7 barras · G8 líneas · G9 doble eje · G10 dispersión · "
          "G11 burbujas por área · G12 tortas · G13 partes suman 100 % · G14 cascada cierra · G15 paneles · G16 orden · G17 daltonismo · G18 sin leyenda · "
          "G21 advertencia de escenario/juicio/atribución · LETRA ≥ 20 px · NOTA ≤ 2 líneas · RES ancho ≥ 4.680 px.", ""]
    fallas = [(f["figure_num"], r, v[1]) for f in filas for r, v in f["_lint"].items() if v[0] == "falla" and f["status"] == "done"]
    L += ["## Fallas abiertas", ""] + ([f"- {a} {b}: {c}" for a, b, c in fallas] or ["Ninguna en las figuras terminadas."]) + [""]
    just = [(f["figure_num"], r, v[1]) for f in filas for r, v in f["_lint"].items() if v[0] == "justificada"]
    L += ["## Excepciones justificadas", ""] + ([f"- {a} {b}: {c}" for a, b, c in just] or ["Ninguna."]) + [""]
    L += ["## Detalle por figura (qué se cambió y qué midió el control)", ""]
    for f in filas:
        L.append(f"### {f['figure_num']} · {f['slide_id']} · {f['storyline_point']}")
        L.append("")
        if f["message_es"]:
            L.append(f"- **Mensaje:** {f['message_es']}")
        for c in f["changes_applied"].split(" | "):
            if c:
                L.append(f"- {c}")
        det = [f"{r} {v[1]}" for r, v in f["_lint"].items() if v[1] and r in ("G13", "G14", "G17", "LETRA", "RES", "G8")]
        if det:
            L.append(f"- Control: {'; '.join(det)}")
        if f["notes"]:
            L.append(f"- Nota: {f['notes']}")
        L.append("")
    mt = {f["figure_num"] + f["file_slide"]: f["_meta"] for f in filas}
    get = lambda num: next((f["_meta"] for f in filas if f["figure_num"] == num), {})  # noqa: E731
    n6, n4, n5, n8, n9, f131 = get("N.6"), get("N.4"), get("N.5"), get("N.8"), get("N.9"), get("1.3.1")
    L += ["## Discrepancias", ""]
    L += [f"- {d}" for d in discrepancias] or ["- Numeración: todos los números del mapa coinciden con `ORDEN` (components/numeracion.py)."]
    L += [
        "- **Biobío excluida de la selección (pedido 20-nov):** la regla de dos preguntas (`Scripts/35`) y el dashboard dan 8 regiones; en las diapositivas la selección es de **7** "
        "(`EXCLUIDAS` en este script). Biobío entraba solo por la brecha (3.ª, 34.037 personas). Se quitó de: mapa 1.1.1 (borde y conteo), 1.1.8-1.1.10 (barra en gris), 1.1.20 y N.5 (fila «No (excluida)»), "
        "N.5c (barra gris «excluida»; 7 regiones = 224.160 de 295.330 = 75,9 %), N.5d y 1.1.25 (descomposición de 7), 1.1.6 (sin la ficha h), 1.1.31, 1.1.32, N.9, franja de seguimiento y N.1. "
        "La regla del dashboard, `Scripts/35` y los CSV no cambian: es una decisión de presentación, no de datos.",
        f"- **Cifras de las 7 regiones (1.1.25, S14/S17):** de los {cl(n5.get('brecha_8', 224160), 0)} cotizantes que faltan, ponderando por población, 80,4 % (180.355) vienen de ocupados que no cotizan, 18,4 % (41.158) de la participación y 1,2 % (2.648) del empleo "
        "(fórmula: Σ aporte_pp × población 15-64 / 100 por región, `kpi_cobertura_descomposicion.csv` «Nivel frente a Chile en 2024»). Con las 8 eran 69,6 / 28,0 / 2,4 %. "
        "Sin Biobío (la única donde lideraba la participación), «ocupados que cotizan» es el factor mayor en las 7 y la informalidad es desfavorable en las 7 (1.1.32): el titular de S14 pasa de «casi todas» a «las siete».",
        f"- **N.4 (limpieza):** el pedido esperaba ≈ 5,86 millones de total y ≈ 5,81 millones con región. Los datos: total {cl(n4.get('total', 0), 0)}, sin región {cl(n4.get('sin', 0), 0)}, "
        f"con región {cl(n4.get('con', 0), 0)} (16 regiones; control de igualdad en el script). 5,81 millones son los dependientes que cotizan (1.1.4).",
        f"- **N.6:** costo 2025 = gastos de administración ÷ personas: ${cl(n6.get('costo_cot', 0), 0)} por cotizante y ${cl(n6.get('costo_af', 0), 0)} por afiliado "
        "(igual a docs/COSTOS_AFP_HALLAZGOS.md). El mensaje pedido («menos cotizantes activos y más cuentas pasivas») no está en los datos 2010-2025: "
        f"la razón afiliados/cotizantes fue {n6.get('razon', {})}; se cambió por un mensaje que sí muestran los datos.",
        f"- **1.3.1:** el dashboard titula 56 % (redondeo a entero); la línea 1.3.2/1.3.3 rotula 55,5 % para 2025. La diapositiva usa {cl(f131.get('pct_2025', 55.5), 1)} %.",
        "- **1.3.3:** el eje y del dashboard va de 0 a 70 %: no está truncado (el pedido suponía 50-56 %); la nota no lleva «el eje no parte de 0». Su titular en el dashboard es el mismo de 1.3.2.",
        "- **1.2.4:** el dashboard tiene 8 barras (2010-2070), no 3; se mantienen y se destacan las tres del mensaje.",
        "- **1.1.8-1.1.10 (error del dashboard, no corregido aquí):** el subtítulo del dashboard dice «de la peor (arriba) a la mejor», pero el gráfico dibuja "
        "la peor abajo (Plotly pone la primera categoría de `categoryarray` abajo; `region_ranking_bars` pasa la lista invertida). En las diapositivas la peor va arriba. "
        "Corregirlo en `components/charts.py::region_ranking_bars` queda para el equipo (el encargo prohibía cambiar el dashboard).",
        "- **1.1.4:** el pedido hablaba de cinco bloques; el gráfico tiene seis (cotizan dependientes / independientes y voluntarios se ven como un bloque «Cotizan»). Suman 100,0 %.",
        "- **1.1.25:** el dashboard tiene cuatro paneles (los tres factores y la diferencia total); se mantiene el cuarto, en gris oscuro, porque muestra que los tres suman la diferencia.",
        "- **1.2.8:** el cruce es entre la razón observada y la razón de equilibrio (1,47 cotizantes por persona de 65+), no un cociente que cruce 1,00.",
        "- **1.1.31:** ambos ejes del dashboard ya parten de 0.",
        f"- **N.8:** años de cruce tomados del gráfico 1.2.10 = {n8.get('cruces', {})}; calculados por interpolación al exportar = {n8.get('cruces_calc', {})}. "
        "La tabla 1.2.11 dice «Sin informalidad» y «Mitad del camino»; en las diapositivas se usan los nombres de los paneles («Todos los informales cotizan», «Mitad de los informales cotiza»).",
        f"- **N.9 / S17:** la participación de la encuesta de empleo de diciembre 2024 está bajo Chile ({cl(n9.get('chile', 62.3), 1)} %) en {n9.get('n_bajo', '?')} de 7 regiones críticas "
        f"({n9.get('peores', {})}). El corte por sexo no existe en los archivos regionales.",
        "- **N.2:** `config/sources.yaml` no existe; la matriz sale de `Data raw/INVENTARIO_FUENTES.md`, `docs/AUDITORIA_FUENTES.md`, `docs/DATOS_ABIERTOS.md` y `docs/RESUMEN_CAMBIOS_KPI_1_1_Y_1_2.md`. "
        "El archivo de la encuesta de empleo regional llega a mayo 2024 (el pedido lo anotaba como vacío «después de mayo 2024»); diciembre 2024 viene del anexo de la Asociación de AFP.",
        f"- **N.3:** conteos calculados al exportar: {ctx['conteos']}. Correspondencia de capas: bronce = `Data raw/`; plata = `Scripts/NN_*.py` y tablas limpias de `Data processed/`; "
        "oro = `Data processed/kpi_*.csv`; consumo = `Dashboards/`. La propuesta de septiembre usaba carpetas 00_raw…30_gold que no existen en el repositorio.",
        "- **Ancho de las figuras H:** 780 px × 3 = 2.340 px no llega a los 4.680 px que pide la sección 8; las figuras H se exportan con escala 6 (4.680 px de ancho).",
        "- **Regla de dos preguntas (20-nov-2026, N.5a-N.5d):** reemplaza a N.5 (estado `superseded`, se conserva). Cifras de `Data processed/kpi_seleccion_dos_preguntas.csv` "
        "(`Scripts/35_seleccion_dos_preguntas.py`); coinciden con las del pedido: Chile 37,1 → 46,5 %, +9,4 puntos, +25,3 %; la regla da 8 regiones = 258.197 de 295.330 cotizantes (87,4 %) y 36,6 % de la población de 15 a 64 años; sin Biobío (decisión de presentación), 7 regiones = 224.160 (75,9 %).",
        "- **Nombre «siete» con 8 regiones:** `kpi_cobertura_siete_vs_chile.csv` y `docs/SIETE_VS_CHILE.md` dicen «siete» pero resumen las 8 regiones (suma de brechas 258.198). No se renombró.",
        "- **N.5c:** la definición de brecha va dentro de la figura, no en la nota de fuente (en 780 px la nota larga ocupaba tres líneas, el máximo es dos). Las dos regiones azules (Arica y Parinacota, Tarapacá) quedan al final porque la lista está ordenada por brecha, "
        "así que el grupo no es contiguo (y Biobío, excluida, queda en gris entre las naranjas): se rotula con el total («7 regiones: 224 mil de 295 mil = 76 %»).",
        "- **N.5a:** el lienzo de la variante standalone es más alto que 720 px (el titular ocupa cuatro líneas); la variante slide cabe en 780 × 720.",
        "- **N.5b:** la franja 2020-2021 se rotula «Pandemia» dentro de la figura (en 1.1.18 el rótulo iba en la nota). La población de 2007 usa la proyección del Instituto Nacional de Estadísticas base 2017 llevada al nivel del Censo 2024 (igual que `kpi_cobertura_tendencia.csv`).",
        "- **Sin números de figura en las imágenes (pedido 20-nov):** se quitó «Fig. x.y.z» de la franja de la nota y las referencias a números de figura de las notas de fuente de 1.2.8, 1.2.10, N.0r y N.8 y de las descripciones de N.1. El número solo va en el nombre del archivo.",
        "- **P.3 (envejecimiento):** se quitaron los rótulos «Estimado» y «Proyección del Instituto Nacional de Estadísticas»; queda la franja gris «Proyección» y el tono más claro.",
        "- **Estabilidad de la regla:** con año de partida 2007…2018 las ocho regiones de la regla no cambian a corte 80 %; a 70 % sale Los Ríos (7 regiones, 80 % de la brecha); a 90 % entran las diez (`kpi_seleccion_sensibilidad.csv`).",
        "", "## Decisiones abiertas (para el equipo)", "",
        "0. **¿Llevar la regla de dos preguntas al dashboard?** (tabla de puestos y barras de brecha coloreadas junto a 1.1.8-1.1.10). La regla da las mismas 8 regiones del dashboard, y Biobío se excluye solo en las diapositivas; "
        "requiere claves nuevas en `ORDEN` (components/numeracion.py). No se hizo sin confirmación.",
        "1. **¿Pasar 2.4.x a la versión final?** Hoy 2.4.1 y 2.4.5 solo existen en la extendida (se exportaron desde allí). Si se pasan, conservan su número 2.4.x "
        "(las claves exclusivas de la extendida se numeran con la lista extendida en ambas versiones).",
        "2. **Confirmar Y = participación laboral** como segunda razón (S17-S19). Los datos la apoyan (18 % de lo que falta en las 7 regiones), pero N.10 y N.11 están bloqueadas.",
        "3. **Redacción en S14:** con 7 regiones, «las siete» es correcto (en las 7 lidera «ocupados que cotizan»).",
        "4. **Líneas punteadas:** el 9-nov el equipo decidió mantener el escenario punteado en el dashboard hasta consultarlo con el profesor. En estas diapositivas "
        "se aplicó la pauta G8 de la clase (escenario continuo en tono claro + franja «Escenario»), como pide el encargo; el dashboard no se tocó.",
        "5. **N.6:** el mensaje cambió respecto del pedido (ver Discrepancias). Confirmar el titular.",
        "6. **N.8 con 5 líneas:** cuatro capacidades + el costo en un panel (la especificación N.8 lo pide así). Alternativa sin excepción: 1.2.10 en tres paneles.",
        "", "## Pruebas", "",
        "- Línea base antes de este trabajo: `pytest tests/test_numeracion.py tests/test_dashboard_smoke.py -q` → 61 passed.",
        "- Nueva: `tests/test_figuras_presentacion.py` (manifest completo, archivos, resolución, números contra `ORDEN`, control sin fallas y pruebas del control con figuras de ejemplo).",
        ""]
    (out / "qa_report.md").write_text("\n".join(L), encoding="utf-8")


def escribir_readme(out: Path, cfg: dict, filas: list):
    pulg = {"W": "12,3 × 5,5 pulgadas (ancho completo bajo el titular)", "H": "6,0 × 5,5 pulgadas (media diapositiva; dos lado a lado)",
            "F": "12,3 × 6,8 pulgadas (mapas, 16 regiones, varios paneles)", "T": "12,3 × 0,7 pulgadas (franja arriba del titular)",
            "R": "12,3 × 2,3 pulgadas (fila de recuadros)", "M": "12,3 × 3,7 pulgadas (media diapositiva, abajo)", "A": "12,3 × 9,6 pulgadas (tabla de anexo a página completa)"}
    L = ["# Figuras para la presentación (pptx)", "",
         "Paquete generado por `Scripts/34_exportar_figuras_presentacion.py` desde `config/figuras_presentacion.yaml`. No cambia el dashboard.", "",
         "## Cómo insertar una figura", "",
         "1. Abrir la carpeta de la diapositiva (`S04_demografia/`, `S05_…`). Cada figura tiene dos archivos:",
         "   - `…__slide.png`: **sin ningún título** (ni el titular en negrita ni el subtítulo gris). El mensaje va como titular de la diapositiva (columna `message_es` de `manifest.csv`; el subtítulo, en `subtitle_es`).",
         "   - `…__standalone.png`: la misma figura con los dos títulos (mensaje en negrita y subtítulo gris), para usarla fuera de la presentación (informe, correo).",
         "2. En PowerPoint: Insertar → Imágenes → Este dispositivo. Fijar el **ancho** según el lienzo (bloquear la relación de aspecto):", ""]
    L += [f"   - **{k}** ({' × '.join(map(str, v))} px): {pulg[k]}" for k, v in cfg["lienzos"].items()]
    L += ["", "3. La **fuente** ya está impresa abajo a la izquierda de cada imagen. El **número de la figura no aparece dentro de la imagen**: va solo en el nombre del archivo (`1.2.9__…png`) y en `manifest.csv`. No hace falta otro pie.",
          "4. Bajo la figura, una línea de texto con el resultado (pauta de la clase: titular con el mensaje + figura destacada + una línea con el resultado).",
          "5. Escenarios: la nota ya dice «Escenario, no es un pronóstico»; los juicios, «juicio del equipo». No quitarlo al recortar.", "",
          "Resolución: ancho ≥ 4.680 px en todas (≈ 380 ppp a 12,3 pulgadas). Fondo #fcfcfb, sin barra de herramientas.", "",
          "## Orden de la historia", "",
          "Introducción (S04-S05) → Desarrollo (S06-S08) → Método (S09-S12) → Conflicto/clímax (S13-S14, S17) → Llamado a la acción (S15, S18) → "
          "Resolución (S16, S19). Terminar con la acción (S15/S18), no con un gráfico. La franja `S13-S19_seguimiento/` va arriba de las diapositivas S13-S19 "
          "con el paso activo en naranja.", "",
          "| Diapositiva | Figura | Rol | Titular (mensaje) | Archivo | Estado |", "|---|---|---|---|---|---|"]
    for f in filas:
        L.append(f"| {f['slide_id']} | {f['figure_num']} | {f.get('role', '')} | {f['message_es']} | `{f['file_slide']}` | {f['status']} |")
    L += ["", "## Para la exposición (pauta G23)", "",
          "- Sin jerga técnica: decir «administradoras», «Pensión Garantizada Universal», «encuesta de empleo»; nada de siglas en voz alta sin explicarlas.",
          "- Controlar el tiempo: una idea por diapositiva; las figuras de respaldo (`role = backup/appendix`) quedan para preguntas.",
          "- Estructura clara: anunciar en qué paso de la franja de seguimiento se está.",
          "- Decir siempre «escenario, no pronóstico» en S06, S08, S16 y «juicio del equipo» en S15/S18.", "",
          "## Archivos", "",
          "- `manifest.csv` / `manifest.json`: una fila por figura (mensaje, subtítulo, fuente, tamaño, cambios, control, estado).",
          "- `qa_report.md`: figura × regla, cambios, discrepancias y decisiones abiertas.",
          "- `contact_sheet.pdf`: todas las figuras, 6 por página.", "- `figuras_pptx.zip`: todo lo anterior.", ""]
    (out / "README.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
