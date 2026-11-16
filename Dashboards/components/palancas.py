"""KPI 1.1, cierre: «¿Qué puede hacer una administradora y qué le corresponde al Estado?» (Scripts/31 -> kpi_cobertura_palancas.csv).
Tabla de palancas ordenada por efecto y por cuántas personas alcanzan; el alcance de la administradora y el impacto son un juicio del equipo (columna «Respaldo»)."""
import pandas as pd
import streamlit as st
from utils import load_csv, es_cl
from utils import subtitulo_visible as _subtitulo_visible


def _millones(x: float) -> str:
    return es_cl(f"{x / 1e6:.2f}") + " millones"


def render_palancas():
    st.divider()
    st.markdown("#### ¿Qué puede hacer una administradora y qué le corresponde al Estado?")
    d = load_csv("kpi_cobertura_palancas.csv")
    suma = d[d.efecto == "Suma personas"]
    directas = d[d.alcance_afp == "Directo"]
    grandes = suma[suma.alcance_afp != "Directo"].sort_values("personas", ascending=False).head(3)
    cobranza = suma[suma.alcance_afp == "Directo"].iloc[0]
    _subtitulo_visible(
        f"Qué muestra: {len(d)} palancas frente a la cobertura estancada: {len(suma)} que suman personas a la base y {len(d) - len(suma)} que protegen a quienes ya cotizan. Solo {len(directas)} de las {len(d)} dependen "
        f"directamente de la administradora y de ellas solo la cobranza suma personas ({_millones(cobranza.personas)}, y no todas). Las tres que alcanzan a más personas "
        f"({', '.join(grandes.palanca.str.lower())}) pasan por el Estado, los empleadores y el mercado laboral. La reforma de 2025 sube cuánto se cotiza, no cuántos cotizan.")
    t = pd.DataFrame({
        "Palanca": d.palanca, "Qué es": d.que_es, "Quién actúa": d.actor, "Alcance de la administradora": d.alcance_afp,
        "A quiénes alcanza": d.grupo + " (" + d.personas.map(_millones) + ")", "Efecto": d.efecto, "Impacto": d.impacto, "Respaldo": d.respaldo,
    }).set_index("Palanca")
    st.table(t.map(es_cl))
    st.caption(es_cl(
        "Fuente: Subsecretaría de Previsión Social, Nota Técnica de la Ley 21.735 (secciones 3.1.4, 5 y 6); Asociación de AFP, Hoja de Ruta 555 (2023) y Propuestas de la Mesa de Formalidad Laboral (2024); "
        "personas de kpi_cobertura_composicion*.csv (diciembre de 2024, Censo 2024). **El alcance de la administradora y el impacto son un juicio del equipo**, no una medición: no hay estimaciones del "
        "efecto de estas palancas. Los grupos se superponen (parte de los informales son independientes) y por eso no se suman. Las propuestas del gremio se citan, no se evalúan. "
        "Los independientes sin cotizar son los ocupados independientes del Censo menos los cotizantes independientes de la Superintendencia: orden de magnitud, porque las dos fuentes clasifican distinto "
        "(los honorarios, que pagan una vez al año en la declaración de renta, figuran aquí como no cotizantes)."))
