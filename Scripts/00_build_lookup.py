"""
Build a clean region/provincia/comuna lookup table (with proper Spanish accents)
matching the numeric codes used in the Censo 2024 microdata (region: 1-16 int,
comuna: 5-digit DPA code as int, e.g. 5802 == '05802').

Source: miguelcarrascoq/chile-regiones-provincias-comunas (MySQL dump of the
official DPA - Division Politico Administrativa - codes), cross-checked against
codigos_territoriales.csv (pachadotdev/chilemapas) for completeness (346 comunas).
"""
import re
import csv
from pathlib import Path

RAW_SQL = Path("/tmp/chile_regiones.sql")
OUT = Path(__file__).resolve().parent.parent / "Data processed" / "region_comuna_lookup.csv"

sql = RAW_SQL.read_text(encoding="utf-8")


def parse_block(table_name, sql_text):
    m = re.search(rf"INSERT INTO `{table_name}`.*?VALUES\n(.*?);\n", sql_text, re.S)
    block = m.group(1)
    rows = re.findall(r"\(([^()]*)\)", block)
    parsed = []
    for r in rows:
        # split on commas not inside quotes
        parts = re.findall(r"'((?:[^'\\]|\\.)*)'|(-?\d+)", r)
        vals = []
        for a, b in parts:
            if a != "":
                vals.append(a.replace("\\'", "'"))
            else:
                vals.append(int(b))
        parsed.append(vals)
    return parsed


regiones = {rid: nombre for rid, nombre in parse_block("region", sql)}
provincias = {pid: (nombre, region_id) for pid, nombre, region_id in parse_block("provincia", sql)}
comunas = parse_block("comuna", sql)

# Clean up region display names (keep official but shorter form for charts)
region_short = {
    1: "Tarapacá", 2: "Antofagasta", 3: "Atacama", 4: "Coquimbo",
    5: "Valparaíso", 6: "O'Higgins", 7: "Maule", 8: "Biobío",
    9: "La Araucanía", 10: "Los Lagos", 11: "Aysén", 12: "Magallanes",
    13: "Metropolitana", 14: "Los Ríos", 15: "Arica y Parinacota", 16: "Ñuble",
}

rows_out = []
for comuna_id, comuna_nombre, provincia_id in comunas:
    prov_nombre, region_id = provincias[provincia_id]
    rows_out.append({
        "comuna_id": comuna_id,
        "comuna_nombre": comuna_nombre,
        "provincia_id": provincia_id,
        "provincia_nombre": prov_nombre,
        "region_id": region_id,
        "region_nombre": regiones[region_id],
        "region_nombre_corto": region_short[region_id],
    })

rows_out.sort(key=lambda r: r["comuna_id"])

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
    w.writeheader()
    w.writerows(rows_out)

print(f"Wrote {len(rows_out)} comunas to {OUT}")
print(f"Regions: {len(regiones)}")
