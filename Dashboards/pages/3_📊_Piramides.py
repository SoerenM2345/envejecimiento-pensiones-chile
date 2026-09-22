"""Pirámides demográficas: nacional con evolución 1992-2070 (proyección INE),
y transversal por región/comuna (Censo 2024, tramos quinquenales)."""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from utils import load_csv, BLUE, ORANGE, INK_MUTED, GRIDLINE, SURFACE

st.set_page_config(page_title="Pirámides demográficas", page_icon="📊", layout="wide")
st.title("📊 Pirámides demográficas y su evolución")

tab1, tab2 = st.tabs(["🇨🇱 Evolución nacional (1992–2070)", "📍 Región / comuna (Censo 2024)"])

# ---------------------------------------------------------------------------
# Tab 1: evolucion nacional (small multiples)
# ---------------------------------------------------------------------------
with tab1:
    proy = load_csv("proyeccion_pais_edad_sexo.csv")
    censo_pais = load_csv("censo_pais_edad_simple.csv")
    censo_pais["anio"] = 2024

    años_disponibles = sorted(proy["anio"].unique().tolist())
    seleccion = st.multiselect("Años a comparar (máx. 4)", años_disponibles,
                                default=[1992, 2024, 2050, 2070], max_selections=4)
    fuente_2024 = st.radio("Para 2024, usar", ["Censo 2024 (real)", "Proyección INE (para comparar metodologías)"],
                            horizontal=True)

    if not seleccion:
        st.info("Elige al menos un año.")
    else:
        n = len(seleccion)
        fig = make_subplots(rows=1, cols=n, subplot_titles=[str(a) for a in seleccion], shared_yaxes=True,
                             horizontal_spacing=0.02)
        xmax = 0
        for i, anio in enumerate(seleccion, start=1):
            if anio == 2024 and fuente_2024.startswith("Censo"):
                h = censo_pais[censo_pais.sexo == 1].set_index("edad")["poblacion"].reindex(range(0, 86), fill_value=0)
                m = censo_pais[censo_pais.sexo == 2].set_index("edad")["poblacion"].reindex(range(0, 86), fill_value=0)
            else:
                sub = proy[proy.anio == anio]
                h = sub[sub.sexo == "H"].set_index("edad")["poblacion"].reindex(range(0, 101), fill_value=0)
                m = sub[sub.sexo == "M"].set_index("edad")["poblacion"].reindex(range(0, 101), fill_value=0)
            xmax = max(xmax, (h.max() + m.max()) / 1000 * 0.6)
            fig.add_trace(go.Bar(y=h.index, x=-h.values / 1000, orientation="h", marker_color=BLUE,
                                  name="Hombres", showlegend=(i == 1), legendgroup="H"), row=1, col=i)
            fig.add_trace(go.Bar(y=m.index, x=m.values / 1000, orientation="h", marker_color=ORANGE,
                                  name="Mujeres", showlegend=(i == 1), legendgroup="M"), row=1, col=i)

        fig.update_layout(
            barmode="overlay", height=560, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
            font=dict(family="system-ui, sans-serif", size=12),
            title="Pirámide poblacional de Chile — comparación entre años (miles de personas)",
            margin=dict(t=70, l=10, r=10, b=10),
        )
        fig.update_xaxes(range=[-xmax, xmax], gridcolor=GRIDLINE, zeroline=True, zerolinecolor=INK_MUTED)
        fig.update_yaxes(gridcolor=GRIDLINE, title_text="Edad", col=1)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("1992–2070: INE, Estimaciones y proyecciones de población base 2024 (nacional, corte 30-jun). "
                   "2024 (Censo): edad simple, top-codeada a 85+.")

    st.divider()
    proy_ind = load_csv("proyeccion_envejecimiento_pais.csv")
    st.line_chart(proy_ind.set_index("anio")[["pct_0_14", "pct_65_mas"]].rename(
        columns={"pct_0_14": "% 0-14 años", "pct_65_mas": "% 65+ años"}))
    st.caption("Cruce de las curvas ≈ 2032: primer año en que la población de 65+ supera a la de 0-14 a nivel nacional.")

# ---------------------------------------------------------------------------
# Tab 2: corte transversal region/comuna
# ---------------------------------------------------------------------------
with tab2:
    nivel = st.radio("Nivel", ["Región", "Comuna"], horizontal=True, key="nivel_piramide")
    if nivel == "Región":
        df = load_csv("censo_region_edad_sexo.csv")
        opciones = sorted(df["region_nombre"].dropna().unique())
        sel = st.selectbox("Región", opciones)
        sub = df[df.region_nombre == sel]
    else:
        df = load_csv("censo_comuna_edad_sexo.csv")
        regiones = sorted(df["region_nombre"].dropna().unique())
        col1, col2 = st.columns(2)
        reg_sel = col1.selectbox("Región", regiones)
        comunas = sorted(df.loc[df.region_nombre == reg_sel, "comuna_nombre"].dropna().unique())
        com_sel = col2.selectbox("Comuna", comunas)
        sub = df[(df.region_nombre == reg_sel) & (df.comuna_nombre == com_sel)]
        sel = com_sel

    piv = sub.groupby(["edad_quinquenal", "sexo"])["poblacion"].sum().reset_index()
    h = piv[piv.sexo == 1].set_index("edad_quinquenal")["poblacion"].reindex(range(0, 90, 5), fill_value=0)
    m = piv[piv.sexo == 2].set_index("edad_quinquenal")["poblacion"].reindex(range(0, 90, 5), fill_value=0)
    etiquetas = [f"{e}-{e+4}" if e < 85 else "85+" for e in h.index]

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(y=etiquetas, x=-h.values, orientation="h", name="Hombres", marker_color=BLUE))
    fig2.add_trace(go.Bar(y=etiquetas, x=m.values, orientation="h", name="Mujeres", marker_color=ORANGE))
    xmax2 = max(h.max(), m.max()) * 1.1
    fig2.update_layout(
        barmode="overlay", height=650, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        title=f"Pirámide poblacional — {sel} (Censo 2024)",
        xaxis=dict(range=[-xmax2, xmax2], gridcolor=GRIDLINE, title="Personas"),
        yaxis=dict(title="Grupo de edad", categoryorder="array", categoryarray=etiquetas),
        font=dict(family="system-ui, sans-serif", size=12),
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.caption(f"Total: {int(h.sum()+m.sum()):,} personas (tramos quinquenales, cobertura 100% incluidas comunas bajo umbral de edad exacta).")
