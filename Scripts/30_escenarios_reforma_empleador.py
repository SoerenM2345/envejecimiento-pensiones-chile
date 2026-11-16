"""
KPI 1.2: dos escenarios con la reforma de la cotización del empleador (Ley 21.735), para comparar con la base (tope de carga de 10 % y cotizantes como hoy).
Ejecutar DESPUÉS de Scripts/15_kpi_participacion_partes.py (usa kpi_reforma_empleo_factor.csv).

La reforma sube el costo de contratar a un trabajador dependiente de 1,88 % (seguro de invalidez) a 8,5 % del sueldo imponible en 2033. Si el empleador
lo traspasa a los sueldos, no pasa nada con el empleo (el escenario base); si contrata menos con contrato formal, bajan los cotizantes dependientes y el
punto crítico del KPI 1.2 llega antes. La elasticidad es un supuesto (config/escenarios.yaml, reforma_empleador): un efecto bajo y uno alto, no una estimación.
El Seguro Social NO se suma a la capacidad del punto crítico: sus ingresos pagan otras prestaciones (Beneficio por Años Cotizados, compensación a las mujeres y
seguro de invalidez y sobrevivencia), no el Pilar Solidario; el aporte del Estado al fondo del Seguro Social ya está en el KPI 2.2.

Salida (Data processed/): kpi_pc_escenarios_reforma.csv  una fila por escenario (clave, nombre, grupo, carga_max, elasticidad, descripcion, orden,
  aumento_costo_2033_pp, cotizantes_2033_vs_2025_pct). La trayectoria año a año del factor de cotizantes está en kpi_reforma_empleo_factor.csv.
"""
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
DP = ROOT / "Data processed"
CFG = yaml.safe_load((ROOT / "config" / "escenarios.yaml").read_text(encoding="utf-8"))


def escenarios() -> pd.DataFrame:
    tope = CFG["tope_carga"]["base"]
    factor = pd.read_csv(DP / "kpi_reforma_empleo_factor.csv")
    f33 = factor[factor.anio == 2033].set_index("escenario")
    filas = [("base", "Base: tope 10 %, cotizantes como hoy", 0.0, 0.0,
              "Referencia del KPI 1.2. Equivale a que el empleador traspase todo el costo de la reforma a los sueldos: el empleo formal no cambia", 1)]
    for orden, (clave, nombre) in enumerate([("reforma_baja", "Reforma con efecto bajo en el empleo"), ("reforma_alta", "Reforma con efecto alto en el empleo")], start=2):
        e, aumento, rel = (float(f33.loc[clave, c]) for c in ("elasticidad", "aumento_costo_pp", "factor_vs_2025"))
        filas.append((clave, nombre, e, aumento,
                      f"Por cada 1 % más de costo laboral, {abs(e):.1f} % menos de cotizantes dependientes (supuesto); el costo sube {aumento:.2f} puntos hasta 2033 "
                      f"y los cotizantes quedan {100 * (1 - rel):.1f} % bajo los de 2025".replace(".", ","), orden))
    d = pd.DataFrame(filas, columns=["clave", "nombre", "elasticidad", "aumento_costo_2033_pp", "descripcion", "orden"])
    d["grupo"] = ["Referencia"] + ["Reforma del empleador"] * 2
    d["carga_max"] = tope
    d["cotizantes_2033_vs_2025_pct"] = [0.0] + [100 * (float(f33.loc[c, "factor_vs_2025"]) - 1) for c in d.clave[1:]]
    return d[["clave", "nombre", "grupo", "carga_max", "elasticidad", "descripcion", "orden", "aumento_costo_2033_pp", "cotizantes_2033_vs_2025_pct"]]


def main():
    d = escenarios()
    assert d.elasticidad.abs().is_monotonic_increasing  # base, efecto bajo, efecto alto
    d.round(6).to_csv(DP / "kpi_pc_escenarios_reforma.csv", index=False)
    print(d.drop(columns="descripcion").to_string(index=False))


if __name__ == "__main__":
    main()
