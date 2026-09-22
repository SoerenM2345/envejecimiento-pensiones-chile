"""
Procesa los informes de la Superintendencia de Pensiones sobre PAGO DE
PENSIONES (stock de pensionados y monto pagado), corte Julio 2026:

  - c1_202607.xlsx -> por Ex Caja de Prevision
  - c2_202607.xlsx -> por Region
  - c3_202607.xlsx -> por Tramo de Edad

Estructura fuente (igual en los 3 archivos): filas = categoria (ex-caja /
region / tramo edad); columnas = 5 tipos de pension (Antiguedad, Vejez,
Invalidez, Ley Especial, Sobrevivencia) x 2 sexos (Hombres, Mujeres) x
2 medidas (Numero de pensionados, Monto pagado en miles de $), mas una
columna "Sin informacion de sexo" y una columna "Total" (num y monto).

Salidas (formato largo):
  - pensiones_pagadas_por_region.csv     (de c2)
  - pensiones_pagadas_por_tramo_edad.csv (de c3)
  - pensiones_pagadas_por_ex_caja.csv    (de c1)

Cada una con columnas: categoria, tipo_pension, sexo, numero_pensionados,
monto_miles_pesos. tipo_pension='Sin información de sexo' se usa para la
columna agregada que no discrimina por sexo (no está desagregada por tipo).
"""
import pandas as pd
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "Data raw"
OUT = Path(__file__).resolve().parent.parent / "Data processed"
OUT.mkdir(parents=True, exist_ok=True)

TIPOS = ["Antigüedad", "Vejez", "Invalidez", "Ley Especial", "Sobrevivencia"]
# columna inicial (1-indexed en la hoja) de cada bloque tipo x sexo x medida
# col 1..20: 5 tipos x (Hombres num,monto, Mujeres num,monto)
# col 21,22: Sin informacion de sexo (num, monto) -- no desagregado por tipo
# col 23,24: Total (num, monto)

REGION_ID = {
    "Tarapacá": 1, "Antofagasta": 2, "Atacama": 3, "Coquimbo": 4, "Valparaíso": 5,
    "Libertador Gral. Bernardo O'Higgins": 6, "Maule": 7, "Biobío": 8,
    "La Araucanía": 9, "Los Lagos": 10,
    "Aysén del Gral. Carlos Ibáñez del Campo": 11,
    "Magallanes y de la Antártica Chilena": 12,
    "Metropolitana de Santiago": 13, "Los Ríos": 14, "Arica y Parinacota": 15,
    "Ñuble": 16,
}


def parse_file(path, categoria_col_name):
    df = pd.read_excel(path, sheet_name=0, header=None)
    rows = []
    for r in range(5, len(df)):
        cat = df.iloc[r, 0]
        if pd.isna(cat):
            continue
        cat = str(cat).strip()
        if cat.lower().startswith(("fuente", "nota")):
            break
        total_num = df.iloc[r, 23]
        if pd.isna(total_num):
            continue

        col = 1
        for tipo in TIPOS:
            for sexo in ("Hombres", "Mujeres"):
                numero = df.iloc[r, col]
                monto = df.iloc[r, col + 1]
                col += 2
                if pd.isna(numero) and pd.isna(monto):
                    continue
                rows.append({
                    categoria_col_name: cat,
                    "tipo_pension": tipo,
                    "sexo": sexo,
                    "numero_pensionados": int(numero) if pd.notna(numero) else 0,
                    "monto_miles_pesos": float(monto) if pd.notna(monto) else 0.0,
                })
        # sin informacion de sexo (cols 21,22 -> index 21,22 since col var now 21)
        sin_info_num = df.iloc[r, 21]
        sin_info_monto = df.iloc[r, 22]
        rows.append({
            categoria_col_name: cat,
            "tipo_pension": "Sin información de tipo/sexo",
            "sexo": "Sin información",
            "numero_pensionados": int(sin_info_num) if pd.notna(sin_info_num) else 0,
            "monto_miles_pesos": float(sin_info_monto) if pd.notna(sin_info_monto) else 0.0,
        })
    return pd.DataFrame(rows)


print("1) c2_202607.xlsx (por región) ...")
c2 = parse_file(RAW / "c2_202607.xlsx", "region_nombre")
c2["region_id"] = c2["region_nombre"].map(REGION_ID)
c2.to_csv(OUT / "pensiones_pagadas_por_region.csv", index=False)
print("   filas:", len(c2), "| categorias:", c2["region_nombre"].nunique())
sin_map = c2[c2["region_id"].isna()]["region_nombre"].unique()
if len(sin_map):
    print("   (sin mapear a region_id, esperado para 'Sin información'):", sin_map)

print("2) c3_202607.xlsx (por tramo de edad) ...")
c3 = parse_file(RAW / "c3_202607.xlsx", "tramo_edad")
c3.to_csv(OUT / "pensiones_pagadas_por_tramo_edad.csv", index=False)
print("   filas:", len(c3), "| categorias:", c3["tramo_edad"].nunique())

print("3) c1_202607.xlsx (por ex caja de previsión) ...")
c1 = parse_file(RAW / "c1_202607.xlsx", "ex_caja")
c1.to_csv(OUT / "pensiones_pagadas_por_ex_caja.csv", index=False)
print("   filas:", len(c1), "| categorias:", c1["ex_caja"].nunique())

# Validacion cruzada: total nacional de pensionados debe coincidir en los 3
for name, df_, cat in [("c1/ex_caja", c1, "ex_caja"), ("c2/region", c2, "region_nombre"), ("c3/tramo_edad", c3, "tramo_edad")]:
    total = df_.loc[df_[cat] != "TOTAL PAIS", "numero_pensionados"].sum() if "TOTAL PAIS" in df_[cat].values else df_["numero_pensionados"].sum()
    print(f"   [{name}] suma total numero_pensionados (todas las filas, ojo con doble conteo si hay fila Total): {df_['numero_pensionados'].sum():,}")

print("\nListo. Archivos escritos en:", OUT)
