"""
Series de la Superintendencia de Pensiones que faltaban en Data processed (solo las usa el modo desarrollador):

  - cotizantes_tipo_sexo.xls  (anual 1985-2025, cotizantes por tipo de afiliado y sexo)
  - cotizantes_region_afp.xls (mensual dic-1993 a jun-2026, cotizantes por region x AFP)
  - cotizaciones_totales.xls  (mensual ene-1984 a jul-2026, numero de COTIZACIONES por AFP; no son pesos)

Fuente: Data raw/development sources/

Salidas (Data processed/), en formato largo:
  cotizantes_por_tipo_sexo.csv    anio, tipo (Dependientes / Independientes / Afiliados voluntarios / Total),
                                  sexo (Total / Masculino / Femenino / Sin información), cotizantes
  cotizantes_por_region_afp.csv   fecha, anio, afp, region_label, region_id, region_nombre, cotizantes
  cotizaciones_por_afp.csv        fecha, anio, afp, cotizaciones

Notas:
  - cotizantes_por_tipo_sexo: en 1985 el archivo no desglosa por tipo (solo Total); esos años quedan solo en tipo = Total.
    Las filas sexo = Total de cada tipo son subtotales: no sumarlas junto con Masculino/Femenino.
  - cotizantes_por_region_afp: incluye filas afp = 'Sistema' (total de todas las AFP) y region_label = 'TOTAL' / 'Sin información'
    (region_id vacío). Filtrar antes de sumar para no contar dos veces. Los cotizantes son afiliados con pago del mes de
    devengamiento anterior, solo no pensionados.
  - cotizaciones_por_afp: cuenta cotizaciones de cualquier período, no personas ni pesos (no sirve como monto del KPI 1.3).
    Cada junio sube por los independientes obligados a cotizar, que paga la Tesorería. El archivo repite columnas de una
    misma AFP en períodos sucesivos (PlanVital x3, Qualitas x2): se unen bajo un solo nombre. 'SISTEMA' es el total y
    coincide con la suma de las AFP (se verifica al correr).
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEV = ROOT / "Data raw" / "development sources"
OUT = ROOT / "Data processed"
OUT.mkdir(parents=True, exist_ok=True)

REGION_ALIAS = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
    "IX": 9, "X": 10, "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15, "XVI": 16,
}
REGION_NAME = {
    1: "Tarapacá", 2: "Antofagasta", 3: "Atacama", 4: "Coquimbo", 5: "Valparaíso",
    6: "O'Higgins", 7: "Maule", 8: "Biobío", 9: "La Araucanía", 10: "Los Lagos",
    11: "Aysén", 12: "Magallanes", 13: "Metropolitana", 14: "Los Ríos",
    15: "Arica y Parinacota", 16: "Ñuble",
}


def a_numero(v):
    """Número o None: el archivo usa '-' para 'no existía' y '' para vacío."""
    if pd.isna(v):
        return None
    if isinstance(v, str):
        v = v.strip()
        if v in ("", "-"):
            return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# 1) cotizantes_tipo_sexo.xls
# ---------------------------------------------------------------------------
print("1) cotizantes_tipo_sexo.xls ...")
df = pd.read_excel(DEV / "cotizantes_tipo_sexo.xls", header=None)
anios = df.iloc[5, 1:42].astype(int).tolist()
TIPOS = {"DEPENDIENTES": "Dependientes", "INDEPENDIENTES": "Independientes",
         "AFILIADOS VOLUNTARIOS": "Afiliados voluntarios", "TOTAL": "Total"}
SEXOS = {"masculino": "Masculino", "femenino": "Femenino", "sin información": "Sin información"}
filas, tipo = [], None
for r in range(7, 23):
    etiqueta = df.iloc[r, 0]
    if pd.isna(etiqueta):
        continue
    clave = str(etiqueta).strip()
    if clave.upper() in TIPOS:
        tipo, sexo = TIPOS[clave.upper()], "Total"
    elif clave.lower() in SEXOS:
        sexo = SEXOS[clave.lower()]
    else:
        raise ValueError(f"fila inesperada en cotizantes_tipo_sexo.xls: {clave!r}")
    for anio, v in zip(anios, df.iloc[r, 1:42]):
        v = a_numero(v)
        if v is not None:
            filas.append({"anio": anio, "tipo": tipo, "sexo": sexo, "cotizantes": int(v)})
tipo_sexo = pd.DataFrame(filas)
tipo_sexo.to_csv(OUT / "cotizantes_por_tipo_sexo.csv", index=False)

# Validación: Total = Dependientes + Independientes + Voluntarios (donde hay desglose) y Total = Masculino + Femenino + S/I
t = tipo_sexo[tipo_sexo.sexo == "Total"].pivot(index="anio", columns="tipo", values="cotizantes")
desg = t.dropna(subset=["Dependientes"])
dif_tipo = (desg["Total"] - desg[["Dependientes", "Independientes", "Afiliados voluntarios"]].fillna(0).sum(axis=1)).abs().max()
s = tipo_sexo[(tipo_sexo.tipo == "Total") & (tipo_sexo.sexo != "Total")].groupby("anio").cotizantes.sum()
dif_sexo = (t["Total"] - s).abs().max()
print(f"  filas: {len(tipo_sexo)} | anios: {tipo_sexo.anio.min()}-{tipo_sexo.anio.max()} | "
      f"dif. máx. Total vs suma de tipos: {dif_tipo:.0f} | vs suma de sexos: {dif_sexo:.0f}")

# ---------------------------------------------------------------------------
# 2) cotizantes_region_afp.xls
# ---------------------------------------------------------------------------
print("2) cotizantes_region_afp.xls ...")
df = pd.read_excel(DEV / "cotizantes_region_afp.xls", header=None)
cabecera = df.iloc[1].tolist()  # PERIODO, AFP, 'I\n Tarapacá', ..., 'Sin información', 'TOTAL'
regiones = {}  # columna -> (region_label, region_id)
for col in range(2, len(cabecera)):
    texto = str(cabecera[col]).strip()
    token = re.split(r"\s+", texto)[0].upper()
    rid = REGION_ALIAS.get(token)
    if rid:
        regiones[col] = (token, rid)
    else:
        regiones[col] = ("TOTAL" if token == "TOTAL" else "Sin información", None)
filas = []
for r in range(2, len(df)):
    fecha, afp = df.iloc[r, 0], df.iloc[r, 1]
    if pd.isna(afp) or pd.isna(pd.to_datetime(fecha, errors="coerce")):
        continue  # notas al pie
    fecha = pd.to_datetime(fecha)
    for col, (label, rid) in regiones.items():
        v = a_numero(df.iloc[r, col])
        if v is None:
            continue
        filas.append({"fecha": fecha.date().isoformat(), "anio": fecha.year, "afp": str(afp).strip(),
                      "region_label": label, "region_id": rid, "region_nombre": REGION_NAME.get(rid),
                      "cotizantes": int(v)})
reg_afp = pd.DataFrame(filas)
reg_afp["region_id"] = reg_afp["region_id"].astype("Int64")
reg_afp.to_csv(OUT / "cotizantes_por_region_afp.csv", index=False)

# Validación: regiones + sin información = TOTAL de cada fila afp x fecha
piv = reg_afp.assign(es_total=reg_afp.region_label.eq("TOTAL")).groupby(["fecha", "afp", "es_total"]).cotizantes.sum().unstack("es_total")
dif = (piv[True] - piv[False]).abs()
print(f"  filas: {len(reg_afp)} | meses: {reg_afp.fecha.nunique()} | rango: {reg_afp.fecha.min()} a {reg_afp.fecha.max()} | "
      f"AFP: {reg_afp.afp.nunique()} | filas afp x mes con regiones != TOTAL: {(dif > 0).sum()} (dif. máx. {dif.max():.0f})")

# ---------------------------------------------------------------------------
# 3) cotizaciones_totales.xls
# ---------------------------------------------------------------------------
print("3) cotizaciones_totales.xls ...")
df = pd.read_excel(DEV / "cotizaciones_totales.xls", header=None)
cabecera = [str(c).strip().title() for c in df.iloc[1].tolist()]
cuerpo = df.iloc[2:].copy()
cuerpo[0] = pd.to_datetime(cuerpo[0], errors="coerce")
cuerpo = cuerpo[cuerpo[0].notna()]
filas = []
for col in range(1, len(cabecera)):
    nombre = "Sistema" if cabecera[col] == "Sistema" else cabecera[col]
    for fecha, v in zip(cuerpo[0], cuerpo[col]):
        v = a_numero(v)
        if v is None:
            continue
        filas.append({"fecha": fecha.date().isoformat(), "anio": fecha.year, "afp": nombre, "cotizaciones": int(v)})
cot = pd.DataFrame(filas)
# una misma AFP repetida en columnas de períodos sucesivos: no deben solaparse
dup = cot.duplicated(["fecha", "afp"], keep=False)
assert not dup.any(), cot[dup].head()
cot.to_csv(OUT / "cotizaciones_por_afp.csv", index=False)

piv = cot.assign(es_sistema=cot.afp.eq("Sistema")).groupby(["fecha", "es_sistema"]).cotizaciones.sum().unstack("es_sistema")
print(f"  filas: {len(cot)} | meses: {cot.fecha.nunique()} | rango: {cot.fecha.min()} a {cot.fecha.max()} | "
      f"AFP: {cot[cot.afp != 'Sistema'].afp.nunique()} | dif. máx. Sistema vs suma de AFP: {(piv[True] - piv[False]).abs().max():.0f}")

print("\nListo. Archivos escritos en:", OUT)
