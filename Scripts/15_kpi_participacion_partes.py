"""
KPI 1.3: participación del flujo comisionable, desde la mirada de una AFP. Real 2024-2025 y escenario 2026-2035.

  KPI 1.3 = Aportes a cuentas individuales / Flujo total al sistema
  Aportes a cuentas individuales = trabajadores (10% obligatorio) + parte del empleador que va a la cuenta individual
  Flujo total = cuentas individuales + Seguro Social (FAPP) + Estado (PGU + PBS + APS)

SIS (Seguro de Invalidez y Sobrevivencia): hasta jul-2026 el empleador paga la prima aparte (1,88%); desde la remuneración de
agosto 2026 queda dentro del 2,5% del Seguro Social. Para no crear un salto artificial se calculan dos variantes:
  - sin_sis (principal): el SIS no entra al flujo en ningún año; desde ago-2026 se resta del Seguro Social.
    Razón: es una prima de seguro, no financiamiento de pensiones ni base comisionable.
  - con_sis (sensibilidad): el SIS entra al flujo en todos los años (columna 'sis').
En ambas el Seguro Social se informa sin SIS y el SIS va en su propia columna; solo cambia si suma al flujo total.

La AFP solo cobra comisión sobre lo que entra a las cuentas individuales; lo que va al FAPP o paga el Estado no genera comisión.

Base (secciones 1-3, sin cambios de método): flujos reales por pagador -> kpi_participacion_partes.csv.

Fuentes:
  - Aporte trabajadores (estimado): Fichas Estadísticas Previsionales de la Superintendencia de Pensiones,
    Data raw/_external/fichas_previsionales/ (N° 136-159, mar-2024 a feb-2026). De cada ficha, Tabla N° 4
    "Estadísticas generales": N° Cotizantes del mes e Ingreso promedio cotizantes.
      aporte mensual = cotizantes × ingreso promedio × 10% (cotización obligatoria)
      aporte anual   = suma de los meses de referencia de los cotizantes del año calendario
    Se verifica que haya 12 meses de referencia por año (tabla año × mes en el log). Si faltan, se proyecta a 12
    (× 12 / n), se informa n_meses en las salidas y se listan las fichas que hay que descargar.
  - Aporte empleador: Estado de Variación Patrimonial del FAPP al 31-12-2025 (Data raw/_external/fapp/),
    cuentas 40.110 "Cotizaciones" + 40.187 "Cotizaciones del Seguro Social por Identificar" (M$ = miles de pesos).
    2024 = 0: la cotización del empleador al FAPP (Ley 21.735) rige desde las remuneraciones de agosto de 2025.
  - División de la cotización del empleador (cuenta individual / Seguro Social) y tasa del SIS: Nota Técnica
    "Reforma de Pensiones, Ley N°21.735" (Subsecretaría de Previsión Social, ago-2025),
    Data raw/_external/ley_21735/nota_tecnica_ley_21735_previsionsocial.pdf, Tabla 1 (pág. 11 del documento, pág. 12
    del PDF): se lee del PDF. Publica todos los años intermedios: no se interpola nada. Tasa SIS = nota * de la Tabla 1
    ("Desde julio de 2025 ... 1,88%"); la Nota no fija qué parte del 2,5% es SIS (pág. 39: se determina según el
    DL 3.500), así que se supone 1,88% constante (supuesto documentado).
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

Pago con desfase: la remuneración de agosto se paga en septiembre. Cada tasa nueva rige para las remuneraciones desde agosto,
así que en un año calendario se pagan 8 meses con la tasa anterior (ene-ago) y 4 con la nueva (sep-dic). En 2025 el FAPP recauda 4 meses.

Escenario 2026-2035 (no es pronóstico, pesos de 2025). Supuestos en config/escenarios.yaml (compartidos con los KPI 1.2 y 2.2):
  - Masa imponible = masa mensual promedio 2025 × (población 15-64 INE del año / 2025) × (1 + g)^(año - 2025):
    cobertura constante; g = crecimiento real del salario. Base 'escenario': g = crecimiento_salario_real.base (1%);
    variantes 'escenario_crec_0' y 'escenario_crec_1_5' (0% y 1,5%).
  - Estado = gasto PGU/PBS/APS 2025 × (población 65+ INE del año / 2025): beneficio real constante.

Salidas (Data processed/):
  - fichas_previsionales_mensual.csv  n_ficha, mes_publicacion, mes_ref_cotizantes, mes_ref_ingreso, cotizantes,
                                      ingreso_promedio, aporte_trabajadores_mes, gasto_pgu_pbs_aps_12m_mm
  - kpi_participacion_partes.csv      base real por pagador: anio, aporte_trabajadores, aporte_empleador, aporte_estado,
                                      financiamiento_total, n_meses, fuente (montos en pesos)
  - kpi_flujo_comisionable.csv        anio, tipo (real / escenario / escenario_crec_0 / escenario_crec_1_5), variante (sin_sis / con_sis),
                                      trabajadores, empleador_ci, cuentas_individuales, seguro_social_fapp (sin SIS), sis,
                                      estado, flujo_total, kpi_1_3_pct, n_meses, supuestos
"""
import logging
import re
from pathlib import Path

