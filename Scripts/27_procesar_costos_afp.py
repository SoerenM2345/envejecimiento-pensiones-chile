"""
Ingresos, gastos y rentabilidad de las Administradoras de Fondos de Pensiones (sistema), 2016-2025.
Insumo para el modelo de negocio de la AFP (ingreso = cotizantes × sueldo imponible × comisión) y el costo por cliente.

Fuente: Data raw/_external/sp_costos_administracion/costos_administracion_AAAA.pdf, Superintendencia de Pensiones,
«Costos de administración de los Fondos de Pensiones» (art. 28 del DL 3.500), un informe anual por año. Descargados de
https://www.spensiones.cl/portal/institucional/594/articles-NNNNN_recurso_1.pdf (ver LEEME.md de la carpeta).
Se lee el texto de la página 2-3 (resumen del sistema), que trae las cifras ya agregadas:
  ingresos totales, por comisiones, rentabilidad del encaje y otros; gastos totales, de personal, de operación,
  depreciación y otros; ganancia; rentabilidad sobre patrimonio y activos (bruta y neta del encaje y coligadas).

Además se leen los cuadros N° 1 (estado de resultados por administradora, M$ de diciembre del año) y N° 2 (rentabilidad por
administradora) del año de cada informe, y del texto la composición del gasto en % (personal administrativo y de ventas; dentro
de la operación: administración, computación, otros y comercialización).

Salida (Data processed/):
  - afp_resultados_sistema.csv   una fila por año: anio, ingresos_mm, comisiones_mm, encaje_mm, otros_ingresos_mm,
        gastos_mm, gastos_personal_mm, gastos_operacion_mm, depreciacion_mm, otros_gastos_mm, ganancia_mm,
        roe_pct, roa_pct, roe_neta_pct, roa_neta_pct, personal_admin_pct, personal_ventas_pct, op_administracion_pct,
        op_computacion_pct, op_otros_pct, op_comercializacion_pct (% del gasto total), deflactor_2025, y las cifras en millones
        de pesos de 2025 (*_mm_2025)
  - afp_resultados_por_afp.csv   una fila por año y administradora (y «Sistema»): ingresos_ordinarios, encaje, prima_sis,
        gastos_personal, depreciacion, deterioro, otros_gastos_operacion, ganancia_antes_impuesto, impuesto, descontinuadas
        (millones de pesos del año, gastos con signo negativo como en el cuadro), roe_pct, roa_pct, roe_neta_pct, roa_neta_pct
        (UNO 2019 sin rentabilidad: partió en octubre). Página: cuadro N° 1 = p. 4 (2016) o 5; cuadro N° 2 = p. 6 o 7.

Notas:
  - Millones de pesos de cada año (el informe usa pesos de diciembre). Para pesos de 2025 se usa el IPC anual promedio
    (ipc_anual.csv), el mismo deflactor del resto del proyecto; difiere un poco del IPC de diciembre que usa la Superintendencia.
  - Las comisiones incluyen las de cotizantes, pensionados en retiro programado y renta temporal, APV y Cuenta 2: no son solo
    las de los cotizantes obligatorios.
  - Comparaciones entre AFP (cuadro 1 por administradora) no se extraen aquí.
"""
import re
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Data raw" / "_external" / "sp_costos_administracion"
DP = ROOT / "Data processed"

