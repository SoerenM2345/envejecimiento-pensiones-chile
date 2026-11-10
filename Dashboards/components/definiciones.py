"""Bloque «Definiciones y fórmulas» que va antes de los gráficos de una descomposición (KPI 1.1 y KPI 2.1).
Cada pieza lleva su pregunta, su fórmula con el numerador y el denominador escritos, lo que no mide y qué razones caen en ella; después, un
ejemplo con cifras reales y una tabla de términos parecidos que no hay que confundir. Sin lectura de archivos: recibe todo ya armado."""
import pandas as pd
import streamlit as st
from utils import es_cl


def _md(texto: str):
    st.markdown(es_cl(texto).replace("$", "\\$"))


def _tabla(df: pd.DataFrame):
    """st.table interpreta markdown: dos «$» en una celda abren una fórmula y deforman el texto entre ellos; la entidad HTML lo evita."""
    esc = lambda v: v.replace("$", "&#36;") if isinstance(v, str) else v
    st.table(df.map(esc).rename(index=esc))


def bloque_definiciones(titulo: str, intro: str, formula: str, piezas: list, confusiones: pd.DataFrame, ejemplo_titulo: str = "",
                        ejemplo: pd.DataFrame = None, ejemplo_nota: str = "", clave: str = ""):
    """piezas = [dict(numero, nombre, pregunta, formula (LaTeX), terminos (lista de textos), no_mide, razones)]; confusiones y ejemplo son
    DataFrames de texto con el primer campo como índice. Se muestra abierto (se puede cerrar) para que se lea antes de los gráficos."""
    with st.expander(titulo, expanded=True):
        _md(intro)
        st.latex(formula)
        for col, p in zip(st.columns(len(piezas)), piezas):
            with col.container(border=True):
                _md(f"**{p['numero']}. {p['nombre']}**")
                _md(f"*{p['pregunta']}*")
                st.latex(p["formula"])
                _md("\n".join(f"- {t}" for t in p["terminos"]))
                _md(f"**Qué no mide:** {p['no_mide']}")
                _md(f"**Qué razones caen aquí:** {p['razones']}")
        if ejemplo is not None:
            _md(f"**{ejemplo_titulo}**")
            _tabla(ejemplo)
            if ejemplo_nota:
                _md(ejemplo_nota)
        _md("**No confundir con**")
        _tabla(confusiones)
