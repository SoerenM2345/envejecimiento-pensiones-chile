"""
KPI 1.3: participación de las partes interesadas en el financiamiento previsional, 2024 y 2025.

  KPI 1.3 = (Aporte empleador + Aporte Estado) / Financiamiento total
  Financiamiento total = Aporte trabajadores + Aporte empleador + Aporte Estado

Fuentes:
  - Aporte trabajadores (estimado): Fichas Estadísticas Previsionales de la Superintendencia de Pensiones,
    Data raw/_external/fichas_previsionales/ (N° 136-159, mar-2024 a feb-2026). De cada ficha, Tabla N° 4
    "Estadísticas generales": N° Cotizantes del mes e Ingreso promedio cotizantes.
      aporte mensual = cotizantes × ingreso promedio × 10% (cotización obligatoria)
      aporte anual   = suma de los meses de referencia de los cotizantes del año calendario
    Si faltan meses se proyecta a 12 (× 12 / n) y se informa n_meses.
  - Aporte empleador: Estado de Variación Patrimonial del FAPP al 31-12-2025 (Data raw/_external/fapp/),
    cuentas 40.110 "Cotizaciones" + 40.187 "Cotizaciones del Seguro Social por Identificar" (M$ = miles de pesos).
    2024 = 0: la cotización del empleador al FAPP (Ley 21.735) rige desde las remuneraciones de agosto de 2025.
  - Aporte Estado: PGU + PBS + APS (vejez e invalidez), monto nominal anual de
    Data processed/pgu_pbs_aps_nacional_anual.csv (script 12, misma base que el KPI 2.2).

Ojo con los meses de cada ficha: el mes de publicación NO es el mes de referencia. La ficha de septiembre 2025
trae los cotizantes de julio 2025 y el ingreso de junio 2025 (remuneraciones del mes anterior al pago).
Cada ficha se asigna siempre por el mes de referencia de los cotizantes ("Al 31 de <mes> de <año>").

Formato chileno en los PDF: punto = miles, coma = decimales.

Controles (al log):
  - Ficha N° 157 (dic-2025): 5.795.995 cotizantes × $1.362.207 × 10% ≈ 789.500 millones de pesos.
  - Empleador: 1% × masa imponible estimada (cotizantes × ingreso) de los meses ago-dic 2025 vs. valor FAPP.
  - Estado: gasto promedio mensual últimos 12 meses PGU, PBS y APS de la ficha con cotizantes de diciembre × 12.

Salidas (Data processed/):
  - fichas_previsionales_mensual.csv  n_ficha, mes_publicacion, mes_ref_cotizantes, mes_ref_ingreso, cotizantes,
                                      ingreso_promedio, aporte_trabajadores_mes, gasto_pgu_pbs_aps_12m_mm
  - kpi_participacion_partes.csv      anio, aporte_trabajadores, aporte_empleador, aporte_estado, financiamiento_total,
                                      kpi_1_3_pct, n_meses, fuente (montos en pesos)
"""
import logging
import re
from pathlib import Path

import pandas as pd
import pypdf

logging.getLogger("pypdf").setLevel(logging.ERROR)  # avisos de texto rotado en los gráficos de las fichas

ROOT = Path(__file__).resolve().parent.parent
FICHAS = ROOT / "Data raw" / "_external" / "fichas_previsionales"
FAPP = ROOT / "Data raw" / "_external" / "fapp" / "FAPP_estados_financieros_2025-12-31.pdf"
OUT = ROOT / "Data processed"
ANIOS = [2024, 2025]
TASA_TRABAJADOR = 0.10
TASA_EMPLEADOR = 0.01  # cotización del empleador al FAPP desde ago-2025 (solo para el control)

MESES = {m: i for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
     "noviembre", "diciembre"], start=1)}


def numero_cl(s):
    """'5.799.169' -> 5799169 ; '1.306.914' -> 1306914 (formato chileno, sin decimales)."""
    return int(re.sub(r"[.\s]", "", s))


def periodo(mes, anio):
    return pd.Period(year=int(anio), month=MESES[mes.lower()], freq="M")


