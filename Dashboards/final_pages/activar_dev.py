"""Entrada visible en el menú lateral para activar el modo desarrollador (en modo final)."""
import streamlit as st


def _activar():
    # Se ejecuta como callback, antes de que se instancie el toggle del sidebar: aquí sí se puede cambiar su valor.
    st.session_state["dev_mode"] = True
    st.query_params["mode"] = "dev"


st.title("🛠️ Modo desarrollador")
st.markdown(
    "El modo desarrollador agrega al menú lateral todas las páginas de análisis y exploración:\n\n"
    "- **Explorador de datos:** elige cualquier tabla de `Data processed/`, cruza dos fuentes, filtra y agrega (suma, promedio, mediana, conteo, mínimo, máximo).\n"
    "- **Mapas, Pirámides, Pensiones y salud, Socioeconómico, Políticas** y el **Panorama general**.\n"
    "- **Estado de datos y KPIs:** inventario de archivos y estado de los 6 KPIs.\n\n"
    "Para volver al dashboard final, apaga el interruptor «Modo desarrollador» del menú lateral."
)
st.button("Activar modo desarrollador", type="primary", on_click=_activar)
st.caption("También puedes abrir la app directamente en este modo con `http://localhost:8501/?mode=dev`.")
