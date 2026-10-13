"""
Hojas de DIPRES que el script 13 no usa y que sirven de contexto fiscal para el KPI 2.2 (ratio 2: reservas frente al gasto
previsional) y para el sistema antiguo: pasivos y activos financieros del Gobierno Central y stock de Bonos de Reconocimiento.

Fuente: Data raw/_external/dipres/articles-416517_doc_xls.xlsx (Estadísticas de las Finanzas Públicas 2016-2025, mayo 2026,
cuadros del Sector Público). Hojas: PAFGC, PAFGC%PIB, Bono_Reconocimiento.

Salidas (Data processed/):
  dipres_pasivos_activos_gc.csv   anio, codigo, concepto, nivel (1 = total de rubro, 2 = detalle), unidad, valor
                                  unidad: 'MM$' (millones de pesos corrientes), 'MMUS$' (millones de dólares) o '% PIB'.
                                  Saldos al 31 de diciembre de cada año, 2016-2025.
  bonos_reconocimiento.csv        anio, bonos_liquidados, stock_mm, stock_pct_pib
                                  Bonos de Reconocimiento 1982-2025: N° liquidados en el año y valor actualizado (nominal
                                  reajustado + intereses capitalizados) de los bonos emitidos y no pagados, en MM$ y % PIB.

Notas:
  - En PAFGC el rubro 5 (activos en dólares) agrupa, en la línea 5.3 'Otros', el Fondo de Estabilización Económica y Social, el
    Fondo de Reserva de Pensiones (FRP), el Fondo de Estabilización del Petróleo, el Fondo de Infraestructura y otras
    inversiones en moneda extranjera. El archivo NO separa el FRP: para el saldo del FRP hace falta el informe trimestral del
    fondo de DIPRES, que no está en Data raw.
  - Los rubros en pesos y en dólares están en unidades distintas: no sumar filas de distinta `unidad` (el rubro 7 y el 8 ya
    traen el total convertido, en MM$).
  - El stock de Bonos de Reconocimiento cae de 8.217.112 MM$ (2002) a 49.441 MM$ (2025): es el pasivo del Estado con los
    afiliados que venían del sistema antiguo, y se extingue.
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Data raw" / "_external" / "dipres" / "articles-416517_doc_xls.xlsx"
OUT = ROOT / "Data processed"
OUT.mkdir(parents=True, exist_ok=True)


def lee_pafgc(hoja, unidad_fija=None):
    d = pd.read_excel(SRC, sheet_name=hoja, header=None)
    hdr = next(i for i in range(15) if str(d.iloc[i, 3]).replace(".0", "") == "2016")
    cols = [c for c in range(3, d.shape[1]) if pd.notna(d.iloc[hdr, c])]
    anios = [int(float(d.iloc[hdr, c])) for c in cols]
    filas, unidad_rubro = [], None
    for i in range(hdr + 1, len(d)):
        etiqueta0, etiqueta1 = d.iloc[i, 0], d.iloc[i, 1]
        if str(etiqueta0).strip().lower().startswith("nota"):
            break
        if pd.isna(etiqueta1):
            continue
        if pd.notna(etiqueta0):  # fila de rubro: '1.' | 'PASIVOS EN PESOS' | 'Mill. $'
            codigo, nivel = str(etiqueta0).strip().rstrip("."), 1
            concepto = str(etiqueta1).strip()
            u = str(d.iloc[i, 2]).strip() if pd.notna(d.iloc[i, 2]) else None
            unidad_rubro = {"Mill. $": "MM$", "Mill. US$": "MMUS$"}.get(u, unidad_rubro)
        else:  # detalle: '1.2 Deuda Externa'
            m = re.match(r"^(\d+(?:\.\d+)*)\s+(.*)$", str(etiqueta1).strip())
            codigo, concepto, nivel = (m.group(1), m.group(2), 2) if m else (None, str(etiqueta1).strip(), 2)
        for anio, c in zip(anios, cols):
            v = pd.to_numeric(d.iloc[i, c], errors="coerce")
            if pd.notna(v):
                filas.append({"anio": anio, "codigo": codigo, "concepto": concepto, "nivel": nivel,
                              "unidad": unidad_fija or unidad_rubro, "valor": float(v)})
    return pd.DataFrame(filas)


print("1) PAFGC y PAFGC%PIB ...")
mm = lee_pafgc("PAFGC")
pib = lee_pafgc("PAFGC%PIB", unidad_fija="% PIB")
activos = pd.concat([mm, pib], ignore_index=True)
activos.to_csv(OUT / "dipres_pasivos_activos_gc.csv", index=False)
print("  filas:", len(activos), "| anios:", activos.anio.min(), "-", activos.anio.max(), "| rubros:", activos[activos.nivel == 1].codigo.nunique())

# Validación: rubro 9 (pasivo financiero neto total) = rubro 7 (pasivo bruto) - rubro 8 (activos totales), en MM$
p = mm[(mm.nivel == 1) & (mm.unidad == "MM$")].pivot(index="anio", columns="codigo", values="valor")
print("  dif. máx. rubro 9 vs (7 - 8): {:.0f} MM$".format((p["9"] - (p["7"] - p["8"])).abs().max()))

print("2) Bono_Reconocimiento ...")
b = pd.read_excel(SRC, sheet_name="Bono_Reconocimiento", header=None)
b = b[pd.to_numeric(b[1], errors="coerce").between(1900, 2100)]
bonos = pd.DataFrame({
    "anio": b[1].astype(int),
    "bonos_liquidados": pd.to_numeric(b[2]).astype(int),
    "stock_mm": pd.to_numeric(b[4]),
    "stock_pct_pib": pd.to_numeric(b[5]),
}).reset_index(drop=True)
bonos.to_csv(OUT / "bonos_reconocimiento.csv", index=False)
print("  filas:", len(bonos), "| anios:", bonos.anio.min(), "-", bonos.anio.max(),
      "| stock 2025:", bonos.loc[bonos.anio == 2025, "stock_mm"].iloc[0], "MM$")

print("\nListo. Archivos escritos en:", OUT)
