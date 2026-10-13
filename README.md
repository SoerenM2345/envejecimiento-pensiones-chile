# Envejecimiento demográfico y sostenibilidad de las pensiones

ICS100 — Herramientas de Análisis y Visualización de Datos · Proyecto de cierre, Desafío 1.

## Estructura

```
Proyecto/
├── Data raw/           # fuentes originales; ver Data raw/README.md (KPIs en _external/<tema>/, development sources/, archive/<KPI>/)
│   └── .venv/           # entorno Python del proyecto (ver Scripts/requirements.txt)
├── Data processed/      # todas las tablas limpias/agregadas + geo/ (GeoJSON) — ver README.md ahí
├── config/
│   └── kpis.yaml         # catálogo de KPIs: fórmula, fuente, grano, archivo, track del enunciado
├── Scripts/              # pipeline numerado 00→14, reproducible de punta a punta (ver abajo)
├── Dashboards/           # app Streamlit con dos modos: final (6 KPIs + problema) y desarrollador (todo el análisis)
├── Outputs/figures/      # gráficos exploratorios estáticos (validación, no el dashboard final)
├── docs/                 # GUIA_KPIs_DASHBOARD.md (cómo ver/reconstruir cada KPI), DATOS_ABIERTOS.md (lo que falta), PLAN_KPIs.md
└── tests/                # pruebas: páginas, tablas de los KPIs y recetas del modo manual (pytest)
```

## Archivos que NO están en GitHub

Por el límite de 100 MB de GitHub, estos archivos se excluyen (`.gitignore`) y hay que copiarlos a mano:

- `Data raw/personas_censo2024.csv` (2,3 GB) — microdatos Censo 2024, INE. Solo hace falta para re-correr `01_procesar_censo.py`; el dashboard funciona sin él (usa `Data processed/`).
- `.venv/` — se recrea con `python3 -m venv "Data raw/.venv" && "Data raw/.venv/bin/pip" install -r Scripts/requirements.txt`.
- Archivos DEIS (egresos/defunciones, `.zip`) — ver `docs/PLAN_KPIs.md` §0.

## Cómo correr el pipeline

```bash
cd "Data raw" && source .venv/bin/activate   # el venv ya tiene todo instalado

python3 ../Scripts/00_build_lookup.py                 # tabla región/comuna con tildes
python3 ../Scripts/01_procesar_censo.py                # censo -> indicadores por comuna/región (DuckDB, ~20s)
python3 ../Scripts/02_procesar_proyecciones.py         # proyecciones INE nacionales 1992-2070
python3 ../Scripts/03_procesar_cotizantes_afiliados.py # series Superintendencia de Pensiones
python3 ../Scripts/04_procesar_pensiones_pagadas.py    # pago de pensiones jul-2026 (c1/c2/c3)
python3 ../Scripts/05_graficos_exploratorios.py        # PNGs de validación
python3 ../Scripts/06_construir_mapas.py               # geojson comuna/región + indicadores
python3 ../Scripts/07_kpis_pension_salud.py            # cobertura previsional, proyección regional, índice de salud
python3 ../Scripts/08_ingresos_casen.py                # ingresos CASEN 2022 (extracto de terceros; development sources/)
python3 ../Scripts/10_procesar_piramide_alemania.py    # pirámide de Alemania (Destatis)
python3 ../Scripts/12_procesar_pilar_solidario.py      # PGU/PBS/APS 2008-2025 (KPI 2.1, 2.2)
python3 ../Scripts/13_procesar_macro_gasto.py          # PIB (Banco Central) y gasto en vejez (DIPRES) (KPI 2.1, 2.2)
python3 ../Scripts/14_procesar_casen_pobreza.py        # pobreza 65+ por región, CASEN 2022 completa (KPI 2.3)
python3 ../Scripts/17_procesar_series_superintendencia_extra.py  # cotizantes por tipo/sexo y por región x AFP, cotizaciones por AFP (modo dev)
python3 ../Scripts/16_procesar_dipres_activos_bonos.py # pasivos/activos del Gobierno Central y Bonos de Reconocimiento (DIPRES)
python3 ../Scripts/15_descargar_sp_ingreso_imponible.py # baja de spensiones.cl los meses que faltan del cuadro 04A (necesita internet; ya descargado)
python3 ../Scripts/18_kpi_punto_critico.py            # ingreso por trabajador, costo por persona de 65+ y reforma (punto crítico del KPI 1.2)
```

