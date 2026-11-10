"""KPI 1.1: tendencia de la cobertura y causas posibles (Scripts/24, docs/EXPLORACION_COBERTURA.md).
Ejecutar desde la raíz del proyecto:  python -I -m pytest tests -q   (venv: Data raw/.venv)"""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
DP = ROOT / "Data processed"
sys.path.insert(0, str(ROOT / "Dashboards"))


@pytest.fixture(scope="module")
def datos():
    return dict(t=pd.read_csv(DP / "kpi_cobertura_tendencia.csv"), r=pd.read_csv(DP / "kpi_cobertura_regiones.csv"),
                f=pd.read_csv(DP / "kpi_cobertura_factores.csv"), cor=pd.read_csv(DP / "kpi_cobertura_correlaciones_region.csv"))


def test_cobertura_2024_coincide_con_la_del_kpi_1_1(datos):
    """El Censo manda: la serie regional se lleva al nivel del Censo 2024, así que 2024 coincide con la cobertura que ya mostraba el KPI 1.1."""
    t, cor = datos["t"], datos["cor"].set_index("region_id")
    c24 = t[(t.anio == 2024) & t.territorio_id.between(1, 16)].set_index("territorio_id").cobertura_pct
    assert (c24 - cor.cobertura_previsional_pct.reindex(c24.index)).abs().max() < 0.05
    pais = t[(t.anio == 2024) & (t.territorio_id == 0)].cobertura_pct.iloc[0]
    assert round(pais, 1) == 46.5  # la misma razón de soporte / cobertura del país que usa el KPI 1.2


def test_serie_larga_fusiona_las_regiones_que_se_separaron(datos):
    """Hasta 2006 Arica va dentro de Tarapacá y Los Ríos dentro de Los Lagos; las series fusionadas no tienen saltos en 2007 por el cambio."""
    t = datos["t"]
    assert t.anio.min() == 2002 and t[t.territorio_id == 15].anio.min() == 2007 and t[t.territorio_id == 14].anio.min() == 2007
    for tid in (801, 810, 816):
        s = t[t.territorio_id == tid].set_index("anio").cobertura_pct
        assert s.index.min() == 2002 and abs(s[2007] - s[2006]) < 4.5
    # el país: la serie del KPI desde 2010 y la suma de las regiones antes
    assert t[(t.territorio_id == 0) & (t.anio == 2010)].cobertura_pct.iloc[0] == pytest.approx(40.36, abs=0.01)


def test_proyeccion_sin_ajustar_difiere_solo_por_una_constante_por_region(datos):
    """El ajuste al Censo es un factor constante por región: la cobertura sin ajustar tiene la misma forma, solo cambia el nivel."""
    t = datos["t"]
    r = (t.cobertura_sin_ajuste_pct / t.cobertura_pct)[t.territorio_id == 9]
    assert r.max() - r.min() < 1e-4  # redondeo del CSV
    # la proyección 2017 sobreestimó la población del país y de la Metropolitana; en Ñuble el Censo contó más gente que la proyección
    for tid, menor in ((0, True), (13, True), (16, False)):
        x = t[t.territorio_id == tid]
        assert (x.cobertura_sin_ajuste_pct < x.cobertura_pct).all() == menor


def test_biobio_y_nuble_no_se_rompen_en_2018(datos):
    """Antes de 2018 la Superintendencia publica Ñuble dentro de Biobío: la serie conjunta no tiene el salto de 10 puntos de Biobío solo."""
    t = datos["t"]
    j = t[t.territorio_id == 816].set_index("anio").cobertura_pct
    assert abs(j[2018] - j[2017]) < 3
    b = t[t.territorio_id == 8].set_index("anio").cobertura_pct
    assert b.index.min() == 2018 and t[t.territorio_id == 16].anio.min() == 2018


def test_prioridad_son_5_regiones_y_la_brecha_es_cotizantes_que_faltan(datos):
    r = datos["r"][datos["r"].region_id > 0]
    prio = r[r.prioridad.notna()]
    assert sorted(prio.prioridad) == [1, 2, 3, 4, 5]
    nac = datos["r"].query("region_id == 0").cobertura_ref.iloc[0]
    assert (prio.cobertura_ref < nac).all()  # solo regiones bajo el promedio tienen brecha
    ejemplo = prio.iloc[0]
    assert ejemplo.brecha_cotizantes == pytest.approx((nac - ejemplo.cobertura_ref) / 100 * ejemplo.pob_15_64, rel=1e-3)
    assert set(prio.sort_values("prioridad").region_nombre.head(2)) == {"La Araucanía", "Valparaíso"}


