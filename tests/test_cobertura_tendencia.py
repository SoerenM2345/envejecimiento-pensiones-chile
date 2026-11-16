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


SIETE = ["La Araucanía", "Valparaíso", "Biobío", "Coquimbo", "Ñuble", "Los Ríos", "Arica y Parinacota"]  # la lista anterior (brecha o pérdida desde 2022)
OCHO = [*SIETE[:1], "Valparaíso", "Arica y Parinacota", "Coquimbo", "Los Ríos", "Tarapacá", "Ñuble", "Biobío"]  # la recomendada, por suma de rangos


def test_prioridad_recomendada_son_8_regiones_por_nivel_tendencia_y_brecha(datos):
    r = datos["r"][datos["r"].region_id > 0].set_index("region_nombre")
    prio = r[r.prioridad.notna()]
    assert sorted(prio.prioridad) == list(range(1, 9))
    assert list(prio.sort_values("prioridad").index) == ["Valparaíso", "La Araucanía", "Arica y Parinacota", "Coquimbo", "Los Ríos", "Tarapacá", "Ñuble", "Biobío"]
    assert set(prio.index) == set(OCHO)
    nac = datos["r"].query("region_id == 0").cobertura_ref.iloc[0]
    assert (prio.cobertura_ref < nac).all()
    # los tres rangos van de 1 a 16 (con empates en el promedio) y suman lo que dice la columna
    for k in ("rango_nivel", "rango_tendencia", "rango_brecha"):
        assert r[k].sum() == pytest.approx(16 * 17 / 2) and r[k].min() >= 1 and r[k].max() <= 16
    assert (r.rango_suma - (r.rango_nivel + r.rango_tendencia + r.rango_brecha)).abs().max() < 1e-9
    # regla: bajo el promedio y entre las 5 peores de al menos un factor
    esperada = r[(r.cobertura_ref < nac) & (r[["rango_nivel", "rango_tendencia", "rango_brecha"]].min(axis=1) <= 5)]
    assert set(esperada.index) == set(OCHO)
    # la tendencia es de 2007 a 2024 menos lo que ganó Chile; Biobío y Ñuble comparten la serie fusionada
    t = datos["t"]
    c = t.pivot(index="territorio_id", columns="anio", values="cobertura_pct")
    assert r.loc["Valparaíso", "vs_chile_2007"] == pytest.approx((c.loc[5, 2024] - c.loc[5, 2007]) - (c.loc[0, 2024] - c.loc[0, 2007]), abs=1e-3)
    assert r.loc["Biobío", "vs_chile_2007"] == pytest.approx(r.loc["Ñuble", "vs_chile_2007"])
    assert r.loc["Biobío", "vs_chile_2007"] == pytest.approx((c.loc[816, 2024] - c.loc[816, 2007]) - (c.loc[0, 2024] - c.loc[0, 2007]), abs=1e-3)
    # los motivos: Tarapacá entra solo por la tendencia, Biobío solo por la brecha (sobre todo tamaño), Los Ríos solo por el nivel
    assert r.loc["Tarapacá", "motivo_rangos"] == "Tendencia" and r.loc["Biobío", "motivo_rangos"] == "Brecha" and r.loc["Los Ríos", "motivo_rangos"] == "Nivel"
    # Los Lagos queda justo fuera: tercera suma más cercana, pero ningún rango entre los 5 peores
    assert pd.isna(r.loc["Los Lagos", "prioridad"]) and r.loc["Los Lagos", "rango_suma"] < r.loc["Biobío", "rango_suma"]


def test_la_lista_recomendada_es_estable_con_cualquier_inicio_de_la_ventana_hasta_2019():
    rob = pd.read_csv(DP / "kpi_cobertura_prioridad_robustez.csv")
    assert list(rob.inicio) == list(range(2002, 2023))
    assert rob[rob.inicio <= 2019].coincide_con_la_lista.all() and (rob[rob.inicio <= 2019].n_regiones == 8).all()
    assert rob[rob.inicio <= 2018].de_las_7_de_menor_suma_en_la_lista.eq(7).all()  # las 7 de menor suma de rangos siempre están dentro
    assert (rob.n_regiones >= 7).all()


def test_listas_de_regiones_y_la_anterior_une_brecha_y_perdida_de_cotizantes(datos):
    r = datos["r"][datos["r"].region_id > 0].set_index("region_nombre")
    for col in ("prioridad_brecha", "prioridad_caida", "prioridad_peso"):
        assert sorted(r[col].dropna()) == [1, 2, 3, 4, 5], col
    assert list(r.prioridad_brecha.dropna().sort_values().index) == ["La Araucanía", "Valparaíso", "Biobío", "Coquimbo", "Ñuble"]
    assert list(r.prioridad_caida.dropna().sort_values().index)[:3] == ["Arica y Parinacota", "Valparaíso", "Metropolitana"]
    assert list(r.prioridad_peso.dropna().sort_values().index)[:2] == ["Metropolitana", "Valparaíso"]
    # la anterior = bajo el promedio Y (entre las 5 de mayor brecha O con menos cotizantes que en 2022)
    nac = datos["r"].query("region_id == 0").cobertura_ref.iloc[0]
    esperada = r[(r.cobertura_ref < nac) & (r.prioridad_brecha.notna() | (r.dif_cotizantes_22_ref < 0))]
    assert set(r.prioridad_brecha_perdida.dropna().index) == set(esperada.index) == set(SIETE)
    assert (r.prioridad.fillna(0) == r.prioridad_rangos.fillna(0)).all()  # la que muestra el dashboard por defecto
    # los motivos de la anterior: Coquimbo entra solo por brecha (ganó cotizantes), Los Ríos y Arica solo por pérdida
    assert r.loc["Coquimbo", "motivo_prioridad"] == "Solo brecha" and r.loc["Coquimbo", "dif_cotizantes_22_ref"] > 0
    assert r.loc["Los Ríos", "motivo_prioridad"] == r.loc["Arica y Parinacota", "motivo_prioridad"] == "Solo pérdida"
    assert (r.loc[["La Araucanía", "Valparaíso", "Biobío", "Ñuble"], "motivo_prioridad"] == "Brecha y pérdida").all()


def test_siete_regiones_perdieron_cotizantes_y_solo_la_metropolitana_esta_sobre_el_promedio(datos):
    """Entre 2022 y 2024 pierden cotizantes (personas) exactamente 7 regiones; seis están bajo el promedio de Chile y la séptima es la Metropolitana."""
    r = datos["r"][datos["r"].region_id > 0].set_index("region_nombre")
    pierden = set(r[r.dif_cotizantes_22_ref < 0].index)
    assert pierden == {"Metropolitana", "Valparaíso", "Biobío", "La Araucanía", "Ñuble", "Arica y Parinacota", "Los Ríos"}
    nac = datos["r"].query("region_id == 0").cobertura_ref.iloc[0]
    assert set(r[r.index.isin(pierden) & (r.cobertura_ref >= nac)].index) == {"Metropolitana"}


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
    at = AppTest.from_file(str(ROOT / "Dashboards" / "extended_pages" / "objetivo1.py"), default_timeout=180).run()
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
