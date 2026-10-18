"""
KPI 1.2: control y sensibilidad del punto crítico (país, base cotizantes, promedio).

Usa el mismo motor que el dashboard (Dashboards/components/critical_point.py) con los supuestos de config/escenarios.yaml.

Definición (ver el motor):
  - Costo     = gasto del Pilar Solidario de VEJEZ (PGU + APS vejez + PBS vejez; sin PBS/APS de invalidez), pesos de 2025.
  - Capacidad = tope de carga × masa imponible anual (12 meses de cotizantes × ingreso imponible promedio, Superintendencia).
  - Carga requerida = costo / masa imponible.
  - Punto crítico = primer año en que el costo alcanza a la capacidad (carga requerida >= tope).

Log: tabla de control 2024 / 2030 / punto crítico / 2050 con los valores intermedios y conciliación con el KPI 1.3.

Salida (Data processed/):
  - kpi_punto_critico_sensibilidad.csv   crecimiento_salario_real, tope_carga, estado, punto_critico, punto_critico_exacto,
                                         carga_requerida_2024, carga_requerida_2050, es_base   (3 × 3 = 9 filas)
"""
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Dashboards"))
from components import critical_point as cp  # noqa: E402

DP = ROOT / "Data processed"
ESC = yaml.safe_load((ROOT / "config" / "escenarios.yaml").read_text(encoding="utf-8"))
G_BASE, TOPE_BASE = ESC["crecimiento_salario_real"]["base"], ESC["tope_carga"]["base"]
CRECIMIENTOS = sorted([G_BASE] + ESC["crecimiento_salario_real"]["variantes"])
TOPES = sorted([TOPE_BASE] + ESC["tope_carga"]["variantes"])

nac = pd.read_csv(DP / "kpi_pc_nacional.csv")
proy = pd.read_csv(DP / "proyeccion_envejecimiento_pais.csv")
params = pd.read_csv(DP / "kpi_pc_parametros_reforma.csv")


def escenario(g=G_BASE, tope=TOPE_BASE):
    return cp.Escenario(crec_salarial=g, carga_max=tope, pgu_250=ESC["pgu_250"])


# =============================================================================
# 1) Control del escenario base
# =============================================================================
d = cp.serie_pais(nac, proy, params, escenario())
pc = cp.punto_critico(d)
print(f"1) Escenario base: salario real +{G_BASE:.1%}, tope {TOPE_BASE:.0%}, PGU $250.000 = {ESC['pgu_250']}, cobertura constante")
print(f"   Punto crítico: {pc['anio']} (cruce exacto {pc['anio_exacto']:.2f})")
anios = sorted({2024, 2030, pc["anio"] or 2050, 2050})
t = d[d.anio.isin(anios)].assign(
    cotizantes=lambda x: x.trabajadores.round(0),
    ingreso_mensual=lambda x: x.ingreso_trab.round(0),
    masa_billones=lambda x: (x.masa_ingreso / 1e12).round(2),
    costo_vejez_billones=lambda x: (x.costo_total / 1e12).round(2),
    carga_pct=lambda x: (100 * x.carga_requerida).round(2),
    razon=lambda x: x.razon_soporte.round(3),
    tipo=lambda x: x.proyectado.map({False: "real", True: "escenario"}),
)[["anio", "tipo", "cotizantes", "ingreso_mensual", "masa_billones", "costo_vejez_billones", "carga_pct", "razon"]]
print(t.to_string(index=False))
print("   (pesos de 2025; cotizantes = diciembre con región; masa = 12 meses; costo = solo vejez)")

# conciliación con el KPI 1.3 (misma masa) y con el Pilar Solidario completo
n24 = nac.set_index("anio").loc[2024]
pil = pd.read_csv(DP / "pgu_pbs_aps_nacional_anual.csv")
total24 = pil[(pil.anio == 2024) & (pil.tipo_beneficio == "Total")].monto_nominal_mm.iloc[0] * 1e6
fichas = pd.read_csv(DP / "fichas_previsionales_mensual.csv")
f24 = fichas[pd.PeriodIndex(fichas.mes_ref_cotizantes, freq="M").year == 2024]
masa13 = (f24.cotizantes * f24.ingreso_promedio).sum()
print(f"   Masa 2024 nominal: 1.2 = {n24.masa_imponible_anual_nom / 1e12:.2f} billones; 1.3 (fichas) = {masa13 / 1e12:.2f}")
print(f"   Carga 2024: Pilar total / masa = {100 * total24 / masa13:.2f}% ; solo vejez / masa = "
      f"{100 * n24.costo_vejez_mm_nom * 1e6 / n24.masa_imponible_anual_nom:.2f}% (la invalidez no es costo de la vejez)")

# =============================================================================
# 2) Sensibilidad 3 × 3
# =============================================================================
print("\n2) kpi_punto_critico_sensibilidad.csv ...")
filas = []
for g in CRECIMIENTOS:
    for tope in TOPES:
        s = cp.serie_pais(nac, proy, params, escenario(g, tope))
        p = cp.punto_critico(s)
        filas.append({"crecimiento_salario_real": g, "tope_carga": tope, "estado": p["estado"], "punto_critico": p["anio"],
                      "punto_critico_exacto": round(p["anio_exacto"], 2) if p["anio_exacto"] else None,
                      "carga_requerida_2024": round(cp.fila_anio(s, 2024).carga_requerida, 4),
                      "carga_requerida_2050": round(cp.fila_anio(s, 2050).carga_requerida, 4),
                      "es_base": g == G_BASE and tope == TOPE_BASE})
sens = pd.DataFrame(filas)
assert len(sens) == 9
sens.to_csv(DP / "kpi_punto_critico_sensibilidad.csv", index=False)
print(sens.pivot(index="crecimiento_salario_real", columns="tope_carga", values="punto_critico").to_string())
