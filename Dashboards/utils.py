"""Utilidades compartidas por todas las páginas del dashboard: rutas, carga
cacheada de datos, y la paleta de color de referencia (dataviz skill)."""
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = ROOT / "Data processed"
GEO = DATA_PROCESSED / "geo"

# --- paleta de referencia --------------------------------------------------
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
MAGENTA = "#e87ba4"
GREEN = "#008300"
VIOLET = "#4a3aa7"
RED = "#e34948"
CATEGORICAL = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED]

SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#184f95", "#0d366b"]

INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
SURFACE = "#fcfcfb"

MACROZONA = {
    "Arica y Parinacota": "Norte Grande", "Tarapacá": "Norte Grande", "Antofagasta": "Norte Grande",
    "Atacama": "Norte Chico", "Coquimbo": "Norte Chico",
    "Valparaíso": "Centro", "Metropolitana": "Centro", "O'Higgins": "Centro",
    "Maule": "Centro-Sur", "Ñuble": "Centro-Sur", "Biobío": "Centro-Sur", "La Araucanía": "Centro-Sur",
    "Los Ríos": "Sur", "Los Lagos": "Sur",
    "Aysén": "Austral", "Magallanes": "Austral",
}
MACROZONA_ORDER = ["Norte Grande", "Norte Chico", "Centro", "Centro-Sur", "Sur", "Austral"]

REGION_ORDER = [
    "Tarapacá", "Antofagasta", "Atacama", "Coquimbo", "Valparaíso", "O'Higgins",
    "Maule", "Ñuble", "Biobío", "La Araucanía", "Los Ríos", "Los Lagos", "Aysén",
    "Magallanes", "Metropolitana", "Arica y Parinacota",
]

# Config para st.plotly_chart: hace que el botón de cámara (descargar PNG) del
# toolbar exporte a 4x la resolución de pantalla en vez de la imagen de baja
# calidad por defecto (util para figuras/anexos).
PLOTLY_DL_CONFIG = {"toImageButtonOptions": {"format": "png", "scale": 4}}

PLOTLY_LAYOUT = dict(
    font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=INK_PRIMARY, size=13),
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    margin=dict(l=10, r=10, t=50, b=10),
    xaxis=dict(gridcolor=GRIDLINE, zeroline=False),
    yaxis=dict(gridcolor=GRIDLINE, zeroline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_PROCESSED / name)


@st.cache_data
def list_processed_csvs() -> list[str]:
    return sorted(p.name for p in DATA_PROCESSED.glob("*.csv"))


@st.cache_data
def load_geojson(name: str):
    import json
    with open(GEO / name, encoding="utf-8") as f:
        return json.load(f)


# Normaliza nombres de columnas equivalentes entre archivos para que el
# Explorador pueda cruzarlos ("mezclar fuentes") sin fricción.
KEY_ALIASES = {
    "region_id": "region_id", "region": "region_id",
    "comuna_id": "comuna_id", "comuna": "comuna_id",
    "region_nombre_corto": "region_nombre", "region_nombre": "region_nombre",
    "comuna_nombre": "comuna_nombre",
    "anio": "anio", "año": "anio",
}


def standardize_keys(df: pd.DataFrame) -> pd.DataFrame:
    rename = {c: KEY_ALIASES[c] for c in df.columns if c in KEY_ALIASES and KEY_ALIASES[c] != c}
    return df.rename(columns=rename)


def lighten(hex_color: str, ratio: float = 0.55) -> str:
    """Mezcla un color hex con blanco (ratio=0 -> igual, ratio=1 -> blanco).
    Util para distinguir subgrupos (p.ej. tramos de edad) dentro de la misma serie."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r2 = round(r + (255 - r) * ratio)
    g2 = round(g + (255 - g) * ratio)
    b2 = round(b + (255 - b) * ratio)
    return f"#{r2:02x}{g2:02x}{b2:02x}"


def kpi_card_row(cols_data):
    """cols_data: list of (label, value, help) tuples."""
    cols = st.columns(len(cols_data))
    for col, (label, value, help_text) in zip(cols, cols_data):
        col.metric(label, value, help=help_text)