def leer_ficha(path):
    """Extrae de una ficha los campos de la Tabla N° 4 y el gasto PGU/PBS/APS."""
    paginas = pypdf.PdfReader(path).pages
    titulo = re.search(r"N°\s*(\d+)\s*[–-]\s*([a-záéíóú]+)\s+(\d{4})", paginas[0].extract_text(extraction_mode="layout"))
    texto = "\n".join(p.extract_text(extraction_mode="layout") for p in paginas)

    tabla = texto[texto.index("Estadísticas generales"):]
    # el día puede venir partido ("Al 3 1 de enero") o ser 28/30
    fecha = re.search(r"Al\s+\d\s*\d?\s+de\s+([a-z]+)\s+de\s+(\d{4})", tabla)
    cot = re.search(r"Cotizantes del mes[\d,]*\s+([\d.]{7,})", tabla)
    # "Ingreso promedio cotizantes1,2   $1.284.657"; a veces la etiqueta se corta en dos líneas: primer monto en $ después
    ing = re.search(r"Ingreso promedio co.*?\$\s*([\d.]{7,})", tabla, re.S)
    hombres = re.search(r"Ingreso promedio Hombres.*?\$\s*([\d.]{7,})", tabla, re.S)
    mujeres = re.search(r"Ingreso promedio Mujeres.*?\$\s*([\d.]{7,})", tabla, re.S)
    nota = texto[texto.index("ingreso promedio corresponde"):][:400]
    ref_ing = re.search(r"remuneraciones\s+de\s*.*?([a-z]+)\s+(?:de\s+)?(\d{4})", nota, re.S)
    gasto = re.search(r"Gasto promedio mensual[^\n]*?MM\$\s*([\d.][\d. ]*)", texto)

    fila = {
        "n_ficha": int(titulo.group(1)),
        "mes_publicacion": periodo(titulo.group(2), titulo.group(3)),
        "mes_ref_cotizantes": periodo(*fecha.groups()),
        "mes_ref_ingreso": periodo(*ref_ing.groups()),
        "cotizantes": numero_cl(cot.group(1)),
        "ingreso_promedio": numero_cl(ing.group(1)),
        "gasto_pgu_pbs_aps_12m_mm": numero_cl(gasto.group(1)) if gasto else None,
        "archivo": path.name,
    }
    # el ingreso total tiene que quedar entre el de mujeres y el de hombres (control del parser)
    if not numero_cl(mujeres.group(1)) < fila["ingreso_promedio"] < numero_cl(hombres.group(1)):
        raise ValueError(f"{path.name}: ingreso promedio {fila['ingreso_promedio']} fuera de [mujeres, hombres]")
    return fila


def leer_fapp(path):
    """Cuentas 40.110 y 40.187 del Estado de Variación Patrimonial (M$), ejercicio actual."""
    texto = "\n".join(p.extract_text() for p in pypdf.PdfReader(path).pages)
    evp = texto[texto.index("ESTADO DE VARIACION PATRIMONIAL"):]
    cuentas = {}
    for codigo in ("40.110", "40.187"):
        m = re.search(rf"^{re.escape(codigo)}\s+\D+?\s([\d.]+)", evp, re.M)
        cuentas[codigo] = numero_cl(m.group(1))
    return cuentas


# =============================================================================
# 1) Fichas: aporte de los trabajadores por mes
# =============================================================================
print("1) fichas_previsionales_mensual.csv ...")
fichas = pd.DataFrame([leer_ficha(p) for p in sorted(FICHAS.glob("*.pdf"))]).sort_values("mes_ref_cotizantes")
assert fichas.mes_ref_cotizantes.is_unique, "dos fichas con el mismo mes de referencia de cotizantes"
desfase = (fichas.mes_ref_cotizantes - fichas.mes_ref_ingreso).apply(lambda d: d.n)
if (desfase != 1).any():
    print("   AVISO: ingreso no corresponde al mes anterior a los cotizantes en:",
          fichas.loc[desfase != 1, "n_ficha"].tolist())
fichas["aporte_trabajadores_mes"] = fichas.cotizantes * fichas.ingreso_promedio * TASA_TRABAJADOR

out_fichas = fichas[[
    "n_ficha", "mes_publicacion", "mes_ref_cotizantes", "mes_ref_ingreso", "cotizantes", "ingreso_promedio",
    "aporte_trabajadores_mes", "gasto_pgu_pbs_aps_12m_mm",
]]
out_fichas.to_csv(OUT / "fichas_previsionales_mensual.csv", index=False)
print(out_fichas.to_string(index=False))

ctrl = fichas[fichas.n_ficha == 157]
if len(ctrl):
    print(f"   Control ficha N° 157: {ctrl.aporte_trabajadores_mes.iloc[0] / 1e6:,.0f} millones de pesos (esperado ≈ 789.500)")

