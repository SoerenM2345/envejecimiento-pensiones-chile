"""
Procesa los "Informe Estadístico Trimestral del Pilar Solidario" (Subsecretaría de
Previsión Social), ubicados en Data raw/_external/pilar_solidario/ (solo los informes de cierre OND;
los intermedios están en archive/). Cubre PGU, APS de vejez, PBS de
vejez, PBS de invalidez y APS de invalidez. Insumo de los KPI 2.1 (costo real por adulto
mayor) y 2.2 (financiamiento dedicado).

Fuente de cada salida:
  - Serie mensual país: bloque 'Serie resumen de pagos de beneficios acumulados' de la hoja
    '1.1' del informe MÁS RECIENTE (jul-2008 en adelante). Tiene N° de beneficios, monto real y
    monto nominal por tipo de beneficio. La PGU aparece sumada (contributiva + no contributiva).
  - Resumen anual país: bloque 'Resumen anual' ('Año AAAA') de cada informe de cierre (OND).
    Se usa para validar la suma de la serie mensual.
  - Región: hoja '1.2' de los informes que traen el desglose regional trimestral.

Salidas (Data processed/):
  - pgu_pbs_aps_nacional_mensual.csv   periodo, tipo_beneficio, n_beneficios, monto_real_mm, monto_nominal_mm
  - pgu_pbs_aps_nacional_anual.csv     anio, tipo_beneficio, n_promedio_beneficios, monto_nominal_mm, monto_real_mm, meses
  - pgu_pbs_aps_region_trimestral.csv  trimestre, region_id, region_nombre, tipo_beneficio, sexo, n_beneficiarios, monto_total_mm

Notas:
  - Unidad de salida: millones de pesos (MM$). Los informes de 2023 y anteriores vienen en miles de
    pesos (M$); se detecta en el encabezado y se convierte.
  - 'monto_real' viene en pesos del último mes del informe fuente (diciembre de su año), no en pesos de hoy.
  - 'Total' es la suma de todos los tipos: no sumarlo junto a los demás.
  - Los informes de 2022 (otro formato) y los de trimestres intermedios de 2023 (hojas por beneficio) no se usan.
  - El orden de los informes sale del año en el nombre del archivo (anio_informe); el más reciente aporta la serie mensual.
"""
import re
import warnings
from datetime import datetime
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")  # openpyxl: avisos de estilos de los xlsx fuente

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "Data raw" / "_external" / "pilar_solidario"  # informes de cierre (OND) 2023, 2024 y 2025
OUT = ROOT / "Data processed"
OUT.mkdir(parents=True, exist_ok=True)

TIPOS = [  # (prefijo normalizado, nombre de salida); el orden importa ('pgu no contrib' antes que 'pgu')
    ("pgu no contrib", "PGU no contributiva"),
    ("pgu contrib", "PGU contributiva"),
    ("pgu", "PGU"),
    ("aps vejez", "APS vejez"),
    ("pbs vejez", "PBS vejez"),
    ("pbs invalidez", "PBS invalidez"),
    ("aps invalidez", "APS invalidez"),
    ("total", "Total"),
]
SEXOS = ["Mujeres", "Hombres", "Total"]

REGION_KEYS = [  # (fragmento en el nombre, id oficial, nombre corto)
    ("arica", 15, "Arica y Parinacota"), ("tarapac", 1, "Tarapacá"), ("antofagasta", 2, "Antofagasta"),
    ("atacama", 3, "Atacama"), ("coquimbo", 4, "Coquimbo"), ("valpara", 5, "Valparaíso"),
    ("metropolitana", 13, "Metropolitana"), ("o'higgins", 6, "O'Higgins"), ("libertador", 6, "O'Higgins"),
    ("maule", 7, "Maule"), ("ñuble", 16, "Ñuble"), ("biob", 8, "Biobío"), ("araucan", 9, "La Araucanía"),
    ("los ríos", 14, "Los Ríos"), ("los lagos", 10, "Los Lagos"), ("ays", 11, "Aysén"),
    ("magallanes", 12, "Magallanes"),
]


def tipo_beneficio(label):
    if not isinstance(label, str):
        return None
    s = re.sub(r"\d+", "", label).strip().lower()  # quita marcas de nota al pie ('PGU no contributiva1')
    s = re.sub(r"\s+", " ", s)
    for key, nombre in TIPOS:
        if s.startswith(key):
            return nombre
    return None


def region_de(label):
    s = str(label).lower()
    for key, rid, nombre in REGION_KEYS:
        if key in s:
            return rid, nombre
    return None, None


def factor_a_mm(texto):
    """'(MM$)' -> 1; '(M$)' -> 1/1000 (miles de pesos a millones)."""
    t = str(texto)
    if "MM$" in t:
        return 1.0
    if "M$" in t:
        return 1 / 1000
    raise ValueError(f"no se reconoce la unidad en {t!r}")