import pandas as pd
import pypdf
import yaml

logging.getLogger("pypdf").setLevel(logging.ERROR)  # avisos de texto rotado en los gráficos de las fichas

ROOT = Path(__file__).resolve().parent.parent
FICHAS = ROOT / "Data raw" / "_external" / "fichas_previsionales"
FAPP = ROOT / "Data raw" / "_external" / "fapp" / "FAPP_estados_financieros_2025-12-31.pdf"
OUT = ROOT / "Data processed"
ANIOS = [2024, 2025]
TASA_TRABAJADOR = 0.10
ANIOS_ESCENARIO = range(2026, 2036)
ESCENARIOS = yaml.safe_load((ROOT / "config" / "escenarios.yaml").read_text(encoding="utf-8"))
CRECIMIENTO_BASE = ESCENARIOS["crecimiento_salario_real"]["base"]          # salario real, escenario base
CRECIMIENTO_VARIANTES = ESCENARIOS["crecimiento_salario_real"]["variantes"]


def nombre_escenario(g):
    """'escenario' para el base; 'escenario_crec_0', 'escenario_crec_1_5' para las variantes."""
    return "escenario" if g == CRECIMIENTO_BASE else "escenario_crec_" + f"{100 * g:g}".replace(".", "_")

NOTA_TECNICA = ROOT / "Data raw" / "_external" / "ley_21735" / "nota_tecnica_ley_21735_previsionsocial.pdf"

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


def tasa_cl(s):
    """'0,25%' -> 0.0025 ; 'No existe' / 'No existe**' -> 0.0"""
    s = s.strip().rstrip("*")
    return 0.0 if s.startswith("No") else float(s.rstrip("%").replace(",", ".")) / 100


def leer_nota_tecnica(path):
    """Tabla 1 de la Nota Técnica (pág. 12 del PDF): por año de inicio (agosto) -> (cuenta individual, rentabilidad
    protegida, SIS + compensación por expectativas de vida, SIS dentro del Seguro Social). Más la tasa SIS de la nota *."""
    texto = pypdf.PdfReader(path).pages[11].extract_text()
    fila = re.compile(r"^Agosto (\d{4})\s+(No existe\**|[\d,]+%)\s+([\d,]+%)\s+(No existe|[\d,]+%)\s+([\d,]+%)\s+"
                      r"([\d,]+%)\s+([\d,]+%)", re.M)
    tabla = {}
    for m in fila.finditer(texto):
        sis_aparte, ci, crp, sis_cev, total_reforma = (tasa_cl(m.group(k)) for k in (2, 3, 4, 5, 6))
        assert abs(ci + crp + sis_cev - total_reforma) < 1e-9, f"Tabla 1 no cuadra en {m.group(1)}"
        tabla[int(m.group(1))] = (ci, crp, sis_cev, sis_aparte == 0.0)
    nota = re.search(r"tasa vigente del SIS.*?es de\s*([\d,\s]+)%", texto, re.S)
    tasa_sis = tasa_cl(re.sub(r"\s", "", nota.group(1)) + "%")
    assert sorted(tabla) == list(range(2025, 2034)), f"años leídos de la Tabla 1: {sorted(tabla)}"
    return tabla, tasa_sis


def tasas_empleador(remuneracion):
    """(cuenta individual, Seguro Social sin SIS, SIS) para una remuneración (pd.Period mensual).
    La prima SIS existe en todos los años: hasta jul-2026 aparte, desde ago-2026 dentro del 2,5% del Seguro Social."""
    tramo = remuneracion.year if remuneracion.month >= 8 else remuneracion.year - 1
    vigentes = [a for a in TABLA_LEY if a <= tramo]
    if not vigentes:
        return 0.0, 0.0, TASA_SIS
    ci, crp, sis_cev, sis_dentro = TABLA_LEY[max(vigentes)]
    return ci, crp + sis_cev - (TASA_SIS if sis_dentro else 0.0), TASA_SIS


def tasas_pagadas_en(anio):
    """Suma de las tasas de los 12 meses pagados en `anio` (cada pago corresponde a la remuneración del mes anterior)."""
    ci = ss = sis = 0.0
    for mes in range(1, 13):
        t_ci, t_ss, t_sis = tasas_empleador(pd.Period(year=anio, month=mes, freq="M") - 1)
        ci, ss, sis = ci + t_ci, ss + t_ss, sis + t_sis
    return ci, ss, sis


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