def test_cuatro_listas_de_5_regiones_y_la_recomendada_es_brecha_mas_caida(datos):
    r = datos["r"][datos["r"].region_id > 0].set_index("region_nombre")
    for col in ("prioridad_brecha", "prioridad_caida", "prioridad_peso", "prioridad_brecha_caida"):
        assert sorted(r[col].dropna()) == [1, 2, 3, 4, 5], col
    assert list(r.prioridad_brecha.dropna().sort_values().index) == ["La Araucanía", "Valparaíso", "Biobío", "Coquimbo", "Ñuble"]
    assert list(r.prioridad_caida.dropna().sort_values().index)[:3] == ["Arica y Parinacota", "Valparaíso", "Metropolitana"]
    # con 2024 como año de referencia las 5 de mayor brecha ya cayeron todas desde 2022: la lista «bajo el promedio y en caída» coincide con la de brecha
    assert set(r.prioridad_brecha_caida.dropna().index) == set(r.prioridad_brecha.dropna().index)
    assert list(r.prioridad_peso.dropna().sort_values().index)[:2] == ["Metropolitana", "Valparaíso"]
    rec = r[r.prioridad_brecha_caida.notna()]
    assert (rec.brecha_cotizantes > 0).all() and (rec.cambio_2022_ref < 0).all()  # bajo el promedio de Chile y en caída
    assert (r.prioridad.fillna(0) == r.prioridad_brecha_caida.fillna(0)).all()  # la que muestra el dashboard por defecto


def test_factores_elegidos_cubren_las_hipotesis_del_profesor(datos):
    f = datos["f"]
    nivel = f[f.objetivo == "nivel"]
    assert len(nivel) >= 24 and (f.objetivo == "cambio").sum() == 3
    el = f[f.elegido]
    assert len(el) == 6
    assert {"Desempleo", "Informalidad", "Industria", "Migración"} <= set(el.hipotesis)
    # desempleo e informalidad: la medida oficial de la ENE, no la que mejor calza
    assert {"desocupacion_ene", "informalidad_ene", "migracion_interna_neta"} <= set(el.factor)
    assert (el[~el.factor.isin(["desocupacion_ene"])].pearson_p < 0.05).all()


def test_codigos_del_censo_coinciden_con_las_cifras_oficiales_agregadas_del_ine():
    """Valparaíso (Base_zona_localidad_CPV24 del INE): 823.510 ocupados, 78.065 desocupados, 296.092 independientes; en la tabla regional
    la desocupación de Valparaíso es 78.065 / (823.510 + 78.065)."""
    r = pd.read_csv(DP / "kpi_cobertura_regiones.csv").set_index("region_id")
    assert round(r.loc[5, "desocupacion"], 2) == round(100 * 78065 / (823510 + 78065), 2)


def test_pagina_muestra_la_tendencia_entre_el_primer_bloque_y_las_correlaciones():
    at = AppTest.from_file(str(ROOT / "Dashboards" / "final_pages" / "objetivo1.py"), default_timeout=180).run()
    assert not at.exception, [e.value for e in at.exception]
    titulos = [json.loads(el.proto.spec).get("layout", {}).get("title", {}).get("text", "") for el in at.get("plotly_chart")]
    i_tendencia = next(i for i, t in enumerate(titulos) if t.startswith("Desde 2019 la cobertura de Chile"))
    i_correl = next(i for i, t in enumerate(titulos) if "ingreso per cápita tienen" in t and "r = " in t and i > i_tendencia)
    i_barras = next(i for i, t in enumerate(titulos) if "valor más alto" in t)
    assert i_barras < i_tendencia < i_correl
    assert any(t.startswith("Las regiones con más") for t in titulos)  # gráfico de factores
    subtitulos = [h.value for h in at.markdown if h.value.startswith("#### ")]
    assert "#### ¿Sube o baja la cobertura?" in subtitulos
    assert "#### ¿Qué puede explicar la baja cobertura en las regiones prioritarias?" in subtitulos


def test_el_ano_de_referencia_es_2024_en_todo_el_bloque(datos):
    """Problema y causas comparten el mismo año: el del Censo y el último con empleo por región (2024)."""
    r = datos["r"]
    assert (r.anio_ref == 2024).all()
    reg = r[r.region_id > 0].set_index("region_id")
    t = datos["t"]
    c = t[t.territorio_id.between(1, 16)].pivot(index="territorio_id", columns="anio", values="cobertura_pct")
    assert (reg.cobertura_ref - c[2024].reindex(reg.index)).abs().max() < 1e-3
    assert (reg.cambio_2022_ref - (c[2024] - c[2022]).reindex(reg.index)).abs().max() < 1e-3
    assert reg.peso_cotizantes_pct.sum() == pytest.approx(100, abs=0.01)
