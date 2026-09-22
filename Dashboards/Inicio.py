import streamlit as st
from utils import load_csv, kpi_card_row, REGION_ORDER

st.set_page_config(
    page_title="Envejecimiento demográfico y pensiones — Chile",
    page_icon="👴",
    layout="wide",
)

st.title("Envejecimiento demográfico y sostenibilidad de las pensiones")
st.caption("Desafío 1 — Censo 2024, proyecciones INE, Superintendencia de Pensiones, CASEN 2022")

reg = load_csv("indicadores_region.csv")
proy = load_csv("proyeccion_envejecimiento_pais.csv")
pres = load_csv("kpi_presion_previsional_region.csv")

national_pct = 100 * reg["pob_65_mas"].sum() / reg["pob_total"].sum()
pct_2050 = proy.loc[proy.anio == 2050, "pct_65_mas"].iloc[0]
soporte_nacional = pres["cotizantes"].sum() / pres["pob_65_mas"].sum()
region_top = reg.sort_values("pct_65_mas", ascending=False).iloc[0]

kpi_card_row([
    ("Población 65+ (Censo 2024)", f"{national_pct:.1f}%", "Sobre 18.480.432 personas censadas"),
    ("Proyección 65+ a 2050", f"{pct_2050:.0f}%", "INE, proyecciones base 2024 (nacional)"),
    ("Cotizantes por adulto mayor", f"{soporte_nacional:.2f}", "Cotizantes AFP 2025 / población 65+ censada"),
    ("Región más envejecida", region_top["region_nombre"], f"{region_top['pct_65_mas']:.1f}% de 65+"),
])

st.divider()

col1, col2 = st.columns([3, 2])
with col1:
    st.subheader("Qué hay en este dashboard")
    st.markdown("""
- **🔍 Explorador de datos** — vista "backend": elige cualquier archivo procesado, filtra, agrupa y suma
  (por región, comuna, año, sexo…) y cruza hasta dos fuentes a la vez. Para explorar antes de decidir qué graficar.
- **🗺️ Mapas** — choropleth de envejecimiento por comuna y por región.
- **📊 Pirámides** — pirámide nacional (Censo 2024) y su evolución proyectada 1992–2070; comparador de pirámides por región.
- **💰 Pensiones y salud** — cobertura previsional, razón de soporte (cotizantes por adulto mayor), proyección regional 2024→2035→2050 y un índice de presión sobre salud.
- **🏙️ Socioeconómico** — cruce con urbanización (Censo) e ingresos (CASEN 2022); único proxy socioeconómico disponible, con sus limitaciones documentadas.
- **📋 Políticas** — propuestas de envejecimiento activo priorizadas por los propios datos (qué región/comuna necesita qué tipo de política).
    """)
with col2:
    st.subheader("Fuentes")
    st.markdown("""
| Fuente | Cobertura |
|---|---|
| Censo 2024 (INE) | 18.480.432 personas, 346 comunas |
| Proyecciones INE base 2024 | Nacional, 1992–2070 |
| Superintendencia de Pensiones | Cotizantes/afiliados 1985–2026; pago de pensiones jul-2026 |
| CASEN 2022 | Ingresos, muestra n=202.231, 334/346 comunas |
| chilemapas (geometría) | 345/346 comunas |
    """)
    st.caption("Ver `Data processed/README.md` y `config/kpis.yaml` para el detalle metodológico completo de cada indicador.")

st.divider()
st.subheader("Ranking regional rápido")
st.dataframe(
    reg.sort_values("pct_65_mas", ascending=False)[[
        "region_nombre", "pob_total", "pct_65_mas", "pct_0_14", "indice_envejecimiento",
        "indice_dependencia_vejez", "edad_mediana", "pct_urbano",
    ]].rename(columns={
        "region_nombre": "Región", "pob_total": "Población", "pct_65_mas": "% 65+",
        "pct_0_14": "% 0-14", "indice_envejecimiento": "Índice envejecimiento",
        "indice_dependencia_vejez": "Dependencia vejez", "edad_mediana": "Edad mediana",
        "pct_urbano": "% urbano",
    }),
    hide_index=True, use_container_width=True,
)
