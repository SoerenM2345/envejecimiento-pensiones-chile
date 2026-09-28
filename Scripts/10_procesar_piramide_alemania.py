"""
Procesa la base de datos de la Bevölkerungsvorausberechnung (Destatis, proyeccion
de poblacion oficial de Alemania) para extraer el "Basisjahr" 2024 -- el ultimo
anio de poblacion real (no proyectada) -- por edad simple y sexo, y dejarlo listo
para compararlo con la piramide del Censo 2024 de Chile en el dashboard.

Fuente: Data raw/_external/16_bevoelkerungsvorausberechnung_daten.csv
  - Variante=0 es el unico valor con anios 1950-2024 (datos historicos reales);
    las variantes 1-29 son hipotesis de proyeccion 2025-2070 y no se usan aqui.
  - mw='m' (mannlich/hombres), 'w' (weiblich/mujeres).
  - Bev_X_Y = poblacion con edad exacta X (en miles, con coma decimal); la
    ultima columna Bev_99_100 es "99 anios y mas" (abierta), analoga al 85+
    con que el Censo 2024 chileno top-codea su piramide de edad simple.

Salida: alemania_piramide_edad_simple_2024.csv -> anio x edad x sexo x poblacion
(edad 0-99, sexo H/M, poblacion en personas).
"""
import pandas as pd
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "Data raw" / "_external"
OUT = Path(__file__).resolve().parent.parent / "Data processed"
OUT.mkdir(parents=True, exist_ok=True)

SRC = RAW / "16_bevoelkerungsvorausberechnung_daten.csv"

df = pd.read_csv(SRC, sep=";", decimal=",")
basisjahr = df[(df["Variante"] == 0) & (df["Simulationsjahr"] == 2024)].copy()

edad_cols = [c for c in basisjahr.columns if c.startswith("Bev_")]
# "Bev_X_Y" -> edad = X (edad exacta cumplida; Bev_99_100 queda como edad 99 = "99 y mas")
edad_de_col = {c: int(c.split("_")[1]) for c in edad_cols}

largo = basisjahr.melt(id_vars=["mw"], value_vars=edad_cols, var_name="col", value_name="poblacion_miles")
largo["edad"] = largo["col"].map(edad_de_col)
largo["sexo"] = largo["mw"].map({"m": "H", "w": "M"})
largo["anio"] = 2024
largo["poblacion"] = (largo["poblacion_miles"] * 1000).round().astype(int)

piramide = largo[["anio", "edad", "sexo", "poblacion"]].sort_values(["sexo", "edad"])
piramide.to_csv(OUT / "alemania_piramide_edad_simple_2024.csv", index=False)

print("Total Alemania 2024 (Basisjahr, Destatis):", f"{piramide['poblacion'].sum():,}".replace(",", "."))
print(piramide.groupby("sexo")["poblacion"].sum())
print("Escrito en:", OUT / "alemania_piramide_edad_simple_2024.csv")