# completitud: 12 meses de referencia por año, sin vacíos en cotizantes/ingreso
assert not fichas[["cotizantes", "ingreso_promedio"]].isna().any().any(), "fichas con cotizantes o ingreso vacío"
presentes = set(fichas.mes_ref_cotizantes)
print("\n   Completitud (mes de referencia de los cotizantes; x = ficha presente):")
print("   año  " + " ".join(f"{m:>3}" for m in range(1, 13)) + "   n")
faltantes = []
for anio in ANIOS:
    marcas = []
    for mes in range(1, 13):
        ref = pd.Period(year=anio, month=mes, freq="M")
        marcas.append("  x" if ref in presentes else "  -")
        if ref not in presentes:
            faltantes.append(ref)
    print(f"   {anio} " + " ".join(marcas) + f"  {sum(m == '  x' for m in marcas):>2}")
for ref in faltantes:  # la ficha sale ~2 meses después; N° 136 = marzo 2024
    pub = ref + 2
    print(f"   FALTA {ref}: descargar Ficha Estadística Previsional N° {136 + (pub - pd.Period('2024-03', 'M')).n} "
          f"({pub.strftime('%m-%Y')}) en spensiones.cl")

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
TABLA_LEY, TASA_SIS = leer_nota_tecnica(NOTA_TECNICA)
print(f"   Nota Técnica Ley 21.735, Tabla 1 (leída del PDF), tasa SIS {TASA_SIS:.2%}:")
for a, (ci, crp, sis_cev, dentro) in TABLA_LEY.items():
    print(f"     ago-{a}: cuenta individual {ci:.2%} | rentabilidad protegida {crp:.2%} | "
          f"SIS+CEV {sis_cev:.2%} {'(SIS dentro)' if dentro else '(SIS aparte)'}")
fapp = leer_fapp(FAPP)
empleador_2025 = (fapp["40.110"] + fapp["40.187"]) * 1000  # M$ -> pesos
print(f"   FAPP 40.110 Cotizaciones: M$ {fapp['40.110']:,} ; 40.187 SSP por identificar: M$ {fapp['40.187']:,}")

# masa imponible de cada mes de pago = cotizantes del mes × ingreso promedio (remuneración del mes anterior)
fichas["masa_imponible_mes"] = fichas.cotizantes * fichas.ingreso_promedio
fichas["tasa_ci"], fichas["tasa_ss"], fichas["tasa_sis"] = zip(*[tasas_empleador(m - 1) for m in fichas.mes_ref_cotizantes])
fichas["empleador_ci_mes"] = fichas.masa_imponible_mes * fichas.tasa_ci
fichas["empleador_ss_mes"] = fichas.masa_imponible_mes * fichas.tasa_ss
fichas["sis_mes"] = fichas.masa_imponible_mes * fichas.tasa_sis

# control del cambio de jul a ago 2026: sin el SIS, el Seguro Social solo sube por la cotización nueva
jul, ago = (tasas_empleador(pd.Period(m, "M")) for m in ("2026-07", "2026-08"))
print(f"   Control jul->ago 2026 (remuneración): SS sin SIS {jul[1]:.2%} -> {ago[1]:.2%} (+{ago[1] - jul[1]:.2%}); "
      f"SS + SIS {jul[1] + jul[2]:.2%} -> {ago[1] + ago[2]:.2%} (+{ago[1] + ago[2] - jul[1] - jul[2]:.2%}); "
      f"cotización nueva del empleador sin cuenta individual: +{(sum(TABLA_LEY[2026][:3]) - TABLA_LEY[2026][0]) - (sum(TABLA_LEY[2025][:3]) - TABLA_LEY[2025][0]) - TASA_SIS:.2%}")
ss_estimado_2025 = fichas.loc[fichas.mes_ref_cotizantes.dt.year == 2025, "empleador_ss_mes"].sum()
print(f"   Control empleador: 0,9% × masa imponible pagos sep-dic 2025 = {ss_estimado_2025 / 1e9:,.1f} mil millones "
      f"vs FAPP {empleador_2025 / 1e9:,.1f} mil millones ({empleador_2025 / ss_estimado_2025 - 1:+.1%})")

pilar = pd.read_csv(OUT / "pgu_pbs_aps_nacional_anual.csv")
estado = pilar[pilar.tipo_beneficio == "Total"].set_index("anio")["monto_nominal_mm"] * 1e6  # MM$ -> pesos

# =============================================================================
# 3) KPI por año
# =============================================================================
print("\n3) kpi_participacion_partes.csv (base real por pagador) ...")
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

