"""KPI 2.3: cifras de control de la pobreza 65+ (CASEN 2022) y estilo común de los gráficos."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Dashboards"))
from components.charts import estilo_kpi, poverty_bars, region_choropleth  # noqa: E402
from utils import INK_PRIMARY, load_geojson  # noqa: E402

P = pd.read_csv(ROOT / "Data processed" / "pobreza_65_region.csv")
NAC, REG = P[P.region_id == 0].iloc[0], P[P.region_id != 0].copy()


def test_cifras_de_control_pais():
    assert round(NAC.pct_pobreza_65, 1) == 14.9 and round(NAC.pct_pobreza_extrema_65, 1) == 4.9
    assert round(NAC.pob_65_expandida * NAC.pct_pobreza_65 / 100, -3) == 388_000      # «388 mil personas» de la lectura


def test_regiones_suman_el_pais():
    """Las 16 regiones deben cubrir la población 65+ y las personas en pobreza del país (un 17.º grupo faltante rompería esto)."""
    assert len(REG) == 16
    assert REG.pob_65_expandida.sum() == NAC.pob_65_expandida
    pobres = (REG.pob_65_expandida * REG.pct_pobreza_65 / 100).sum()
    assert abs(pobres / (NAC.pob_65_expandida * NAC.pct_pobreza_65 / 100) - 1) < 0.005


def test_graficos_con_estilo_comun_sin_error():
    """El mapa (sin textfont) y las barras pasan por estilo_kpi: texto negro, leyenda abajo, altura pedida."""
    figs = [poverty_bars(REG, NAC.pct_pobreza_65),
            region_choropleth(REG, load_geojson("regiones_chile.geojson"), "pct_pobreza_65", "% 65+ en pobreza", "Oranges")]
    for fig in figs:
        f = estilo_kpi(fig, 520)
        assert f.layout.height == 520 and f.layout.legend.orientation == "h"
        assert f.layout.title.font.color == INK_PRIMARY
