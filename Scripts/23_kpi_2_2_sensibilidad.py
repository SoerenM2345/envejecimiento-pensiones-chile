"""
KPI 2.2: control de las cifras del financiamiento dedicado y sensibilidad del ratio 2 a la rentabilidad real.

Usa el mismo motor que el dashboard (Dashboards/components/financiamiento.py y cost_analysis.py) con los supuestos de
config/escenarios.yaml (crecimiento del PIB, PGU de $250.000, aporte al FAPP, horizonte, rentabilidad real).

Ratio 2 «cobertura de reservas» = cartera propia del FRP al 31-dic-2025 / valor presente 2026-horizonte del alza de la carga
fiscal (Pilar + aporte del Estado al FAPP) sobre el peso que el Pilar tenía en el PIB en 2025, descontado a la rentabilidad real.
Es la alternativa al valor presente oficial del déficit, que no está publicado.

«Pilar» = PGU + PBS/APS de vejez + PBS/APS de invalidez (la fila 'Total' del Pilar Solidario), igual que el KPI 1.3 (aporte del
Estado). El KPI 1.2 (punto crítico) usa solo vejez: mide el costo de la vejez, no el peso fiscal del Pilar.

Log: cifras del resumen (peso fiscal 2025 / pico / 2037 con FAPP, agotamiento y cobertura, personas sin pensión propia).

Salida (Data processed/):
  - kpi_2_2_sensibilidad.csv   rentabilidad_real, reserva_billones, vp_gasto_billones, cobertura_pct, anio_agotamiento, es_base
"""
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Dashboards"))
from components.cost_analysis import serie_historica  # noqa: E402
from components.financiamiento import (proyeccion_carga, trayectoria_reserva, dependencia_regional,  # noqa: E402
                                       proyeccion_sin_pension)

DP = ROOT / "Data processed"
ESC = yaml.safe_load((ROOT / "config" / "escenarios.yaml").read_text(encoding="utf-8"))
R_BASE = ESC["rentabilidad_real_reservas"]["base"]
TASAS = sorted([R_BASE] + ESC["rentabilidad_real_reservas"]["variantes"])


def leer(nombre):
    return pd.read_csv(DP / nombre)


pilar = leer("pgu_pbs_aps_nacional_anual.csv")
h = serie_historica(leer("gasto_proteccion_social.csv"), leer("macro_pib_anual.csv"), leer("proyeccion_envejecimiento_pais.csv"),
                    leer("kpi_pc_nacional.csv"), pilar, "mediana")
p = proyeccion_carga(h, pilar, leer("macro_pib_anual.csv"), leer("proyeccion_envejecimiento_pais.csv"),
                     leer("kpi_pc_parametros_reforma.csv"), leer("fapp_aporte_fiscal.csv"), ESC["crecimiento_pib_real"],
                     ESC["pgu_250"], ESC["aporte_fapp"], ESC["horizonte_proyeccion"])

# =============================================================================
# 1) Control: gasto 2025 y peso fiscal
# =============================================================================
total25 = pilar[(pilar.anio == 2025) & (pilar.tipo_beneficio == "Total")].monto_nominal_mm.iloc[0] * 1e6
print(f"1) Pilar 2025 (vejez + invalidez): motor {p.loc[2025, 'pilar'] / 1e12:.3f} billones; "
      f"pgu_pbs_aps_nacional_anual 'Total' {total25 / 1e12:.3f}")
assert abs(p.loc[2025, "pilar"] - total25) < 1e6, "el gasto 2025 del motor no coincide con el Pilar Solidario"
pico = p.pilar_pct_pib.idxmax()
print(f"   Peso fiscal: 2025 {p.loc[2025, 'pilar_pct_pib']:.2f}% del PIB | máximo del Pilar {p.loc[pico, 'pilar_pct_pib']:.2f}% en {pico} | "
      f"con aporte al FAPP 2037 {p.loc[2037, 'carga_pct_pib']:.2f}% (supuestos: PIB +{ESC['crecimiento_pib_real']:.0%}, "
      f"PGU $250.000 = {ESC['pgu_250']}, aporte FAPP = {ESC['aporte_fapp']})")

# =============================================================================
# 2) Sensibilidad del ratio 2 a la rentabilidad real
# =============================================================================
print("\n2) kpi_2_2_sensibilidad.csv ...")
reserva0 = leer("frp_reserva_anual.csv").set_index("anio").loc[2025, "cartera_propia_mm"] * 1e6
filas = []
for r in TASAS:
    _, res = trayectoria_reserva(p, reserva0, r, "incremento")
    filas.append({"rentabilidad_real": r, "reserva_billones": round(reserva0 / 1e12, 3),
                  "vp_gasto_billones": round(res["vp_gasto"] / 1e12, 2), "cobertura_pct": round(100 * res["ratio_cobertura"], 1),
                  "anio_agotamiento": res["anio_agotamiento"], "es_base": r == R_BASE})
sens = pd.DataFrame(filas)
assert len(sens) == 3
sens.to_csv(DP / "kpi_2_2_sensibilidad.csv", index=False)
print(sens.to_string(index=False))

# =============================================================================
# 3) Personas sin pensión propia (beneficiarios de la PGU no contributiva)
# =============================================================================
reg = dependencia_regional(leer("pgu_pbs_aps_region_trimestral.csv"), pilar, leer("kpi_presion_previsional_region.csv"),
                           leer("kpi_pc_nacional.csv"))
ch = reg[reg.region_id == 0].iloc[0]
rr = reg[reg.region_id != 0].sort_values("pct_sin_pension", ascending=False)
n35 = proyeccion_sin_pension(reg, leer("kpi_proyeccion_regional.csv"), 2035).n_anio.sum()
print(f"\n3) Sin pensión propia (PGU no contributiva, prom. mensual 4.º trim. 2024, pgu_pbs_aps_region_trimestral.csv): "
      f"{ch.n_sin_pension:,.0f} = {ch.pct_sin_pension:.1f}% de los beneficiarios de la PGU")
print("   Mayores: " + ", ".join(f"{r.region_nombre} {r.pct_sin_pension:.1f}%" for r in rr.head(3).itertuples())
      + " | menores: " + ", ".join(f"{r.region_nombre} {r.pct_sin_pension:.1f}%" for r in rr.tail(2).itertuples()))
print(f"   Escenario 2035 (tasa regional 2024 × población 65+ regional, reparto de tasas nacionales): {n35:,.0f}")
