"""Tarjeta de KPI del modo final: definición + fórmula + estado + gráfico (o aviso de data pendiente).
Los KPIs vienen de config/kpis.yaml (sección `kpis_presentacion`)."""
from typing import Callable, Optional
import streamlit as st
import yaml
from utils import ROOT

STATUS_LABEL = {
    "live": ("🟢", "Calculado con datos reales"),
    "partial": ("🟡", "Calculado en parte"),
    "pending": ("⚪", "Pendiente de datos"),
}


@st.cache_data
def load_presentation_kpis() -> dict:
    with open(ROOT / "config" / "kpis.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return {k["id"]: k for k in cfg["kpis_presentacion"]}


def kpi_card(kpi_id: str, render: Optional[Callable[[], None]] = None):
    """Dibuja la tarjeta del KPI `kpi_id`. `render` dibuja el contenido cuando hay datos
    (status live/partial); si el KPI está pendiente, se muestra la definición y qué falta."""
    kpi = load_presentation_kpis()[kpi_id]
    icon, status_text = STATUS_LABEL[kpi["status"]]

    with st.container(border=True):
        st.subheader(f"{kpi['id']} · {kpi['nombre']}")
        st.caption(f"{icon} {status_text} · {kpi['objetivo']}")
        st.markdown(kpi["descripcion"])
        st.code(kpi["formula"], language=None)

        if kpi["status"] == "pending" or render is None:
            if kpi.get("pendiente_motivo"):
                st.info(f"**Pendiente.** {kpi['pendiente_motivo']}")
            else:
                st.info("**Pendiente de datos.** Para calcular este KPI falta:\n\n"
                        + "\n".join(f"- {d}" for d in kpi.get("datos_faltantes", ["(sin detalle)"])))
        else:
            render()
        if kpi.get("caveat"):
            st.caption(f"⚠️ {kpi['caveat']}")