def anio_informe(path):
    """Año del informe según el nombre del archivo (OND-2023, OND-2024, OND-2025): el más reciente gana al deduplicar."""
    return int(re.findall(r"20\d{2}", path.name)[-1])


def parse_serie_mensual(path):
    """Bloque 'Serie resumen ...' de la hoja 1.1: filas = mes, 5 columnas por tipo [N, %, real, %, nominal]."""
    df = pd.read_excel(path, sheet_name="1.1", header=None)
    ini = next(i for i in range(len(df)) if str(df.iloc[i, 1]).lower().startswith("serie resumen"))
    fila_tipos = next(i for i in range(ini, ini + 8) if tipo_beneficio(df.iloc[i, 2]) is not None)
    fila_medidas = fila_tipos + 1
    # columna de cada medida dentro de cada bloque de tipo. Informes 2023-2024: 5 columnas por tipo
    # [N, %, real, %, nominal]; informes 2025: 3 columnas [N, real, nominal]. Se lee de la fila de encabezados.
    tipo_cols = [(j, tipo_beneficio(df.iloc[fila_tipos, j])) for j in range(2, df.shape[1])]
    tipo_cols = [(j, t) for j, t in tipo_cols if t is not None]
    cols = {}
    for k, (j, t) in enumerate(tipo_cols):
        j_fin = tipo_cols[k + 1][0] if k + 1 < len(tipo_cols) else df.shape[1]
        medidas = {}
        for c in range(j, j_fin):
            etiqueta = str(df.iloc[fila_medidas, c]).lower()
            if "nominal" in etiqueta:
                medidas["nom"] = c
            elif "real" in etiqueta:
                medidas["real"] = c
            elif etiqueta.startswith("n°") and "n" not in medidas:
                medidas["n"] = c
        if len(medidas) == 3:
            cols[t] = medidas
    f = factor_a_mm(df.iloc[fila_medidas, next(iter(cols.values()))["real"]])
    filas = []
    for i in range(fila_tipos + 3, len(df)):
        c1 = df.iloc[i, 1]
        if isinstance(c1, str) and c1.strip().lower().startswith("fuente"):
            break
        if not isinstance(c1, (datetime, pd.Timestamp)):
            continue  # filas 'Promedio AAAA'
        for t, m in cols.items():
            n, real, nom = df.iloc[i, m["n"]], df.iloc[i, m["real"]], df.iloc[i, m["nom"]]
            if pd.isna(n) and pd.isna(nom):
                continue
            filas.append(dict(periodo=c1.strftime("%Y-%m-01"), tipo_beneficio=t, n_beneficios=n,
                              monto_real_mm=real * f if pd.notna(real) else None,
                              monto_nominal_mm=nom * f if pd.notna(nom) else None))
    return filas


def parse_resumen_anual(path):
    df = pd.read_excel(path, sheet_name="1.1", header=None)
    out, anio, f = [], None, 1.0
    for i in range(len(df)):
        c1 = df.iloc[i, 1]
        if isinstance(c1, str) and c1.strip().lower().startswith("periodo") and pd.notna(df.iloc[i, 4]):
            try:
                f = factor_a_mm(df.iloc[i, 4])
            except ValueError:
                pass
        if isinstance(c1, str) and re.match(r"^Año\s+\d{4}", c1.strip()):
            anio = int(re.findall(r"\d{4}", c1)[0])
        elif isinstance(c1, str) and c1.strip().lower().startswith("fuente"):
            anio = None
        t = tipo_beneficio(df.iloc[i, 2])
        if anio is None or t is None:
            continue
        out.append(dict(anio=anio, tipo_beneficio=t, n_promedio_beneficios=df.iloc[i, 9],
                        monto_nominal_mm=df.iloc[i, 10] * f, monto_real_mm=df.iloc[i, 11] * f, fuente=path.name))
    return out


