"""
Construye los GeoJSON para los mapas territoriales del envejecimiento:

  - comunas_chile.geojson  -> 346 comunas, geometria simplificada + todos los
    indicadores de indicadores_comuna.csv ya embebidos (listo para choropleth).
  - regiones_chile.geojson -> 16 regiones (disuelve las comunas) + indicadores
    de indicadores_region.csv.

Fuente de geometria: pachadotdev/chilemapas (GitHub), descargado por region en
Data processed/geo/r01..r16.geojson. Se simplifica (Douglas-Peucker, tolerancia
en grados) porque el archivo de Magallanes (r12) trae ~7.6MB de detalle de
fiordos/islas que no aporta a un mapa nacional a esta escala.
"""
import geopandas as gpd
import pandas as pd
from pathlib import Path

DP = Path(__file__).resolve().parent.parent / "Data processed"
GEO = DP / "geo"
SIMPLIFY_TOL = 0.001  # ~100m, suficiente para un mapa nacional/regional

print("1) Leyendo y uniendo las 16 regiones ...")
gdfs = [gpd.read_file(GEO / f"r{i:02d}.geojson") for i in range(1, 17)]
comunas = pd.concat(gdfs, ignore_index=True)
comunas = gpd.GeoDataFrame(comunas, crs=gdfs[0].crs)
comunas["comuna_id"] = comunas["codigo_comuna"].astype(int)

size_before = sum(len(g.to_json()) for g in [comunas]) / 1e6
comunas["geometry"] = comunas["geometry"].simplify(SIMPLIFY_TOL, preserve_topology=True)
size_after = len(comunas.to_json()) / 1e6
print(f"   {len(comunas)} comunas | tamaño geojson: {size_before:.1f}MB -> {size_after:.1f}MB (simplificado)")

print("2) Cruzando con indicadores_comuna.csv ...")
ind_comuna = pd.read_csv(DP / "indicadores_comuna.csv").rename(columns={"comuna": "comuna_id"})
comunas_out = comunas[["comuna_id", "geometry"]].merge(ind_comuna, on="comuna_id", how="left")
missing = comunas_out["pct_65_mas"].isna().sum()
print(f"   comunas sin match de indicadores: {missing} (de {len(comunas_out)})")
if missing:
    print("   ids sin match:", comunas_out.loc[comunas_out['pct_65_mas'].isna(), 'comuna_id'].tolist())
faltantes = set(ind_comuna['comuna_id']) - set(comunas['comuna_id'])
if faltantes:
    nombres = ind_comuna.set_index('comuna_id').loc[list(faltantes), 'comuna_nombre'].to_dict()
    print(f"   comunas en indicadores sin geometria (quedan fuera del mapa, no del resto del analisis): {nombres}")
comunas_out.to_file(GEO / "comunas_chile.geojson", driver="GeoJSON")

print("3) Disolviendo a nivel región y cruzando con indicadores_region.csv ...")
regiones = comunas[["codigo_region", "geometry"]].copy()
regiones["region_id"] = regiones["codigo_region"].astype(int)
regiones = regiones.dissolve(by="region_id", as_index=False)
ind_region = pd.read_csv(DP / "indicadores_region.csv").rename(columns={"region": "region_id"})
regiones_out = regiones[["region_id", "geometry"]].merge(ind_region, on="region_id", how="left")
regiones_out.to_file(GEO / "regiones_chile.geojson", driver="GeoJSON")

print("\nListo:")
for f in ["comunas_chile.geojson", "regiones_chile.geojson"]:
    p = GEO / f
    print(f"  {f}: {p.stat().st_size/1e6:.2f} MB")
