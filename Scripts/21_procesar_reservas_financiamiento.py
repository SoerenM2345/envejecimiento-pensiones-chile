"""
Financiamiento dedicado de las pensiones del Estado (KPI 2.2, ratio 2): reservas y aporte fiscal por ley.

Fuentes (Data raw/_external/). Los PDF no se leen por programa (el entorno no trae lector de PDF): las cifras se
transcribieron a mano de las tablas indicadas y el script las valida contra otras fuentes del proyecto.
  - frp/FRP_informe_ejecutivo_mensual_2026-07.pdf   DIPRES, Informe Ejecutivo Mensual del Fondo de Reserva de
        Pensiones (FRP) a julio de 2026, pág. 2: valor de mercado, aportes, retiros y composición, en millones de US$.
  - fapp/FAPP_estados_financieros_2025-12-31.pdf y ..._interinos_2026-06-30.pdf   Balance General y Estado de Variación
        Patrimonial del Fondo Autónomo de Protección Previsional (FAPP), en miles de pesos (aquí pasados a millones).
  - ley_21735/nota_tecnica_ley_21735_previsionsocial.pdf   Subsecretaría de Previsión Social, Tabla 2 (pág. 13-14):
        aporte anual del Estado al FAPP en millones de UTM, 2028-2037. La nota técnica de DIPRES (dipres/articles-397500)
        dice que desde el «año 12» el aporte queda en 15 millones de UTM, y lo mantenemos hasta 2050.
  - SII (https://www.sii.cl/valores_y_fechas/utm/utm2025.htm y .../dolar/dolarAAAA.htm, abiertas el 2026-10-13):
        valor de la UTM de 2025 y dólar observado (promedios mensuales y último día hábil de cada año).
  - Tablas ya procesadas: pgu_pbs_aps_nacional_anual.csv, macro_pib_anual.csv, dipres_pasivos_activos_gc.csv.

Salidas (Data processed/):
  - frp_reserva_anual.csv   anio, valores del FRP en US$ y en pesos corrientes (2022-2025 en pesos), retiros como % del
        Pilar Solidario y del PIB. Los pesos de los retiros usan el dólar PROMEDIO del año (es un flujo); los de la
        cartera usan el dólar del ÚLTIMO día hábil (es un stock al 31 de diciembre).
  - fapp_balance.csv        una fila por fecha de cierre (2025-12-31 y 2026-06-30), en millones de pesos corrientes.
  - fapp_aporte_fiscal.csv  anio 2028-2050: millones de UTM por ley y su equivalente en millones de pesos de 2025.

Notas de método:
  - El valor del FRP a fines de 2025 (US$ 10.313 M) incluye US$ 222 M que el FRP transfirió al FAPP (agosto de 2025). Para
    no contar dos veces ese dinero, la «cartera propia» del FRP es el total menos esa transferencia (US$ 10.091 M).
  - El dólar de cierre se valida contra el que implica la tabla de activos en dólares de DIPRES (script 16): coinciden al
    centavo en 2022-2025.
  - Los retiros de 2020 y 2021 del FRP (US$ 1.576 M y US$ 2.960 M) son ajenos al ritmo normal (el informe no los desglosa);
    quedan en US$, sin pasar a pesos ni a % del Pilar.
  - La UTM se reajusta por IPC: se usa el promedio de 2025 como valor real en pesos de 2025.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Data processed"

# ---- FRP, informe ejecutivo mensual julio 2026, pág. 2 (millones de US$) --------------------------------------------
FRP = pd.DataFrame({
    "anio":                 [2020,      2021,     2022,     2023,     2024,     2025],
    "valor_inicial_musd":   [10812.08,  10156.83, 7472.93,  6475.28,  8638.56,  9378.29],
    "aportes_musd":         [0.00,      0.00,     531.60,   1640.53,  607.17,   0.00],
    "retiros_musd":         [1576.48,   2959.82,  268.92,   299.94,   303.59,   332.39],
    "valor_final_musd":     [10156.83,  7472.93,  6475.28,  8638.56,  9378.29,  10313.19],
    # cartera propia = total - transferencia al FAPP (US$ 200 M del 1-ago-2025, valorada en 222,05 a fin de año)
    "transferencia_fapp_musd": [0.0,    0.0,      0.0,      0.0,      0.0,      222.05],
})
# ---- SII: dólar observado, promedios mensuales (pesos por US$) y valor del último día hábil del año -----------------
DOLAR_MENSUAL = {
    2022: [822.05, 807.07, 799.19, 815.12, 849.39, 857.77, 953.71, 904.35, 921.01, 955.89, 917.05, 875.66],
    2023: [826.34, 798.26, 809.50, 803.84, 798.64, 799.87, 813.40, 855.66, 884.40, 926.35, 886.61, 874.67],
    2024: [907.99, 963.44, 967.93, 960.14, 917.88, 926.08, 937.56, 929.90, 926.21, 933.81, 971.60, 982.30],
    2025: [1000.76, 956.62, 932.55, 961.96, 941.01, 938.04, 951.55, 966.30, 960.37, 953.97, 935.70, 916.16],
}
DOLAR_CIERRE = {2022: 859.51, 2023: 884.59, 2024: 992.12, 2025: 911.18}  # 30-dic-22, 29-dic-23, 31-dic-24, 30-dic-25
# ---- SII: UTM 2025 (pesos) ------------------------------------------------------------------------------------------
UTM_2025 = [67429, 67294, 68034, 68306, 68648, 68785, 68923, 68647, 69265, 69265, 69542, 69542]
# ---- Ley 21.735, Tabla 2 (Subsecretaría de Previsión Social): aporte anual del Estado al FAPP, millones de UTM -------
APORTE_UTM = {2028: 2.2, 2029: 2.2, 2030: 5.0, 2031: 7.0, 2032: 9.0, 2033: 10.0, 2034: 12.0, 2035: 13.0, 2036: 14.0, 2037: 15.0}
ANIO_FIN = 2050
# ---- FAPP, estados financieros (miles de pesos en el original) ------------------------------------------------------
FAPP = [
    dict(cierre="2025-12-31", desde="2025-08-01", activos=486_240_298, deuda_frp=200_196_177, patrimonio=282_861_092,
         cotizaciones=272_374_252, beneficios=0, rentabilidad=6_355_226 - 4_932_394, patrimonio_inicial=0),
    dict(cierre="2026-06-30", desde="2026-01-01", activos=241_523_054, deuda_frp=208_272_126, patrimonio=25_719_095,
         cotizaciones=439_587_480, beneficios=698_890_077, rentabilidad=9_001_349 - 8_519_939, patrimonio_inicial=282_861_092),
]
# Totales de control: activos = pasivos exigibles + patrimonio
FAPP_PASIVO_EXIGIBLE = {"2025-12-31": 486_240_298 - 282_861_092, "2026-06-30": 215_803_959}


def frp_anual() -> pd.DataFrame:
    pil = pd.read_csv(OUT / "pgu_pbs_aps_nacional_anual.csv")
    pib = pd.read_csv(OUT / "macro_pib_anual.csv").set_index("anio")
    d = FRP.copy()
    # el valor final debe cerrar: inicial + aportes - retiros + (interés y ganancias) = final; aquí solo se comprueba el encadenado
    assert np.allclose(d.valor_final_musd.iloc[:-1].values, d.valor_inicial_musd.iloc[1:].values, atol=0.01)
    d["cartera_propia_musd"] = d.valor_final_musd - d.transferencia_fapp_musd
    d["tc_prom"] = d.anio.map({a: float(np.mean(v)) for a, v in DOLAR_MENSUAL.items()})
    d["tc_cierre"] = d.anio.map(DOLAR_CIERRE)
    d["retiros_mm"] = d.retiros_musd * d.tc_prom
    d["cartera_propia_mm"] = d.cartera_propia_musd * d.tc_cierre
    tot = pil[pil.tipo_beneficio == "Total"].set_index("anio").monto_nominal_mm
    d["pilar_total_mm"] = d.anio.map(tot)
    d.loc[d.tc_prom.isna(), "pilar_total_mm"] = np.nan
    d["retiros_pct_pilar"] = 100 * d.retiros_mm / d.pilar_total_mm
    d["retiros_pct_pib"] = 100 * d.retiros_mm / d.anio.map(pib.pib_corriente_mm)
    return d


def valida_dolar_con_dipres(frp: pd.DataFrame) -> None:
    """El dólar de cierre del SII debe coincidir con el que implica la tabla de activos en dólares de DIPRES."""
    dip = pd.read_csv(OUT / "dipres_pasivos_activos_gc.csv")
    pib = pd.read_csv(OUT / "macro_pib_anual.csv").set_index("anio")
    for a in (2022, 2023, 2024, 2025):
        x = dip[(dip.anio == a) & (dip.codigo.astype(str) == "5")]
        implicito = x[x.unidad == "% PIB"].valor.iloc[0] / 100 * pib.loc[a, "pib_corriente_mm"] / x[x.unidad == "MMUS$"].valor.iloc[0]
        assert abs(implicito - DOLAR_CIERRE[a]) < 0.02, (a, implicito, DOLAR_CIERRE[a])


def fapp_balance() -> pd.DataFrame:
    rows = []
    for f in FAPP:
        assert f["activos"] - FAPP_PASIVO_EXIGIBLE[f["cierre"]] == f["patrimonio"], f["cierre"]
        meses = (pd.Timestamp(f["cierre"]) - pd.Timestamp(f["desde"])).days / 30.4375
        rows.append(dict(
            cierre=f["cierre"], desde=f["desde"], meses=round(meses, 1),
            activos_mm=f["activos"] / 1000, deuda_frp_mm=f["deuda_frp"] / 1000, patrimonio_mm=f["patrimonio"] / 1000,
            cotizaciones_periodo_mm=f["cotizaciones"] / 1000, beneficios_periodo_mm=f["beneficios"] / 1000,
            rentabilidad_neta_periodo_mm=f["rentabilidad"] / 1000))
    return pd.DataFrame(rows)


def fapp_aporte_fiscal() -> pd.DataFrame:
    utm = float(np.mean(UTM_2025))
    anios = list(range(2028, ANIO_FIN + 1))
    musd = [APORTE_UTM.get(a, 15.0) for a in anios]   # desde 2037 se mantiene en 15 millones de UTM («año 12 en adelante»)
    d = pd.DataFrame({"anio": anios, "millones_utm": musd})
    d["utm_pesos_2025"] = utm
    d["aporte_mm_2025"] = d.millones_utm * 1e6 * utm / 1e6   # millones de UTM x pesos por UTM = pesos; /1e6 = millones de pesos
    d["fuente"] = np.where(d.anio <= 2037, "Ley 21.735 (Tabla 2, Subsecretaría de Previsión Social)", "DIPRES: 15 millones de UTM desde el año 12")
    return d


def main():
    frp = frp_anual()
    valida_dolar_con_dipres(frp)
    frp.round(4).to_csv(OUT / "frp_reserva_anual.csv", index=False)
    bal = fapp_balance()
    bal.round(3).to_csv(OUT / "fapp_balance.csv", index=False)
    ap = fapp_aporte_fiscal()
    ap.round(3).to_csv(OUT / "fapp_aporte_fiscal.csv", index=False)
    print(frp[["anio", "retiros_musd", "retiros_mm", "retiros_pct_pilar", "retiros_pct_pib", "cartera_propia_mm"]].round(3).to_string(index=False))
    print(bal.to_string(index=False))
    print(ap.head(3).to_string(index=False), "...", ap.iloc[-1].aporte_mm_2025)


if __name__ == "__main__":
    main()