NUM = r"([\d\.]+)"
P = r"\([\d,\.]+%\)"  # porcentaje entre paréntesis
# El texto del PDF trae espacios sueltos dentro de números y palabras («7 48.085», «patrimoni o»): se buscan los patrones en el
# texto SIN espacios.
PATRONES = {  # columna -> expresión regular sobre el texto de las páginas 2 y 3 sin espacios (millones de pesos)
    "ingresos_mm": rf"obtuvieroningresosporuntotalde{NUM}millones",
    "comisiones_mm": rf"obtenidosporlasAFP,{NUM}millones",
    "encaje_mm": rf"{NUM}millonesdepesos{P}(?:deltotaldeingresos,)?(?:provienendela|correspondenala)rentabilidaddelencaje",
    "otros_ingresos_mm": rf"{NUM}millonesdepesos{P}(?:deltotaldeingresos,provienendeotros|correspondenaotros)ingresos",
    "gastos_mm": rf"gastosqueascendieronauntotalde{NUM}millones",
    "gastos_personal_mm": rf"{NUM}millonesdepesos{P}correspondenalgastoenpersonal",
    "gastos_operacion_mm": rf"{NUM}millonesdepesos{P}(?:deloscostostotales)?correspondenagastosdeoperación",
    "depreciacion_mm": rf"{NUM}millonesdepesos{P}correspondenadepreciación",
    "otros_gastos_mm": rf"{NUM}millonesdepesos{P}correspondenaotrosgastos",
    "ganancia_mm": rf"obtuvieronunagananciade{NUM}millones",
    "roe_pct": r"patrimoniodelasAFPalcanzó(?:a|un)([\d,]+)%",
    "roa_pct": r"activostotales,enelmismoperíodo,fuede([\d,]+)%",
}
NETAS = r"corresponden?a([\d,]+)%y([\d,]+)%,respectivamente"
PARTES_PCT = {  # columna -> patrón (% del gasto total, con una decimal, como lo publica el informe)
    "personal_admin_pct": r"personaldeventas,repartidosentre([\d,]+)%y[\d,]+%",
    "personal_ventas_pct": r"personaldeventas,repartidosentre[\d,]+%y([\d,]+)%",
    "op_administracion_pct": r"administración\(([\d,]+)%\)",
    "op_computacion_pct": r"computación\(([\d,]+)%\)",
    "op_otros_pct": r"otrosgastosoperacionales\(([\d,]+)%\)",
    "op_comercializacion_pct": r"comercialización\(([\d,]+)%\)",
}
FILAS_C1 = {  # fila del cuadro N° 1 (estado de resultados por administradora, M$ de diciembre del año) -> columna
    "Ingresos ordinarios": "ingresos_ordinarios",
    "Rentabilidad del Encaje": "encaje",
    "Prima de seguro de invalidez y sobrevivencia": "prima_sis",
    "Gastos de personal": "gastos_personal",
    "Depreciación y amortización": "depreciacion",
    "Pérdidas por deterioro": "deterioro",
    "Otros gastos varios de operación": "otros_gastos_operacion",
    "Ganancia (pérdida) antes de impuesto": "ganancia_antes_impuesto",
    "Gasto (ingreso) por impuesto a las ganancias": "impuesto",
    "Ganancia (pérdida) de operaciones descontinuadas": "descontinuadas",
}
FILAS_C2 = {"RENTABILIDAD SOBRE EL PATRIMONIO": "roe_pct", "RENTABILIDAD SOBRE ACTIVOS TOTALES": "roa_pct",
            "RENTABILIDAD NETA SOBRE EL PATRIMONIO": "roe_neta_pct", "RENTABILIDAD NETA SOBRE ACTIVOS TOTALES": "roa_neta_pct"}
ES_NUM = re.compile(r"^-?\d{1,3}(?:\.\d{3})*$")
ES_PCT = re.compile(r"^-?[\d\.]+,\d+%$|^-$")


def _num(s: str) -> float:
    return float(s.replace(".", "").replace(",", "."))


def leer(pdf: Path) -> dict:
    texto = " ".join((PdfReader(pdf).pages[i].extract_text() or "") for i in (1, 2))
    anio = int(re.search(r"AÑO\s*(\d{4})", texto).group(1))
    texto = re.sub(r"\s+", "", texto)
    fila = {"anio": anio}
    for col, pat in PATRONES.items():
        m = re.search(pat, texto)
        assert m, f"{pdf.name}: no se encontró {col}"
        fila[col] = _num(m.group(1).rstrip("."))
    m = re.search(NETAS, texto)
    fila["roe_neta_pct"], fila["roa_neta_pct"] = _num(m.group(1)), _num(m.group(2))
    for col, pat in PARTES_PCT.items():
        m = re.search(pat, texto)
        assert m, f"{pdf.name}: no se encontró {col}"
        fila[col] = _num(m.group(1))
    return fila


def _valores(tokens: list, inicio: int, n: int, es_valor) -> list:
    """Los n valores que siguen a la etiqueta (salta palabras como «(menos)» antes del primero)."""
    out = []
    for t in tokens[inicio:]:
        if es_valor(t):
            out.append(t)
            if len(out) == n:
                return out
        elif out:
            break
    raise ValueError(f"faltan valores: {out}")


