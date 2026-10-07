"""Estado de datos y KPIs (modo desarrollador): inventario de archivos y estado de los 6 KPIs de la presentación."""
import os
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st
from utils import DATA_PROCESSED, ROOT, page_config
from components.kpi_card import load_presentation_kpis, STATUS_LABEL

page_config(page_title="Estado de datos", page_icon="🧪")
st.title("🧪 Estado de datos y KPIs")

# --- KPIs de la presentación -------------------------------------------------
st.subheader("KPIs de la presentación")
kpis = load_presentation_kpis()
rows = []
for k in kpis.values():
    icon, text = STATUS_LABEL[k["status"]]
    rows.append({
        "KPI": f"{k['id']} {k['nombre']}",
        "Estado": f"{icon} {text}",
        "Archivos": ", ".join(k.get("archivo", [])),
        "Falta / caveat": k.get("pendiente_motivo") or "; ".join(k.get("datos_faltantes", [])) or k.get("caveat", ""),
    })
st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
conteo = pd.Series([k["status"] for k in kpis.values()]).value_counts()
st.caption(" · ".join(f"{STATUS_LABEL[s][0]} {n} {s}" for s, n in conteo.items()))

# --- Inventario ---------------------------------------------------------------
@st.cache_data
def inventario(carpeta: str) -> pd.DataFrame:
    base = ROOT / carpeta
    out = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d != "__pycache__")  # no entrar a .venv
        for name in sorted(filenames):
            p = Path(dirpath) / name
            if name.startswith(".") or name == "README.md":
                continue
            fila = {"Archivo": str(p.relative_to(base)), "MB": round(p.stat().st_size / 1e6, 2),
                    "Modificado": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d")}
            if p.suffix == ".csv" and p.stat().st_size < 50e6:
                with open(p, encoding="utf-8", errors="replace") as f:
                    header = f.readline()
                    sep = ";" if header.count(";") > header.count(",") else ","  # Destatis usa ';'
                    fila["Columnas"] = len(header.rstrip("\n").split(sep))
                    fila["Filas"] = sum(1 for _ in f)
            out.append(fila)
    return pd.DataFrame(out)

st.subheader("Data processed")
st.dataframe(inventario("Data processed"), hide_index=True, use_container_width=True)
st.subheader("Data raw")
st.caption("Se omiten el entorno virtual y los archivos ocultos. Los CSV pesados no se leen.")
st.dataframe(inventario("Data raw"), hide_index=True, use_container_width=True)
