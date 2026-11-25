"""N.5e-v2: tabla de los 15 territorios (16 regiones, Biobío y Ñuble unidos) en letra Calibri, solo la versión «slide».

Columnas: Región · Cambio (%) · Cambio de puestos · Cobertura 2007 · Cobertura 2024. Orden: cambio en %, de mayor a menor (Chile arriba, como referencia).
Se dibuja directamente con Pillow porque Calibri no está instalada en el sistema: se usa el archivo de Microsoft Office (PowerPoint / OneNote).
Datos: Data processed/kpi_seleccion_dos_preguntas.csv (Scripts/35_seleccion_dos_preguntas.py).

Uso: python Scripts/36_tabla_cambio_regiones_calibri.py
Salida: Outputs/figuras_pptx/S13_regiones_criticas/N.5e-v2__tabla_16_regiones_calibri__slide.png (4680 px de ancho)
"""
import sys
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Dashboards"))
from utils import BLUE, INK_PRIMARY, INK_SECONDARY, INK_MUTED, GRIDLINE, SURFACE, lighten  # noqa: E402

DIRS_FUENTE = [Path("/Applications/Microsoft PowerPoint.app/Contents/Resources/DFonts"),
               Path("/Applications/Microsoft OneNote.app/Contents/Resources/DFonts"),
               Path("/Applications/Microsoft Word.app/Contents/Resources/DFonts")]
SALIDA = ROOT / "Outputs" / "figuras_pptx" / "S13_regiones_criticas" / "N.5e-v2__tabla_16_regiones_calibri__slide.png"
S = 6                       # escala: 780 px × 6 = 4680 px de ancho
W = 780                     # ancho de la diapositiva (px CSS)
PAD = 24
GRIS_CHILE = "#eceae4"


def fuente(nombre: str, tam: float) -> ImageFont.FreeTypeFont:
    for d in DIRS_FUENTE:
        if (d / nombre).exists():
            return ImageFont.truetype(str(d / nombre), round(tam * S))
    raise FileNotFoundError(f"No se encontró {nombre} en {[str(d) for d in DIRS_FUENTE]}")


def cl(v: float, d: int = 1, signo: bool = False) -> str:
    """Número con formato es-CL (coma decimal, signo menos tipográfico)."""
    s = f"{abs(v):.{d}f}".replace(".", ",")
    if v < 0 and float(s.replace(",", ".")) != 0:
        return "−" + s
    return ("+" + s) if signo and v > 0 else s


def partir(texto: str, f, ancho: float) -> list:
    lineas, actual = [], ""
    for p in texto.split():
        prueba = (actual + " " + p).strip()
        if f.getlength(prueba) <= ancho * S:
            actual = prueba
        else:
            lineas.append(actual)
            actual = p
    return lineas + ([actual] if actual else [])