Todo se regenera desde `Data raw/` — `Data processed/` se puede borrar y reconstruir corriendo lo anterior en orden.

## Cómo correr el dashboard

```bash
cd Dashboards && source "../Data raw/.venv/bin/activate"
streamlit run Inicio.py
```

Abre `http://localhost:8501` (si el puerto está ocupado, Streamlit imprime la URL real en la terminal). Para detenerlo: `Ctrl+C`.

Si el entorno virtual no existe todavía: `python3 -m venv "Data raw/.venv" && "Data raw/.venv/bin/pip" install -r Scripts/requirements.txt`.

Sin activar el venv, en una sola línea desde la raíz del proyecto:

```bash
"Data raw/.venv/bin/streamlit" run Dashboards/Inicio.py --server.headless true
```

**Guía completa de los 6 KPIs** (dónde verlos, cómo reconstruirlos en el modo manual, qué datos faltan): [`docs/GUIA_KPIs_DASHBOARD.md`](docs/GUIA_KPIs_DASHBOARD.md).

**Dos modos:** por defecto abre el **modo final** (Resumen, Problema, Objetivo 1, Objetivo 2, Fuentes y método: los 6 KPIs de la presentación). Para ver las páginas exploratorias de abajo: la entrada **🛠️ Activar modo desarrollador** del menú, el interruptor «Modo desarrollador» del sidebar, o abrir `http://localhost:8501/?mode=dev`. Si el menú aún muestra una entrada «Inicio», es un servidor anterior: ciérralo (`lsof -ti :8501 | xargs kill`) y vuelve a abrirlo.

Páginas del modo desarrollador:

| Página | Qué responde |
|---|---|
| 🏠 Panorama general | La antigua página de inicio: ranking regional rápido |
| 🔍 Explorador de datos | "back end": cualquier archivo de `Data processed/`, con filtros dinámicos, cruce de dos fuentes, columna calculada (A ÷ B × factor) y agrupar/sumar por lo que sea |
| 🗺️ Mapas | *Mapas territoriales del envejecimiento* |
| 📊 Pirámides | *Construir pirámides demográficas y su evolución* |
| 💰 Pensiones y salud | *Proyectar la presión sobre salud y pensiones* |
| 🏙️ Socioeconómico | *Relacionar con variables socioeconómicas (ingresos, urbanización)* |
| 📋 Políticas | *Propuestas de políticas de envejecimiento activo* (segmentación basada en datos, no genérica) |
| 🧪 Estado de datos y KPIs | Estado de los 6 KPIs e inventario de archivos |

El **Panorama general** también responde *Identificar regiones y comunas con mayor envejecimiento* (ranking) y sirve de *Dashboard territorial* general.

## Estado por track del enunciado

| Track | Estado |
|---|---|
| Identificar regiones/comunas con mayor envejecimiento | ✅ completo — `indicadores_comuna.csv`/`indicadores_region.csv`, ranking en Inicio |
| Construir pirámides demográficas y su evolución | ✅ completo — nacional 1992-2070 + región/comuna 2024 |
| Mapas territoriales | ✅ completo (345/346 comunas; falta geometría de Antártica) |
| Variables socioeconómicas (ingresos, urbanización) | 🟡 parcial — urbanización 100% (Censo); ingreso vía CASEN 2022 (334/346 comunas, encuesta muestral, no censo) |
| Presión sobre salud y pensiones | 🟡 parcial — cobertura/razón de soporte previsional real; proyección regional y demanda de salud son **aproximaciones** (INE no publica proyección subnacional base 2024; no hay datos DEIS de uso real de salud) |
| Dashboard territorial | ✅ completo (Streamlit: 5 páginas en modo final y 8 en modo desarrollador) |
| Propuestas de envejecimiento activo | ✅ completo — 5 segmentos de comunas + propuestas regionales, todo trazable a los datos |

Detalle metodológico completo, fórmulas y limitaciones de cada indicador: `config/kpis.yaml` y `Data processed/README.md`.
