"""Figuras de la presentación (Scripts/34_exportar_figuras_presentacion.py → Outputs/figuras_pptx/).

Revisa el paquete ya exportado (no lo vuelve a generar: exportar tarda minutos y necesita Chrome para kaleido):
manifest completo, archivos presentes, resolución mínima, números de figura iguales a los de components/numeracion.py,
control de pautas sin fallas en las figuras terminadas, y que el control detecte los errores típicos con figuras de ejemplo.
Si el paquete no existe, las pruebas del paquete se saltan con el comando para generarlo.
"""
import csv
import importlib.util
import re
import sys
from pathlib import Path

import plotly.graph_objects as go
import pytest
import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Dashboards"))
OUT = ROOT / "Outputs" / "figuras_pptx"
CFG = yaml.safe_load((ROOT / "config" / "figuras_presentacion.yaml").read_text(encoding="utf-8"))


def _script():
    spec = importlib.util.spec_from_file_location("exportar_figuras", ROOT / "Scripts" / "34_exportar_figuras_presentacion.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def filas():
    if not (OUT / "manifest.csv").exists():
        pytest.skip('Falta el paquete: "Data raw/.venv/bin/python" Scripts/34_exportar_figuras_presentacion.py')
    with open(OUT / "manifest.csv", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _ids_esperados():
    ids = []
    for f in CFG["figuras"]:
        ids += [f"{f['id']}{le}" for le in f["letters"]] if f.get("letters") else [f["id"]]
    ids += [f"N.0{le}" for le in "abcdef"[: len(CFG["seguimiento"]["pasos"])]]
    return ids


def test_manifest_completo(filas):
    """Cada figura del mapa (y cada variante de la franja de seguimiento) tiene su fila, con estado honesto."""
    en_manifest = [r["figure_num"] for r in filas]
    for i in _ids_esperados():
        assert i in en_manifest, i
    assert len(filas) == len(_ids_esperados())
    columnas = ["slide_id", "storyline_point", "figure_num", "key", "canvas", "version", "file_slide", "file_standalone", "message_es",
                "subtitle_es", "source_es", "width_px", "height_px", "changes_applied", "qa_flags", "status", "notes"]
    assert all(c in filas[0] for c in columnas)
    assert {r["status"] for r in filas} <= {"done", "needs_data", "blocked", "superseded"}
    bloqueadas = {f["id"] for f in CFG["figuras"] if f.get("status") == "blocked"}
    assert {r["figure_num"] for r in filas if r["status"] == "blocked"} == bloqueadas == {"N.10", "N.11"}


def test_archivos_existen_y_resolucion(filas):
    for r in filas:
        for col in ("file_slide", "file_standalone"):
            if not r[col]:
                continue
            p = OUT / r[col]
            assert p.exists(), p
            with Image.open(p) as im:
                assert im.width >= CFG["ancho_min_px"], (p.name, im.size)
    for nombre in ("README.md", "qa_report.md", "manifest.json", "contact_sheet.pdf", "figuras_pptx.zip"):
        assert (OUT / nombre).exists(), nombre


def test_numeros_iguales_a_numeracion(filas):
    """El número impreso en cada figura del dashboard sale de ORDEN (components/numeracion.py)."""
    from components.numeracion import numero
    for r in filas:
        if not r["key"]:
            continue
        letra = re.search(r"[a-z]$", r["figure_num"])
        clave = r["key"] + (f":{letra.group(0)}" if letra and r["key"].endswith("composicion_region") else "")
        assert numero(clave, extendida=r["version"] == "extendida") == r["figure_num"], r["key"]


def test_control_sin_fallas_en_figuras_terminadas(filas):
    for r in filas:
        if r["status"] == "done":
            assert r["qa_flags"] == "ok", (r["figure_num"], r["qa_flags"])


def test_mensajes_cortos_y_sin_siglas(filas):
    siglas = re.compile(r"\b(AFP|PGU|FAPP|SIS|ENE|CASEN|INE|PIB|FRP|IPS|DIPRES|APS|PBS)\b")
    for r in filas:
        if r["status"] != "done" or not r["message_es"]:
            continue
        palabras = [p for p in r["message_es"].split() if re.search(r"\w", p)]
        assert len(palabras) <= 25, (r["figure_num"], len(palabras))
        assert not siglas.search(r["message_es"] + " " + r["subtitle_es"]), r["figure_num"]
        assert r["source_es"], r["figure_num"]


def test_escenarios_y_juicios_llevan_su_advertencia(filas):
    naturaleza = {}
    for f in CFG["figuras"]:
        naturaleza[f["id"]] = f["nature"]
    for r in filas:
        nat = naturaleza.get(re.sub(r"[a-z]$", "", r["figure_num"]))
        if nat == "escenario":
            assert "no es un pronóstico" in r["source_es"], r["figure_num"]
        if nat == "juicio":
            assert "juicio del equipo" in r["source_es"], r["figure_num"]
    mapa = next(r for r in filas if r["key"] == "1.1/mapa")
    assert "OpenStreetMap" in mapa["source_es"]


# ---------------------------------------------------------------- el control detecta los errores típicos
SPEC = {"transform": "x", "canvas": "W", "nature": "dato"}
INFO = {"note_lines": 1, "width_px": 4800, "height_px": 2160}


def _lint(fig, mensaje="Un mensaje corto.", sub="Qué se mide, unidad y período", fuente="Fuente: prueba"):
    return _script().lint(fig, SPEC, mensaje, sub, fuente, INFO)


def test_lint_linea_punteada_y_leyenda():
    f = go.Figure([go.Scatter(x=[1, 2, 3], y=[1, 2, 3], mode="lines", line=dict(dash="dash", width=3), showlegend=True, name="a"),
                   go.Scatter(x=[1, 2, 3], y=[2, 3, 4], mode="lines", line=dict(width=3), showlegend=True, name="b")])
    r = _lint(f)
    assert r["G8"][0] == "falla" and r["G18"][0] == "falla"


def test_lint_torta_siglas_y_largo():
    f = go.Figure(go.Pie(values=[1, 2]))
    assert _lint(f)["G12"][0] == "falla"
    assert _lint(go.Figure(), mensaje="La AFP gana.")["G3"][0] == "falla"
    assert _lint(go.Figure(), mensaje=" ".join(["palabra"] * 26))["G3"][0] == "falla"


def test_lint_burbujas_por_diametro_y_eje_que_no_parte_de_cero():
    f = go.Figure(go.Scatter(x=[1, 2, 3, 4, 5], y=[5, 6, 7, 8, 9], mode="markers", marker=dict(size=[5, 10, 15, 20, 25], sizemode="diameter")))
    f.update_yaxes(range=[4, 10])
    r = _lint(f)
    assert r["G11"][0] == "falla" and r["G10"][0] == "falla"


def test_lint_figura_correcta_pasa():
    f = go.Figure(go.Bar(x=["a", "b", "c"], y=[3, 2, 1], marker_color=["#eb6834", "#c9c8c2", "#c9c8c2"]))
    f.update_layout(bargap=0.33, showlegend=False)
    f.update_yaxes(range=[0, 4])
    r = _lint(f)
    assert all(v[0] in ("ok", "n.a.") for k, v in r.items()), {k: v for k, v in r.items() if v[0] not in ("ok", "n.a.")}


# ---------------------------------------------------------------- regla de dos preguntas (N.5a-N.5d) y sin números dentro de las imágenes
NUEVAS = ["N.5a", "N.5b", "N.5b-v2", "N.5c", "N.5d"]


def test_figuras_de_la_regla_de_dos_preguntas(filas):
    por_num = {r["figure_num"]: r for r in filas}
    for n in NUEVAS:
        assert n in por_num, n
        r = por_num[n]
        assert r["status"] == "done" and r["qa_flags"] == "ok", (n, r["qa_flags"])
        assert r["file_slide"].split("/")[-1].startswith(n + "__") and r["file_standalone"].split("/")[-1].startswith(n + "__")
        for col in ("file_slide", "file_standalone"):
            with Image.open(OUT / r[col]) as im:
                assert im.width >= 4680, (n, im.size)
    assert por_num["N.5"]["status"] == "superseded"
    assert {por_num[n]["slide_id"] for n in ("N.5a", "N.5b", "N.5b-v2", "N.5c")} == {"S13"} and por_num["N.5d"]["slide_id"] == "S14"
    with Image.open(OUT / por_num["N.5a"]["file_slide"]) as im:       # H = 780 × 720 a escala 6 (4.680 px de ancho)
        assert im.size == (4680, 4320)


def test_cifras_de_los_mensajes_salen_del_csv(filas):
    """Cada número citado en el mensaje de N.5a-N.5d aparece en Data processed/kpi_seleccion_dos_preguntas.csv (formato es-CL)."""
    import pandas as pd
    cl = _script().cl
    d = pd.read_csv(ROOT / "Data processed" / "kpi_seleccion_dos_preguntas.csv")
    valores = set()
    for col, dec in (("cov_start", 1), ("cov_end", 1), ("change_pp", 1), ("change_pct", 1), ("rank_start", 0), ("rank_end", 0), ("participacion_pp", 1)):
        for v in d[col].dropna():
            valores |= {cl(v, dec), cl(v, dec, True)}
    S = _script()._seleccion()          # con las regiones excluidas por decisión del equipo (Biobío): 7 regiones
    s8 = S["selection"][S["selection"].selected].gap_people.sum() / S["gap"].gap_people.sum() * 100
    valores.add(cl(s8, 0))
    d_ = S["decomposition"]
    tot = d_[["cotizacion_people", "participacion_people", "empleo_people"]].sum()
    valores.add(cl(tot.cotizacion_people / tot.sum() * 100, 0))
    por_num = {r["figure_num"]: r for r in filas}
    for n in NUEVAS:
        for tok in re.findall(r"[+−]?\d+(?:,\d+)?", por_num[n]["message_es"]):
            if tok in ("2007", "2024"):
                continue
            assert tok in valores, (n, tok)


def test_numero_de_figura_solo_en_el_nombre_del_archivo():
    """El número no se imprime en la imagen: ni «Fig. x» en la franja de la nota ni referencias a otras figuras en notas y descripciones."""
    src = (ROOT / "Scripts" / "34_exportar_figuras_presentacion.py").read_text(encoding="utf-8")
    assert 'f"Fig. {' not in src
    ref = re.compile(r"\b(?:\d\.\d\.\d+|N\.\d+[a-z]?|P\.\d)\b")
    for f in CFG["figuras"]:
        for campo in ("subtitle", "source"):
            assert not ref.search(f.get(campo, "")), (f["id"], campo)
    pasos = re.search(r"PASOS = \[(.*?)\]\nFASES", src, re.S).group(1)
    assert not re.search(r"\bP\.\d|\b1\.1\.33", pasos)


def test_p3_sin_etiquetas_estimado_ni_proyeccion_del_instituto():
    src = (ROOT / "Scripts" / "34_exportar_figuras_presentacion.py").read_text(encoding="utf-8")
    cuerpo = src[src.index("def t_envejecimiento"):src.index("def _ticks_absolutos")]
    assert 'text="Estimado"' not in cuerpo and "Proyección del Instituto" not in cuerpo


# ------------------------------------------------------------------------------------------------ pie de fuente (Scripts/pie_fuente.py)
PROHIBIDAS = re.compile(r"dashboard|motor|claude|chatgpt|\bgpt\b|\bAI\b|\bIA\b|notebook|Scripts/|\.py\b|\.csv\b|repositorio", re.I)


def test_fuentes_no_citan_herramientas_ni_archivos_del_proyecto():
    """Una fuente nombra instituciones, no el dashboard, los scripts, los archivos del repositorio ni una herramienta de IA."""
    malas = [(f["id"], f["source"]) for f in CFG["figuras"] if PROHIBIDAS.search(f.get("source", ""))]
    assert not malas, malas


def test_escenarios_citan_instituciones():
    """Las figuras de escenario llevan «Fuente: …» con las instituciones y, después, la advertencia."""
    for f in CFG["figuras"]:
        if f.get("nature") == "escenario":
            assert "Fuente:" in f["source"] or "Superintendencia de Pensiones" in f["source"], f["id"]
            assert "no es un pronóstico" in f["source"], f["id"]


def test_pie_de_fuente_comun():
    """El pie común mantiene el tamaño de la imagen, parte el texto en ≤ 2 líneas y alinea el número a la derecha cuando se pide."""
    sys.path.insert(0, str(ROOT / "Scripts"))
    import pie_fuente
    img = Image.new("RGB", (1600, 720), pie_fuente.SURFACE)
    n = pie_fuente.add_source_footer(img, "Fuente: Superintendencia de Pensiones y Censo 2024 (Instituto Nacional de Estadísticas).", fig_num="1.1.2",
                                     mostrar_numero=True)
    assert img.size == (1600, 720) and n == 1
    caja = img.crop((1200, 720 - pie_fuente.NOTE_BAND, 1600, 720)).convert("L")
    assert caja.getextrema()[0] < 200, "el número de la figura no se dibujó a la derecha"
    largo = "Fuente: " + "Superintendencia de Pensiones " * 12
    assert pie_fuente.add_source_footer(Image.new("RGB", (1600, 720), pie_fuente.SURFACE), largo) > pie_fuente.MAX_LINEAS
