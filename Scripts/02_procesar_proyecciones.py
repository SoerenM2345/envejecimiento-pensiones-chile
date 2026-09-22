"""
Procesa 'Estimaciones y proyecciones de poblacion 1992-2070 (base 2024)' del INE
(nivel PAIS, edad simple 0-100, sexo H/M, FECHA=1 de enero o 30 de junio de
cada anio) y produce:

  1. proyeccion_pais_edad_sexo.csv   -> long: anio x edad x sexo x poblacion
     (solo el corte de mitad de anio 30/6, un dato por anio -> sirve para
     piramides comparativas 2024 vs 2035/2050/2070)
  2. proyeccion_envejecimiento_pais.csv -> anio x indicadores de envejecimiento
     nacionales (serie 1992-2070) para graficar la evolucion y proyectar la
     presion futura sobre salud y pensiones.
"""
import pandas as pd
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "Data raw"
OUT = Path(__file__).resolve().parent.parent / "Data processed"
OUT.mkdir(parents=True, exist_ok=True)

SRC = RAW / "estimaciones-y-proyecciones-de-población-1992-2070_base-2024_base-de-datos.xlsx"

df = pd.read_excel(SRC)
df.columns = [c.strip() for c in df.columns]
df["FECHA"] = pd.to_datetime(df["FECHA"], format="%d/%m/%Y")
df["ANIO"] = df["FECHA"].dt.year
df["SEXO"] = df["SEXO"].str.strip()

# Nos quedamos con el corte de mitad de anio (30-jun), que es el estandar de
# stock de poblacion que usa el INE para sus indicadores anuales; evita
# duplicar cada anio con dos filas (1-ene y 30-jun).
df_mid = df[df["FECHA"].dt.month == 6].copy()

# ---------------------------------------------------------------------------
# 1) Piramide por anio x edad x sexo (formato largo, listo para graficar)
# ---------------------------------------------------------------------------
piramide = df_mid[["ANIO", "EDAD", "SEXO", "POBLACION"]].rename(
    columns={"ANIO": "anio", "EDAD": "edad", "SEXO": "sexo", "POBLACION": "poblacion"}
)
piramide.to_csv(OUT / "proyeccion_pais_edad_sexo.csv", index=False)

# ---------------------------------------------------------------------------
# 2) Indicadores de envejecimiento nacionales por anio (serie 1992-2070)
#    EDAD tope 100 = "100 y mas" (sin top-coding relevante aqui).
# ---------------------------------------------------------------------------
def bucket(edad):
    if edad <= 14:
        return "0_14"
    if edad <= 64:
        return "15_64"
    return "65_mas"


df_mid["grupo"] = df_mid["EDAD"].apply(bucket)
df_mid["es_80_mas"] = df_mid["EDAD"] >= 80

rows = []
for anio, g in df_mid.groupby("ANIO"):
    pob_total = g["POBLACION"].sum()
    pob_0_14 = g.loc[g["grupo"] == "0_14", "POBLACION"].sum()
    pob_15_64 = g.loc[g["grupo"] == "15_64", "POBLACION"].sum()
    pob_65_mas = g.loc[g["grupo"] == "65_mas", "POBLACION"].sum()
    pob_80_mas = g.loc[g["es_80_mas"], "POBLACION"].sum()
    rows.append({
        "anio": anio,
        "pob_total": pob_total,
        "pob_0_14": pob_0_14,
        "pob_15_64": pob_15_64,
        "pob_65_mas": pob_65_mas,
        "pob_80_mas": pob_80_mas,
        "pct_65_mas": round(100 * pob_65_mas / pob_total, 2),
        "pct_0_14": round(100 * pob_0_14 / pob_total, 2),
        "pct_80_mas": round(100 * pob_80_mas / pob_total, 2),
        "indice_envejecimiento": round(100 * pob_65_mas / pob_0_14, 2),
        "indice_dependencia_total": round(100 * (pob_0_14 + pob_65_mas) / pob_15_64, 2),
        "indice_dependencia_vejez": round(100 * pob_65_mas / pob_15_64, 2),
    })

serie = pd.DataFrame(rows).sort_values("anio")
serie.to_csv(OUT / "proyeccion_envejecimiento_pais.csv", index=False)

print("Anios cubiertos:", serie["anio"].min(), "-", serie["anio"].max())
print(serie[serie["anio"].isin([1992, 2002, 2017, 2024, 2030, 2035, 2040, 2050, 2060, 2070])].to_string(index=False))
print("\nEscrito en:", OUT)