def main() -> None:
    d = pd.read_csv(ROOT / "Data processed" / "kpi_seleccion_dos_preguntas.csv")
    ch = d[d.section == "chile"].iloc[0]
    rk = d[d.section == "ranking"].sort_values("change_pct", ascending=False).reset_index(drop=True)
    assert len(rk) == 15, "se esperaban 15 territorios (16 regiones, Biobío y Ñuble unidos)"
    pierden = set(rk[rk.below_chile.astype(bool) & rk.by_trend.astype(bool)]["name"])
    assert pierden == {"Valparaíso", "Tarapacá", "Arica y Parinacota"}, pierden

    f_txt, f_neg = fuente("Calibri.ttf", 24), fuente("Calibrib.ttf", 24)
    f_cab, f_sub, f_nota = fuente("Calibrib.ttf", 22), fuente("Calibri.ttf", 22), fuente("Calibri.ttf", 20)

    sub = ("Cotizantes de diciembre ÷ población de 15 a 64 años, %, 2007 y 2024; cambio de puestos entre 15 territorios "
           "(1 = mayor cobertura); Biobío y Ñuble unidos")
    lineas_sub = partir(sub, f_sub, W - 2 * PAD)
    fuente_txt = "Fuente: Superintendencia de Pensiones (cotizantes de diciembre), Censo 2024; elaboración propia."
    lineas_fte = partir(fuente_txt, f_nota, W - 2 * PAD)

    y_sub, lh_sub = 14, 28
    y_cab = y_sub + len(lineas_sub) * lh_sub + 14
    h_cab, fila = 62, 38
    y_ini = y_cab + h_cab
    n = len(rk) + 1
    y_fin = y_ini + n * fila
    y_leyenda = y_fin + 30
    y_fte = y_leyenda + 58
    alto = y_fte + len(lineas_fte) * 26 + 14

    img = Image.new("RGB", (W * S, int(alto * S)), SURFACE)
    g = ImageDraw.Draw(img)

    def t(x, y, texto, f, color=INK_PRIMARY, anchor="lm"):
        g.text((x * S, y * S), texto, font=f, fill=color, anchor=anchor)

    def triangulo(cx, cy, arriba, color, r=7.5):
        pts = [(cx, cy - r), (cx - r * 1.05, cy + r * 0.8), (cx + r * 1.05, cy + r * 0.8)] if arriba else \
              [(cx, cy + r), (cx - r * 1.05, cy - r * 0.8), (cx + r * 1.05, cy - r * 0.8)]
        g.polygon([(px * S, py * S) for px, py in pts], fill=color)

    for k, l in enumerate(lineas_sub):
        g.text((PAD * S, (y_sub + k * lh_sub) * S), l, font=f_sub, fill=INK_SECONDARY, anchor="lt")

    # columnas: región a la izquierda; las demás, centradas
    X = dict(reg=PAD + 6, pct=318, pue=444, c07=570, c24=696)
    g.rectangle([PAD * S, y_cab * S, (W - PAD) * S, y_ini * S], fill="#e7eef7")
    t(X["reg"], y_cab + h_cab / 2, "Región", f_cab)
    for k, (a, b) in dict(pct=("Cambio", "2007–2024 (%)"), pue=("Cambio de", "puestos"), c07=("Cobertura", "2007 (%)"), c24=("Cobertura", "2024 (%)")).items():
        t(X[k], y_cab + h_cab / 2 - 14, a, f_cab, anchor="mm")
        t(X[k], y_cab + h_cab / 2 + 13, b, f_cab, anchor="mm")

    filas = [dict(nombre="Chile", chile=True, pct=ch.change_pct, c07=ch.cov_start, c24=ch.cov_end)]
    filas += [dict(nombre=r["name"], chile=False, pct=r.change_pct, c07=r.cov_start, c24=r.cov_end, gan=-int(r.places_lost), pierde=r["name"] in pierden)
              for _, r in rk.iterrows()]
    y = y_ini
    for r in filas:
        yc = y + fila / 2
        destaca = r["chile"] or r.get("pierde", False)
        g.rectangle([PAD * S, y * S, (W - PAD) * S, (y + fila) * S],
                    fill=GRIS_CHILE if r["chile"] else (lighten(BLUE, 0.86) if r.get("pierde") else SURFACE))
        g.line([PAD * S, (y + fila) * S, (W - PAD) * S, (y + fila) * S], fill=GRIDLINE, width=max(1, S // 2))
        fb = f_neg if destaca else f_txt
        t(X["reg"], yc, r["nombre"], fb)
        t(X["pct"], yc, cl(r["pct"], 1, True), fb, anchor="mm")
        if r["chile"]:
            t(X["pue"], yc, "–", f_txt, INK_MUTED, "mm")
        elif r["gan"] == 0:
            t(X["pue"], yc, "=", f_txt, INK_SECONDARY, "mm")
        else:
            col = BLUE if r["pierde"] else INK_MUTED
            triangulo(X["pue"] - 26, yc, r["gan"] > 0, col)
            t(X["pue"] - 8, yc, cl(r["gan"], 0, True), f_neg if r["pierde"] else f_txt, col if r["pierde"] else INK_SECONDARY)
        t(X["c07"], yc, cl(r["c07"], 1), fb, anchor="mm")
        t(X["c24"], yc, cl(r["c24"], 1), fb, anchor="mm")
        y += fila
    g.line([PAD * S, y_fin * S, (W - PAD) * S, y_fin * S], fill=INK_MUTED, width=S)

    # leyenda
    x = PAD
    triangulo(x + 8, y_leyenda, False, BLUE)
    t(x + 24, y_leyenda, "azul = bajo Chile y pierde puestos", f_nota, INK_SECONDARY)
    x2 = x + 24 + f_nota.getlength("azul = bajo Chile y pierde puestos") / S + 28
    triangulo(x2 + 8, y_leyenda, True, INK_MUTED)
    t(x2 + 24, y_leyenda, "gris = el resto", f_nota, INK_SECONDARY)
    t(x2 + 24 + f_nota.getlength("gris = el resto") / S + 28, y_leyenda, "= igual", f_nota, INK_SECONDARY)
    t(PAD, y_leyenda + 24, "Orden: cambio de la cobertura en %, de mayor a menor; Chile arriba como referencia.", f_nota, INK_SECONDARY)

    for k, l in enumerate(lineas_fte):
        g.text((PAD * S, (y_fte + k * 26) * S), l, font=f_nota, fill=INK_SECONDARY, anchor="lt")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    img.save(SALIDA, dpi=(380, 380), optimize=True)
    print(f"{SALIDA.relative_to(ROOT)}  {img.width}×{img.height} px")


if __name__ == "__main__":
    main()