def _tabla(texto: str, filas: dict, es_valor, conv) -> pd.DataFrame:
    """Primera tabla «A.F.P. ...» del texto: una fila por administradora (y SISTEMA), una columna por fila del cuadro."""
    texto = re.sub(r"\s+", " ", texto)
    i = texto.index("A.F.P. ")
    cab = texto[i + 7:].split(" ")
    afps = []
    for t in cab:
        if t.isupper() and not ES_NUM.match(t) and t not in ("(5)", "(1)"):
            afps.append(t)
            if t == "SISTEMA":
                break
    cuerpo = texto[i:]
    out = {}
    for etiqueta, col in filas.items():
        j = cuerpo.find(etiqueta)
        if j < 0:
            continue
        resto = cuerpo[j + len(etiqueta):].split(" ")
        out[col] = [conv(v) for v in _valores(resto, 0, len(afps), es_valor)]
    return pd.DataFrame(out, index=pd.Index(afps, name="afp"))


def leer_por_afp(pdf: Path) -> pd.DataFrame:
    """Cuadros N° 1 y 2 del año del informe (no los del año anterior, que vienen en la página siguiente)."""
    r = PdfReader(pdf)
    paginas = [p.extract_text() or "" for p in r.pages]
    anio = int(re.search(r"AÑO\s*(\d{4})", paginas[1]).group(1))
    c1 = next(t for t in paginas if "CUADRO" in t and "ESTADO DE RESULTADOS" in t)
    c2 = next(t for t in paginas if "CUADRO" in t and "RENTABILIDAD DE LAS" in t)
    a = _tabla(c1, FILAS_C1, lambda t: bool(ES_NUM.match(t)), lambda v: _num(v) / 1e3)      # M$ -> millones de pesos
    b = _tabla(c2, FILAS_C2, lambda t: bool(ES_PCT.match(t)), lambda v: float("nan") if v == "-" else _num(v.rstrip("%")))
    d = a.join(b).reset_index()
    d["afp"] = d.afp.str.capitalize().replace({"Planvital": "PlanVital", "Sistema": "Sistema"})
    d.insert(0, "anio", anio)
    return d


def main():
    d = pd.DataFrame([leer(p) for p in sorted(SRC.glob("costos_administracion_*.pdf"))]).sort_values("anio")
    assert list(d.anio) == list(range(2016, 2026)), d.anio.tolist()
    # chequeos: las partes suman el total (redondeo del informe: ±3 millones)
    ing = d.comisiones_mm + d.encaje_mm + d.otros_ingresos_mm
    gas = d.gastos_personal_mm + d.gastos_operacion_mm + d.depreciacion_mm + d.otros_gastos_mm
    assert ((ing - d.ingresos_mm).abs() <= 3).all(), d.assign(dif=ing - d.ingresos_mm)[["anio", "dif"]]
    # gastos: en 2019 y 2021 el total del informe incluye además la prima del seguro de invalidez y sobrevivencia (≈ 330 millones,
    # cuadro N° 1), que no aparece en el desglose del texto; se acepta esa diferencia
    assert ((gas - d.gastos_mm).abs() <= 400).all(), d.assign(dif=gas - d.gastos_mm)[["anio", "dif"]]
    ipc = pd.read_csv(DP / "ipc_anual.csv").set_index("anio").deflactor_2025
    d["deflactor_2025"] = d.anio.map(ipc)
    for c in [c for c in d.columns if c.endswith("_mm")]:
        d[f"{c}_2025"] = (d[c] * d.deflactor_2025).round(0)
    d.to_csv(DP / "afp_resultados_sistema.csv", index=False)
    a = pd.concat([leer_por_afp(p) for p in sorted(SRC.glob("costos_administracion_*.pdf"))], ignore_index=True)
    a = a.fillna({"deterioro": 0.0, "descontinuadas": 0.0})
    sis = a[a.afp == "Sistema"].set_index("anio")
    # chequeo: la suma de las administradoras = la columna SISTEMA (±2 millones por redondeo)
    suma = a[a.afp != "Sistema"].groupby("anio")[["ingresos_ordinarios", "gastos_personal", "otros_gastos_operacion"]].sum()
    assert ((suma - sis[suma.columns]).abs() <= 2).all().all(), suma - sis[suma.columns]
    assert (sis.encaje.round(0) == d.set_index("anio").encaje_mm).all(), "encaje del cuadro N° 1 distinto del texto"
    a.round(3).to_csv(DP / "afp_resultados_por_afp.csv", index=False)
    print(a[a.anio == 2025].round(1).to_string(index=False))
    print(d[["anio", "ingresos_mm", "comisiones_mm", "gastos_mm", "ganancia_mm", "roe_pct", "comisiones_mm_2025", "gastos_mm_2025"]].to_string(index=False))


if __name__ == "__main__":
    main()
