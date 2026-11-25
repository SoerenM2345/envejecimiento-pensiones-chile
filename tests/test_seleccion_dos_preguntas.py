"""Regla de dos preguntas (Scripts/35_seleccion_dos_preguntas.py → Data processed/kpi_seleccion_dos_preguntas.csv).

Revisa el CSV ya generado contra las cifras de acuerdo con el equipo (tolerancia ±1 en personas, ±0,05 en porcentajes) y la lógica del script.
Si el CSV no existe se salta con el comando para generarlo.
"""
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
DP = ROOT / "Data processed"
OCHO = {"La Araucanía", "Biobío", "Ñuble", "Valparaíso", "Coquimbo", "Los Ríos", "Arica y Parinacota", "Tarapacá"}


@pytest.fixture(scope="module")
def S():
    ruta = DP / "kpi_seleccion_dos_preguntas.csv"
    if not ruta.exists():
        pytest.skip('Falta el CSV: "Data raw/.venv/bin/python" Scripts/35_seleccion_dos_preguntas.py')
    d = pd.read_csv(ruta)
    return {k: d[d.section == k].reset_index(drop=True) for k in ("chile", "ranking", "gap", "selection", "decomposition")}


def _script():
    spec = importlib.util.spec_from_file_location("seleccion", ROOT / "Scripts" / "35_seleccion_dos_preguntas.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_ranking_de_15_territorios_y_gap_de_10_regiones(S):
    assert len(S["ranking"]) == 15
    assert len(S["gap"]) == 10
    assert sorted(S["ranking"].rank_start) == list(range(1, 16)) and sorted(S["ranking"].rank_end) == list(range(1, 16))
    assert "Biobío y Ñuble" in set(S["ranking"].name)


def test_seleccion_son_las_ocho_regiones(S):
    sel = S["selection"]
    assert len(sel) == 16
    assert set(sel.loc[sel.selected.astype(bool), "name"]) == OCHO
    assert sel.set_index("name").loc["Valparaíso", "motivo"] == "ambas"
    assert set(sel.loc[sel.motivo == "tendencia", "name"]) == {"Arica y Parinacota", "Tarapacá"}
    assert set(sel.loc[sel.motivo == "brecha", "name"]) == {"La Araucanía", "Biobío", "Ñuble", "Coquimbo", "Los Ríos"}
    assert set(sel.loc[sel.motivo == "ninguna", "name"]) >= {"Maule", "Los Lagos", "Metropolitana"}


def test_cifras_de_la_brecha(S):
    g, sel = S["gap"], S["selection"]
    assert g.gap_people.sum() == pytest.approx(295330, abs=1)
    s8 = g.loc[g.name.isin(OCHO), "gap_people"].sum()
    assert s8 == pytest.approx(258197, abs=1)
    assert s8 / g.gap_people.sum() * 100 == pytest.approx(87.4, abs=0.05)
    pop = sel.pop_15_64.sum()
    assert sel.loc[sel.selected.astype(bool), "pop_15_64"].sum() / pop * 100 == pytest.approx(36.6, abs=0.1)
    esperado = {"La Araucanía": 67220, "Valparaíso": 53659, "Biobío": 34037, "Coquimbo": 33342, "Ñuble": 29346, "Los Ríos": 22315,
                "Los Lagos": 19099, "Maule": 18034, "Arica y Parinacota": 10346, "Tarapacá": 7932}
    for _, r in g.iterrows():
        assert r.gap_people == pytest.approx(esperado[r["name"]], abs=1), r["name"]
    assert [round(x * 100) for x in g.gap_cum_share[:6]] == [23, 41, 52, 64, 74, 81]
    assert g.gap_cum_share.iloc[5] >= 0.8 > g.gap_cum_share.iloc[4]   # Los Ríos cruza el 80 %


def test_las_tres_que_pierden_puestos(S):
    r = S["ranking"]
    bajo = r[r.below_chile.astype(bool)]
    assert len(bajo) == 9
    assert set(bajo.loc[bajo.places_lost > 0, "name"]) == {"Arica y Parinacota", "Tarapacá", "Valparaíso"}
    assert set(r.loc[r.by_trend.astype(bool), "name"]) == {"Arica y Parinacota", "Tarapacá", "Valparaíso"}
    d = r.set_index("name")
    for nombre, a, b in (("Maule", 11, 7), ("Los Lagos", 9, 8), ("Tarapacá", 7, 9), ("Valparaíso", 8, 10), ("Biobío y Ñuble", 12, 11), ("Coquimbo", 13, 12),
                         ("Arica y Parinacota", 10, 13), ("Los Ríos", 14, 14), ("La Araucanía", 15, 15)):
        assert (d.loc[nombre, "rank_start"], d.loc[nombre, "rank_end"]) == (a, b), nombre
    assert d.loc["Valparaíso", "change_pct"] > S["chile"].change_pct.iloc[0] and d.loc["Valparaíso", "change_pp"] < S["chile"].change_pp.iloc[0]


def test_chile(S):
    c = S["chile"].iloc[0]
    assert (round(c.cov_start, 1), round(c.cov_end, 1), round(c.change_pp, 1), round(c.change_pct, 1)) == (37.1, 46.5, 9.4, 25.3)


def test_descomposicion_suma_la_diferencia_y_las_etapas_100(S):
    d = S["decomposition"]
    assert set(d.name) == OCHO
    suma = d.participacion_pp + d.empleo_pp + d.cotizacion_pp
    assert (suma - d.total_pp).abs().max() < 0.01
    gente = {k: -d[f"{k}_people"].sum() for k in ("cotizacion", "participacion", "empleo")}
    tot = sum(gente.values())
    assert tot == pytest.approx(258198, abs=3)
    assert sum(v / tot * 100 for v in gente.values()) == pytest.approx(100, abs=1e-6)
    assert [round(gente[k] / tot * 100) for k in ("cotizacion", "participacion", "empleo")] == [70, 28, 2]
    assert gente["cotizacion"] == pytest.approx(179677, abs=2) and gente["participacion"] == pytest.approx(72268, abs=2) and gente["empleo"] == pytest.approx(6253, abs=2)
    a = d.set_index("name").loc["La Araucanía"]
    assert (round(a.participacion_level_chile, 1), round(a.participacion_level, 1), round(a.cotizacion_level_chile, 1), round(a.cotizacion_level, 1)) == (74.9, 71.5, 67.4, 56.0)
    assert (round(a.participacion_pp, 1), round(a.empleo_pp, 1), round(a.cotizacion_pp, 1), round(a.total_pp, 1)) == (-1.9, -0.4, -7.7, -10.0)
    mayor = d[["cotizacion_pp", "participacion_pp", "empleo_pp"]].idxmin(axis=1)
    assert (mayor == "cotizacion_pp").sum() == 7 and d.loc[mayor != "cotizacion_pp", "name"].tolist() == ["Biobío"]


def test_sensibilidad():
    ruta = DP / "kpi_seleccion_sensibilidad.csv"
    if not ruta.exists():
        pytest.skip("Falta kpi_seleccion_sensibilidad.csv")
    s = pd.read_csv(ruta)
    assert sorted(s.start_year.unique()) == list(range(2007, 2019)) and sorted(s.cutoff.unique()) == [0.7, 0.8, 0.9]
    base = s[(s.start_year == 2007) & (s.cutoff == 0.8)].iloc[0]
    assert base.n_regions == 8 and base.gap_share == pytest.approx(0.874, abs=0.0005)
    corte70 = s[(s.start_year == 2007) & (s.cutoff == 0.7)].iloc[0]
    assert corte70.n_regions == 7 and "Los Ríos" not in corte70.regions and corte70.gap_share == pytest.approx(0.80, abs=0.005)
    assert (s[s.start_year >= 2018].n_territories == 16).all() and (s[s.start_year < 2018].n_territories == 15).all()


def test_regla_en_un_caso_pequeno():
    """El corte incluye la región que cruza el umbral y la tendencia pasa de territorios a regiones (Biobío y Ñuble = dos regiones)."""
    m = _script()
    g = pd.DataFrame({"region_id": [1, 2, 3, 4], "acumulada": [0.5, 0.79, 0.81, 1.0]})
    assert m.entran_por_brecha(g, 0.8) == {1, 2, 3}
    r = pd.DataFrame({"territorio_id": [816, 5], "entra_tendencia": [True, False]})
    assert m.regiones_por_tendencia(r) == {8, 16}
