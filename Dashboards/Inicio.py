"""Entry point del dashboard: `cd Dashboards && streamlit run Inicio.py`.

Dos modos (ver utils.mode_toggle):
  - final (por defecto): problema + los 6 KPIs de la presentación, en final_pages/.
  - dev (toggle del sidebar o ?mode=dev): además, todas las páginas de análisis en pages/.
"""
import streamlit as st
from utils import mode_toggle

st.set_page_config(
    page_title="Envejecimiento demográfico y pensiones — Chile",
    page_icon="👴",
    layout="wide",
)
# Con st.navigation la config de página vive solo aquí; las páginas llaman a utils.page_config(), que queda en no-op.
st.session_state["_nav_active"] = True

mode = mode_toggle()

final_pages = [
    st.Page("final_pages/resumen.py", title="Resumen", icon="📌", url_path="resumen", default=True),
    st.Page("final_pages/problema.py", title="Problema", icon="🔎", url_path="problema"),
    st.Page("final_pages/objetivo1.py", title="Objetivo 1: base activa", icon="🎯", url_path="objetivo-1"),
    st.Page("final_pages/objetivo2.py", title="Objetivo 2: costo por cliente", icon="💰", url_path="objetivo-2"),
    st.Page("final_pages/fuentes.py", title="Fuentes y método", icon="📚", url_path="fuentes"),
]
nav = {"Dashboard": final_pages}

if mode == "dev":
    nav["Modo desarrollador"] = [
        st.Page("pages/0_🏠_Panorama_general.py", title="Panorama general", icon="🏠", url_path="dev-panorama"),
        st.Page("pages/1_🔍_Explorador_de_datos.py", title="Explorador de datos", icon="🔍", url_path="dev-explorador"),
        st.Page("pages/2_🗺️_Mapas.py", title="Mapas", icon="🗺️", url_path="dev-mapas"),
        st.Page("pages/3_📊_Piramides.py", title="Pirámides", icon="📊", url_path="dev-piramides"),
        st.Page("pages/4_💰_Pensiones_y_Salud.py", title="Pensiones y salud", icon="💰", url_path="dev-pensiones-salud"),
        st.Page("pages/5_🏙️_Socioeconomico.py", title="Socioeconómico", icon="🏙️", url_path="dev-socioeconomico"),
        st.Page("pages/6_📋_Politicas.py", title="Políticas", icon="📋", url_path="dev-politicas"),
        st.Page("pages/7_🧪_Estado_de_datos.py", title="Estado de datos y KPIs", icon="🧪", url_path="dev-estado-datos"),
    ]

st.navigation(nav).run()