base = pd.DataFrame(filas)
base["financiamiento_total"] = base.aporte_trabajadores + base.aporte_empleador + base.aporte_estado
base = base[["anio", "aporte_trabajadores", "aporte_empleador", "aporte_estado", "financiamiento_total", "n_meses", "fuente"]]
base.to_csv(OUT / "kpi_participacion_partes.csv", index=False)
print(base.drop(columns="fuente").to_string(index=False))

# =============================================================================
# 4) KPI 1.3, real: flujo comisionable 2024-2025
# =============================================================================
print("\n4) kpi_flujo_comisionable.csv ...")
filas = []
for _, b in base.iterrows():
    anio = int(b.anio)
    # parte del empleador a la cuenta individual: estimada (0,1% de la masa; en 2024 no existe)
    meses = fichas[fichas.mes_ref_cotizantes.dt.year == anio]
    empleador_ci = round(meses.empleador_ci_mes.sum() * 12 / len(meses))
    filas.append({
        "anio": anio, "tipo": "real", "trabajadores": b.aporte_trabajadores, "empleador_ci": empleador_ci,
        "seguro_social_fapp": b.aporte_empleador, "estado": b.aporte_estado, "n_meses": int(b.n_meses),
        "sis": round(meses.sis_mes.sum() * 12 / len(meses)),
        "supuestos": ("Trabajadores estimado (cotizantes × ingreso promedio × 10%); empleador a cuenta individual estimado "
                      "(0,1% de la masa imponible pagada sep-dic, Ley 21.735); Seguro Social = FAPP real; Estado = PGU+PBS+APS nominal"),
    })

# =============================================================================
# 5) Escenario 2026-2035 (pesos de 2025)
# =============================================================================
proy = pd.read_csv(OUT / "proyeccion_envejecimiento_pais.csv").set_index("anio")
masa_mensual_2025 = fichas.loc[fichas.mes_ref_cotizantes.dt.year == 2025, "masa_imponible_mes"].mean()
for tipo, g in [(nombre_escenario(g), g) for g in [CRECIMIENTO_BASE] + CRECIMIENTO_VARIANTES]:
    for anio in ANIOS_ESCENARIO:
        masa = (masa_mensual_2025 * proy.loc[anio, "pob_15_64"] / proy.loc[2025, "pob_15_64"]
                * (1 + g) ** (anio - 2025))
        suma_ci, suma_ss, suma_sis = tasas_pagadas_en(anio)
        filas.append({
            "anio": anio, "tipo": tipo,
            "trabajadores": round(12 * masa * TASA_TRABAJADOR),
            "empleador_ci": round(masa * suma_ci),
            "seguro_social_fapp": round(masa * suma_ss),
            "sis": round(masa * suma_sis), "n_meses": 12,
            "estado": round(estado.loc[2025] * proy.loc[anio, "pob_65_mas"] / proy.loc[2025, "pob_65_mas"]),
            "supuestos": ("Escenario, pesos de 2025: cobertura constante (masa 2025 × población 15-64 INE), "
                          + ("ingreso real constante" if g == 0 else f"ingreso real +{g:.1%} anual".replace(".", ","))
                          + "; Estado = gasto 2025 × población 65+ INE (beneficio real constante); "
                          "tasas del empleador según Nota Técnica Ley 21.735, Tabla 1"),
        })

base_flujo = pd.DataFrame(filas)
base_flujo["cuentas_individuales"] = base_flujo.trabajadores + base_flujo.empleador_ci
variantes = []
for variante, suma_sis in [("sin_sis", False), ("con_sis", True)]:
    v = base_flujo.assign(variante=variante)
    v["flujo_total"] = v.cuentas_individuales + v.seguro_social_fapp + v.estado + (v.sis if suma_sis else 0)
    v["supuestos"] = v.supuestos + ("; SIS fuera del flujo en todos los años" if not suma_sis else
                                    f"; SIS {TASA_SIS:.2%} de la masa imponible dentro del flujo en todos los años".replace(".", ","))
    variantes.append(v)
flujo = pd.concat(variantes, ignore_index=True)
flujo["kpi_1_3_pct"] = round(100 * flujo.cuentas_individuales / flujo.flujo_total, 2)
flujo = flujo[["anio", "tipo", "variante", "trabajadores", "empleador_ci", "cuentas_individuales", "seguro_social_fapp",
               "sis", "estado", "flujo_total", "kpi_1_3_pct", "n_meses", "supuestos"]]
flujo.to_csv(OUT / "kpi_flujo_comisionable.csv", index=False)
print((flujo.drop(columns="supuestos").set_index(["variante", "tipo", "anio"])
       .assign(**{c: lambda d, c=c: (d[c] / 1e12).round(2) for c in
                  ["trabajadores", "empleador_ci", "cuentas_individuales", "seguro_social_fapp", "sis", "estado",
                   "flujo_total"]}))
      .to_string())
print("   (montos en billones de pesos)")