# =============================================================================
# 2) Aporte empleador (FAPP) y aporte Estado (PGU/PBS/APS)
# =============================================================================
print("\n2) Aporte empleador y Estado ...")
fapp = leer_fapp(FAPP)
empleador_2025 = (fapp["40.110"] + fapp["40.187"]) * 1000  # M$ -> pesos
print(f"   FAPP 40.110 Cotizaciones: M$ {fapp['40.110']:,} ; 40.187 SSP por identificar: M$ {fapp['40.187']:,}")

ref_2025 = fichas[fichas.mes_ref_cotizantes.dt.year == 2025]
masa_ago_dic = (ref_2025.loc[ref_2025.mes_ref_cotizantes.dt.month >= 8, ["cotizantes", "ingreso_promedio"]]
                .prod(axis=1).sum())
print(f"   Control empleador: 1% × masa imponible ago-dic 2025 = {TASA_EMPLEADOR * masa_ago_dic / 1e9:,.1f} mil millones "
      f"vs FAPP {empleador_2025 / 1e9:,.1f} mil millones ({empleador_2025 / (TASA_EMPLEADOR * masa_ago_dic) - 1:+.1%})")
# la cotización rige desde las remuneraciones de agosto, que se pagan en septiembre: ventana de pago sep-dic
masa_sep_dic = (ref_2025.loc[ref_2025.mes_ref_cotizantes.dt.month >= 9, ["cotizantes", "ingreso_promedio"]]
                .prod(axis=1).sum())
print(f"   Control empleador (pagos sep-dic, remuneraciones ago-nov): {TASA_EMPLEADOR * masa_sep_dic / 1e9:,.1f} mil millones "
      f"({empleador_2025 / (TASA_EMPLEADOR * masa_sep_dic) - 1:+.1%})")

pilar = pd.read_csv(OUT / "pgu_pbs_aps_nacional_anual.csv")
estado = pilar[pilar.tipo_beneficio == "Total"].set_index("anio")["monto_nominal_mm"] * 1e6  # MM$ -> pesos

# =============================================================================
# 3) KPI por año
# =============================================================================
print("\n3) kpi_participacion_partes.csv ...")
filas = []
for anio in ANIOS:
    meses = fichas[fichas.mes_ref_cotizantes.dt.year == anio]
    n = len(meses)
    trabajadores = meses.aporte_trabajadores_mes.sum() * 12 / n
    empleador = empleador_2025 if anio == 2025 else 0
    filas.append({
        "anio": anio,
        "aporte_trabajadores": round(trabajadores),
        "aporte_empleador": empleador,
        "aporte_estado": round(estado.loc[anio]),
        "n_meses": n,
        "fuente": ("Trabajadores: Fichas Estadísticas Previsionales N° "
                   f"{meses.n_ficha.min()}-{meses.n_ficha.max()} (cotizantes × ingreso promedio × 10%); "
                   "Empleador: FAPP EEFF 31-12-2025, cuentas 40.110 + 40.187; "
                   "Estado: PGU + PBS + APS nominal (Pilar Solidario, script 12)"),
    })
    # control del gasto del Estado: promedio móvil 12 meses de la ficha con cotizantes de diciembre × 12
    dic = meses[meses.mes_ref_cotizantes.dt.month == 12]
    if len(dic) and pd.notna(dic.gasto_pgu_pbs_aps_12m_mm.iloc[0]):
        ficha_x12 = dic.gasto_pgu_pbs_aps_12m_mm.iloc[0] * 12 * 1e6
        print(f"   Control Estado {anio}: ficha N° {dic.n_ficha.iloc[0]} × 12 = {ficha_x12 / 1e9:,.0f} mil millones "
              f"vs Pilar Solidario {estado.loc[anio] / 1e9:,.0f} mil millones ({estado.loc[anio] / ficha_x12 - 1:+.1%})")

kpi = pd.DataFrame(filas)
kpi["financiamiento_total"] = kpi.aporte_trabajadores + kpi.aporte_empleador + kpi.aporte_estado
kpi["kpi_1_3_pct"] = round(100 * (kpi.aporte_empleador + kpi.aporte_estado) / kpi.financiamiento_total, 2)
kpi = kpi[["anio", "aporte_trabajadores", "aporte_empleador", "aporte_estado", "financiamiento_total", "kpi_1_3_pct",
           "n_meses", "fuente"]]
kpi.to_csv(OUT / "kpi_participacion_partes.csv", index=False)
print(kpi.drop(columns="fuente").to_string(index=False))
