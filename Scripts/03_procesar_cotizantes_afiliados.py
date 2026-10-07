"""
Procesa las series historicas de la Superintendencia de Pensiones:

  - cotizantes_edad.xls    (anual 1985-2025, cotizantes por tramo de edad)
  - cotizantes_region.xls  (anual 1985-2025, cotizantes por region)
  - afiliados_region_edad.xls (mensual 1993-2026, afiliados por region x tramo edad)

y los deja en formato largo (tidy) para cruzar con los indicadores de
envejecimiento del censo.

Notas:
  - "Afiliados" = personas con cuenta individual (stock, no necesariamente
    activos). "Cotizantes" = personas que efectivamente cotizaron ese mes/año
    (flujo, subconjunto activo de los afiliados). Ambos son relevantes: el
    envejecimiento de los AFILIADOS anticipa presion futura sobre el sistema,
    mientras que los COTIZANTES actuales financian las pensiones de hoy.
  - Las etiquetas de region cambian de formato entre archivos (numeros
    romanos, 'R. Metrop.', 'R. Metropolitana'); se normalizan a region_id
    1-16 usando el mismo esquema que el Censo (ver region_comuna_lookup.csv).
  - Nuevas regiones (Los Rios=XIV y Arica y Parinacota=XV en 2007-2010,
    Nuble=XVI en 2018) no existen en los anios previos a su creacion: se
    mantienen NaN/ausentes en esos periodos (no es un error de parseo).
"""
import re
import pandas as pd
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "Data raw"
DEV = RAW / "development sources"  # cotizantes_edad.xls y afiliados_region_edad.xls: solo los usan las páginas dev
OUT = Path(__file__).resolve().parent.parent / "Data processed"
OUT.mkdir(parents=True, exist_ok=True)

REGION_ALIAS = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
    "IX": 9, "X": 10, "XI": 11, "XII": 12,
    "RM": 13, "R. METROPOLITANA": 13, "R. METROP.": 13, "METROPOLITANA": 13,
    "XIII": 13,  # usado por afiliados_region_edad.xls en meses recientes (== RM)
    "XIV": 14, "XV": 15, "XVI": 16,
}
REGION_NAME = {
    1: "Tarapacá", 2: "Antofagasta", 3: "Atacama", 4: "Coquimbo", 5: "Valparaíso",
    6: "O'Higgins", 7: "Maule", 8: "Biobío", 9: "La Araucanía", 10: "Los Lagos",
    11: "Aysén", 12: "Magallanes", 13: "Metropolitana", 14: "Los Ríos",
    15: "Arica y Parinacota", 16: "Ñuble",
}


def region_id_from_label(label):
    """Match full label ('RM') or, for newer rows like 'I Tarapacá', just the
    leading roman-numeral token before the region name."""
    key = str(label).strip().upper()
    if key in REGION_ALIAS:
        return REGION_ALIAS[key]
    first_token = key.split(" ")[0] if key else key
    return REGION_ALIAS.get(first_token)


def to_int_or_none(v):
    """Handle blanks/placeholder '-' used for regions that didn't exist yet."""
    if pd.isna(v):
        return None
    if isinstance(v, str):
        v = v.strip()
        if v in ("", "-", "S/I", "n.d."):
            return None
        v = v.replace(".", "").replace(",", "")
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# 1) cotizantes_edad.xls -> anual, por tramo de edad
# ---------------------------------------------------------------------------
print("1) cotizantes_edad.xls ...")
df = pd.read_excel(DEV / "cotizantes_edad.xls", header=None)
years = df.iloc[5, 1:42].astype(int).tolist()
rows = []
for r in range(7, 20):  # Hasta 20 ... Total (13 categorias)
    label = str(df.iloc[r, 0]).strip()
    vals = df.iloc[r, 1:42].tolist()
    for y, v in zip(years, vals):
        v = to_int_or_none(v)
        if v is None:
            continue
        rows.append({"anio": y, "tramo_edad": label, "cotizantes": v})
cot_edad = pd.DataFrame(rows)
cot_edad.to_csv(OUT / "cotizantes_por_edad.csv", index=False)
print("  filas:", len(cot_edad), "| anios:", cot_edad['anio'].min(), '-', cot_edad['anio'].max())

# ---------------------------------------------------------------------------
# 2) cotizantes_region.xls -> anual, por region
# ---------------------------------------------------------------------------
print("2) cotizantes_region.xls ...")
df = pd.read_excel(RAW / "cotizantes_region.xls", header=None)
years = df.iloc[5, 1:42].astype(int).tolist()
rows = []
for r in range(8, 27):  # I..XVI, Sin Informacion, (gap), Total
    label_raw = df.iloc[r, 0]
    if pd.isna(label_raw):
        continue
    label = str(label_raw).strip()
    region_id = region_id_from_label(label)
    vals = df.iloc[r, 1:42].tolist()
    for y, v in zip(years, vals):
        v = to_int_or_none(v)
        if v is None:
            continue
        rows.append({
            "anio": y,
            "region_label": label,
            "region_id": region_id,
            "region_nombre": REGION_NAME.get(region_id),
            "cotizantes": v,
        })
cot_region = pd.DataFrame(rows)
cot_region.to_csv(OUT / "cotizantes_por_region.csv", index=False)
print("  filas:", len(cot_region), "| regiones:", cot_region['region_label'].nunique())

# ---------------------------------------------------------------------------
# 3) afiliados_region_edad.xls -> mensual, por region x tramo edad
# ---------------------------------------------------------------------------
print("3) afiliados_region_edad.xls ...")
df = pd.read_excel(DEV / "afiliados_region_edad.xls", header=None)
tramo_cols = {
    3: "Hasta 20", 4: "20-25", 5: "25-30", 6: "30-35", 7: "35-40", 8: "40-45",
    9: "45-50", 10: "50-55", 11: "55-60", 12: "60-65", 13: "65 y más", 14: "S/I",
}
rows = []
for r in range(2, len(df)):
    fecha = df.iloc[r, 0]
    region_label = df.iloc[r, 1]
    total = to_int_or_none(df.iloc[r, 2])
    if pd.isna(fecha) or pd.isna(region_label) or total is None:
        continue
    try:
        fecha = pd.to_datetime(fecha)
    except Exception:
        continue
    region_id = region_id_from_label(region_label)
    for col, tramo in tramo_cols.items():
        v = to_int_or_none(df.iloc[r, col])
        if v is None:
            continue
        rows.append({
            "fecha": fecha.date().isoformat(),
            "anio": fecha.year,
            "region_label": str(region_label).strip(),
            "region_id": region_id,
            "region_nombre": REGION_NAME.get(region_id),
            "tramo_edad": tramo,
            "afiliados": v,
        })
afiliados = pd.DataFrame(rows)
afiliados.to_csv(OUT / "afiliados_por_region_edad.csv", index=False)
print("  filas:", len(afiliados), "| meses:", afiliados['fecha'].nunique(),
      "| rango:", afiliados['fecha'].min(), '-', afiliados['fecha'].max())

print("\nListo. Archivos escritos en:", OUT)
