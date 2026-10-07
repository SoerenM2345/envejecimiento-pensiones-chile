"""
Explorador de datos ("back end"): carga cualquier archivo de Data processed,
opcionalmente lo cruza con un segundo archivo, permite filtrar columna por
columna, y agrupar/sumar (o promediar/contar) por las dimensiones que se
quiera — todo desde controles, sin tocar código. Pensado para responder
preguntas ad-hoc del tipo "dame la suma de X por región, filtrando Y".
"""
import pandas as pd
import plotly.express as px
import streamlit as st
from utils import list_processed_csvs, load_csv, standardize_keys, page_config, CATEGORICAL, PLOTLY_LAYOUT, PLOTLY_DL_CONFIG

page_config(page_title="Explorador de datos", page_icon="🔍")
st.title("🔍 Explorador de datos")
st.caption("Selecciona fuente(s), filtra, agrupa y suma/promedia. Todas las tablas de `Data processed/`.")

archivos = list_processed_csvs()

# ---------------------------------------------------------------------------
# 1) Selección de fuente(s)
# ---------------------------------------------------------------------------
st.sidebar.header("1. Fuente de datos")
f1 = st.sidebar.selectbox("Fuente principal", archivos, index=archivos.index("indicadores_region.csv") if "indicadores_region.csv" in archivos else 0)
df = standardize_keys(load_csv(f1))

mezclar = st.sidebar.checkbox("Mezclar con una segunda fuente", value=False)
df2_info = None
if mezclar:
    opciones2 = [a for a in archivos if a != f1]
    f2 = st.sidebar.selectbox("Segunda fuente", opciones2)
    df2 = standardize_keys(load_csv(f2))
    comunes = [c for c in df.columns if c in df2.columns]
    if not comunes:
        st.sidebar.error("Sin columnas en común tras normalizar claves (region_id/comuna_id/anio) — no se puede cruzar.")
    else:
        clave = st.sidebar.selectbox("Cruzar por", comunes, index=0)
        tipo_join = st.sidebar.radio("Tipo de cruce", ["left", "inner", "outer"], horizontal=True,
                                       help="left: conserva todo de la fuente principal. inner: solo coincidencias. outer: todo de ambas.")
        len1, len2 = len(df), len(df2)
        # evita duplicar columnas no-clave con el mismo nombre
        overlap = [c for c in comunes if c != clave]
        df2_ren = df2.rename(columns={c: f"{c}_2" for c in overlap})
        df = df.merge(df2_ren, on=clave, how=tipo_join, suffixes=("", "_2"))
        df2_info = f2
        # fan-out check: ¿el cruce multiplicó las filas de la fuente principal?
        # (si df2 tiene varias filas por clave, cada fila de df se repite -> sumar
        # una columna de df tal cual queda inflada)
        if len1 and len(df) > 1.5 * len1:
            st.sidebar.warning(
                f"⚠️ El cruce infla filas ({len1:,} → {len(df):,}): '{f2}' tiene varias filas por "
                f"'{clave}' (ej. por mes/tramo de edad). Sumar una columna de '{f1}' tal cual quedará "
                f"duplicada. Filtra '{f2}' por sus otras columnas (ej. un año/tramo específico) antes "
                f"de agregar, o agrúpala primero con este mismo Explorador."
            )

st.subheader("Vista previa" + (f" — {f1} + {df2_info}" if df2_info else f" — {f1}"))
st.caption(f"{len(df):,} filas × {df.shape[1]} columnas")

# ---------------------------------------------------------------------------
# 2) Filtros dinámicos
# ---------------------------------------------------------------------------
st.sidebar.header("2. Filtros")
cols_filtrables = st.sidebar.multiselect("Columnas a filtrar", df.columns.tolist())

df_filtrado = df.copy()
for col in cols_filtrables:
    serie = df_filtrado[col]
    if pd.api.types.is_numeric_dtype(serie):
        lo, hi = float(serie.min()), float(serie.max())
        if lo == hi:
            st.sidebar.caption(f"{col}: único valor = {lo}")
            continue
        sel = st.sidebar.slider(col, lo, hi, (lo, hi))
        df_filtrado = df_filtrado[(df_filtrado[col] >= sel[0]) & (df_filtrado[col] <= sel[1])]
    else:
        valores = sorted(serie.dropna().unique().tolist(), key=str)
        if len(valores) <= 60:
            sel = st.sidebar.multiselect(col, valores, default=valores)
            df_filtrado = df_filtrado[df_filtrado[col].isin(sel)]
        else:
            texto = st.sidebar.text_input(f"{col} contiene…", "")
            if texto:
                df_filtrado = df_filtrado[df_filtrado[col].astype(str).str.contains(texto, case=False, na=False)]

st.dataframe(df_filtrado, use_container_width=True, height=320)
st.download_button("⬇ Descargar tabla filtrada (CSV)", df_filtrado.to_csv(index=False).encode("utf-8"),
                    file_name="explorador_filtrado.csv", mime="text/csv")

# ---------------------------------------------------------------------------
# 3) Agrupar y agregar
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Agrupar y agregar")

cols_categ = [c for c in df_filtrado.columns if not pd.api.types.is_numeric_dtype(df_filtrado[c]) or df_filtrado[c].nunique() <= 60]
cols_num = [c for c in df_filtrado.columns if pd.api.types.is_numeric_dtype(df_filtrado[c])]

c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
with c1:
    group_cols = st.multiselect("Agrupar por", cols_categ, default=(["region_nombre"] if "region_nombre" in cols_categ else cols_categ[:1]))
with c2:
    default_idx = next((i for i, c in enumerate(cols_num) if not c.endswith("_id")), 0) if cols_num else None
    value_col = st.selectbox("Columna a agregar", cols_num, index=default_idx)
with c3:
    func = st.selectbox("Función", ["sum", "mean", "median", "count", "min", "max"])
with c4:
    top_n = st.number_input("Mostrar top N (0 = todos)", min_value=0, value=0, step=1)

if group_cols and value_col:
    agg = df_filtrado.groupby(group_cols, dropna=False)[value_col].agg(func).reset_index()
    agg = agg.sort_values(value_col, ascending=False)
    if top_n:
        agg = agg.head(int(top_n))

    st.dataframe(agg, use_container_width=True)
    st.download_button("⬇ Descargar agregado (CSV)", agg.to_csv(index=False).encode("utf-8"),
                        file_name="explorador_agregado.csv", mime="text/csv")

    if len(group_cols) <= 2 and len(agg) <= 200:
        if len(group_cols) == 1:
            fig = px.bar(agg, x=group_cols[0], y=value_col, color_discrete_sequence=[CATEGORICAL[0]])
        else:
            fig = px.bar(agg, x=group_cols[0], y=value_col, color=group_cols[1], barmode="group",
                         color_discrete_sequence=CATEGORICAL)
        fig.update_layout(**PLOTLY_LAYOUT, title=f"{func}({value_col}) por {', '.join(group_cols)}")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DL_CONFIG)
    else:
        st.caption("Demasiadas categorías o dimensiones para graficar automáticamente — usa la tabla o descarga el CSV.")
else:
    st.info("Elige al menos una columna para agrupar y una columna numérica para agregar.")
