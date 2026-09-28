"""Pirámides demográficas: nacional con evolución 1992-2070 (proyección INE),
y transversal por región/comuna (Censo 2024, tramos quinquenales)."""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from utils import (load_csv, BLUE, ORANGE, RED, AQUA, VIOLET, INK_PRIMARY, INK_MUTED, GRIDLINE, SURFACE, lighten,
                    PLOTLY_DL_CONFIG)

st.set_page_config(page_title="Pirámides demográficas", page_icon="📊", layout="wide")
st.title("📊 Pirámides demográficas y su evolución")

BLUE_LIGHT = lighten(BLUE)
ORANGE_LIGHT = lighten(ORANGE)
UMBRAL_VEJEZ = 65  # umbral OMS/INE para "adulto mayor", marcado con la línea roja

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
            h_colors = [BLUE_LIGHT if edad < UMBRAL_VEJEZ else BLUE for edad in h.index]
            m_colors = [ORANGE_LIGHT if edad < UMBRAL_VEJEZ else ORANGE for edad in m.index]
            fig.add_trace(go.Bar(y=h.index, x=-h.values / 1000, orientation="h", marker_color=h_colors,
                                  name="Hombres", showlegend=(i == 1), legendgroup="H"), row=1, col=i)
            fig.add_trace(go.Bar(y=m.index, x=m.values / 1000, orientation="h", marker_color=m_colors,
                                  name="Mujeres", showlegend=(i == 1), legendgroup="M"), row=1, col=i)

        fig.update_layout(
            barmode="overlay", height=560, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
            font=dict(family="system-ui, sans-serif", size=12),
            title="Pirámide poblacional de Chile — comparación entre años (miles de personas)",
            margin=dict(t=70, l=10, r=10, b=10),
        )
        fig.update_xaxes(range=[-xmax, xmax], gridcolor=GRIDLINE, zeroline=True, zerolinecolor=INK_MUTED)
        fig.update_yaxes(gridcolor=GRIDLINE, title_text="Edad", col=1)
        # Línea roja en cada subgráfico (no una sola a través de toda la figura) marcando
        # el umbral de 65 años; col="all" la repite de forma idéntica en cada panel.
        fig.add_hline(y=UMBRAL_VEJEZ, line_color=RED, line_width=1.5, line_dash="dot", row=1, col="all")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DL_CONFIG)
        st.caption("1992–2070: INE, Estimaciones y proyecciones de población base 2024 (nacional, corte 30-jun). "
                   "2024 (Censo): edad simple, top-codeada a 85+. Tonos claros = menores de 65 años, tonos "
                   "sólidos = 65 años y más; la línea roja marca ese umbral en cada panel.")

    st.divider()
    proy_ind = load_csv("proyeccion_envejecimiento_pais.csv")

    ANIO_BASE = 2024  # "base 2024": ultimo anio estimado; en adelante es proyeccion INE
    AQUA_LIGHT = lighten(AQUA)
    VIOLET_LIGHT = lighten(VIOLET)
    RED_LIGHT = lighten(RED)
    SERIES_PCT = [("pct_0_14", "% 0-14 años", AQUA, AQUA_LIGHT), ("pct_65_mas", "% 65+ años", VIOLET, VIOLET_LIGHT)]

    col_pct, col_idx = st.columns(2)

    with col_pct:
        fig3 = go.Figure()
        for col, label, color_fuerte, color_claro in SERIES_PCT:
            real = proy_ind[proy_ind.anio <= ANIO_BASE]
            proyectado = proy_ind[proy_ind.anio >= ANIO_BASE]
            fig3.add_trace(go.Scatter(
                x=real["anio"], y=real[col], mode="lines+markers", name=f"{label} (estimado)",
                legendgroup=label, line=dict(color=color_fuerte, width=2.5), marker=dict(size=5, color=color_fuerte),
                hovertemplate="Año %{x:.0f}<br>" + label + ": %{y:.1f}%<extra></extra>",
            ))
            fig3.add_trace(go.Scatter(
                x=proyectado["anio"], y=proyectado[col], mode="lines+markers", name=f"{label} (proyectado)",
                legendgroup=label, line=dict(color=color_claro, width=2.5, dash="dash"),
                marker=dict(size=5, color=color_claro, symbol="circle-open"),
                hovertemplate="Año %{x:.0f}<br>" + label + ": %{y:.1f}%<extra></extra>",
            ))

        y_all = pd.concat([proy_ind["pct_0_14"], proy_ind["pct_65_mas"]])
        pad = (y_all.max() - y_all.min()) * 0.08
        fig3.update_layout(
            height=520, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
            font=dict(family="system-ui, sans-serif", size=12),
            title="Evolución de la estructura por edad (% de la población total)",
            margin=dict(t=60, l=10, r=10, b=10),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        fig3.update_xaxes(title_text="Año", tickformat="d", gridcolor=GRIDLINE)
        fig3.update_yaxes(title_text="% de la población", gridcolor=GRIDLINE,
                           range=[max(0, y_all.min() - pad), y_all.max() + pad])
        st.plotly_chart(fig3, use_container_width=True, config=PLOTLY_DL_CONFIG)
        st.caption("Línea sólida = estimaciones INE ancladas en censos (1992–2024); línea discontinua = proyección "
                   "INE según hipótesis de fecundidad/mortalidad/migración (2025–2070). Cruce de las curvas ≈ 2032: "
                   "primer año en que la población de 65+ supera a la de 0-14 a nivel nacional.")

    with col_idx:
        real_idx = proy_ind[proy_ind.anio <= ANIO_BASE]
        proyectado_idx = proy_ind[proy_ind.anio >= ANIO_BASE]

        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=real_idx["anio"], y=real_idx["indice_envejecimiento"], mode="lines+markers",
            name="Índice de envejecimiento (estimado)", line=dict(color=RED, width=2.5),
            marker=dict(size=5, color=RED),
            hovertemplate="Año %{x:.0f}<br>Índice: %{y:.0f} mayores por c/100 niños<extra></extra>",
        ))
        fig4.add_trace(go.Scatter(
            x=proyectado_idx["anio"], y=proyectado_idx["indice_envejecimiento"], mode="lines+markers",
            name="Índice de envejecimiento (proyectado)", line=dict(color=RED_LIGHT, width=2.5, dash="dash"),
            marker=dict(size=5, color=RED_LIGHT, symbol="circle-open"),
            hovertemplate="Año %{x:.0f}<br>Índice: %{y:.0f} mayores por c/100 niños<extra></extra>",
        ))
        fig4.add_hline(y=100, line_color=INK_MUTED, line_width=1, line_dash="dot",
                       annotation_text="Paridad: 100 mayores por c/100 niños", annotation_position="bottom right",
                       annotation_font=dict(size=10, color=INK_MUTED))
        for anio_ref in (1992, 2024, 2050, 2070):
            val = float(proy_ind.loc[proy_ind.anio == anio_ref, "indice_envejecimiento"].iloc[0])
            fig4.add_annotation(x=anio_ref, y=val, text=f"{val:.0f}", showarrow=False, yshift=16,
                                 font=dict(size=11, color=INK_PRIMARY))

        fig4.update_layout(
            height=520, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
            font=dict(family="system-ui, sans-serif", size=12),
            title="Índice de envejecimiento — aceleración 1992-2070",
            margin=dict(t=60, l=10, r=10, b=10),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        fig4.update_xaxes(title_text="Año", tickformat="d", gridcolor=GRIDLINE)
        fig4.update_yaxes(title_text="Mayores de 65 por c/100 niños de 0-14", gridcolor=GRIDLINE)
        st.plotly_chart(fig4, use_container_width=True, config=PLOTLY_DL_CONFIG)
        st.caption("Mismo dato que el gráfico de la izquierda, expresado como razón: pasa de 22 (1992) a 80 "
                   "(2024, censo) y a 596 (2070, proyección INE) — una curva claramente acelerada, no lineal: "
                   "se multiplica ×3.6 entre 1992-2024, pero ×7.5 entre 2024-2070. Cruza 100 (más mayores que "
                   "niños) alrededor de 2028.")

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

    h_colors2 = [BLUE_LIGHT if edad < UMBRAL_VEJEZ else BLUE for edad in h.index]
    m_colors2 = [ORANGE_LIGHT if edad < UMBRAL_VEJEZ else ORANGE for edad in m.index]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(y=etiquetas, x=-h.values, orientation="h", name="Hombres", marker_color=h_colors2))
    fig2.add_trace(go.Bar(y=etiquetas, x=m.values, orientation="h", name="Mujeres", marker_color=m_colors2))
    xmax2 = max(h.max(), m.max()) * 1.1
    fig2.update_layout(
        barmode="overlay", height=650, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        title=f"Pirámide poblacional — {sel} (Censo 2024)",
        xaxis=dict(range=[-xmax2, xmax2], gridcolor=GRIDLINE, title="Personas"),
        yaxis=dict(title="Grupo de edad", categoryorder="array", categoryarray=etiquetas),
        font=dict(family="system-ui, sans-serif", size=12),
    )
    # Umbral de 65 años: linea entre las categorias "60-64" y "65-69".
    idx_65 = etiquetas.index("65-69")
    fig2.add_hline(y=idx_65 - 0.5, line_color=RED, line_width=1.5, line_dash="dot")
    st.plotly_chart(fig2, use_container_width=True, config=PLOTLY_DL_CONFIG)
    st.caption(f"Total: {int(h.sum()+m.sum()):,} personas (tramos quinquenales, cobertura 100% incluidas comunas bajo umbral de edad exacta).")
