"""Pie de fuente común de todas las figuras (referencia: Fig. 1.2.4, «Cotizantes por persona de 65+»).

El pie va impreso en la propia imagen, en una franja al fondo, bajo el eje x, alineado a la izquierda con el margen del gráfico:
  - letra Helvetica Neue de 18 px sobre un lienzo de 1600 px (= 12,3 pulgadas de diapositiva, ≈ 10 pt), gris INK_SECONDARY;
  - empieza con «Fuente: » y sigue con las instituciones y el año de los datos, y después los supuestos o la advertencia de escenario;
  - como máximo 2 líneas;
  - opcional: el número de la figura («Fig. 1.2.4») alineado a la derecha, en la misma línea base y el mismo gris. Está apagado
    (NUMERO_EN_IMAGEN = False) porque la Fig. 1.2.4 de referencia no lo lleva: el número va en el nombre del archivo.

Lo usan Scripts/34 (todas las figuras de la presentación) y Scripts/05 y Scripts/11 (las pirámides, hechas con matplotlib).
La imagen se dibuja siempre con la franja ya reservada: el pie no cambia el tamaño ni la proporción de la figura.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

FONT_FILE = "/System/Library/Fonts/HelveticaNeue.ttc"
INK_SECONDARY = "#52514e"
SURFACE = "#fcfcfb"

REF_CSS_W = 1600          # ancho del lienzo de referencia, px CSS
REF_IN_W = 12.3           # ancho de ese lienzo en la diapositiva, pulgadas
NOTE = 18                 # tamaño de la letra del pie, px CSS (sobre REF_CSS_W)
NOTE_BAND = 66            # alto de la franja del pie, px CSS: 8 px de aire + 2 líneas de 1,32 × 18 px + margen
PAD = 24                  # margen lateral, px CSS
LINE_H = 1.32             # interlineado, × tamaño de letra
MAX_LINEAS = 2
NUMERO_EN_IMAGEN = False  # «Fig. X.Y.Z» a la derecha del pie (ver arriba)


def fuente_pil(tam: int, negrita: bool = False):
    try:
        return ImageFont.truetype(FONT_FILE, tam, index=1 if negrita else 0)
    except OSError:
        return ImageFont.load_default(size=tam)


def partir_nota(texto: str, fuente, ancho_px: float) -> list:
    lineas, actual = [], ""
    for p in texto.split():
        prueba = (actual + " " + p).strip()
        if fuente.getlength(prueba) <= ancho_px:
            actual = prueba
        else:
            lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas


def css_ancho(placed_width_in: float) -> float:
    """Ancho de lienzo CSS equivalente a una imagen que se inserta con ese ancho (pulgadas): mantiene la letra del pie en ≈ 10 pt."""
    return REF_CSS_W * placed_width_in / REF_IN_W


def banda_px(img_width: int, css_width: float = REF_CSS_W) -> int:
    """Alto en px reales de la franja que hay que reservar abajo de una imagen de ese ancho."""
    return round(NOTE_BAND * img_width / css_width)


def add_source_footer(img: Image.Image, source: str, *, css_width: float = REF_CSS_W, y_top: int | None = None, fig_num: str | None = None,
                      mostrar_numero: bool | None = None, max_lineas: int = MAX_LINEAS) -> int:
    """Imprime el pie de fuente en `img` (modo RGB, se modifica en el lugar) y devuelve cuántas líneas ocupó.

    css_width: ancho de lienzo CSS que representa la imagen (1600 para las figuras de la presentación). Escala la letra y los márgenes:
               px reales por px CSS = img.width / css_width.
    y_top:     fila (px reales) donde empieza la franja del pie (por omisión, la franja ocupa el fondo de la imagen).
    fig_num:   número de la figura; solo se imprime si mostrar_numero (por omisión NUMERO_EN_IMAGEN) es verdadero.
    El texto que pase de `max_lineas` no se corta en silencio: se devuelve el número real de líneas para que el llamador lo marque.
    """
    escala = img.width / css_width
    if y_top is None:
        y_top = img.height - round(NOTE_BAND * escala)
    fnt = fuente_pil(round(NOTE * escala))
    pad = round(PAD * escala)
    num = f"Fig. {fig_num}" if (fig_num and (NUMERO_EN_IMAGEN if mostrar_numero is None else mostrar_numero)) else ""
    ancho_num = fnt.getlength(num) + round(24 * escala) if num else 0
    lineas = partir_nota(source, fnt, img.width - 2 * pad - ancho_num)
    d = ImageDraw.Draw(img)
    y0 = y_top + round(8 * escala)
    paso = int(NOTE * LINE_H * escala)
    for k, linea in enumerate(lineas[:max(max_lineas, 3)]):
        d.text((pad, y0 + k * paso), linea, fill=INK_SECONDARY, font=fnt)
    if num:  # misma línea base que la última línea del pie, alineado a la derecha
        d.text((img.width - pad, y0 + (min(len(lineas), max(max_lineas, 3)) - 1) * paso), num, fill=INK_SECONDARY, font=fnt, anchor="ra")
    return len(lineas)
