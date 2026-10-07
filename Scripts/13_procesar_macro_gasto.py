"""
PIB (Banco Central) y gasto público en vejez (DIPRES). Insumo de los KPI 2.1 y 2.2.

Fuentes (Data raw/_external/):
  - macro/CCNN2018_P0_V2.xlsx        PIB anual 2013-2025, referencia 2018, miles de millones de pesos:
                                     a precios corrientes y volumen a precios del año anterior encadenado.
  - dipres/articles-416514_doc_xls.xlsx   Estadísticas de las Finanzas Públicas 2016-2025, hojas de clasificación funcional
                                     del Gobierno Central: CFEGCT (millones de pesos corrientes), CFEGCT$25 (millones de pesos de 2025),
                                     CFEGCT%PIB (% del PIB).

Salidas (Data processed/):
  - macro_pib_anual.csv        anio, pib_corriente_mm, pib_real_mm_2018, pib_real_var_pct
                               (mm = millones de pesos; real = volumen encadenado, referencia 2018)
  - gasto_proteccion_social.csv  anio, categoria (Gasto total / Protección social / Edad avanzada),
                               gasto_corriente_mm, gasto_mm_2025, pct_pib

Notas:
  - 'Edad avanzada' (código COFOG 7102) incluye las pensiones del sistema antiguo, la PGU y los aportes solidarios que
    paga el Estado; es el costo público en vejez que usa el KPI 2.1. 2021 es atípico en 'Protección social' total por los
    bonos COVID, pero no afecta 'Edad avanzada'.
  - El PIB real encadenado (referencia 2018) NO es comparable por nivel con pesos de 2025: para los índices se usa base 2016 = 100.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
EXT = ROOT / "Data raw" / "_external"
OUT = ROOT / "Data processed"
OUT.mkdir(parents=True, exist_ok=True)


def pib():
    d = pd.read_excel(EXT / "macro" / "CCNN2018_P0_V2.xlsx", sheet_name="Cuadro", header=None)
    hdr = next(i for i in range(len(d)) if str(d.iloc[i, 0]).strip() == "Reg")
    fechas = pd.to_datetime(d.iloc[hdr, 2:], errors="coerce")
    corr = d.loc[d[1].astype(str).str.contains("corrientes", case=False), :].iloc[0, 2:].astype(float)
    real = d.loc[(d[1].astype(str).str.contains("encadenado")) & ~d[1].astype(str).str.contains("desestac"), :].iloc[0, 2:].astype(float)
    out = pd.DataFrame({"anio": fechas.dt.year.values,
                        "pib_corriente_mm": corr.values * 1000,  # miles de millones -> millones
                        "pib_real_mm_2018": real.values * 1000})
    out["pib_real_var_pct"] = 100 * out["pib_real_mm_2018"].pct_change()
    return out.dropna(subset=["anio"]).astype({"anio": int})


def lee_funcional(hoja):
    d = pd.read_excel(EXT / "dipres" / "articles-416514_doc_xls.xlsx", sheet_name=hoja, header=None)
    hdr = next(i for i in range(15) if str(d.iloc[i, 2]).replace(".0", "") == "2016")
    anios = [int(float(a)) for a in d.iloc[hdr, 2:12]]
    quiero = {"Gasto total": "gasto total", "Protección social": "protección social", "Edad avanzada": "edad avanzada"}
    out = {}
    for i in range(hdr + 1, len(d)):
        etiqueta = " ".join(str(x) for x in d.iloc[i, :2].tolist() if pd.notna(x)).lower()
        for nombre, clave in quiero.items():
            if clave in etiqueta and nombre not in out:
                out[nombre] = d.iloc[i, 2:12].astype(float).tolist()
    return anios, out


def gasto():
    filas = []
    base = {}
    for hoja, col in [("CFEGCT", "gasto_corriente_mm"), ("CFEGCT$25", "gasto_mm_2025"), ("CFEGCT%PIB", "pct_pib")]:
        anios, valores = lee_funcional(hoja)
        for cat, vals in valores.items():
            for a, v in zip(anios, vals):
                base.setdefault((a, cat), {})[col] = v
    for (a, cat), v in sorted(base.items()):
        filas.append(dict(anio=a, categoria=cat, **v))
    return pd.DataFrame(filas)


if __name__ == "__main__":
    p = pib()
    g = gasto()
    p.to_csv(OUT / "macro_pib_anual.csv", index=False)
    g.to_csv(OUT / "gasto_proteccion_social.csv", index=False)
    print(f"macro_pib_anual.csv: {len(p)} filas ({p.anio.min()}-{p.anio.max()})")
    print(p.round(1).to_string(index=False))
    print(f"\ngasto_proteccion_social.csv: {len(g)} filas")
    print(g[g.categoria == "Edad avanzada"].round(2).to_string(index=False))
    # chequeos
    assert set(g.categoria) == {"Gasto total", "Protección social", "Edad avanzada"}, g.categoria.unique()
    assert g.groupby("categoria").anio.nunique().eq(10).all()
    ea = g[g.categoria == "Edad avanzada"].set_index("anio")
    m = p.set_index("anio")
    chk = (100 * ea.gasto_corriente_mm / m.pib_corriente_mm.reindex(ea.index)).round(2)
    print("\nChequeo % PIB (propio vs publicado DIPRES):")
    print(pd.DataFrame({"propio": chk, "dipres": ea.pct_pib.round(2)}).T.to_string())
