"""
Descarga los meses que faltan del cuadro 04A de la Superintendencia de Pensiones
("Número de cotizantes e ingreso imponible promedio por tipo y sexo"). Insumo del KPI 1.2 (script 18).

Fuente: https://www.spensiones.cl/apps/centroEstadisticas/paginaCuadrosCCEE.php?menu=sci&menuN1=cotycot&menuN2=ingimp
  - La página lista los períodos disponibles en <select name="aaaamm0"> (octubre 2002 hasta el último mes publicado).
  - Cada período se descarga de /apps/loadEstadisticas/siSP.php?id=inf_estadistica/aficot/mensual/AAAA/MM/04A.xls&...
    El servidor exige una sesión (cookie de la página), un User-Agent de navegador y el Referer; sin eso redirige a /404.
  - Cada archivo es una tabla HTML con extensión .xls; el título trae la fecha ("Al 31 de Diciembre de 2024").

Qué hace:
  1. Lee los 04A que ya están en Data raw/import_KPI1.2/ (descargados a mano) y detecta qué meses tiene por el título.
  2. Descarga solo los meses que faltan a Data raw/import_KPI1.2/04A_descargas/04A_AAAAMM.xls
     (por defecto desde el primer mes publicado; se puede acotar con --desde AAAAMM).
  3. Valida que el título del archivo bajado corresponda al mes pedido.

Uso (desde la raíz del proyecto):
  "Data raw/.venv/bin/python" -I Scripts/15_descargar_sp_ingreso_imponible.py [--desde 200210] [--hasta 202608] [--seco]

Solo usa la biblioteca estándar.
"""
import argparse
import http.cookiejar
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMPORT = ROOT / "Data raw" / "import_KPI1.2"
DEST = IMPORT / "04A_descargas"

BASE = "https://www.spensiones.cl"
PAGINA = f"{BASE}/apps/centroEstadisticas/paginaCuadrosCCEE.php?menu=sci&menuN1=cotycot&menuN2=ingimp"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
MESES = {m: i + 1 for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"])}
TITULO = "COTIZANTES E INGRESO IMPONIBLE PROMEDIO POR TIPO Y SEXO"


def fecha_del_titulo(texto):
    """'Al 31 de Diciembre de 2024' -> 202412, o None si no es un 04A."""
    t = re.sub(r"<[^>]+>", " ", texto)
    t = t.replace("&Uacute;", "U")
    if TITULO not in t.upper().replace("Ú", "U"):
        return None
    m = re.search(r"Al\s+\d+\s+de\s+(\w+)\s+de\s+(\d{4})", t)
    if not m or m.group(1).lower() not in MESES:
        return None
    return int(m.group(2)) * 100 + MESES[m.group(1).lower()]


def meses_existentes():
    ya = {}
    for f in sorted(list(IMPORT.glob("*.xls")) + list(DEST.glob("*.xls"))):
        ym = fecha_del_titulo(f.read_text(encoding="latin-1", errors="replace"))
        if ym:
            ya[ym] = f
    return ya


def abrir_sesion():
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    op.addheaders = [("User-Agent", UA), ("Referer", PAGINA)]
    return op


def periodos_publicados(op):
    html = op.open(PAGINA, timeout=60).read().decode("latin-1")
    sel = re.search(r'<select\s+name="aaaamm0"\s*>(.*?)</select>', html, re.S)
    if not sel:
        sys.exit("No se encontró <select name='aaaamm0'> en la página: la estructura del sitio cambió.")
    ids = re.findall(r'value="([^"]*)"', sel.group(1))
    out = []
    for v in ids:  # inf_estadistica/aficot/mensual/2026/08/04A
        m = re.search(r"/(\d{4})/(\d{2})/04A$", v)
        if m:
            out.append((int(m.group(1)) * 100 + int(m.group(2)), v))
    return sorted(out)


def descargar(op, ym, ident, intentos=3):
    url = (f"{BASE}/apps/loadEstadisticas/siSP.php?id={ident}.xls"
           "&menu=sci&menuN1=cotycot&menuN2=ingimp&orden=10&ext=.xls")
    for k in range(intentos):
        try:
            cuerpo = op.open(url, timeout=60).read().decode("latin-1")
            if fecha_del_titulo(cuerpo) == ym:
                return cuerpo
            print(f"  {ym}: respuesta inesperada (intento {k + 1})")
        except Exception as e:  # red, 5xx, redirección a /404
            print(f"  {ym}: {e} (intento {k + 1})")
        time.sleep(2 * (k + 1))
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--desde", type=int, default=0, help="AAAAMM, primer mes a bajar (por defecto el primero publicado)")
    ap.add_argument("--hasta", type=int, default=999999, help="AAAAMM, último mes a bajar (por defecto el último publicado)")
    ap.add_argument("--seco", action="store_true", help="solo lista lo que faltaría, sin descargar")
    a = ap.parse_args()

    ya = meses_existentes()
    op = abrir_sesion()
    pub = [(ym, i) for ym, i in periodos_publicados(op) if a.desde <= ym <= a.hasta]
    faltan = [(ym, i) for ym, i in pub if ym not in ya]
    print(f"Publicados en el rango: {len(pub)} · ya presentes: {len(pub) - len(faltan)} · por descargar: {len(faltan)}")
    if a.seco or not faltan:
        return

    DEST.mkdir(parents=True, exist_ok=True)
    fallidos = []
    for n, (ym, ident) in enumerate(faltan, 1):
        cuerpo = descargar(op, ym, ident)
        if cuerpo is None:
            fallidos.append(ym)
            continue
        (DEST / f"04A_{ym}.xls").write_text(cuerpo, encoding="latin-1")
        if n % 20 == 0 or n == len(faltan):
            print(f"  {n}/{len(faltan)} (último: {ym})")
        time.sleep(0.5)  # cortesía con el servidor

    ya = meses_existentes()
    huecos = [ym for ym, _ in pub if ym not in ya]
    print(f"Descargados: {len(faltan) - len(fallidos)} · fallidos: {fallidos or 'ninguno'} · huecos restantes: {huecos or 'ninguno'}")
    if huecos:
        sys.exit(1)


if __name__ == "__main__":
    main()