def parse_region(path):
    """Hoja 1.2 con desglose por región. Devuelve [] si la hoja es de otro tipo (informes de trimestres intermedios)."""
    df = pd.read_excel(path, sheet_name="1.2", header=None)
    hdr = next((i for i in range(15) if str(df.iloc[i, 1]).strip().lower().startswith("regi")), None)
    if hdr is None:
        return []
    cabecera = [str(df.iloc[hdr, j]).lower() for j in range(df.shape[1])]
    if len(df) > hdr + 1 and str(df.iloc[hdr + 1, 3]).lower().startswith("mujeres"):
        col0, trimestre_row = None, hdr + 1  # no se espera: variante con sexos en la segunda fila
    # Variante (a), 2024: bloques mensuales + 'Total <trimestre>' (3 sexos x [N, monto, promedio])
    # Variante (b), 2023: 3 sexos directamente en las columnas 3, 6, 9 (N promedio, monto en M$, promedio)
    col_total = next((j for j, c in enumerate(cabecera) if c.startswith("total ") and j > 3), None)
    if col_total is None and cabecera[3].startswith("mujeres"):
        col_total, inicio_datos = 3, hdr + 2
    elif col_total is not None:
        inicio_datos = hdr + 3
    else:
        return []
    trimestre = str(df.iloc[hdr - 2, 1]).strip("() ") if col_total == 3 else str(df.iloc[hdr, col_total]).replace("Total", "").strip()
    unidad_txt = df.iloc[inicio_datos - 1, col_total + 1]
    f = factor_a_mm(unidad_txt)
    out, region_actual = [], None
    for i in range(inicio_datos, len(df)):
        c1, c2 = df.iloc[i, 1], df.iloc[i, 2]
        if isinstance(c1, str) and c1.strip().lower().startswith(("fuente", "nota")):
            break
        if isinstance(c1, str) and c1.strip():
            region_actual = c1.strip()
        t = tipo_beneficio(c2)
        rid, rnom = region_de(region_actual)
        if t is None or rid is None:
            continue
        for k, sexo in enumerate(SEXOS):
            n, monto = df.iloc[i, col_total + 3 * k], df.iloc[i, col_total + 3 * k + 1]
            if pd.isna(n):
                continue
            out.append(dict(trimestre=trimestre, region_id=rid, region_nombre=rnom, tipo_beneficio=t, sexo=sexo,
                            n_beneficiarios=n, monto_total_mm=monto * f, fuente=path.name))
    return out


def main():
    archivos = sorted(RAW.glob("Informe-Estadistico*.xlsx"), key=anio_informe)
    print(f"{len(archivos)} informes en {RAW}")
    ultimo = archivos[-1]
    print("Serie mensual desde:", ultimo.name)
    mensual = pd.DataFrame(parse_serie_mensual(ultimo))
    mensual = mensual.drop_duplicates(["periodo", "tipo_beneficio"], keep="last").sort_values(["periodo", "tipo_beneficio"])

    anual_inf, region, fallos = [], [], []
    for p in archivos:
        for nombre, fn, destino in [("resumen anual", parse_resumen_anual, anual_inf), ("región", parse_region, region)]:
            try:
                filas = fn(p)
            except Exception as e:  # noqa: BLE001 -- un informe con formato distinto no debe tumbar el resto
                fallos.append((p.name[-34:], nombre, repr(e)[:90]))
                continue
            destino += filas
            print(f"  {p.name[-34:]:34} {nombre:14} {len(filas):4} filas")

    # anual = suma de los meses (flujo) y promedio de beneficiarios, solo años con los 12 meses
    m = mensual.assign(anio=mensual.periodo.str[:4].astype(int))
    g = m.groupby(["anio", "tipo_beneficio"])
    anual = g.agg(n_promedio_beneficios=("n_beneficios", "mean"), monto_nominal_mm=("monto_nominal_mm", "sum"),
                  monto_real_mm=("monto_real_mm", "sum"), meses=("periodo", "nunique")).reset_index()
    anual = anual[anual.meses == 12]

    region = pd.DataFrame(region).drop_duplicates(["trimestre", "region_id", "tipo_beneficio", "sexo"], keep="last")
    mensual.to_csv(OUT / "pgu_pbs_aps_nacional_mensual.csv", index=False)
    anual.to_csv(OUT / "pgu_pbs_aps_nacional_anual.csv", index=False)
    region.drop(columns="fuente").to_csv(OUT / "pgu_pbs_aps_region_trimestral.csv", index=False)
    print(f"-> nacional_mensual {len(mensual)} filas | nacional_anual {len(anual)} | region_trimestral {len(region)}")
    for f_ in fallos:
        print("   (omitido)", f_)

    # validación: suma de la serie mensual vs 'Resumen anual' publicado
    pub = pd.DataFrame(anual_inf)
    if len(pub):
        chk = pub[pub.tipo_beneficio == "Total"].merge(anual[anual.tipo_beneficio == "Total"], on="anio", suffixes=("_pub", "_serie"))
        chk["dif_pct"] = 100 * (chk.monto_nominal_mm_serie / chk.monto_nominal_mm_pub - 1)
        print("Validación Total nominal MM$ (serie mensual vs resumen anual publicado):")
        print(chk[["anio", "monto_nominal_mm_pub", "monto_nominal_mm_serie", "dif_pct"]].round(2).to_string(index=False))
    print("\nGasto anual nominal (MM$), tipos principales:")
    print(anual[anual.anio >= 2019].pivot(index="anio", columns="tipo_beneficio", values="monto_nominal_mm").round(0))


if __name__ == "__main__":
    main()
